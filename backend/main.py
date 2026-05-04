from datetime import datetime, timedelta

import logging
import os
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import distinct, func, or_

# IMPORTANTE: Importar config validado PRIMEIRO
# Isso vai falhar se variáveis de ambiente estiverem inválidas (fail-fast)
from backend.config import CORS_ORIGINS, EXTERNAL_SYNC_TOKEN, IS_PRODUCTION

from backend.data import CATEGORIES, STATUSES
from backend.db import SessionLocal, init_db
from backend.metrics_engine import get_total_revenue
from backend.models.product import Product
from backend.routers.analytics import router as analytics_router
from backend.routers.external import router as external_router
from backend.routers.external_sync import router as external_sync_router
from backend.routers.products import router as products_router
from fastapi import FastAPI, Query
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.requests import Request


load_dotenv()


app = FastAPI(title="Analytics Dashboard API", version="1.0.0")
app.include_router(products_router, prefix="/api")
app.include_router(external_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
# Rota de sincronização externa movida para prefixo /internal para uso backend-only
# Evita exposição direta para frontends sem o token apropriado
app.include_router(external_sync_router, prefix="/internal")


init_db()


class CustomCORSMiddleware(BaseHTTPMiddleware):
    """Middleware customizado para CORS que adiciona headers manualmente"""
    def __init__(self, app, allow_origins=None, allow_credentials=False):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        logging.info(f"[CORS] CustomCORSMiddleware initializado com allow_origins={self.allow_origins}, allow_credentials={self.allow_credentials}")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Handle preflight requests (OPTIONS)
        if request.method == "OPTIONS":
            origin = request.headers.get("origin", "*")
            if "*" in self.allow_origins or origin in self.allow_origins:
                return Response(
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, x-internal-token",
                        "Access-Control-Allow-Credentials": "true" if self.allow_credentials else "false",
                        "Access-Control-Max-Age": "3600",
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        origin = request.headers.get("origin", "*")
        if "*" in self.allow_origins or origin in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, x-internal-token"
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
# Quando origins=['*'], credentials DEVE ser False (padrão CORS)
allow_credentials = False  # Hardcoded for dev
logging.info(f"[CORS] Loaded CORS_ORIGINS={cors_origins_env}, parsed={cors_origins}, allow_credentials={allow_credentials}")

app.add_middleware(
    CustomCORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
)


# Global error handlers (fail-safe, don't expose internals)
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with safe error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "state": "error",
            "reason": exc.detail if isinstance(exc.detail, str) else "http_error",
            "data": []
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with generic safe message (don't expose stack trace)"""
    logging.error(f"[ERROR] Unhandled exception: {exc.__class__.__name__}", exc_info=False)
    return JSONResponse(
        status_code=500,
        content={
            "state": "error",
            "reason": "internal_server_error",
            "data": []
        }
    )


# Endpoint de teste para diagnosticar CORS
@app.get("/api/test-cors")
def test_cors():
    return {"message": "CORS is working!"}


# Health check endpoints for production (Fly.io)
@app.get("/health")
def health_check():
    """Liveness probe: service is running"""
    return {"status": "ok", "service": "dashboard-backend"}


@app.get("/readiness")
def readiness_check():
    """Readiness probe: service is ready to accept traffic (DB connection verified)"""
    try:
        db = SessionLocal()
        # Simple query to verify DB connection
        db.query(Product).limit(1).all()
        db.close()
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        logging.error(f"[READINESS] Database connection failed: {e.__class__.__name__}", exc_info=False)
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "failed", "reason": "db_connection_error"}
        )


def _get_period_reference_date(db):
    """_summary_: Obtém a data de referência para o cálculo do período, que é a data mais recente presente no banco de dados. Se não houver registros com data válida, retorna a data atual. Essa função é útil para garantir que os cálculos de período sejam baseados na data mais recente disponível nos dados, proporcionando uma referência consistente para filtros de período como "30d", "90d", etc.

    Args:
        db (_type_): _description_: Instância do banco de dados.

    Returns:
        _type_: _description_: Data de referência para o cálculo do período, que é a data mais recente presente no banco de dados ou a data atual se não houver registros com data válida.
    """
    latest_date = db.query(func.max(Product.date)).scalar()
    if latest_date is not None:
        return latest_date
    return datetime.now().date()
def _apply_db_filters(query, period, category, status, search):
    """_summary_: Aplica os filtros de período, categoria, status e busca textual em uma consulta do SQLAlchemy, retornando a consulta filtrada. O filtro de período restringe os produtos com base na data, o filtro de categoria restringe os produtos a uma categoria específica, o filtro de status restringe os produtos a um status específico, e o filtro de busca textual permite filtrar os produtos com base em uma correspondência parcial no nome do cliente ou na categoria. A função é útil para refinar os resultados exibidos para o usuário com base em suas preferências e necessidades específicas, garantindo que a lógica de filtragem seja centralizada e reutilizável em diferentes partes do código que realizam consultas ao banco de dados.

    Args:
        query (_type_): _description_: Consulta do SQLAlchemy que será filtrada com base nos critérios especificados.
        period (_type_): _description_: Filtro de período,
        category (_type_): _description_: Filtro de categoria,
        status (_type_): _description_: Filtro de status,
        search (_type_): _description_: Filtro de busca textual.


    Returns:
        _type_: _description_: Consulta do SQLAlchemy filtrada com base nos critérios especificados.
    """
    # Always exclude synthetic (test) data by default
    query = query.filter(Product.is_synthetic == False)
    
    if period != "all":
        days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
        days = days_map.get(period, 365)
        reference_date = _get_period_reference_date(query.session)
        min_date = reference_date - timedelta(days=days)
        query = query.filter(Product.date >= min_date)
    
    if category != "all":
        query = query.filter(Product.category == category)
        
    if status != "all":
        query = query.filter(Product.status == status)
        
    if search:
        search_term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                Product.client.ilike(search_term),
                Product.category.ilike(search_term)
            )
        )
    return query


