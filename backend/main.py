from sqlalchemy import func, distinct

from sqlalchemy import func, distinct, or_
import logging
def _build_overview_db(db):
    """_summary_: método para calcular as métricas de visão geral a partir dos dados do banco, incluindo total de pedidos, receita total, número de clientes únicos e taxa de conversão. O método realiza consultas ao banco de dados para obter os valores necessários e calcula as métricas com base nesses valores. O resultado é um dicionário contendo as métricas calculadas, que podem ser utilizadas para exibir a visão geral no dashboard de análise.

    Args:
        db (_type_): _description_: sessão do banco de dados para realizar as consultas necessárias para calcular as métricas de visão geral.
    """
    total = db.query(func.count(Product.id)).scalar() or 0
    total_revenue = db.query(func.sum(Product.revenue)).scalar() or 0.0
    total_customers = db.query(func.count(distinct(Product.client))).scalar() or 0
    completed_orders = db.query(func.count(Product.id)).filter(Product.status == "Completed").scalar() or 0
from datetime import datetime, timedelta

def _apply_db_filters(query, period, category, status, search):
    """_summary_: função auxiliar para aplicar os filtros de período, categoria, status e busca em uma consulta do SQLAlchemy. Ela modifica a consulta original adicionando as condições de filtro com base nos parâmetros fornecidos. O resultado é a consulta modificada que pode ser executada para obter os dados filtrados do banco de dados.

    Args:
        query (_type_): _description_: consulta do SQLAlchemy para aplicar os filtros
        period (_type_): _description_: 30d, 90d, 180d, 365d ou all
        category (_type_): _description_: Electronics, Clothing, Home, Sports ou all
        status (_type_): _description_: active, inactive, pending ou all
        search (_type_): _description_: termo de busca para client ou category

    Returns:
        _type_: _description_: consulta do SQLAlchemy modificada com os filtros aplicados
    """
    if period != "all":
        days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
        days = days_map.get(period, 365)
        min_date = datetime.now() - timedelta(days=days)
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
    """_summary_: método para calcular as métricas de visão geral a partir dos dados do banco, aplicando os filtros de período, categoria, status e busca. Ele utiliza a função auxiliar _apply_db_filters para modificar a consulta do SQLAlchemy com os filtros fornecidos, e depois realiza as consultas necessárias para calcular as métricas de total de pedidos, receita total, número de clientes únicos e taxa de conversão. O resultado é um dicionário contendo as métricas calculadas, que podem ser utilizadas para exibir a visão geral no dashboard de análise.

    Args:
        db (_type_): _description_
        period (str, optional): _description_. Defaults to "all".: 30d, 90d, 180d, 365d ou all
        category (str, optional): _description_. Defaults to "all".: Electronics, Clothing, Home, Sports ou all
        status (str, optional): _description_. Defaults to "all".: active, inactive, pending ou all
        search (str, optional): _description_. Defaults to "".: termo de busca para client ou category

    Returns:
        _type_: _description_: dicionário contendo as métricas de visão geral calculadas, incluindo total de pedidos, receita total, número de clientes únicos e taxa de conversão, com os filtros aplicados.
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
    """_summary_: método para calcular as métricas de vendas a partir dos dados do banco, agrupando por mês e somando a receita total e contando o número de pedidos para cada mês. O método realiza consultas ao banco de dados para obter os valores necessários e calcula as métricas com base nesses valores. O resultado é uma lista de dicionários contendo o mês, a receita total, o número de pedidos e o número de clientes para cada mês, que podem ser utilizadas para exibir a distribuição mensal de vendas no dashboard de análise.

    Args:
        db (_type_): _description_: sessão do banco de dados para realizar as consultas necessárias para calcular as métricas de vendas agrupadas por mês.
    """
    total = db.query(func.count(Product.id)).filter(Product.date != None).scalar() or 0

def _build_sales_db(db, period="all", category="all", status="all", search=""):
    """_summary_: método para calcular as métricas de vendas a partir dos dados do banco, aplicando os filtros de período, categoria, status e busca, e agrupando por mês. Ele utiliza a função auxiliar _apply_db_filters para modificar a consulta do SQLAlchemy com os filtros fornecidos, e depois realiza as consultas necessárias para calcular as métricas de receita total, número de pedidos e número de clientes para cada mês. O resultado é uma lista de dicionários contendo o mês, a receita total, o número de pedidos e o número de clientes para cada mês, que podem ser utilizadas para exibir a distribuição mensal de vendas no dashboard de análise.

    Args:
        db (_type_): _description_
        period (str, optional): _description_. Defaults to "all".: 30d, 90d, 180d, 365d ou all
        category (str, optional): _description_. Defaults to "all".: Electronics, Clothing, Home, Sports ou all
        status (str, optional): _description_. Defaults to "all".: active, inactive, pending ou all
        search (str, optional): _description_. Defaults to "".: termo de busca para client ou category

    Returns:
        _type_: _description_
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
    """_summary_: método para calcular a distribuição de produtos por categoria a partir dos dados do banco, agrupando os produtos por categoria e contando o número de produtos em cada categoria. O método realiza consultas ao banco de dados para obter os valores necessários e calcula a distribuição com base nesses valores. O resultado é uma lista de dicionários contendo a categoria e a contagem de produtos para cada categoria, que podem ser utilizadas para exibir a distribuição por categoria no dashboard de análise. Se não houver registros com data válida, retorna uma lista com um único dicionário indicando que não há dados disponíveis.

    Args:
        db (_type_): _description_: sessão do banco de dados para realizar as consultas necessárias para calcular a distribuição de produtos por categoria.

    Returns:
        _type_: _description_: lista de dicionários contendo a categoria e a contagem de produtos para cada categoria, que podem ser utilizadas para exibir a distribuição por categoria no dashboard de análise. Se não houver registros com data válida, retorna uma lista com um único dicionário indicando que não há dados disponíveis.
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
    """_summary_: método para calcular a receita total por categoria a partir dos dados do banco, agrupando por categoria e somando a receita para cada uma.

    Args:
        db (_type_): _description_: sessão do banco de dados para realizar as consultas

    Returns:
        _type_: _description_: lista de dicionários representando a receita por categoria, onde cada dicionário contém a categoria e a receita total associada a ela. Se não houver registros com data válida, retorna uma lista com um único dicionário indicando que não há dados disponíveis.
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

