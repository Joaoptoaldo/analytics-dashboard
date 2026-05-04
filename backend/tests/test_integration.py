"""
Quick integration test to validate core endpoints work correctly
"""
import pytest
from fastapi.testclient import TestClient
import os
from backend.main import app
from backend.db import SessionLocal
from backend.models.sync_state import SyncState
from backend.models.product import Product
from datetime import date

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


def test_get_sales_endpoint():
    """Validate /api/sales returns 200 with valid data"""
    resp = client.get("/api/sales")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_get_overview_endpoint():
    """Validate /api/overview returns 200 with expected structure"""
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "state" in data


def test_internal_sync_no_token_when_not_required():
    """Validate /internal/external-products/sync works without token if not configured"""
    # Ensure EXTERNAL_SYNC_TOKEN is not set
    os.environ.pop("EXTERNAL_SYNC_TOKEN", None)
    
    resp = client.post("/internal/external-products/sync")
    # Should succeed since no token is required
    assert resp.status_code == 200
    data = resp.json()
    assert "synced" in data


def test_internal_sync_with_valid_token():
    """Validate /internal/external-products/sync accepts valid token"""
    # Set token requirement
    os.environ["EXTERNAL_SYNC_TOKEN"] = "test-token-123"
    
    try:
        # Request with valid token should succeed
        resp = client.post(
            "/internal/external-products/sync",
            headers={"x-internal-token": "test-token-123"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "synced" in data
    finally:
        os.environ.pop("EXTERNAL_SYNC_TOKEN", None)


def test_internal_sync_rejects_invalid_token():
    """Validate /internal/external-products/sync rejects invalid token"""
    # Set token requirement
    os.environ["EXTERNAL_SYNC_TOKEN"] = "test-token-123"
    
    try:
        # Request with wrong token should be rejected (401)
        resp = client.post(
            "/internal/external-products/sync",
            headers={"x-internal-token": "wrong-token"}
        )
        assert resp.status_code == 401
    finally:
        os.environ.pop("EXTERNAL_SYNC_TOKEN", None)


def test_health_check():
    """Validate root health endpoint"""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "version" in data