def _calculate_overview_metrics(query):
    total = query.with_entities(func.count(Product.id)).scalar() or 0
    total_revenue = query.with_entities(func.sum(Product.revenue)).scalar() or 0.0
    total_customers = query.with_entities(func.count(distinct(Product.client))).scalar() or 0
    completed_orders = query.filter(Product.status == "Completed").with_entities(func.count(Product.id)).scalar() or 0
    conversion_rate = round((completed_orders / total) * 100, 2) if total else 0
    return {
        "total": total,
        "total_revenue": float(total_revenue or 0.0),
        "total_customers": total_customers,
        "completed_orders": completed_orders,
        "conversion_rate": conversion_rate,
    }


def _percentage_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None if current == 0 else 100.0
    return round(((current - previous) / abs(previous)) * 100, 2)

def _build_overview_db(db, period="all", category="all", status="all", search=""):
    """_summary_: Calcula metricas de overview a partir de dados do banco de dados, onde a resposta inclui o valor total da receita, número total de pedidos, número total de clientes únicos e taxa de conversão, além de metadados como estado da resposta e razão para casos de ausência de dados. O endpoint é útil para fornecer uma visão geral do desempenho do negócio com base nos dados disponíveis, permitindo que os usuários avaliem rapidamente as métricas-chave e identifiquem áreas que podem exigir atenção ou melhoria.

    Args:
        db (_type_): _description_
        period (str, optional): _description_. Defaults to "all".
        category (str, optional): _description_. Defaults to "all".
        status (str, optional): _description_. Defaults to "all".
        search (str, optional): _description_. Defaults to "".

    Returns:
        _type_: _description_: Dicionário contendo as métricas de overview, onde os campos "total_revenue", "total_orders", "total_customers" e "conversion_rate" representam as métricas calculadas a partir dos dados do banco de dados, e os campos "state" e "reason" fornecem informações sobre o estado da resposta e a razão para casos de ausência de dados, garantindo que o endpoint seja informativo e robusto mesmo quando não houver registros válidos para calcular as métricas de overview.
    """
    base_query = db.query(Product)
    filtered_query = _apply_db_filters(base_query, period, category, status, search)

    current_metrics = _calculate_overview_metrics(filtered_query)
    total = current_metrics["total"]
    total_revenue = current_metrics["total_revenue"]
    total_customers = current_metrics["total_customers"]
    completed_orders = current_metrics["completed_orders"]
    conversion_rate = current_metrics["conversion_rate"]
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

    previous_metrics = None
    days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
    if period in days_map:
        reference_date = _get_period_reference_date(db)
        current_start = reference_date - timedelta(days=days_map[period] - 1)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days_map[period] - 1)
        previous_query = db.query(Product).filter(Product.date != None)
        previous_query = previous_query.filter(Product.date >= previous_start, Product.date <= previous_end)
        previous_query = _apply_db_filters(previous_query, "all", category, status, search)
        previous_metrics = _calculate_overview_metrics(previous_query)

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total,
        "total_customers": total_customers,
        "conversion_rate": conversion_rate,
        "revenue_change": _percentage_change(total_revenue, previous_metrics["total_revenue"]) if previous_metrics else None,
        "orders_change": _percentage_change(total, previous_metrics["total"]) if previous_metrics else None,
        "customers_change": _percentage_change(total_customers, previous_metrics["total_customers"]) if previous_metrics else None,
        "conversion_change": _percentage_change(conversion_rate, previous_metrics["conversion_rate"]) if previous_metrics else None,
        "state": "valid"
    }
