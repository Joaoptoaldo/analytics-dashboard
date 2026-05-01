import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta


from backend.db import SessionLocal
from backend.models.product import Product


DUMMYJSON_URL = "https://dummyjson.com/products?limit=100"


def fetch_external_products() -> List[Dict[str, Any]]:
    """_summary_: método para buscar produtos de uma API externa (DummyJSON), processar os dados e retornar uma lista de dicionários com os campos necessários para persistência no banco.

    Returns:
        List[Dict[str, Any]]: _description_: lista de dicionários representando os produtos, onde cada dicionário contém os campos id, client, category, revenue, status e date. O campo date é extraído do campo meta.createdAt ou de outros campos de data disponíveis, e é convertido para o formato YYYY-MM-DD. O status é mapeado de forma determinística com base no id do produto. Se a API externa não fornecer um campo de data válido, o campo date será None.
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
                normalized = date_str.replace('Z', '+00:00')
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
    """_summary_: método para sincronizar os produtos da API externa com o banco de dados local. Ele busca os produtos usando fetch_external_products(), e para cada produto, verifica se já existe um registro com o mesmo external_id. Se existir, atualiza os campos client, category, revenue, status e date. Se não existir, cria um novo registro. Ao final, retorna o número total de produtos processados (inseridos ou atualizados)

    Returns:
        int: _description_: número total de produtos processados (inseridos ou atualizados) no banco de dados após a sincronização com a API externa. Se ocorrer algum erro durante o processo, o método deve lançar uma exceção apropriada.
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
    """_summary_: método para buscar os produtos persistidos no banco de dados local, retornando uma lista de dicionários com os campos id, client, category, revenue, status e date. O campo date é formatado como string no formato YYYY-MM-DD. Este método é útil para verificar os dados que foram sincronizados a partir da API externa e estão disponíveis para consulta no banco de dados local.

    Returns:
        List[Dict[str, Any]]: _description_: lista de produtos persistidos no banco de dados local
    """
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.date.desc()).all()
        return [p.to_dict() for p in products]
    finally:
        db.close()
