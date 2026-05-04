from fastapi.testclient import TestClient
from backend.main import app
from backend.db import SessionLocal
from backend.models.product import Product
from datetime import date

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
    assert isinstance(data, list)
    # Should contain at least one entry (monthly aggregation)
    assert any(item.get("revenue") is not None for item in data)
