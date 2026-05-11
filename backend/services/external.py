from datetime import date as date_type, datetime, timedelta
from typing import Any, Dict, List, Optional
import os
import zlib
import logging
import requests

from sqlalchemy import func

from ..db import SessionLocal
from ..models.product import Product

logger = logging.getLogger(__name__)


RECENT_DATA_WINDOW_DAYS = 180


def _test_external_products() -> List[Dict[str, Any]]:
    """Deterministic fixtures for test/CI environments without external network access."""
    return [
        {
            "id": "1",
            "client": "Test Product 1",
            "category": "Test",
            "revenue": 10.0,
            "status": "Completed",
            "date": datetime.now().date().strftime("%Y-%m-%d"),
        },
        {
            "id": "2",
            "client": "Test Product 2",
            "category": "Test",
            "revenue": 20.0,
            "status": "Processing",
            "date": datetime.now().date().strftime("%Y-%m-%d"),
        },
    ]


def _as_date(value: object, fallback: Optional[datetime.date] = None) -> Optional[datetime.date]:
    if value is None:
        return fallback

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date_type):
        return value

    if hasattr(value, "date"):
        try:
            candidate = value.date()
        except Exception:
            return fallback

        if isinstance(candidate, datetime):
            return candidate.date()
        if isinstance(candidate, date_type):
            return candidate

    return fallback


def _parse_iso_date(s: Optional[str]) -> Optional[datetime.date]:
    """_summary_: tenta parsear uma string de data em formatos ISO comuns, retornando None se a string for vazia ou inválida

    Args:
        s (Optional[str]): _description_: string de data a ser parseada

    Returns:
        Optional[datetime.date]: _description_: um objeto datetime.date se o parse for bem-sucedido, ou None se a string for vazia ou inválida
    """
    if not s:
        return None
    try:
        # support multiple formats including ISO with Z
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        try:
            return datetime.strptime(s.split("T")[0], "%Y-%m-%d").date()
        except Exception:
            return None


def _get_reference_date() -> datetime.date:
    """_summary_: busca a data mais recente dos produtos não sintéticos no banco para usar como referência

    Returns:
        datetime.date: _description_: data mais recente dos produtos não sintéticos no banco ou data atual se não houver produtos ou em caso de erro
    """
    db = SessionLocal()
    try:
        reference = (
            db.query(func.max(Product.date))
            .filter(Product.is_synthetic == False)
            .scalar()
        )
        return reference or datetime.now().date()
    finally:
        db.close()


def _deterministic_recent_date(key: int, horizon_days: int = RECENT_DATA_WINDOW_DAYS, reference_date: Optional[datetime.date] = None) -> datetime.date:
    """_summary_: mapeia um inteiro (ex: id do produto) para uma data dentro de uma janela recente de forma determinística, garantindo que produtos sem data ou com data inválida sejam distribuídos ao longo dos últimos meses, evitando picos artificiais em datas específicas

    Args:
        key (int): _description_: um inteiro único relacionado ao produto (ex: id ou hash de algum atributo)
        horizon_days (int, optional): _description_. Defaults to RECENT_DATA_WINDOW_DAYS.
        reference_date (Optional[datetime.date], optional): _description_. Defaults to None.

    Returns:
        datetime.date: _description_: uma data dentro dos últimos `horizon_days` dias a partir de `reference_date` (ou data atual se não fornecida), mapeada de forma determinística a partir do `key`
    """
    anchor = reference_date or datetime.now().date()
    return anchor - timedelta(days=key % horizon_days)


