from fastapi.testclient import TestClient
from backend.main import app
from backend.db import SessionLocal
from backend.models.product import Product
from datetime import date, timedelta

client = TestClient(app)


def setup_function():
    db = SessionLocal()
    try:
        db.query(Product).delete()
        db.commit()
    finally:
        db.close()


def teardown_function():
    db = SessionLocal()
    try:
        db.query(Product).delete()
        db.commit()
    finally:
        db.close()


def test_sales_returns_data_after_insert():
    db = SessionLocal()
    try:
        p = Product(external_id=1, client="ACME", category="Tools", revenue=123.45, status="Completed", date=date(2023, 1, 15))
        db.add(p)
        db.commit()
    finally:
        db.close()

    resp = client.get("/api/sales")
    assert resp.status_code == 200
    data = resp.json()
    # Response should be {state, data, reason}
    assert isinstance(data, dict)
    assert "state" in data
    assert "data" in data
    assert "reason" in data
    assert data["state"] == "valid"
    # Data should be a list containing monthly aggregation
    assert isinstance(data["data"], list)
    assert any(item.get("revenue") is not None for item in data["data"])


def test_sales_monthly_pads_until_current_month():
    today = date.today()
    previous_month_end = today.replace(day=1) - timedelta(days=1)
    historical_date = previous_month_end.replace(day=15)

    db = SessionLocal()
    try:
        p = Product(
            external_id=2,
            client="ACME",
            category="Tools",
            revenue=200.0,
            status="Completed",
            date=historical_date,
        )
        db.add(p)
        db.commit()
    finally:
        db.close()

    resp = client.get("/api/sales/monthly")
    assert resp.status_code == 200
    data = resp.json()

    assert data["state"] == "valid"
    months = [item["month"] for item in data["data"]]
    assert months[-1] == today.strftime("%Y-%m")
    current_month_entry = next(item for item in data["data"] if item["month"] == today.strftime("%Y-%m"))
    assert current_month_entry["revenue"] == 0.0
    assert current_month_entry["orders"] == 0
