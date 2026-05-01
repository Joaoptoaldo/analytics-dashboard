import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta


from backend.db import SessionLocal
from backend.models.product import Product


DUMMYJSON_URL = "https://dummyjson.com/products?limit=100"


def fetch_external_products() -> List[Dict[str, Any]]:
    """Busca produtos do DummyJSON e normaliza para o formato usado pelo projeto.

    Retorna lista de dicts com chaves: id, client, category, revenue, status, date
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

        # Preferir campo de data da API se existir (ex.: 'date', 'createdAt')
        date_str = item.get("date") or item.get("createdAt") or item.get("creation_date")
        if date_str:
            try:
                # aceitar formatos ISO simples
                date_val = datetime.fromisoformat(date_str).date()
            except Exception:
                # fallback para string YYYY-MM-DD
                try:
                    date_val = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                except Exception:
                    date_val = None
        else:
            date_val = None
            # Log estruturado para rastreabilidade
            print(f"[DATA_INTEGRITY][WARN] Produto id={item.get('id', idx)} sem campo 'date' na API externa. Persistindo como NULL.")

        # Mapeamento determinístico para status (não aleatório)
        key2 = int(item.get("id", idx)) if str(item.get("id", idx)).isdigit() else idx
        status = statuses[key2 % len(statuses)]

        rows.append({
            "id": int(item.get("id", 0)),
            "client": item.get("title", "")[:255],
            "category": item.get("category", "Other"),
            "revenue": revenue,
            "status": status,
            "date": date_val.strftime("%Y-%m-%d") if date_val else None,
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
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.date.desc()).all()
        return [p.to_dict() for p in products]
    finally:
        db.close()
