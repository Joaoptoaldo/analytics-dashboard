
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