def _build_sales_db(db, period="all", category="all", status="all", search=""):
    """_summary_: Calcula série mensal de vendas a partir de dados do banco de dados, onde a resposta inclui uma lista de meses com a receita total e o número de pedidos em cada mês, além de metadados como estado da resposta e razão para casos de erro ou ausência de dados. O endpoint é útil para avaliar o desempenho de vendas ao longo do tempo e identificar padrões sazonais ou tendências de crescimento ou declínio.

    Args:
        db (_type_): _description_
        period (str, optional): _description_. Defaults to "all".
        category (str, optional): _description_. Defaults to "all".
        status (str, optional): _description_. Defaults to "all".
        search (str, optional): _description_. Defaults to "".

    Returns:
        _type_: _description_: Lista de dicionários representando a série mensal de vendas, onde cada dicionário contém os campos "month" (mês no formato "MMM YYYY"), "revenue" (receita total para aquele mês), "orders" (número total de pedidos naquele mês) e "customers" (número total de clientes únicos naquele mês). A série é calculada a partir dos dados do banco de dados, permitindo identificar padrões sazonais e tendências de crescimento ou declínio.
    """
    base_query = db.query(Product).filter(Product.date != None)
    filtered_query = _apply_db_filters(base_query, period, category, status, search)
    
    total = filtered_query.with_entities(func.count(Product.id)).scalar() or 0
    if total == 0:
        logging.info(f"[KPI][SALES] Ignorados todos os registros: nenhum com date válido")
        return [{"state": "no_data", "month": None, "revenue": None, "orders": None, "customers": None, "reason": "no_valid_date"}]
    # Agrupar por mês (YYYY-MM)
    # Agrupar por mês (YYYY-MM)
    results = filtered_query.with_entities(
        func.strftime('%Y-%m', Product.date).label('month'),
        func.sum(Product.revenue).label('revenue'),
        func.count(Product.id).label('orders'),
        func.count(distinct(Product.client)).label('customers')
    ).group_by('month').order_by('month').all()

    logging.info(f"[KPI][SALES] total válidos: {total}, meses: {len(results)}")
    
    return [
        {
            "month": r.month,
            "month": r.month, # Mantido para Reports.tsx
            "period": r.month, # Adicionado para Dashboard.tsx (XAxis period)
            "revenue": float(r.revenue),
            "orders": r.orders,
            "customers": r.customers
        }
        for r in results
    ]

