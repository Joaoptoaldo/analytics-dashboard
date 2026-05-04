from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func

from backend.db import SessionLocal
from backend.main import app
from backend.models.product import Product


client = TestClient(app)


def _trend_summary(payload: dict) -> dict:
    data = payload.get("data", []) if isinstance(payload, dict) else []
    revenue_sum = round(sum(float(item.get("revenue") or 0.0) for item in data), 2)
    orders_sum = sum(int(item.get("orders") or 0) for item in data)
    return {
        "state": payload.get("state") if isinstance(payload, dict) else None,
        "reason": payload.get("reason") if isinstance(payload, dict) else None,
        "revenue": revenue_sum,
        "orders": orders_sum,
        "points": len(data),
    }


def _replace_products(rows: list[dict]) -> list[dict]:
    session = SessionLocal()
    try:
        original_rows = [
            {
                "external_id": row.external_id,
                "client": row.client,
                "category": row.category,
                "revenue": row.revenue,
                "status": row.status,
                "region": row.region,
                "date": row.date,
            }
            for row in session.query(Product).all()
        ]

        session.query(Product).delete()
        session.commit()

        for row in rows:
            session.add(Product(**row))
        session.commit()

        return original_rows
    finally:
        session.close()


def _restore_products(rows: list[dict]) -> None:
    session = SessionLocal()
    try:
        session.query(Product).delete()
        session.commit()

        for row in rows:
            session.add(Product(**row))
        session.commit()
    finally:
        session.close()


def _sql_trend_summary(
    *,
    range_value: str = "30d",
    category: str = "all",
    status: str = "all",
    search: str = "",
) -> dict:
    days_map = {"30d": 30, "90d": 90, "180d": 180, "1y": 365}
    window_days = days_map[range_value]

    session = SessionLocal()
    try:
        query = session.query(Product).filter(Product.date.isnot(None), Product.revenue.isnot(None))

        if category != "all":
            query = query.filter(Product.category == category)
        if status != "all":
            query = query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(Product.client.ilike(search_term) | Product.category.ilike(search_term))

        rows = query.all()
        if not rows:
            return {"state": "no_data", "reason": "no_valid_data_in_range", "revenue": 0.0, "orders": 0, "points": 0}

        latest_date = max(row.date for row in rows if row.date is not None)
        cutoff_date = latest_date - timedelta(days=window_days - 1)
        window_rows = [row for row in rows if row.date is not None and cutoff_date <= row.date <= latest_date]

        if not window_rows:
            return {"state": "no_data", "reason": "no_valid_data_in_range", "revenue": 0.0, "orders": 0, "points": 0}

        revenue_sum = round(sum(float(row.revenue or 0.0) for row in window_rows), 2)
        orders_sum = len(window_rows)
        points = (latest_date - cutoff_date).days + 1
        return {"state": "valid", "revenue": revenue_sum, "orders": orders_sum, "points": points, "reason": None}
    finally:
        session.close()


