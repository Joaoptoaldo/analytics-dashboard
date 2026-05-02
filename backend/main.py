from datetime import datetime, timedelta

import logging

from sqlalchemy import distinct, func, or_


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


def _build_overview_db(db):
    """_summary_: Bloco legado parcial; mantido por compatibilidade e sem uso no fluxo atual.

    Args:
        db (_type_): _description_: Instância do banco de dados.
    """
    total = db.query(func.count(Product.id)).scalar() or 0
    total_revenue = db.query(func.sum(Product.revenue)).scalar() or 0.0
    total_customers = db.query(func.count(distinct(Product.client))).scalar() or 0
    completed_orders = db.query(func.count(Product.id)).filter(Product.status == "Completed").scalar() or 0
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
    
    total = filtered_query.with_entities(func.count(Product.id)).scalar() or 0
    total_revenue = filtered_query.with_entities(func.sum(Product.revenue)).scalar() or 0.0
    total_customers = filtered_query.with_entities(func.count(distinct(Product.client))).scalar() or 0
    completed_orders = filtered_query.filter(Product.status == "Completed").with_entities(func.count(Product.id)).scalar() or 0
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
    """_summary_: Bloco legado parcial; mantido por compatibilidade e sem uso no fluxo atual.

    Args:
        db (_type_): _description_: Instância do banco de dados.
    """
    total = db.query(func.count(Product.id)).filter(Product.date != None).scalar() or 0

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
    results = db.query(

    results = filtered_query.with_entities(
        func.strftime('%Y-%m', Product.date).label('month'),
        func.sum(Product.revenue).label('revenue'),
        func.count(Product.id).label('orders'),
        func.count(distinct(Product.client)).label('customers')
    ).filter(Product.date != None)
    )
    results = results.group_by('month').order_by('month').all()
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

# Distribuição por Categoria (count)
def _build_category_distribution_db(db):
    """_summary_: Calcula a distribuição de produtos por categoria a partir dos dados do banco de dados, onde a resposta inclui uma lista de categorias com a contagem de produtos em cada categoria, além de metadados como estado da resposta e razão para casos de ausência de dados. O endpoint é útil para entender a composição do portfólio de produtos e identificar quais categorias são mais representativas em termos de quantidade, permitindo que os usuários tomem decisões informadas sobre estratégias de marketing, estoque e desenvolvimento de produtos.

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



app = FastAPI(title="Analytics Dashboard API", version="1.0.0")
app.include_router(products_router, prefix="/api")
app.include_router(external_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(external_sync_router, prefix="/api")


init_db()

# CORS config
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
allow_credentials = "*" not in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dados e constantes agora em backend.data


def _apply_filters(
    rows: list[dict[str, Any]],
    period: str = "all",
    category: str = "all",
    status: str = "all",
    search: str = "",
) -> list[dict[str, Any]]:
    """_summary_: Aplica os filtros de período, categoria, status e busca textual na lista de produtos, retornando apenas os produtos que correspondem aos critérios especificados. O filtro de período restringe os produtos com base na data, o filtro de categoria restringe os produtos a uma categoria específica, o filtro de status restringe os produtos a um status específico, e o filtro de busca textual permite filtrar os produtos com base em uma correspondência parcial no nome do cliente ou na categoria. A função é útil para refinar os resultados exibidos para o usuário com base em suas preferências e necessidades específicas.

    Args:
        rows (list[dict[str, Any]]): _description_
        period (str, optional): _description_. Defaults to "all".
        category (str, optional): _description_. Defaults to "all".
        status (str, optional): _description_. Defaults to "all".
        search (str, optional): _description_. Defaults to "".

    Returns:
        list[dict[str, Any]]: _description_: Lista de produtos que correspondem aos critérios especificados.
    """
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
    """_summary_: Calcula metricas de overview a partir de dados em memoria, onde a resposta inclui o valor total da receita, número total de pedidos, número total de clientes únicos e taxa de conversão, além de metadados como estado da resposta e razão para casos de ausência de dados. O endpoint é útil para fornecer uma visão geral do desempenho do negócio com base nos dados disponíveis, permitindo que os usuários avaliem rapidamente as métricas-chave e identifiquem áreas que podem exigir atenção ou melhoria.

    Args:
        rows (list[dict[str, Any]]): _description_: Lista de dicionários representando os produtos, onde cada dicionário contém os campos "id", "client", "category", "revenue", "status" e "date". O campo "id" é extraído do campo "id" da API, o campo "client" é extraído do campo "title", o campo "category" é extraído do campo "category", o campo "revenue" é extraído do campo "price" e convertido para float, o campo "status" é atribuído com base em um mapeamento determinístico usando o ID do produto, e o campo "date" é extraído de campos de data disponíveis na resposta da API, com tratamento de erros para garantir a robustez do processo.

    Returns:
        dict[str, Any]: _description_: Dicionário contendo as métricas de overview, onde os campos "total_revenue", "total_orders", "total_customers" e "conversion_rate" representam as métricas calculadas a partir dos dados em memória, e os campos "state" e "reason" fornecem informações sobre o estado da resposta e a razão para casos de ausência de dados, garantindo que o endpoint seja informativo e robusto mesmo quando não houver registros válidos para calcular as métricas de overview.
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
        "revenue_change": 0.0,  # implementa cálculo real vs período anterior
        "orders_change": 0.0,
        "customers_change": 0.0,
        "conversion_change": 0.0,
        "state": "valid"
    }


