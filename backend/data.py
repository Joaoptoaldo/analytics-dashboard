
from datetime import datetime, timedelta
from typing import Any

CATEGORIES = ["SaaS", "E-commerce", "Fintech", "Education", "Health"]
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
]


def _apply_filters(
    rows: list[dict[str, Any]],
    period: str = "all",
    category: str = "all",
    status: str = "all",
    search: str = "",
) -> list[dict[str, Any]]:
    """_summary_: método para aplicar os filtros de período, categoria, status e busca em uma lista de produtos representados como dicionários. Ele filtra os produtos com base no período (últimos 30, 90, 180 ou 365 dias), na categoria, no status e em um termo de busca que pode corresponder ao nome do cliente ou à categoria. O método retorna a lista de produtos que atendem a todos os critérios de filtragem.

    Args:
        rows (list[dict[str, Any]]): _description_: lista de produtos a ser filtrada, onde cada produto é representado como um dicionário contendo os campos id, client, category, revenue, status e date.
        period (str, optional): _description_. Defaults to "all".: 30d, 90d, 180d, 365d ou all
        category (str, optional): _description_. Defaults to "all".: Electronics, Clothing, Home, Sports ou all
        status (str, optional): _description_. Defaults to "all".: active, inactive, pending ou all
        search (str, optional): _description_. Defaults to "".: termo de busca para client ou category

    Returns:
        list[dict[str, Any]]: _description_: lista de produtos que atendem aos critérios de filtragem
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
