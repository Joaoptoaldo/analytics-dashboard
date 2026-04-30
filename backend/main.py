from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Query
from backend.routers.products import router as products_router
from backend.routers.external import router as external_router
from backend.db import init_db
from backend.routers.external_sync import router as external_sync_router
from backend.data import CATEGORIES, REGIONS, STATUSES
from backend.db import SessionLocal
from backend.models.product import Product
from backend.metrics_engine import get_total_revenue
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
import random
from typing import Any
from backend.routers.products import router as products_router



app = FastAPI(title="Analytics Dashboard API", version="1.0.0")
app.include_router(products_router, prefix="/api")
app.include_router(external_router, prefix="/api")
app.include_router(external_sync_router, prefix="/api")


init_db()

# CORS config
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## Dados e constantes agora em backend.data


def _apply_filters(
    rows: list[dict[str, Any]],
    period: str = "all",
    category: str = "all",
    region: str = "all",
    status: str = "all",
    search: str = "",
) -> list[dict[str, Any]]:
    filtered = rows
    now = datetime.now()

    if period != "all":
        days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
        days = days_map.get(period, 365)
        min_date = now - timedelta(days=days)
        filtered = [
            row
            for row in filtered
            if datetime.strptime(row["date"], "%Y-%m-%d") >= min_date
        ]

    if category != "all":
        filtered = [row for row in filtered if row["category"] == category]

    if region != "all":
        filtered = [row for row in filtered if row["region"] == region]

    if status != "all":
        filtered = [row for row in filtered if row["status"] == status]

    if search:
        search_term = search.strip().lower()
        filtered = [
            row
            for row in filtered
            if search_term in row["client"].lower()
            or search_term in row["category"].lower()
            or search_term in row["region"].lower()
        ]

    return filtered


def _build_overview(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """_summary_: método para calcular as métricas de visão geral a partir dos dados filtrados

    Args:
        rows (list[dict[str, Any]]): _description_: lista de dicionários representando os dados filtrados, onde cada dicionário contém informações sobre um pedido, como receita, cliente, categoria, região, status e data.

    Returns:
        dict[str, Any]: _description_
    """
    total_revenue = round(sum(item["revenue"] for item in rows), 2)
    total_orders = len(rows)
    customers = {item["client"] for item in rows}
    total_customers = len(customers)
    completed_orders = sum(1 for item in rows if item["status"] == "Completed")
    conversion_rate = round((completed_orders / total_orders) * 100, 2) if total_orders else 0

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "conversion_rate": conversion_rate,
        "revenue_change": 0.0,  # TODO: Implementar cálculo real vs período anterior
        "orders_change": 0.0,
        "customers_change": 0.0,
        "conversion_change": 0.0,
    }