def _build_sales(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """_summary_: Calcula série mensal de vendas a partir de dados em memória, onde a resposta inclui uma lista de meses com a receita total e o número de pedidos em cada mês, além de metadados como estado da resposta e razão para casos de erro ou ausência de dados. O endpoint é útil para avaliar o desempenho de vendas ao longo do tempo e identificar padrões sazonais ou tendências de crescimento ou declínio.

    Args:
        rows (list[dict[str, Any]]): _description_: Lista de dicionários representando os produtos, onde cada dicionário contém os campos "id", "client", "category", "revenue", "status" e "date". O campo "id" é extraído do campo "id" da API, o campo "client" é extraído do campo "title", o campo "category" é extraído do campo "category", o campo "revenue" é extraído do campo "price" e convertido para float, o campo "status" é atribuído com base em um mapeamento determinístico usando o ID do produto, e o campo "date" é extraído de campos de data disponíveis na resposta da API, com tratamento de erros para garantir a robustez do processo.

    Returns:
        list[dict[str, Any]]: _description_: Lista de dicionários representando a série mensal de vendas, onde cada dicionário contém os campos "month" (mês no formato "MMM YYYY"), "revenue" (receita total para aquele mês), "orders" (número total de pedidos naquele mês) e "customers" (número total de clientes únicos naquele mês). A série é calculada a partir dos dados em memória, permitindo identificar padrões sazonais e tendências de crescimento ou declínio.
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
    """_summary_: Endpoint de vendas; no estado atual retorna sem aplicar filtros recebidos.

    Args:
        period (str, optional): _description_. Defaults to Query(default="all").
        category (str, optional): _description_. Defaults to Query(default="all").
        region (str, optional): _description_. Defaults to Query(default="all").
        status (str, optional): _description_. Defaults to Query(default="all").
        search (str, optional): _description_. Defaults to Query(default="").

    Returns:
        _type_: _description_: Lista de dicionários representando a série mensal de vendas, onde cada dicionário contém os campos "month" (mês no formato "MMM YYYY"), "revenue" (receita total para aquele mês), "orders" (número total de pedidos naquele mês) e "customers" (número total de clientes únicos naquele mês). A série é calculada a partir dos dados do banco de dados, aplicando os filtros recebidos como parâmetros. O endpoint é útil para visualizar a evolução da receita, número de pedidos e clientes ao longo do tempo, permitindo identificar padrões sazonais e tendências de crescimento ou declínio.
    """
    if region != "all":
        logging.warning("[DEPRECATED] region filter ignored")
    db = SessionLocal()
    try:
        return _build_sales_db(db, period, category, status, search)
    finally:
        db.close()




# Nova rota: Distribuição por Categoria
@app.get("/api/category-distribution")
async def get_category_distribution():
    """Endpoint de distribuicao por categoria"""
    db = SessionLocal()
    try:
        return _build_category_distribution_db(db)
    finally:
        db.close()

# Nova rota: Receita por Categoria
@app.get("/api/category-revenue")
async def get_category_revenue():
    """Endpoint de receita por categoria; no estado atual retorna sem aplicar filtros recebidos"""
    db = SessionLocal()
    try:
        return _build_category_revenue_db(db)
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
    # Mock temporário removendo a aleatoriedade pura para consistência
    return [{"hour": f"{h:02d}:00", "active_users": 0} for h in range(24)]


@app.get("/api/recent-orders")
async def get_recent_orders():
    """_summary_: Retorna uma lista dos 10 pedidos mais recentes, onde cada pedido inclui um ID formatado, nome do cliente, valor da receita, status do pedido e data. Os pedidos são obtidos do banco de dados local, ordenados por data em ordem decrescente, e limitados aos 10 registros mais recentes. O endpoint é útil para exibir uma visão geral das atividades de vendas recentes e monitorar o desempenho em tempo real.

    Returns:
        _type_: _description_: Lista de dicionários representando os 10 pedidos mais recentes, onde cada dicionário contém os campos "id" (ID formatado do pedido), "customer" (nome do cliente), "amount" (valor da receita), "status" (status do pedido) e "date" (data do pedido). Os pedidos são ordenados por data em ordem decrescente.
    """
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