def test_filters_deterministic_behavior():
    controlled_rows = [
        {
            "external_id": 900001,
            "client": "Alpha 1",
            "category": "A",
            "revenue": 100.0,
            "status": "Completed",
            "region": None,
            "date": date.today() - timedelta(days=1),
        },
        {
            "external_id": 900002,
            "client": "Alpha 2",
            "category": "A",
            "revenue": 120.0,
            "status": "Pending",
            "region": None,
            "date": date.today() - timedelta(days=2),
        },
        {
            "external_id": 900003,
            "client": "Alpha 3",
            "category": "A",
            "revenue": 130.0,
            "status": "Shipped",
            "region": None,
            "date": date.today() - timedelta(days=3),
        },
        {
            "external_id": 900004,
            "client": "Alpha 4",
            "category": "A",
            "revenue": 140.0,
            "status": "Processing",
            "region": None,
            "date": date.today() - timedelta(days=4),
        },
        {
            "external_id": 900005,
            "client": "Alpha 5",
            "category": "A",
            "revenue": 150.0,
            "status": "Completed",
            "region": None,
            "date": date.today() - timedelta(days=5),
        },
        {
            "external_id": 900006,
            "client": "Beta 1",
            "category": "B",
            "revenue": 200.0,
            "status": "Completed",
            "region": None,
            "date": date.today() - timedelta(days=1),
        },
        {
            "external_id": 900007,
            "client": "Beta 2",
            "category": "B",
            "revenue": 210.0,
            "status": "Pending",
            "region": None,
            "date": date.today() - timedelta(days=2),
        },
        {
            "external_id": 900008,
            "client": "Beta 3",
            "category": "B",
            "revenue": 220.0,
            "status": "Shipped",
            "region": None,
            "date": date.today() - timedelta(days=3),
        },
        {
            "external_id": 900009,
            "client": "Beta 4",
            "category": "B",
            "revenue": 230.0,
            "status": "Processing",
            "region": None,
            "date": date.today() - timedelta(days=4),
        },
        {
            "external_id": 900010,
            "client": "Beta 5",
            "category": "B",
            "revenue": 240.0,
            "status": "Completed",
            "region": None,
            "date": date.today() - timedelta(days=5),
        },
    ]

    original_rows = _replace_products(controlled_rows)
    try:
        response_all = client.get("/api/sales/trend?range=30d")
        response_category_a = client.get("/api/sales/trend?range=30d&category=A")

        assert response_all.status_code == 200, f"Unexpected status for all: {response_all.status_code}"
        assert response_category_a.status_code == 200, f"Unexpected status for category=A: {response_category_a.status_code}"

        payload_all = response_all.json()
        payload_category_a = response_category_a.json()

        api_all = _trend_summary(payload_all)
        api_category_a = _trend_summary(payload_category_a)
        sql_all = _sql_trend_summary(range_value="30d")
        sql_category_a = _sql_trend_summary(range_value="30d", category="A")

        assert api_all == sql_all, f"API all != SQL all: api={api_all} sql={sql_all}"
        assert api_category_a == sql_category_a, f"API category=A != SQL category=A: api={api_category_a} sql={sql_category_a}"
        assert api_all != api_category_a, f"Expected different results, got same summaries: all={api_all} category=A={api_category_a}"
    finally:
        _restore_products(original_rows)


def _extract_window_category() -> str:
    session = SessionLocal()
    try:
        latest_date = session.query(func.max(Product.date)).scalar()
        if latest_date is None:
            return "backfill"

        cutoff_date = latest_date - timedelta(days=29)
        categories = (
            session.query(Product.category, func.count(Product.id))
            .filter(Product.date >= cutoff_date, Product.date <= latest_date)
            .group_by(Product.category)
            .order_by(func.count(Product.id).desc())
            .all()
        )
        if categories:
            return categories[0][0]
        return "backfill"
    finally:
        session.close()


def _distinct_window_category() -> str:
    session = SessionLocal()
    try:
        latest_date = session.query(func.max(Product.date)).scalar()
        if latest_date is None:
            return "backfill"

        cutoff_date = latest_date - timedelta(days=29)
        all_categories = [
            row[0]
            for row in session.query(Product.category)
            .filter(Product.date >= cutoff_date, Product.date <= latest_date)
            .distinct()
            .all()
            if row[0] is not None
        ]
        if len(all_categories) > 1:
            return all_categories[0]

        categories = [row[0] for row in session.query(Product.category).distinct().all() if row[0] is not None]
        for category in categories:
            if category != "backfill":
                return category
        return "backfill"
    finally:
        session.close()


