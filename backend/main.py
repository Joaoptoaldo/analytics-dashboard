from sqlalchemy import func, distinct
import logging
def _build_overview_db(db):
    total = db.query(func.count(Product.id)).scalar() or 0
    total_revenue = db.query(func.sum(Product.revenue)).scalar() or 0.0
    total_customers = db.query(func.count(distinct(Product.client))).scalar() or 0
    completed_orders = db.query(func.count(Product.id)).filter(Product.status == "Completed").scalar() or 0
    conversion_rate = round((completed_orders / total) * 100, 2) if total else 0
    logging.info(f"[KPI][OVERVIEW] total: {total}, total_customers: {total_customers}, completed_orders: {completed_orders}")
    if total == 0:
        return {
            "total_revenue": None,
            "total_orders": None,
            "total_customers": None,
            "conversion_rate": None,
            "state": "no_data",
            "reason": "no_data"
        }
    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total,
        "total_customers": total_customers,
        "conversion_rate": conversion_rate,
        "revenue_change": 0.0,
        "orders_change": 0.0,
        "customers_change": 0.0,
        "conversion_change": 0.0,
        "state": "valid"
    }
def _build_sales_db(db):
    total = db.query(func.count(Product.id)).filter(Product.date != None).scalar() or 0
    if total == 0:
        logging.info(f"[KPI][SALES] Ignorados todos os registros: nenhum com date válido")
        return [{"state": "no_data", "month": None, "revenue": None, "orders": None, "customers": None, "reason": "no_valid_date"}]
    # Agrupar por mês (YYYY-MM)
    results = db.query(
        func.strftime('%Y-%m', Product.date).label('month'),
        func.sum(Product.revenue).label('revenue'),
        func.count(Product.id).label('orders'),
        func.count(distinct(Product.client)).label('customers')
    ).filter(Product.date != None)
    results = results.group_by('month').order_by('month').all()
    logging.info(f"[KPI][SALES] total válidos: {total}, meses: {len(results)}")
    return [
        {
            "month": r.month,
            "revenue": float(r.revenue),
            "orders": r.orders,
            "customers": r.customers
        }
        for r in results
    ]

# Distribuição por Categoria (count)
def _build_category_distribution_db(db):
    total = db.query(func.count(Product.id)).filter(Product.date != None).scalar() or 0
    if total == 0:
        logging.info(f"[KPI][CATEGORY_DIST] Nenhum registro com date válido")
        return [{"state": "no_data", "category": None, "count": None, "reason": "no_valid_date"}]
    results = db.query(
        Product.category,
        func.count(Product.id).label('count')
    ).filter(Product.date != None)
    results = results.group_by(Product.category).all()
    return [
        {
            "category": r.category,
            "count": r.count
        }
        for r in results
    ]

# Receita por Categoria (sum)
def _build_category_revenue_db(db):
    total = db.query(func.count(Product.id)).filter(Product.date != None).scalar() or 0
    if total == 0:
        logging.info(f"[KPI][CATEGORY_REVENUE] Nenhum registro com date válido")
        return [{"state": "no_data", "category": None, "revenue": None, "reason": "no_valid_date"}]
    results = db.query(
        Product.category,
        func.sum(Product.revenue).label('revenue')
    ).filter(Product.date != None)
    results = results.group_by(Product.category).all()
    return [
        {
            "category": r.category,
            "revenue": float(r.revenue)
        }
        for r in results
    ]
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Query
from backend.routers.products import router as products_router
from backend.routers.external import router as external_router
from backend.routers.analytics import router as analytics_router
from backend.db import init_db
from backend.routers.external_sync import router as external_sync_router
from backend.data import CATEGORIES, STATUSES
from backend.db import SessionLocal
from backend.models.product import Product
from backend.metrics_engine import get_total_revenue
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
from typing import Any
from backend.routers.products import router as products_router



app = FastAPI(title="Analytics Dashboard API", version="1.0.0")
app.include_router(products_router, prefix="/api")
app.include_router(external_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
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
    status: str = "all",
    search: str = "",
) -> list[dict[str, Any]]:
    filtered = [row for row in rows if row.get("date")]
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

    if status != "all":
        filtered = [row for row in filtered if row["status"] == status]

    if search:
        search_term = search.strip().lower()
        filtered = [
            row
            for row in filtered
            if search_term in row["client"].lower()
            or search_term in row["category"].lower()
        ]

    return filtered


def _build_overview(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """_summary_: método para calcular as métricas de visão geral a partir dos dados filtrados

    Args:
        rows (list[dict[str, Any]]): _description_: lista de dicionários representando os dados filtrados, onde cada dicionário contém informações sobre um pedido, como receita, cliente, categoria, região, status e data.

    Returns:
        dict[str, Any]: _description_
    """
    if not rows:
        return {
            "total_revenue": None,
            "total_orders": None,
            "total_customers": None,
            "conversion_rate": None,
            "state": "no_data"
        }
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
        "state": "valid"
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

    valid_rows = [row for row in rows if row.get("date")]
    if not valid_rows:
        return [{"state": "no_data", "month": None, "revenue": None, "orders": None, "customers": None}]
    for row in valid_rows:
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
    if region != "all":
        logging.warning("[DEPRECATED] region filter ignored")
    db = SessionLocal()
    try:
        return _build_overview_db(db)
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
    if region != "all":
        logging.warning("[DEPRECATED] region filter ignored")
    db = SessionLocal()
    try:
        return _build_sales_db(db)
    finally:
        db.close()




# Nova rota: Distribuição por Categoria
@app.get("/api/category-distribution")
async def get_category_distribution():
    db = SessionLocal()
    try:
        return _build_category_distribution_db(db)
    finally:
        db.close()

# Nova rota: Receita por Categoria
@app.get("/api/category-revenue")
async def get_category_revenue():
    db = SessionLocal()
    try:
        return _build_category_revenue_db(db)
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
        latest = db.query(Product).filter(Product.date != None).order_by(Product.date.desc()).limit(10).all()
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
