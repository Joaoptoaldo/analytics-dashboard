import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

from backend.db import SessionLocal
from backend.models.product import Product


DUMMYJSON_URL = "https://dummyjson.com/products?limit=100"


def fetch_external_products() -> List[Dict[str, Any]]:
    """Busca produtos do DummyJSON e normaliza para o formato usado pelo projeto.

    Retorna lista de dicts com chaves: id, client, category, revenue, status, region, date
    """
    resp = requests.get(DUMMYJSON_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    products = data.get("products", [])
    rng = random.Random(123)
    regions = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    statuses = ["Completed", "Processing", "Shipped", "Pending"]
    rows: List[Dict[str, Any]] = []
    # Gerar datas uniformemente distribuídas nos últimos 365 dias
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=365)
    days_range = (end_date - start_date).days
    for item in products:
        try:
            revenue = float(item.get("price", 0.0))
        except Exception:
            revenue = 0.0
        random_day = rng.randint(0, days_range)
        date_val = start_date + timedelta(days=random_day)
        rows.append({
            "id": int(item.get("id", 0)),
            "client": item.get("title", "")[:255],
            "category": item.get("category", "Other"),
            "revenue": revenue,
            "status": rng.choice(statuses),
            "region": rng.choice(regions),
            "date": date_val.strftime("%Y-%m-%d"),
        })
    return rows


def sync_external_products() -> int:
    """Busca produtos externos e persiste no banco (upsert por external_id).

    Retorna número de registros processados.
    """
    rows = fetch_external_products()
    db = SessionLocal()
    try:
        for r in rows:
            ext_id = int(r["id"])
            date_obj = datetime.strptime(r["date"], "%Y-%m-%d").date()
            prod = db.query(Product).filter_by(external_id=ext_id).first()
            if prod:
                prod.client = r["client"]
                prod.category = r["category"]
                prod.revenue = r["revenue"]
                prod.status = r["status"]
                prod.region = r["region"]
                prod.date = date_obj
            else:
                prod = Product(
                    external_id=ext_id,
                    client=r["client"],
                    category=r["category"],
                    revenue=r["revenue"],
                    status=r["status"],
                    region=r["region"],
                    date=date_obj,
                )
                db.add(prod)
        db.commit()
    finally:
        db.close()
    return len(rows)


def get_persisted_products() -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.date.desc()).all()
        return [p.to_dict() for p in products]
    finally:
        db.close()
