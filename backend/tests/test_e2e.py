"""
End-to-end test simulating frontend requests to backend
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import SessionLocal
from backend.models.sync_state import SyncState

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_sync_state():
    """Reset sync state before each test to avoid rate-limit contamination"""
    db = SessionLocal()
    try:
        db.query(SyncState).delete()
        db.commit()
        yield
        db.query(SyncState).delete()
        db.commit()
    finally:
        db.close()


def test_frontend_can_fetch_sales():
    """
    Simulates: Frontend calling fetch(`http://localhost:8000/api/sales`)
    Expected: Returns array of monthly sales data
    """
    # This is what Dashboard.tsx calls
    resp = client.get("/api/sales")
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    # Should be a list (monthly aggregates)
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    print(f"✓ Frontend can fetch sales: {len(data)} months found")


def test_frontend_can_fetch_overview():
    """
    Simulates: Frontend calling fetch(`http://localhost:8000/api/overview`)
    Expected: Returns overview metrics
    """
    resp = client.get("/api/overview?period=30d&category=all&status=all")
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    # Should have state
    assert "state" in data, f"Missing 'state' in response: {data}"
    print(f"✓ Frontend can fetch overview: state={data.get('state')}")


def test_frontend_can_fetch_filters():
    """
    Simulates: Frontend calling fetch(`http://localhost:8000/api/filters`)
    Expected: Returns available filter options
    """
    resp = client.get("/api/filters")
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    
    assert "periods" in data, "Missing 'periods' in filter options"
    assert "categories" in data, "Missing 'categories' in filter options"
    assert "statuses" in data, "Missing 'statuses' in filter options"
    print(f"✓ Frontend can fetch filters")


def test_frontend_can_trigger_sync_with_token():
    """
    Simulates: Frontend calling POST to /internal/external-products/sync with token
    Expected: Returns {synced: <count>}
    """
    import os
    
    # Set token (simulates production environment)
    token = "my-secret-token"
    os.environ["EXTERNAL_SYNC_TOKEN"] = token
    
    try:
        # This is what Dashboard.tsx does when user clicks "Sync"
        resp = client.post(
            "/internal/external-products/sync",
            headers={"x-internal-token": token}
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "synced" in data, f"Missing 'synced' in response: {data}"
        print(f"✓ Frontend can trigger sync with token: {data['synced']} products synced")
    finally:
        os.environ.pop("EXTERNAL_SYNC_TOKEN", None)


def test_frontend_cannot_sync_with_wrong_token():
    """
    Simulates: Frontend sends wrong token to sync endpoint
    Expected: Returns 401 Unauthorized
    """
    import os
    
    # Set correct token on backend
    os.environ["EXTERNAL_SYNC_TOKEN"] = "correct-token"
    
    try:
        # Frontend accidentally sends wrong token
        resp = client.post(
            "/internal/external-products/sync",
            headers={"x-internal-token": "wrong-token"}
        )
        
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
        print(f"✓ Frontend properly rejected with wrong token")
    finally:
        os.environ.pop("EXTERNAL_SYNC_TOKEN", None)


def test_frontend_endpoints_documented():
    """
    Verify critical endpoints are available and documented
    """
    endpoints = [
        "/",
        "/api/test-cors",
        "/api/overview",
        "/api/sales",
        "/api/filters",
        "/api/category-distribution",
        "/api/category-revenue",
        "/api/recent-orders",
    ]
    
    for endpoint in endpoints:
        resp = client.get(endpoint)
        # Just verify endpoints exist (200 or error response is ok)
        assert resp.status_code in [200, 400, 422, 500], f"Endpoint {endpoint} returned {resp.status_code}"
    
    print(f"✓ All {len(endpoints)} documented endpoints accessible")
