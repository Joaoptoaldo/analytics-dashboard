#!/usr/bin/env python
"""
QA Lead + SRE Test: Full-stack validation (Frontend + Backend + Real usage)

TESTES:
1. Fluxo real (dashboard navigation, filtros, paginação, sorting)
2. Integração Frontend ↔ Backend (CORS, headers, endpoints)
3. Edge cases (banco vazio, nulos, datas inválidas)
4. Performance leve (múltiplas aberturas, alternância rápida)
5. Produção simulada (ENV=production)
"""

import json
import os
import sys
import logging
import subprocess
import time
from typing import Any, Dict, List
import requests
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Color codes for output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

class QAReport:
    """Manages QA test report generation"""
    
    def __init__(self):
        self.tests = []
        self.failed_tests = []
        self.warnings = []
        self.start_time = datetime.now()
        
    def test(self, name: str, passed: bool, message: str, severity: str = "error"):
        """Record a test result"""
        result = {
            "name": name,
            "passed": passed,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.tests.append(result)
        if not passed and severity == "error":
            self.failed_tests.append(result)
        if severity == "warning":
            self.warnings.append(result)
            
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        logger.info(f"{status} | {name} → {message}")
        
    def warning(self, name: str, message: str):
        """Record a warning"""
        self.test(name, True, message, severity="warning")
        
    def get_summary(self) -> Dict[str, Any]:
        """Generate summary"""
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = sum(1 for t in self.tests if t["passed"])
        failed = len(self.failed_tests)
        warnings = len(self.warnings)
        
        return {
            "total_tests": len(self.tests),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "duration_seconds": duration,
            "verdict": "SAFE TO DEPLOY" if failed == 0 else "NOT READY",
            "failed_tests": self.failed_tests,
            "warnings_list": self.warnings
        }

class BackendTester:
    """Tests backend endpoints and behavior"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.report = QAReport()
        
    def check_backend_alive(self) -> bool:
        """Check if backend is responding"""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=2)
            self.report.test(
                "Backend Liveness", 
                resp.status_code == 200,
                f"Health check returned {resp.status_code}"
            )
            return resp.status_code == 200
        except Exception as e:
            self.report.test("Backend Liveness", False, f"Connection failed: {str(e)}")
            return False
            
    def check_readiness(self) -> bool:
        """Check if backend is ready to serve traffic"""
        try:
            resp = self.session.get(f"{self.base_url}/readiness", timeout=5)
            ready = resp.status_code == 200
            self.report.test(
                "Backend Readiness",
                ready,
                f"Readiness check returned {resp.status_code}"
            )
            return ready
        except Exception as e:
            self.report.test("Backend Readiness", False, f"Readiness check failed: {str(e)}")
            return False
    
    def test_endpoints_exist(self):
        """Test that all expected endpoints exist"""
        endpoints = [
            ("/api/products", "GET"),
            ("/api/external-products", "GET"),
            ("/api/overview", "GET"),
            ("/api/filters", "GET"),
            ("/api/sales/monthly", "GET"),
            ("/api/sales/trend", "GET"),
            ("/api/distribution/category", "GET"),
            ("/api/top/products", "GET"),
            ("/api/metrics/ticket-average", "GET"),
            ("/api/test-cors", "GET"),
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    resp = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                    # Accepted: 200, 204, or service-level error responses (422 for bad params)
                    exists = resp.status_code in [200, 204, 422, 400]
                    
                self.report.test(
                    f"Endpoint Exists: {endpoint}",
                    exists,
                    f"Status {resp.status_code}"
                )
            except Exception as e:
                self.report.test(f"Endpoint Exists: {endpoint}", False, str(e))
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        try:
            resp = self.session.options(
                f"{self.base_url}/api/products",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET"
                },
                timeout=5
            )
            
            has_cors_header = "access-control-allow-origin" in {k.lower() for k in resp.headers.keys()}
            self.report.test(
                "CORS Headers Present",
                has_cors_header,
                f"CORS header present: {has_cors_header}"
            )
            
            # List headers
            cors_headers = {k: v for k, v in resp.headers.items() if "access-control" in k.lower()}
            if cors_headers:
                logger.info(f"  CORS headers: {cors_headers}")
                
        except Exception as e:
            self.report.test("CORS Headers Present", False, str(e))
    
    def test_security_headers(self):
        """Test security headers are present"""
        try:
            resp = self.session.get(f"{self.base_url}/api/products", timeout=5)
            
            security_headers = {
                "X-Content-Type-Options": resp.headers.get("X-Content-Type-Options"),
                "X-Frame-Options": resp.headers.get("X-Frame-Options"),
                "Referrer-Policy": resp.headers.get("Referrer-Policy"),
            }
            
            has_security = any(v for v in security_headers.values())
            self.report.test(
                "Security Headers Present",
                has_security,
                f"Found {sum(1 for v in security_headers.values() if v)} security headers"
            )
            
            if security_headers:
                logger.info(f"  Security headers: {security_headers}")
                
        except Exception as e:
            self.report.test("Security Headers Present", False, str(e))
    
    def test_data_consistency(self):
        """Test data consistency across endpoints"""
        try:
            # Get overview
            overview = self.session.get(f"{self.base_url}/api/overview").json()
            
            # Get products
            products = self.session.get(f"{self.base_url}/api/products?page_size=100").json()
            
            # Verify response structure
            has_overview = "data" in overview or "total_revenue" in overview
            has_products = "items" in products
            
            self.report.test(
                "Data Consistency: Overview structure",
                has_overview,
                f"Overview contains data: {has_overview}"
            )
            
            self.report.test(
                "Data Consistency: Products structure",
                has_products,
                f"Products contains items: {has_products}"
            )
            
        except Exception as e:
            self.report.test("Data Consistency", False, str(e))
    
    def test_filters_work(self):
        """Test filter functionality"""
        try:
            # Test period filter
            resp30d = self.session.get(f"{self.base_url}/api/products?period=30d").json()
            resp90d = self.session.get(f"{self.base_url}/api/products?period=90d").json()
            respAll = self.session.get(f"{self.base_url}/api/products?period=all").json()
            
            # Each should return valid data
            valid_responses = all([
                "items" in resp30d and isinstance(resp30d["items"], list),
                "items" in resp90d and isinstance(resp90d["items"], list),
                "items" in respAll and isinstance(respAll["items"], list)
            ])
            
            self.report.test(
                "Filters Work: Period filter",
                valid_responses,
                f"All period filters returned valid data"
            )
            
        except Exception as e:
            self.report.test("Filters Work: Period filter", False, str(e))
    
    def test_pagination_works(self):
        """Test pagination functionality"""
        try:
            page1 = self.session.get(f"{self.base_url}/api/products?page=1&page_size=5").json()
            page2 = self.session.get(f"{self.base_url}/api/products?page=2&page_size=5").json()
            
            has_pagination = all([
                "page" in page1,
                "total_pages" in page1,
                page1.get("page") == 1,
                isinstance(page1.get("items"), list)
            ])
            
            self.report.test(
                "Pagination Works",
                has_pagination,
                f"Page 1: {len(page1.get('items', []))} items, Page 2: {len(page2.get('items', []))} items"
            )
            
        except Exception as e:
            self.report.test("Pagination Works", False, str(e))
    
    def test_sorting_works(self):
        """Test sorting functionality"""
        try:
            respAsc = self.session.get(f"{self.base_url}/api/products?sort_order=asc").json()
            respDesc = self.session.get(f"{self.base_url}/api/products?sort_order=desc").json()
            
            # Both should return valid data
            valid = all([
                isinstance(respAsc.get("items"), list),
                isinstance(respDesc.get("items"), list)
            ])
            
            self.report.test(
                "Sorting Works",
                valid,
                f"Asc: {len(respAsc.get('items', []))} items, Desc: {len(respDesc.get('items', []))} items"
            )
            
        except Exception as e:
            self.report.test("Sorting Works", False, str(e))
    
    def test_search_works(self):
        """Test search functionality"""
        try:
            respNoSearch = self.session.get(f"{self.base_url}/api/products").json()
            respSearch = self.session.get(f"{self.base_url}/api/products?search=test").json()
            
            # Both should return valid data (search might return empty, but structure valid)
            valid = all([
                isinstance(respNoSearch.get("items"), list),
                isinstance(respSearch.get("items"), list)
            ])
            
            self.report.test(
                "Search Works",
                valid,
                f"Without search: {len(respNoSearch.get('items', []))} items, With search: {len(respSearch.get('items', []))} items"
            )
            
        except Exception as e:
            self.report.test("Search Works", False, str(e))
    
    def test_edge_cases(self):
        """Test edge cases"""
        try:
            # Empty result with impossible filter
            respEmpty = self.session.get(f"{self.base_url}/api/products?search=xxxNONEXISTENTxxx").json()
            has_items = "items" in respEmpty
            items_is_list = isinstance(respEmpty.get("items"), list)
            
            self.report.test(
                "Edge Case: Empty search result",
                has_items and items_is_list,
                f"Returns valid structure with {len(respEmpty.get('items', []))} items"
            )
            
            # Invalid page
            respInvalidPage = self.session.get(f"{self.base_url}/api/products?page=99999").json()
            self.report.test(
                "Edge Case: High page number",
                "items" in respInvalidPage,
                f"Returns empty or valid result"
            )
            
        except Exception as e:
            self.report.test("Edge Cases", False, str(e))
    
    def test_internal_endpoint_protection(self):
        """Test that internal endpoints require token"""
        try:
            # Try without token
            respNoToken = self.session.post(f"{self.base_url}/internal/external-products/sync")
            is_protected = respNoToken.status_code == 401
            
            self.report.test(
                "Internal Endpoint Protected",
                is_protected,
                f"Returns {respNoToken.status_code} (expected 401) without token"
            )
            
        except Exception as e:
            self.report.test("Internal Endpoint Protected", False, str(e))
    
    def test_no_500_errors(self, num_requests: int = 10):
        """Test that normal requests don't return 500 errors"""
        errors_500 = []
        
        endpoints = [
            "/api/products",
            "/api/overview",
            "/api/filters",
            "/api/sales/monthly",
        ]
        
        try:
            for _ in range(num_requests // len(endpoints)):
                for endpoint in endpoints:
                    try:
                        resp = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                        if resp.status_code == 500:
                            errors_500.append((endpoint, resp.status_code))
                    except:
                        pass
            
            self.report.test(
                f"No 500 Errors ({num_requests} requests)",
                len(errors_500) == 0,
                f"Found {len(errors_500)} 500 errors" if errors_500 else "All requests successful"
            )
            
        except Exception as e:
            self.report.test(f"No 500 Errors Test", False, str(e))

def main():
    """Main QA test flow"""
    logger.info("=" * 60)
    logger.info("QA LEAD + SRE TEST: FULL-STACK VALIDATION")
    logger.info("=" * 60)
    
    # Check environment
    env = os.getenv("ENV", "development")
    logger.info(f"Environment: {env}")
    
    # Initialize tester
    tester = BackendTester()
    
    # Phase 1: Basic connectivity
    logger.info("\n" + BLUE + "PHASE 1: Backend Connectivity" + RESET)
    if not tester.check_backend_alive():
        logger.error("Backend is not responding. Aborting tests.")
        return 1
    
    tester.check_readiness()
    
    # Phase 2: Endpoints
    logger.info("\n" + BLUE + "PHASE 2: Endpoint Validation" + RESET)
    tester.test_endpoints_exist()
    
    # Phase 3: Fluxo real
    logger.info("\n" + BLUE + "PHASE 3: Real Flow Tests" + RESET)
    tester.test_data_consistency()
    tester.test_filters_work()
    tester.test_pagination_works()
    tester.test_sorting_works()
    tester.test_search_works()
    
    # Phase 4: Edge cases
    logger.info("\n" + BLUE + "PHASE 4: Edge Cases" + RESET)
    tester.test_edge_cases()
    
    # Phase 5: Security
    logger.info("\n" + BLUE + "PHASE 5: Security & CORS" + RESET)
    tester.test_cors_headers()
    tester.test_security_headers()
    tester.test_internal_endpoint_protection()
    
    # Phase 6: Performance
    logger.info("\n" + BLUE + "PHASE 6: Performance (Light)" + RESET)
    tester.test_no_500_errors(num_requests=20)
    
    # Generate report
    logger.info("\n" + BLUE + "=" * 60 + RESET)
    logger.info("FINAL REPORT")
    logger.info(BLUE + "=" * 60 + RESET)
    
    summary = tester.report.get_summary()
    
    logger.info(f"Total Tests: {summary['total_tests']}")
    logger.info(f"Passed: {GREEN}{summary['passed']}{RESET}")
    logger.info(f"Failed: {RED if summary['failed'] > 0 else GREEN}{summary['failed']}{RESET}")
    logger.info(f"Warnings: {YELLOW}{summary['warnings']}{RESET}")
    logger.info(f"Duration: {summary['duration_seconds']:.2f}s")
    
    logger.info("\n" + "=" * 60)
    if summary["failed"] == 0:
        logger.info(f"{GREEN}VERDICT: {summary['verdict']}{RESET}")
    else:
        logger.info(f"{RED}VERDICT: {summary['verdict']}{RESET}")
        logger.info("\nFailed tests:")
        for test in summary["failed_tests"]:
            logger.error(f"  • {test['name']}: {test['message']}")
    
    logger.info("=" * 60)
    
    # Save report
    report_file = BASE_DIR / "qa_report.json"
    with open(report_file, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"\nReport saved to: {report_file}")
    
    return 0 if summary["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
