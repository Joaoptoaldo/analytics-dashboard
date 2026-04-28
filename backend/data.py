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

def _build_seed_data() -> list[dict[str, Any]]:
    rng = random.Random(42)
    rows: list[dict[str, Any]] = []
    start_date = datetime(2024, 1, 1)
    for idx in range(1, 361):
        date = start_date + timedelta(days=rng.randint(0, 364))
        category = rng.choice(CATEGORIES)
        status = rng.choice(STATUSES)
        base_revenue = {
            "SaaS": 2200,
            "E-commerce": 1800,
            "Fintech": 2600,
            "Education": 1400,
            "Health": 2000,
        }[category]
        status_multiplier = {
            "Completed": 1.0,
            "Shipped": 0.95,
            "Processing": 0.82,
            "Pending": 0.65,
        }[status]
        revenue = round((base_revenue + rng.uniform(-350, 950)) * status_multiplier, 2)
        rows.append({
            "id": idx,
            "client": rng.choice(CLIENTS),
            "category": category,
            "revenue": max(revenue, 250.0),
            "status": status,
            "region": rng.choice(REGIONS),
            "date": date.strftime("%Y-%m-%d"),
        })
    return rows

DATASET = _build_seed_data()

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