def _normalize_recent_date(raw_date: Optional[datetime.date], key: int, reference_date: Optional[datetime.date] = None) -> datetime.date:
    """_summary_: normaliza uma data para garantir que esteja dentro de uma janela recente, usando um mapeamento determinístico para casos de datas ausentes ou inválidas, evitando distorções nos dados e garantindo uma distribuição mais realista das datas dos produtos

    Args:
        raw_date (Optional[datetime.date]): _description_: a data original extraída da fonte externa, que pode ser None ou inválida
        key (int): _description_: um inteiro único relacionado ao produto (ex: id ou hash de algum atributo), usado para gerar uma data determinística quando `raw_date` for ausente ou inválida
        reference_date (Optional[datetime.date], optional): _description_. Defaults to None.

    Returns:
        datetime.date: _description_: a data normalizada, que será igual a `raw_date` se esta for válida e recente, ou uma data determinística dentro dos últimos `RECENT_DATA_WINDOW_DAYS` dias caso contrário
    """
    anchor = _as_date(reference_date, datetime.now().date()) or datetime.now().date()
    raw_date = _as_date(raw_date)

    if raw_date is None:
        return _deterministic_recent_date(key, reference_date=anchor)

    cutoff = anchor - timedelta(days=RECENT_DATA_WINDOW_DAYS)
    if raw_date < cutoff or raw_date > anchor:
        return _deterministic_recent_date(key, reference_date=anchor)
    return raw_date


def fetch_external_products() -> List[Dict[str, Any]]:
    """_summary_: busca produtos de fontes externas (Marketstack se API key disponível, caso contrário DummyJSON), aplicando normalização de datas para garantir que estejam dentro de uma janela recente, e mapeando os dados para o formato esperado pela aplicação

    Returns:
        List[Dict[str, Any]]: _description_: uma lista de dicionários representando os produtos externos, com campos normalizados e prontos para serem persistidos no banco local
    """
    DUMMYJSON_URL = os.getenv("DUMMYJSON_URL", "https://dummyjson.com/products")
    api_key = os.getenv("MARKETSTACK_API_KEY")
    reference_date = _get_reference_date()

    if os.getenv("ENV", "").lower().strip() == "test":
        return _test_external_products()

    # Marketstack path (se houver api_key)
    if api_key:
        base = os.getenv("MARKETSTACK_BASE_URL", "https://api.marketstack.com/v1/eod")
        symbols = [s.strip().upper() for s in os.getenv("MARKETSTACK_SYMBOLS", "AAPL,MSFT,GOOGL").split(",") if s.strip()]
        rows: List[Dict[str, Any]] = []
        had_fetch_error = False
        # Prepare optional tracing headers
        try:
            from backend.logging_config import get_trace_id, get_span_id
            t_id = get_trace_id() or None
            s_id = get_span_id() or None
        except Exception:
            t_id = None
            s_id = None

        headers = {}
        if t_id:
            headers["X-Trace-Id"] = t_id
            headers["traceparent"] = f"00-{t_id}-{s_id or '0'*16}-01"

        for sym in symbols:
            try:
                resp = requests.get(base, params={"access_key": api_key, "symbols": sym}, timeout=10, headers=headers or None)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("data") or data.get("results") or []
                if items:
                    item = items[0]
                    price = float(item.get("close") or item.get("adj_close") or 0.0)
                    # Try to extract a date from the response if available
                    date_str = item.get("date") or item.get("trade_date") or None
                    date_val = _parse_iso_date(date_str)
                else:
                    price = 0.0
                    date_val = None
            except Exception as exc:
                logger.warning("[EXTERNAL] Erro ao consultar Marketstack para %s: %s", sym, exc)
                had_fetch_error = True
                price = 0.0
                date_val = None

            ext_id = zlib.adler32(sym.encode("utf-8"))
            # Force a recent deterministic date when the source is missing or too old
            date_val = _normalize_recent_date(date_val, int(ext_id), reference_date=reference_date)

            rows.append(
                {
                    "id": int(ext_id),
                    "client": sym,
                    "category": "Market",
                    "revenue": price,
                    "status": "Completed",
                    "date": date_val.strftime("%Y-%m-%d") if date_val else None,
                }
            )
        if had_fetch_error and not rows:
            raise RuntimeError("[EXTERNAL] Falha ao consultar Marketstack")
        return rows

    # Fallback: DummyJSON (comportamento legado)
    had_fetch_error = False
    try:
        # attach optional trace headers
        try:
            from backend.logging_config import get_trace_id, get_span_id
            t_id = get_trace_id() or None
            s_id = get_span_id() or None
        except Exception:
            t_id = None
            s_id = None
        headers = {}
        if t_id:
            headers["X-Trace-Id"] = t_id
            headers["traceparent"] = f"00-{t_id}-{s_id or '0'*16}-01"

        resp = requests.get(DUMMYJSON_URL, timeout=10, headers=headers or None)
        resp.raise_for_status()
        data = resp.json()
        products = data.get("products", [])
    except Exception as exc:
        logger.warning("[EXTERNAL] Erro ao consultar DummyJSON: %s", exc)
        had_fetch_error = True
        products = []

    statuses = ["Completed", "Processing", "Shipped", "Pending"]
    rows: List[Dict[str, Any]] = []
    for idx, item in enumerate(products):
        try:
            revenue = float(item.get("price", 0.0))
        except Exception:
            revenue = 0.0

        # Extrair data: meta.createdAt (primária) > date/createdAt/creation_date (fallback)
        date_str = None
        meta = item.get("meta", {}) or {}
        if meta and "createdAt" in meta:
            date_str = meta.get("createdAt")

        if not date_str:
            date_str = item.get("date") or item.get("createdAt") or item.get("creation_date")

        date_val = _parse_iso_date(date_str)

        try:
            key2 = int(item.get("id", idx)) if str(item.get("id", idx)).isdigit() else idx
        except Exception:
            key2 = idx

        normalized_date = _normalize_recent_date(date_val, key2, reference_date=reference_date)
        if date_val != normalized_date:
            logger.warning(
                "[DATA_INTEGRITY] Produto id=%s com data antiga/inválida. Normalizando para %s",
                item.get('id', idx),
                normalized_date,
            )
        date_val = normalized_date

        # Mapeamento determinístico para status (não aleatório)
        status = statuses[key2 % len(statuses)]

        rows.append(
            {
                "id": str(int(item.get("id", 0))),
                "client": (item.get("title") or "")[:255],
                "category": item.get("category", "Other"),
                "revenue": revenue,
                "status": status,
                "date": date_val.strftime("%Y-%m-%d") if date_val else None,
            }
        )
    if had_fetch_error and not rows:
        raise RuntimeError("[EXTERNAL] Falha ao consultar DummyJSON")
    return rows


