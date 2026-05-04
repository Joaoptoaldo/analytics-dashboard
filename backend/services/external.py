from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import os
import zlib
import logging
import requests

from ..db import SessionLocal
from ..models.product import Product

logger = logging.getLogger(__name__)


def _parse_iso_date(s: Optional[str]) -> Optional[datetime.date]:
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


def fetch_external_products() -> List[Dict[str, Any]]:
    """Busca produtos em serviços externos. Tenta Marketstack (se `MARKETSTACK_API_KEY` setado),
    caso contrário usa DummyJSON como fallback.
    Ao não encontrar data válida, atribui uma data histórica determinística dentro dos últimos 365 dias.
    """
    DUMMYJSON_URL = os.getenv("DUMMYJSON_URL", "https://dummyjson.com/products")
    api_key = os.getenv("MARKETSTACK_API_KEY")

    # Marketstack path (se houver api_key)
    if api_key:
        base = os.getenv("MARKETSTACK_BASE_URL", "https://api.marketstack.com/v1/eod")
        symbols = [s.strip().upper() for s in os.getenv("MARKETSTACK_SYMBOLS", "AAPL,MSFT,GOOGL").split(",") if s.strip()]
        # Prepare a deterministic fallback date per symbol within last 365 days
        today_date = datetime.now().date()
        rows: List[Dict[str, Any]] = []
        for sym in symbols:
            try:
                resp = requests.get(base, params={"access_key": api_key, "symbols": sym}, timeout=10)
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
                price = 0.0
                date_val = None

            ext_id = zlib.adler32(sym.encode("utf-8"))
            # If no date_val was extracted, create a deterministic historical date within the past year
            if not date_val:
                offset = int(ext_id) % 365
                date_val = today_date - timedelta(days=offset)

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
        return rows

    # Fallback: DummyJSON (comportamento legado)
    try:
        resp = requests.get(DUMMYJSON_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        products = data.get("products", [])
    except Exception as exc:
        logger.warning("[EXTERNAL] Erro ao consultar DummyJSON: %s", exc)
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

        if not date_val:
            # Deterministic fallback: use item id or index to assign a historical date within last 365 days
            try:
                key2 = int(item.get("id", idx)) if str(item.get("id", idx)).isdigit() else idx
            except Exception:
                key2 = idx
            offset = key2 % 365
            date_val = datetime.now().date() - timedelta(days=offset)
            logger.warning("[DATA_INTEGRITY] Produto id=%s sem campo 'date' válido. Atribuindo fallback date=%s", item.get('id', idx), date_val)

        # Mapeamento determinístico para status (não aleatório)
        key2 = int(item.get("id", idx)) if str(item.get("id", idx)).isdigit() else idx
        status = statuses[key2 % len(statuses)]

        rows.append(
            {
                "id": int(item.get("id", 0)),
                "client": (item.get("title") or "")[:255],
                "category": item.get("category", "Other"),
                "revenue": revenue,
                "status": status,
                "date": date_val.strftime("%Y-%m-%d") if date_val else None,
            }
        )
    return rows


def sync_external_products() -> int:
    """Sincroniza produtos externos no banco local por `external_id`.

    Returns:
        int: Quantidade de registros processados (inseridos ou atualizados).
    """
    rows = fetch_external_products()
    db = SessionLocal()
    try:
        for r in rows:
            ext_id = int(r["id"])
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
    """Retorna os produtos persistidos no banco local ordenados por data descrescente."""
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.date.desc()).all()
        return [p.to_dict() for p in products]
    finally:
        db.close()