def test_filters_really_alter_result():
    response_all = client.get("/api/sales/trend?range=30d")
    response_backfill = client.get("/api/sales/trend?range=30d&category=backfill")

    assert response_all.status_code == 200
    assert response_backfill.status_code == 200

    payload_all = response_all.json()
    payload_backfill = response_backfill.json()

    sql_all = _sql_trend_summary(range_value="30d")
    sql_backfill = _sql_trend_summary(range_value="30d", category="backfill")

    if _trend_summary(payload_all) == _trend_summary(payload_backfill) and sql_all == sql_backfill:
        pytest.xfail("Current 30d slice is homogeneous for backfill in the real dataset; difference cannot be asserted without synthetic data.")

    assert _trend_summary(payload_all) != _trend_summary(payload_backfill), (
        f"Expected different payloads but got equal summaries: all={_trend_summary(payload_all)} backfill={_trend_summary(payload_backfill)}"
    )


@pytest.mark.parametrize("category", ["backfill", _distinct_window_category()])
def test_api_filtered_equals_sql_filtered(category: str):
    response = client.get(f"/api/sales/trend?range=30d&category={category}")
    assert response.status_code == 200

    payload = response.json()
    api_summary = _trend_summary(payload)
    sql_summary = _sql_trend_summary(range_value="30d", category=category)

    assert api_summary["state"] == sql_summary["state"], (
        f"State mismatch for category={category}: api={api_summary} sql={sql_summary}"
    )

    if sql_summary["state"] == "no_data":
        assert payload.get("data") == [], f"Expected empty data for category={category}, got {payload}"
        return

    assert api_summary["revenue"] == sql_summary["revenue"], (
        f"Revenue mismatch for category={category}: api={api_summary} sql={sql_summary}"
    )
    assert api_summary["orders"] == sql_summary["orders"], (
        f"Orders mismatch for category={category}: api={api_summary} sql={sql_summary}"
    )


def test_multiple_filters_match_sql():
    category = _extract_window_category()

    session = SessionLocal()
    try:
        latest_date = session.query(func.max(Product.date)).scalar()
        assert latest_date is not None

        cutoff_date = latest_date - timedelta(days=29)
        row = (
            session.query(Product)
            .filter(Product.date.isnot(None), Product.revenue.isnot(None))
            .filter(Product.category == category)
            .filter(Product.date >= cutoff_date, Product.date <= latest_date)
            .first()
        )
        assert row is not None
        status = row.status
        search = row.client.split()[0] if row.client else row.category
    finally:
        session.close()

    response_category_status = client.get(f"/api/sales/trend?range=30d&category={category}&status={status}")
    response_category_search = client.get(f"/api/sales/trend?range=30d&category={category}&search={search}")

    assert response_category_status.status_code == 200
    assert response_category_search.status_code == 200

    api_status = _trend_summary(response_category_status.json())
    api_search = _trend_summary(response_category_search.json())

    sql_status = _sql_trend_summary(range_value="30d", category=category, status=status)
    sql_search = _sql_trend_summary(range_value="30d", category=category, search=search)

    assert api_status["state"] == sql_status["state"], f"State mismatch category+status: api={api_status} sql={sql_status}"
    assert api_search["state"] == sql_search["state"], f"State mismatch category+search: api={api_search} sql={sql_search}"

    if sql_status["state"] == "valid":
        assert api_status["revenue"] == sql_status["revenue"], f"Revenue mismatch category+status: api={api_status} sql={sql_status}"
        assert api_status["orders"] == sql_status["orders"], f"Orders mismatch category+status: api={api_status} sql={sql_status}"

    if sql_search["state"] == "valid":
        assert api_search["revenue"] == sql_search["revenue"], f"Revenue mismatch category+search: api={api_search} sql={sql_search}"
        assert api_search["orders"] == sql_search["orders"], f"Orders mismatch category+search: api={api_search} sql={sql_search}"


def test_no_data_contract():
    response = client.get("/api/sales/trend?range=30d&category=nao_existe")
    assert response.status_code == 200

    payload = response.json()
    assert payload.get("state") == "no_data", f"Expected no_data but got {payload}"
    assert payload.get("data") == [], f"Expected empty data but got {payload}"