def sync_external_products() -> int:
    """_summary_: sincroniza os produtos externos com o banco local, buscando os dados de fontes externas, normalizando as datas, e persistindo as informações no banco, atualizando produtos existentes ou criando novos registros conforme necessário

    Returns:
        int: _description_: o número de produtos processados/sincronizados
    """
    rows = fetch_external_products()
    db = SessionLocal()
    try:
        for r in rows:
            ext_id = str(int(r["id"]))
            date_obj = None
            if r.get("date"):
                try:
                    date_obj = datetime.strptime(r["date"], "%Y-%m-%d").date()
                except Exception:
                    date_obj = None
            prod = db.query(Product).filter_by(external_id=ext_id).first()
            if prod:
                prod.client = r["client"]
                prod.category = r["category"]
                prod.revenue = r["revenue"]
                prod.status = r["status"]
                prod.date = date_obj
            else:
                prod = Product(
                    external_id=ext_id,
                    client=r["client"],
                    category=r["category"],
                    revenue=r["revenue"],
                    status=r["status"],
                    date=date_obj,
                )
                db.add(prod)
        db.commit()
    finally:
        db.close()
    return len(rows)


def get_persisted_products() -> List[Dict[str, Any]]:
    """_summary_: busca os produtos persistidos no banco local, retornando uma lista de dicionários representando os produtos, para serem consumidos pela API ou outras partes da aplicação

    Returns:
        List[Dict[str, Any]]: _description_: uma lista de dicionários representando os produtos persistidos no banco local, com campos convertidos para tipos nativos (ex: date para string) e prontos para consumo
    """
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.date.desc()).all()
        return [p.to_dict() for p in products]
    finally:
        db.close()
