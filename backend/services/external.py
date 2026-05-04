from datetime import datetime
from typing import Any, Dict, List
import os
import zlib
import logging

import requests

from backend.db import SessionLocal
from backend.models.product import Product

logger = logging.getLogger(__name__)

DUMMYJSON_URL = "https://dummyjson.com/products?limit=100"


def _parse_iso_date(date_str: str):
    if not date_str:
        return None
    try:
        normalized = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).date()
    except Exception:
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except Exception:
            return None


def fetch_external_products() -> List[Dict[str, Any]]:
    """Busca dados de mercado via Marketstack quando a chave estiver configurada.

    Se `MARKETSTACK_API_KEY` estiver ausente, mantém o comportamento anterior (DummyJSON).
    Retorna lista de dicionários com `id` (int), `client` (str), `category` (str),
    `revenue` (float), `status` (str) e `date` (YYYY-MM-DD | None).
    """
    api_key = os.getenv("MARKETSTACK_API_KEY", "").strip()
    if api_key:
        # Use HTTPS by default for Marketstack base URL
        base = os.getenv("MARKETSTACK_BASE_URL", "https://api.marketstack.com/v1/eod")
        symbols = [s.strip().upper() for s in os.getenv("MARKETSTACK_SYMBOLS", "AAPL,MSFT,GOOGL").split(",") if s.strip()]
        today = datetime.now().date().strftime("%Y-%m-%d")  # Use data de hoje para Marketstack
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
                    date_str = today
                else:
                    price = 0.0
                    date_str = today
            except Exception as exc:
                logger.warning("[EXTERNAL] Erro ao consultar Marketstack para %s: %s", sym, exc)
                price = 0.0

            ext_id = zlib.adler32(sym.encode("utf-8"))
            rows.append(
                {
                    "id": int(ext_id),
                    "client": sym,
                    "category": "Market",
                    "revenue": price,
                    "status": "Completed",
                    "date": date_str,
                }
            )
        return rows

    # Fallback: DummyJSON (comportamento legado)
    resp = requests.get(DUMMYJSON_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    products = data.get("products", [])
    statuses = ["Completed", "Processing", "Shipped", "Pending"]
    rows: List[Dict[str, Any]] = []
    for idx, item in enumerate(products):
        try:
            revenue = float(item.get("price", 0.0))
        except Exception:
            revenue = 0.0

        # Extrair data: meta.createdAt (primária) > date/createdAt/creation_date (fallback)
        date_str = None

        # Tentar meta.createdAt primeiro (fonte primária: DummyJSON)
        meta = item.get("meta", {})
        if meta and "createdAt" in meta:
            date_str = meta.get("createdAt")

        # Fallback para campos top-level (compatibilidade com outras APIs)
        if not date_str:
            date_str = item.get("date") or item.get("createdAt") or item.get("creation_date")

        date_val = _parse_iso_date(date_str)

        if not date_val:
            # Log estruturado para rastreabilidade
            logger.warning("[DATA_INTEGRITY] Produto id=%s sem campo 'date' válido. meta.createdAt=%s", item.get('id', idx), meta.get('createdAt'))

        # Mapeamento determinístico para status (não aleatório)
        key2 = int(item.get("id", idx)) if str(item.get("id", idx)).isdigit() else idx
        status = statuses[key2 % len(statuses)]

        rows.append(
            {
                "id": int(item.get("id", 0)),
                "client": item.get("title", "")[:255],
                "category": item.get("category", "Other"),
                "revenue": revenue,
                "status": status,
                "date": date_val.strftime("%Y-%m-%d") if date_val else None,
            }
        )
    return rows


def sync_external_products() -> int:
    """_summary_: Sincroniza produtos externos no banco local por `external_id`.

    Returns:
        int: _description_: Quantidade de registros processados (inseridos ou atualizados).
    """
    rows = fetch_external_products()
    db = SessionLocal()
    try:
        for r in rows:
            ext_id = int(r["id"])
            date_obj = None
            if r["date"]:
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
    """_summary_: Retorna os produtos persistidos no banco local ordenados por data descrescente.

    Returns:
        List[Dict[str, Any]]: _description_: Lista de produtos no formato de `Product.to_dict()`.
    """
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.date.desc()).all()
        return [p.to_dict() for p in products]
    finally:
        db.close()