def _build_sales(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """_summary_: método para calcular as métricas de vendas ao longo do tempo a partir dos dados filtrados, agrupando por mês e calculando receita total, número de pedidos e clientes únicos para cada mês.

    Args:
        rows (list[dict[str, Any]]): _description_: lista de dicionários representando os dados filtrados, onde cada dicionário contém informações sobre um pedido, como receita, cliente, categoria, região, status e data.

    Returns:
        list[dict[str, Any]]: _description_: lista de dicionários representando as métricas de vendas ao longo do tempo
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    today = datetime.now()
    month_keys = []
    for i in range(11, -1, -1):
        d = today - relativedelta(months=i)
        month_keys.append(d.strftime("%b %Y"))

    month_data: dict[str, dict[str, Any]] = {
        m: {"month": m, "revenue": 0.0, "orders": 0, "customers_set": set()} for m in month_keys
    }

    for row in rows:
        dt = datetime.strptime(row["date"], "%Y-%m-%d")
        month_key = dt.strftime("%b %Y")
        if month_key in month_data:
            month_data[month_key]["revenue"] += row["revenue"]
            month_data[month_key]["orders"] += 1
            month_data[month_key]["customers_set"].add(row["client"])

    return [
        {
            "month": key,
            "revenue": round(month_data[key]["revenue"], 2),
            "orders": month_data[key]["orders"],
            "customers": len(month_data[key]["customers_set"]),
        }
        for key in month_keys
    ]


def _build_traffic(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """_summary_: método para calcular as métricas de tráfego por região a partir dos dados filtrados, contando o número de pedidos por região e calculando a porcentagem de cada região em relação ao total.

    Args:
        rows (list[dict[str, Any]]): _description_: lista de dicionários representando os dados filtrados, onde cada dicionário contém informações sobre um pedido, como receita, cliente, categoria, região, status e data.

    Returns:
        list[dict[str, Any]]: _description_: lista de dicionários representando as métricas de tráfego por região
    """
    region_counts = {region: 0 for region in REGIONS}
    for row in rows:
        region_counts[row["region"]] += 1

    total = sum(region_counts.values()) or 1
    return [
        {
            "source": region,
            "visitors": count * 120,
            "percentage": round((count / total) * 100, 1),
        }
        for region, count in region_counts.items()
    ]


@app.get("/")
async def root():
    return {"message": "Analytics Dashboard API", "version": "1.0.0"}



@app.get("/api/overview")
async def get_overview(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
):
    db = SessionLocal()
    try:
        from sqlalchemy import or_
        from datetime import datetime, timedelta
        query = db.query(Product)
        if period != "all":
            days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
            days = days_map.get(period, 365)
            min_date = datetime.now().date() - timedelta(days=days)
            query = query.filter(Product.date >= min_date)
        if category != "all":
            query = query.filter(Product.category == category)
        if region != "all":
            query = query.filter(Product.region == region)
        if status != "all":
            query = query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Product.client.ilike(search_term),
                    Product.category.ilike(search_term),
                    Product.region.ilike(search_term),
                )
            )
        rows = [p.to_dict() for p in query.all()]
        return _build_overview(rows)
    finally:
        db.close()



@app.get("/api/sales")
async def get_sales(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
):
    db = SessionLocal()
    try:
        from sqlalchemy import or_
        from datetime import datetime, timedelta
        query = db.query(Product)
        if period != "all":
            days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
            days = days_map.get(period, 365)
            min_date = datetime.now().date() - timedelta(days=days)
            query = query.filter(Product.date >= min_date)
        if category != "all":
            query = query.filter(Product.category == category)
        if region != "all":
            query = query.filter(Product.region == region)
        if status != "all":
            query = query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Product.client.ilike(search_term),
                    Product.category.ilike(search_term),
                    Product.region.ilike(search_term),
                )
            )
        rows = [p.to_dict() for p in query.all()]
        return _build_sales(rows)
    finally:
        db.close()



@app.get("/api/traffic")
async def get_traffic(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
):
    db = SessionLocal()
    try:
        from sqlalchemy import or_
        from datetime import datetime, timedelta
        query = db.query(Product)
        if period != "all":
            days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
            days = days_map.get(period, 365)
            min_date = datetime.now().date() - timedelta(days=days)
            query = query.filter(Product.date >= min_date)
        if category != "all":
            query = query.filter(Product.category == category)
        if region != "all":
            query = query.filter(Product.region == region)
        if status != "all":
            query = query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Product.client.ilike(search_term),
                    Product.category.ilike(search_term),
                    Product.region.ilike(search_term),
                )
            )
        rows = [p.to_dict() for p in query.all()]
        return _build_traffic(rows)
    finally:
        db.close()




@app.get("/api/filters")
async def get_filters():
    return {
        "periods": [
            {"value": "all", "label": "Tudo"},
            {"value": "30d", "label": "30 dias"},
            {"value": "90d", "label": "90 dias"},
            {"value": "180d", "label": "180 dias"},
            {"value": "365d", "label": "1 ano"},
        ],
        "categories": CATEGORIES,
        "regions": REGIONS,
        "statuses": STATUSES,
    }


@app.get("/api/activity")
async def get_activity():
    # Mock temporário removendo a aleatoriedade pura para consistência
    return [{"hour": f"{h:02d}:00", "active_users": 0} for h in range(24)]


@app.get("/api/recent-orders")
async def get_recent_orders():
    db = SessionLocal()
    try:
        latest = db.query(Product).order_by(Product.date.desc()).limit(10).all()
        return [
            {
                "id": f"ORD-{item.id:05d}",
                "customer": item.client,
                "amount": item.revenue,
                "status": item.status,
                "date": str(item.date),
            }
            for item in latest
        ]
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
