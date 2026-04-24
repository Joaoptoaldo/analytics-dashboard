from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os
import random
from typing import Any

app = FastAPI(title="Analytics Dashboard API", version="1.0.0")

# CORS configuration
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

        rows.append(
            {
                "id": idx,
                "client": rng.choice(CLIENTS),
                "category": category,
                "revenue": max(revenue, 250.0),
                "status": status,
                "region": rng.choice(REGIONS),
                "date": date.strftime("%Y-%m-%d"),
            }
        )
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


def _build_overview(rows: list[dict[str, Any]]) -> dict[str, Any]:
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
        "revenue_change": round(random.uniform(-4, 16), 1),
        "orders_change": round(random.uniform(-3, 12), 1),
        "customers_change": round(random.uniform(-2, 10), 1),
        "conversion_change": round(random.uniform(-1, 4), 2),
    }


def _build_sales(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    month_keys = [
        "Jan 2024",
        "Feb 2024",
        "Mar 2024",
        "Apr 2024",
        "May 2024",
        "Jun 2024",
        "Jul 2024",
        "Aug 2024",
        "Sep 2024",
        "Oct 2024",
        "Nov 2024",
        "Dec 2024",
    ]
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
    filtered = _apply_filters(DATASET, period, category, region, status, search)
    return _build_overview(filtered)


@app.get("/api/sales")
async def get_sales(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
):
    filtered = _apply_filters(DATASET, period, category, region, status, search)
    return _build_sales(filtered)


@app.get("/api/traffic")
async def get_traffic(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
):
    filtered = _apply_filters(DATASET, period, category, region, status, search)
    return _build_traffic(filtered)


@app.get("/api/products")
async def get_products(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=50),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="desc"),
):
    filtered = _apply_filters(DATASET, period, category, region, status, search)
    reverse = sort_order == "desc"
    if sort_by in {"id", "client", "category", "revenue", "status", "region", "date"}:
        filtered = sorted(filtered, key=lambda x: x[sort_by], reverse=reverse)

    total = len(filtered)
    total_pages = max((total + page_size - 1) // page_size, 1)
    if page > total_pages:
        page = total_pages
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


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
    rng = random.Random(17)
    return [{"hour": f"{h:02d}:00", "active_users": rng.randint(50, 500)} for h in range(24)]


@app.get("/api/recent-orders")
async def get_recent_orders():
    latest = sorted(DATASET, key=lambda x: x["date"], reverse=True)[:10]
    return [
        {
            "id": f"ORD-{item['id']:05d}",
            "customer": item["client"],
            "amount": item["revenue"],
            "status": item["status"],
            "date": item["date"],
        }
        for item in latest
    ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
