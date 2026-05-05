#!/usr/bin/env python
"""
Production Simulation Test - Validates production-mode strictness
"""

import os
import sys
import json
import logging
from typing import Any, Dict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

class ProductionTester:
    """Tests production-mode behavior and strictness"""
    
    def __init__(self):
        self.tests = []
        self.failed = []
        self.start_time = datetime.now()
        
    def test(self, name: str, passed: bool, message: str):
        result = {"name": name, "passed": passed, "message": message}
        self.tests.append(result)
        if not passed:
            self.failed.append(result)
        
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        logger.info(f"{status} {name} → {message}")
        
    def run_env_test(self):
        """Test 1: Verify ENV=production is set correctly"""
        logger.info(f"\n{BLUE}TEST 1: Environment Configuration{RESET}")
        
        env = os.getenv("ENV")
        self.test("ENV variable set", env is not None, f"ENV={env}")
        
        prod_mode = env == "production"
        self.test("ENV=production enforced", prod_mode, f"ENV={env}")
        
    def run_db_strictness_test(self):
        """Test 2: Verify database validation is strict"""
        logger.info(f"\n{BLUE}TEST 2: Database Strictness (Production){RESET}")
        
        db_url = os.getenv("DATABASE_URL", "")
        
        # Test 2a: SQLite rejected
        is_sqlite = "sqlite" in db_url.lower()
        self.test(
            "SQLite rejected in PROD",
            not is_sqlite,
            f"Using: {db_url[:50]}..."
        )
        
        # Test 2b: Postgres scheme accepted
        has_postgres = db_url.startswith("postgresql://") or db_url.startswith("postgres://")
        self.test(
            "Postgres scheme accepted",
            has_postgres or not os.getenv("ENV") == "production",
            f"Scheme: {db_url.split('://')[0] if '://' in db_url else 'unknown'}"
        )
        
    def run_token_strictness_test(self):
        """Test 3: Verify EXTERNAL_SYNC_TOKEN is enforced"""
        logger.info(f"\n{BLUE}TEST 3: Token Security (Production){RESET}")
        
        token = os.getenv("EXTERNAL_SYNC_TOKEN", "")
        
        has_token = len(token) > 0
        self.test(
            "EXTERNAL_SYNC_TOKEN present",
            has_token,
            f"Token length: {len(token)}"
        )
        
        min_length = 32
        is_long_enough = len(token) >= min_length
        self.test(
            f"Token >= {min_length} chars (if present)",
            is_long_enough or len(token) == 0,
            f"Token length: {len(token)}"
        )
        
    def run_startup_test(self):
        """Test 4: Verify app starts without errors"""
        logger.info(f"\n{BLUE}TEST 4: Application Startup{RESET}")
        
        # Try importing the app
        try:
            from backend.config import IS_PRODUCTION
            self.test(
                "Config loads successfully",
                True,
                f"IS_PRODUCTION={IS_PRODUCTION}"
            )
            
            from backend.main import app
            self.test(
                "Application initializes",
                app is not None,
                "FastAPI app created"
            )
            
        except Exception as e:
            self.test("Application startup", False, f"Error: {str(e)[:50]}")
    
    def test_readiness_endpoint(self):
        """Test 5: Health and Readiness endpoints"""
        logger.info(f"\n{BLUE}TEST 5: Health Endpoints{RESET}")
        
        import requests
        
        try:
            resp = requests.get("http://127.0.0.1:8000/health", timeout=3)
            self.test("Health endpoint", resp.status_code == 200, f"Status: {resp.status_code}")
        except Exception as e:
            self.test("Health endpoint", False, f"Connection failed: {str(e)[:30]}")
        
        try:
            resp = requests.get("http://127.0.0.1:8000/readiness", timeout=5)
            self.test("Readiness endpoint", resp.status_code == 200, f"Status: {resp.status_code}")
        except Exception as e:
            self.test("Readiness endpoint", False, f"Connection failed: {str(e)[:30]}")
    
    def test_internal_endpoint_auth(self):
        """Test 6: Internal endpoint requires token"""
        logger.info(f"\n{BLUE}TEST 6: Internal Endpoint Security{RESET}")
        
        import requests
        
        try:
            # Should fail without token
            resp = requests.post("http://127.0.0.1:8000/internal/external-products/sync", timeout=3)
            unauthorized = resp.status_code == 401
            self.test(
                "Internal endpoint requires auth",
                unauthorized,
                f"Status without token: {resp.status_code}"
            )
            
            # Should also fail with wrong token
            resp = requests.post(
                "http://127.0.0.1:8000/internal/external-products/sync",
                headers={"x-internal-token": "wrong_token"},
                timeout=3
            )
            wrong_token_denied = resp.status_code == 401
            self.test(
                "Wrong token rejected",
                wrong_token_denied,
                f"Status with wrong token: {resp.status_code}"
            )
            
        except Exception as e:
            self.test("Internal endpoint auth", False, f"Error: {str(e)[:30]}")
    
    def test_api_endpoints_working(self):
        """Test 7: Core API endpoints still work"""
        logger.info(f"\n{BLUE}TEST 7: API Functionality{RESET}")
        
        import requests
        
        endpoints = ["/api/products", "/api/overview", "/api/filters"]
        
        for endpoint in endpoints:
            try:
                resp = requests.get(f"http://127.0.0.1:8000{endpoint}", timeout=3)
                working = resp.status_code == 200
                self.test(f"API: {endpoint}", working, f"Status: {resp.status_code}")
            except Exception as e:
                self.test(f"API: {endpoint}", False, f"Error: {str(e)[:30]}")
    
    def get_summary(self) -> Dict[str, Any]:
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            "total": len(self.tests),
            "passed": len(self.tests) - len(self.failed),
            "failed": len(self.failed),
            "duration": duration,
            "verdict": "PRODUCTION READY" if len(self.failed) == 0 else "PRODUCTION ISSUES",
            "failures": self.failed
        }

def main():
    logger.info("=" * 60)
    logger.info("PRODUCTION SIMULATION TEST")
    logger.info("=" * 60)
    
    tester = ProductionTester()
    
    # Run all tests
    tester.run_env_test()
    tester.run_db_strictness_test()
    tester.run_token_strictness_test()
    tester.run_startup_test()
    tester.test_readiness_endpoint()
    tester.test_internal_endpoint_auth()
    tester.test_api_endpoints_working()
    
    # Summary
    logger.info(f"\n{BLUE}=" * 60 + RESET)
    summary = tester.get_summary()
    
    logger.info(f"Total Tests: {summary['total']}")
    logger.info(f"Passed: {GREEN}{summary['passed']}{RESET}")
    logger.info(f"Failed: {RED if summary['failed'] > 0 else GREEN}{summary['failed']}{RESET}")
    logger.info(f"Duration: {summary['duration']:.2f}s")
    
    logger.info(f"\n{BLUE}VERDICT: {summary['verdict']}{RESET}")
    
    if summary['failed'] > 0:
        logger.error("\nProduction issues found:")
        for test in summary['failures']:
            logger.error(f"  • {test['name']}: {test['message']}")
    
    logger.info("=" * 60)
    
    # Save report
    with open(BASE_DIR / "qa_production_test.json", "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Report saved to: qa_production_test.json\n")
    
    return 0 if summary['failed'] == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
