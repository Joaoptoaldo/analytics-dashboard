from datetime import datetime, timedelta
import random
from typing import Any

CATEGORIES = ["SaaS", "E-commerce", "Fintech", "Education", "Health"]
REGIONS = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
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

"""
Funções de seed removidas deste arquivo.
Utilize backend/seeds/seed_data.py para popular o banco em dev/test.
"""

def _apply_filters(
    rows: list[dict[str, Any]],
    period: str = "all",
    category: str = "all",
    region: str = "all",
    status: str = "all",
    search: str = "",
) -> list[dict[str, Any]]:
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