# distribuição por Categoria (count)
def _build_category_distribution_db(db):
    """_summary_: calcula a distribuição de produtos por categoria a partir dos dados do banco de dados, onde a resposta inclui uma lista de categorias com a contagem de produtos em cada categoria, além de metadados como estado da resposta e razão para casos de ausência de dados. O endpoint é útil para entender a composição do portfólio de produtos e identificar quais categorias são mais representativas em termos de quantidade, permitindo que os usuários tomem decisões informadas sobre estratégias de marketing, estoque e desenvolvimento de produtos.

    Args:
        db (_type_): _description_: Instância do banco de dados.

    Returns:
        _type_: _description_: Lista de dicionários representando as categorias e suas contagens, onde cada dicionário contém os campos "category" (nome da categoria) e "count" (número de produtos associados a essa categoria). A lista é ordenada por contagem em ordem decrescente.
    """
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
    """_summary_: Calcula a receita total por categoria a partir dos dados do banco de dados, onde a resposta inclui uma lista de categorias com a receita total associada a cada categoria, além de metadados como estado da resposta e razão para casos de ausência de dados. O endpoint é útil para avaliar o desempenho de diferentes categorias de produtos e identificar quais categorias estão gerando mais receita, permitindo que os usuários tomem decisões informadas sobre estratégias de marketing, estoque e desenvolvimento de produtos.

    Args:
        db (_type_): _description_: Instância do banco de dados.

    Returns:
        _type_: _description_: Lista de dicionários representando as categorias e suas receitas totais, onde cada dicionário contém os campos "category" (nome da categoria) e "revenue" (receita total associada a essa categoria). A lista é ordenada por receita em ordem decrescente.
    """
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


@app.get("/")
async def root():
    """Healthcheck simples da API com nome e versao"""
    return {"message": "Analytics Dashboard API", "version": "1.0.0"}



@app.get("/api/overview")
async def get_overview(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
):
    """_summary_: Endpoint de overview; no estado atual retorna sem aplicar filtros recebidos.

    Args:
        period (str, optional): _description_. Defaults to Query(default="all").
        category (str, optional): _description_. Defaults to Query(default="all").
        region (str, optional): _description_. Defaults to Query(default="all").
        status (str, optional): _description_. Defaults to Query(default="all").
        search (str, optional): _description_. Defaults to Query(default="").

    Returns:
        _type_: _description_: Dicionário contendo as métricas de overview, incluindo receita total, número total de pedidos, número total de clientes, taxa de conversão, mudanças em relação ao período anterior e estado da resposta. O endpoint é útil para fornecer uma visão geral rápida do desempenho de vendas, permitindo que os usuários identifiquem rapidamente o estado atual do negócio e quaisquer áreas que possam exigir atenção.
    """
    if region != "all":
        logging.warning("[DEPRECATED] region filter ignored")
    db = SessionLocal()
    try:
        return _build_overview_db(db, period, category, status, search)
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
    """_summary_: [DEPRECATED] Use /api/sales/monthly instead. 
    Endpoint de vendas com contrato padronizado: {state, data, reason}.

    Args:
        period (str, optional): _description_. Defaults to Query(default="all").
        category (str, optional): _description_. Defaults to Query(default="all").
        region (str, optional): _description_. Defaults to Query(default="all").
        status (str, optional): _description_. Defaults to Query(default="all").
        search (str, optional): _description_. Defaults to Query(default="").

    Returns:
        _type_: _description_: AnalyticsResponse {state, data, reason} onde data é uma lista de dicionários com campos "month", "period", "revenue", "orders" e "customers".
    """
    if region != "all":
        logging.warning("[DEPRECATED] region filter ignored")
    db = SessionLocal()
    try:
        result = _build_sales_db(db, period, category, status, search)
        # Transform [list] response to {state, data, reason} format
        if result and isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if "state" in first_item and first_item["state"] in ["no_data", "error"]:
                # Error case
                return {
                    "state": first_item.get("state", "error"),
                    "data": [],
                    "reason": first_item.get("reason", "unknown_error")
                }
        # Success case
        return {
            "state": "valid",
            "data": result if isinstance(result, list) else [],
            "reason": None
        }
    finally:
        db.close()




