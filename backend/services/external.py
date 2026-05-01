from datetime import datetime
from typing import Any, Dict, List

import requests

from backend.db import SessionLocal
from backend.models.product import Product

DUMMYJSON_URL = "https://dummyjson.com/products?limit=100"


def fetch_external_products() -> List[Dict[str, Any]]:
    """_summary_: Busca produtos na API externa e normaliza os campos para o formato interno.

    Returns:
        List[Dict[str, Any]]: _description_: Lista de dicionários com `id`, `client`, `category`, `revenue`, `status` e `date` (formato `YYYY-MM-DD` ou `None`).
    """
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

        date_val = None
        if date_str:
            try:
                # Aceitar formatos ISO 8601 completos (ex: 2025-04-30T09:41:02.053Z)
                # Replace 'Z' com '+00:00' para compatibilidade com fromisoformat
                normalized = date_str.replace("Z", "+00:00")
                date_val = datetime.fromisoformat(normalized).date()
            except Exception:
                # Fallback para string YYYY-MM-DD
                try:
                    date_val = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                except Exception:
                    date_val = None

        if not date_val:
            # Log estruturado para rastreabilidade
            print(f"[DATA_INTEGRITY][WARN] Produto id={item.get('id', idx)} sem campo 'date' válido. meta.createdAt={meta.get('createdAt')}")

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
