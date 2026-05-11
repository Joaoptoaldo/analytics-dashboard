"""
Pytest configuration - Setup test environment with mocked config.
"""

import os
import sys


def pytest_configure(config):
    """
    Hook called after command line options have been parsed.
    Set ENV=test BEFORE any backend modules are imported.
    Create database schema for tests.
    """
    # Set test environment BEFORE any imports
    os.environ["ENV"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    os.environ["EXTERNAL_SYNC_TOKEN"] = "test-token-at-least-32-characters-long!!"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8000"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Import and create schema AFTER env vars are set
    # Import models to register them with Base.metadata
    from backend.models.product import Product
    from backend.models.sync_state import SyncState
    from backend.db import Base, engine
    
    # Create all tables
    Base.metadata.create_all(bind=engine)




