from datetime import datetime, timedelta
from typing import Any

CATEGORIES = ["groceries", "home-decoration", "kitchen-accessories", "mens-watches", "beauty"]
STATUSES = ["Completed", "Processing", "Shipped", "Pending"]
CLIENTS = [ 
    "Alfa Tech",
    "Beta Commerce",
    "NovaBank",
    "EduPlus",
    "VidaCare",
    "Delta Systems",
    "Prime Retail",
    "CloudOps",
    "SmartLabs",
    "Pulse Group",
    "EcoSolutions",
    "NextGen",
    "Bright Future",
    "Global Ventures",
    "UrbanStyle",
    "HealthFirst",
    "Apex Innovations",
    "Zenith Corp",
    "Vertex Solutions",
    "Synergy Partners",
    "Momentum Inc",
    "Infinity Group",
    "Pioneer Tech",
    "Summit Enterprises",
    "Visionary Labs",
    "Quantum Solutions",
    "Nexus Group",
    "Eclipse Systems",
    "Radiant Ventures",
]


def _apply_filters(
    rows: list[dict[str, Any]],
    period: str = "all",
    category: str = "all",
    status: str = "all",
    search: str = "",
) -> list[dict[str, Any]]:
    """_summary_: Aplica filtros de periodo, categoria, status e busca textual em dados em memoria.

    Args:
        rows (list[dict[str, Any]]): _description_: Lista de registros de produto.
        period (str, optional): _description_. Intervalo (`30d`, `90d`, `180d`, `365d` ou `all`). Defaults to "all".
        category (str, optional): _description_. Categoria especifica ou `all`. Defaults to "all".
        status (str, optional): _description_. Status especifico ou `all`. Defaults to "all".
        search (str, optional): _description_. Busca textual parcial em `client` e `category`. Defaults to "".

    Returns:
        list[dict[str, Any]]: _description_: Lista filtrada de produtos.
    """
    filtered = rows
    now = datetime(2024, 12, 31)
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


def _build_seed_data() -> list[dict[str, Any]]:
    """_summary_: Constrói dataset determinístico de dados fictícios para seed do banco em desenvolvimento.
    
    Gera 100 registros com variação realista: datas distribuídas em 12 meses,
    clientes e categorias aleatórias, receitas entre 100 e 5000, status variados.
    Usa seed aleatório fixo para garantir consistência em execuções consecutivas.

    Returns:
        list[dict[str, Any]]: Lista com 100 dicionários contendo {client, category, revenue, status, date}.
    """
    import random
    
    # Seed determinístico para reprodutibilidade
    random.seed(42)
    
    data = []
    base_date = datetime(2024, 1, 1)
    
    # Gerar 100 registros distribuídos ao longo de 12 meses
    for i in range(100):
        # Data distribuída em 12 meses (aproximadamente 8-9 por mês)
        days_offset = (i * 3) % 365  # Distribui ao longo do ano
        record_date = base_date + timedelta(days=days_offset)
        
        data.append({
            "client": random.choice(CLIENTS),
            "category": random.choice(CATEGORIES),
            "revenue": round(random.uniform(100, 5000), 2),
            "status": random.choice(STATUSES),
            "date": record_date.strftime("%Y-%m-%d"),
        })
    
    return data