# Dados e constantes agora em backend.data


def _apply_filters(
    rows: list[dict[str, Any]],
    period: str = "all",
    category: str = "all",
    status: str = "all",
    search: str = "",
) -> list[dict[str, Any]]:
    """_summary_: método para aplicar os filtros de período, categoria, status e busca em uma lista de dicionários representando os produtos. O método filtra os produtos com base no período (últimos 30, 90, 180 ou 365 dias), categoria (Electronics, Clothing, Home, Sports ou all), status (active, inactive, pending ou all) e um termo de busca que é comparado com os campos client e category. O resultado é uma lista de dicionários contendo apenas os produtos que atendem aos critérios de filtro especificados. Este método é utilizado para processar os dados dos produtos antes de calcular as métricas e gerar os relatórios para o dashboard de análise.

    Args:
        rows (list[dict[str, Any]]): _description_: lista de dicionários representando os produtos a serem filtrados, onde cada dicionário contém informações como id, client, category, revenue, status e date.
        period (str, optional): _description_. Defaults to "all".: 30d, 90d, 180d, 365d ou all
        category (str, optional): _description_. Defaults to "all".: Electronics, Clothing, Home, Sports ou all
        status (str, optional): _description_. Defaults to "all".: active, inactive, pending ou all
        search (str, optional): _description_. Defaults to "".: termo de busca para client ou category

    Returns:
        list[dict[str, Any]]: _description_: lista de dicionários representando os produtos que atendem aos critérios de filtro especificados, onde cada dicionário contém as informações do produto que passou pelos filtros aplicados.
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
        "revenue_change": 0.0,  # implementa cálculo real vs período anterior
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
    """_summary_: rota raiz para verificar se a API está funcionando corretamente. Retorna uma mensagem de boas-vindas e a versão da API, indicando que o serviço está ativo e pronto para receber solicitações.

    Returns:
        _type_: _description_: dicionário contendo uma mensagem de boas-vindas e a versão da API, indicando que o serviço está ativo e funcionando corretamente. O campo "message" contém a mensagem de boas-vindas, enquanto o campo "version" indica a versão atual da API.
    """
    return {"message": "Analytics Dashboard API", "version": "1.0.0"}



@app.get("/api/overview")
async def get_overview(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
):
    """_summary_: método para obter as métricas de visão geral, aplicando os filtros de período, categoria, região, status e busca. O método consulta o banco de dados para recuperar os produtos, aplica os filtros utilizando a função _apply_filters() e calcula as métricas de visão geral utilizando a função _build_overview(). O resultado é um dicionário contendo as métricas calculadas, como receita total, número de pedidos, clientes únicos e taxa de conversão, além do estado do resultado (valid ou no_data) e uma razão detalhada caso não haja dados válidos para calcular as métricas.

    Args:
        period (str, optional): _description_. Defaults to Query(default="all").: 30d, 90d, 180d, 365d ou all
        category (str, optional): _description_. Defaults to Query(default="all").: Electronics, Clothing, Home, Sports ou all
        region (str, optional): _description_. Defaults to Query(default="all").: North, South, East, West ou all (atualmente ignorado e mantido para compatibilidade futura)
        status (str, optional): _description_. Defaults to Query(default="all").: active, inactive, pending ou all
        search (str, optional): _description_. Defaults to Query(default="").: termo de busca para client ou category


    Returns:
        _type_: _description_: dicionário contendo as métricas calculadas, como receita total, número de pedidos, clientes únicos e taxa de conversão, além do estado do resultado (valid ou no_data) e uma razão detalhada caso não haja dados válidos para calcular as métricas. O campo "state" indica se as métricas são válidas ("valid") ou se não há dados suficientes para calcular as métricas ("no_data"). Se o estado for "no_data", o campo "reason" fornece uma explicação detalhada sobre a ausência de dados válidos, como "no_valid_date" indicando que nenhum registro possui uma data válida para análise.
    """
    if region != "all":
        logging.warning("[DEPRECATED] region filter ignored")
    db = SessionLocal()
    try:
        return _build_overview_db(db)
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
    """_summary_: método para obter as métricas de vendas ao longo do tempo, aplicando os filtros de período, categoria, região, status e busca. O método consulta o banco de dados para recuperar os produtos, aplica os filtros utilizando a função _apply_filters() e calcula as métricas de vendas utilizando a função _build_sales(). O resultado é uma lista de dicionários representando as métricas de vendas ao longo do tempo, onde cada dicionário contém informações como mês, receita total, número de pedidos e clientes únicos para aquele mês. Se não houver dados válidos para calcular as métricas, o método retorna uma lista com um único dicionário indicando que não há dados disponíveis para análise.

    Args:
        period (str, optional): _description_. Defaults to Query(default="all").
        category (str, optional): _description_. Defaults to Query(default="all").
        region (str, optional): _description_. Defaults to Query(default="all").
        status (str, optional): _description_. Defaults to Query(default="all").
        search (str, optional): _description_. Defaults to Query(default="").

    Returns:
        # _type_: _description_: lista de dicionários representando as métricas de vendas ao longo do tempo, onde cada dicionário contém informações como mês, receita total, número de pedidos e clientes únicos para aquele mês. Se não houver dados válidos para calcular as métricas, o método retorna uma lista com um único dicionário indicando que não há dados disponíveis para análise, com campos como "state": "no_data", "month": None, "revenue": None, "orders": None e "customers": None.
    """
    if region != "all":
        logging.warning("[DEPRECATED] region filter ignored")
    db = SessionLocal()
    try:
        return _build_sales_db(db)
        return _build_sales_db(db, period, category, status, search)
    finally:
        db.close()




# Nova rota: Distribuição por Categoria
@app.get("/api/category-distribution")
async def get_category_distribution():
    """_summary_: método para obter a distribuição de produtos por categoria, consultando o banco de dados para contar o número de produtos em cada categoria. O método retorna uma lista de dicionários representando a contagem de produtos por categoria, onde cada dicionário contém a categoria e a contagem associada a ela. Se não houver registros com data válida, retorna uma lista com um único dicionário indicando que não há dados disponíveis para calcular a distribuição por categoria.

    Returns:
        _type_: _description_: lista de dicionários representando a contagem de produtos por categoria, onde cada dicionário contém a categoria e a contagem associada a ela. Se não houver registros com data válida, retorna uma lista com um único dicionário indicando que não há dados disponíveis para calcular a distribuição por categoria.
    """
    db = SessionLocal()
    try:
        return _build_category_distribution_db(db)
    finally:
        db.close()

# Nova rota: Receita por Categoria
@app.get("/api/category-revenue")
async def get_category_revenue():
    """_summary_: método para obter a receita total por categoria, consultando o banco de dados para somar a receita de produtos em cada categoria. O método retorna uma lista de dicionários representando a receita por categoria, onde cada dicionário contém a categoria e a receita total associada a ela. Se não houver registros com data válida, retorna uma lista com um único dicionário indicando que não há dados disponíveis para calcular a receita por categoria.

    Returns:
        _type_: _description_: lista de dicionários representando a receita por categoria, onde cada dicionário contém a categoria e a receita total associada a ela. Se não houver registros com data válida, retorna uma lista com um único dicionário indicando que não há dados disponíveis para calcular a receita por categoria.
    """
    db = SessionLocal()
    try:
        return _build_category_revenue_db(db)
    finally:
        db.close()




@app.get("/api/filters")
async def get_filters():
    """_summary_: método para obter as opções de filtros disponíveis para o dashboard de análise, incluindo períodos, categorias e status. O método retorna um dicionário contendo listas de opções para cada tipo de filtro, que podem ser utilizadas no frontend para permitir que os usuários selecionem os critérios de filtragem ao visualizar as métricas e relatórios.

    Returns:
        _type_: _description_: dicionário contendo listas de opções para cada tipo de filtro, incluindo períodos (all, 30d, 90d, 180d, 365d), categorias (definidas na constante CATEGORIES) e status (definidos na constante STATUSES). Este dicionário é utilizado no frontend para preencher os dropdowns ou seletores de filtros, permitindo que os usuários escolham os critérios de filtragem ao visualizar as métricas e relatórios no dashboard de análise.
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
    """_summary_: método para obter os pedidos recentes, consultando o banco de dados para recuperar os 10 pedidos mais recentes com data válida, ordenados por data em ordem decrescente. O método retorna uma lista de dicionários representando os pedidos recentes, onde cada dicionário contém informações como id do pedido, cliente, valor da receita, status e data. Se não houver registros com data válida, o método retornará uma lista vazia ou um indicador de que não há dados disponíveis.

    Returns:
        _type_: _description_: lista de dicionários representando os pedidos recentes, onde cada dicionário contém informações como id do pedido, cliente, valor da receita, status e data. Se não houver registros com data válida, o método retornará uma lista vazia ou um indicador de que não há dados disponíveis.
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