# Nova rota: Distribuição por Categoria
@app.get("/api/category-distribution")
async def get_category_distribution():
    """[DEPRECATED] Use /api/distribution/category instead.
    Endpoint de distribuição por categoria com contrato padronizado: {state, data, reason}"""
    db = SessionLocal()
    try:
        result = _build_category_distribution_db(db)
        # Transform [list] response to {state, data, reason} format
        if result and isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if "state" in first_item and first_item["state"] in ["no_data", "error"]:
                # Error case
                return {
                    "state": first_item.get("state", "error"),
                    "data": [],
                    "reason": first_item.get("reason", "unknown_error")
                }
        # Success case
        return {
            "state": "valid",
            "data": result if isinstance(result, list) else [],
            "reason": None
        }
    finally:
        db.close()

# Nova rota: Receita por Categoria
@app.get("/api/category-revenue")
async def get_category_revenue():
    """[DEPRECATED] Use /api/distribution/category instead.
    Endpoint de receita por categoria com contrato padronizado: {state, data, reason}"""
    db = SessionLocal()
    try:
        result = _build_category_revenue_db(db)
        # Transform [list] response to {state, data, reason} format
        if result and isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if "state" in first_item and first_item["state"] in ["no_data", "error"]:
                # Error case
                return {
                    "state": first_item.get("state", "error"),
                    "data": [],
                    "reason": first_item.get("reason", "unknown_error")
                }
        # Success case
        return {
            "state": "valid",
            "data": result if isinstance(result, list) else [],
            "reason": None
        }
    finally:
        db.close()




@app.get("/api/filters")
async def get_filters():
    """_summary_: Retorna as opções de filtros disponíveis para produtos, incluindo períodos, categorias e status. A resposta é estruturada para fornecer uma lista de opções para cada tipo de filtro, onde cada opção inclui um valor e um rótulo legível. O endpoint é útil para alimentar interfaces de usuário com as opções de filtro corretas, garantindo que os usuários possam selecionar filtros válidos ao consultar os produtos.

    Returns:
        _type_: _description_: Dicionário contendo as opções de filtros disponíveis para produtos, onde o campo "periods" é uma lista de dicionários representando os períodos disponíveis para filtragem (com campos "value" e "label"), o campo "categories" é uma lista de categorias disponíveis para filtragem, e o campo "statuses" é uma lista de status disponíveis para filtragem. Cada opção de filtro é projetada para ser facilmente consumida por interfaces de usuário, permitindo que os usuários selecionem filtros válidos ao consultar os produtos.
    """
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
    """[DEPRECATED] Activity endpoint with standardized contract: {state, data, reason}"""
    # Mock data for consistency
    data = [{"hour": f"{h:02d}:00", "active_users": 0} for h in range(24)]
    return {
        "state": "valid",
        "data": data,
        "reason": None
    }


@app.get("/api/recent-orders")
async def get_recent_orders():
    """[DEPRECATED] Use /api/products instead.
    Endpoint com contrato padronizado: {state, data, reason}.
    Retorna os 10 pedidos mais recentes.

    Returns:
        _type_: _description_: AnalyticsResponse {state, data, reason} onde data é uma lista dos 10 pedidos mais recentes.
    """
    db = SessionLocal()
    try:
        latest = db.query(Product).filter(Product.date != None).order_by(Product.date.desc()).limit(10).all()
        if not latest:
            return {
                "state": "no_data",
                "data": [],
                "reason": "no_recent_orders"
            }
        data = [
            {
                "id": f"ORD-{item.id:05d}",
                "customer": item.client,
                "amount": item.revenue,
                "status": item.status,
                "date": str(item.date),
            }
            for item in latest
        ]
        return {
            "state": "valid",
            "data": data,
            "reason": None
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
