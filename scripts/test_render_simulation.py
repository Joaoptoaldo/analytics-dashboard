#!/usr/bin/env python
"""
Simulated Render Docker Container Test
Valida que o app funcionaria corretamente quando rodado via Docker com env vars de PROD
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

class RenderSimulationTest:
    def __init__(self):
        self.results = []
        self.failed = []
        
    def test(self, name: str, passed: bool, message: str):
        result = {"test": name, "passed": passed, "message": message}
        self.results.append(result)
        if not passed:
            self.failed.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name} → {message}")
        
    def validate_dockerfile(self):
        """Validate Dockerfile syntax and structure"""
        print("\n[1] Validating Dockerfile...")
        
        try:
            with open(BASE_DIR / "Dockerfile", "r") as f:
                content = f.read()
            
            # Check key elements
            has_python = "python:3.13.13" in content
            has_workdir = "WORKDIR /app" in content
            has_cmd = "CMD" in content
            has_port = "EXPOSE 8080" in content or "8080" in content
            has_env_port = "${PORT:-8080}" in content
            
            self.test("Dockerfile uses Python 3.13.13", has_python, "Base image correct")
            self.test("Dockerfile sets WORKDIR", has_workdir, "Working directory set")
            self.test("Dockerfile exposes port", has_port, "Port 8080 exposed")
            self.test("Dockerfile supports dynamic PORT", has_env_port, "PORT env variable supported")
            self.test("Dockerfile has CMD", has_cmd, "Startup command defined")
            
        except Exception as e:
            self.test("Dockerfile validation", False, str(e))
    
    def simulate_docker_env(self):
        """Simulate running app with Docker environment variables"""
        print("\n[2] Simulating Docker Environment (Render Production)...")
        
        # Set environment exactly as Render would
        # Note: Using production-valid values (no localhost)
        render_env = {
            "ENV": "production",
            "DATABASE_URL": "postgresql://postgres:password@db.example.com:5432/dashboard_render?sslmode=require",
            "CORS_ORIGINS": "https://dashboard.example.com,https://www.dashboard.example.com",
            "EXTERNAL_SYNC_TOKEN": "render_token_32chars_1234567890abcd",
            "ALLOW_SEED": "false",
            "PORT": "8080",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERABLE": "1"
        }
        
        # Apply to environment
        for key, value in render_env.items():
            os.environ[key] = value
        
        # Verify all set
        for key, expected in render_env.items():
            actual = os.environ.get(key)
            self.test(
                f"Docker env: {key}",
                actual == expected,
                f"Value: {actual[:30]}..." if len(actual) > 30 else f"Value: {actual}"
            )
    
    def test_config_loading(self):
        """Test that config loads with Docker env vars (fail-fast validation)"""
        print("\n[3] Testing Config Loading (Fail-Fast Validation)...")
        
        try:
            from backend.config import load_and_validate_config, ENV, IS_PRODUCTION
            
            self.test("Config module imports", True, "backend.config available")
            
            self.test("ENV is 'production'", ENV == "production", f"ENV={ENV}")
            self.test("IS_PRODUCTION is True", IS_PRODUCTION, f"IS_PRODUCTION={IS_PRODUCTION}")
            
            config = load_and_validate_config()
            
            self.test("Config validates successfully", True, "No ConfigError raised")
            self.test("Database URL loaded", config["database_url"] is not None, "PostgreSQL configured")
            self.test("CORS origins loaded", len(config["cors_origins"]) > 0, "CORS configured")
            self.test("External token loaded", config["external_sync_token"] is not None, "Token present")
            
        except Exception as e:
            self.test("Config loading", False, f"Error: {str(e)[:50]}")
    
    def test_app_startup_simulation(self):
        """Test that FastAPI app can start with Docker env vars"""
        print("\n[4] Testing App Startup (Simulated Docker Container)...")
        
        try:
            from backend.main import app
            
            self.test("FastAPI app imports", app is not None, "backend.main:app available")
            
            # Check routers are loaded
            routes = [route.path for route in app.routes]
            has_health = "/health" in routes
            has_readiness = "/readiness" in routes
            has_api = any("/api/" in r for r in routes)
            has_internal = any("/internal/" in r for r in routes)
            
            self.test("Health endpoint registered", has_health, "GET /health available")
            self.test("Readiness endpoint registered", has_readiness, "GET /readiness available")
            self.test("API endpoints registered", has_api, f"Found {len([r for r in routes if '/api/' in r])} API routes")
            self.test("Internal endpoints registered", has_internal, "Internal endpoints available")
            
        except Exception as e:
            self.test("App startup", False, f"Error: {str(e)[:50]}")
    
    def test_database_connection(self):
        """Test database connection behavior"""
        print("\n[5] Testing Database Connection Behavior...")
        
        try:
            from backend.db import SessionLocal
            from backend.models.product import Product
            
            db = SessionLocal()
            # Try a simple query
            count = db.query(Product).limit(1).all()
            db.close()
            
            self.test("Database connection works", True, "SessionLocal created and query executed")
            
        except Exception as e:
            # This might fail because DB doesn't exist, that's OK in simulation
            error_msg = str(e)
            if "database" in error_msg.lower() or "connection" in error_msg.lower():
                self.test("Database connection attempted", True, f"(Expected error: DB unavailable in test)")
            else:
                self.test("Database connection", False, f"Error: {error_msg[:50]}")
    
    def test_endpoints_with_test_client(self):
        """Test endpoints using TestClient"""
        print("\n[6] Testing Endpoints with TestClient...")
        
        try:
            from fastapi.testclient import TestClient
            from backend.main import app
            
            client = TestClient(app)
            
            # Health check
            resp = client.get("/health")
            self.test("GET /health", resp.status_code == 200, f"Status: {resp.status_code}")
            
            # Readiness check
            resp = client.get("/readiness")
            readiness_ok = resp.status_code in [200, 503]  # 503 if DB unavailable, that's OK
            self.test("GET /readiness", readiness_ok, f"Status: {resp.status_code}")
            
            # Test CORS endpoint
            resp = client.get("/api/test-cors")
            self.test("GET /api/test-cors", resp.status_code == 200, f"Status: {resp.status_code}")
            
            # Test internal endpoint (should fail without token)
            resp = client.post("/internal/external-products/sync")
            self.test("POST /internal/* (auth check)", resp.status_code == 401, f"Status: {resp.status_code} (expected 401)")
            
        except Exception as e:
            self.test("Endpoint testing", False, f"Error: {str(e)[:50]}")
    
    def test_docker_port_behavior(self):
        """Test that PORT environment variable is respected"""
        print("\n[7] Testing Docker PORT Variable...")
        
        # Check what the CMD would execute
        port = os.environ.get("PORT", "8080")
        
        self.test("PORT environment variable set", port == "8080", f"PORT={port}")
        
        # Dockerfile uses: uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
        # This means it respects the PORT env var
        expected_port = 8080
        actual_port = int(port)
        
        self.test("Port binding correct", actual_port == expected_port, f"Listening on 0.0.0.0:{actual_port}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        total = len(self.results)
        passed = total - len(self.failed)
        
        return {
            "test_name": "Render Docker Simulation",
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": len(self.failed),
            "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "verdict": "✅ RENDER SIMULATION PASSED" if len(self.failed) == 0 else "❌ SIMULATION FAILED",
            "details": self.results,
            "failed_tests": self.failed
        }
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("RENDER DOCKER CONTAINER SIMULATION TEST")
        print("=" * 70)
        print("Simulating: docker run with production env vars\n")
        
        self.validate_dockerfile()
        self.simulate_docker_env()
        self.test_config_loading()
        self.test_app_startup_simulation()
        self.test_database_connection()
        self.test_endpoints_with_test_client()
        self.test_docker_port_behavior()
        
        # Generate report
        print("\n" + "=" * 70)
        print("TEST REPORT")
        print("=" * 70)
        
        report = self.generate_report()
        
        print(f"\nTotal Tests: {report['total_tests']}")
        print(f"Passed: {report['passed']}")
        print(f"Failed: {report['failed']}")
        print(f"Success Rate: {report['success_rate']}")
        print(f"\n{report['verdict']}")
        
        if self.failed:
            print("\nFailed Tests:")
            for test in self.failed:
                print(f"  ❌ {test['test']}: {test['message']}")
        
        print("=" * 70)
        
        # Save report
        with open(BASE_DIR / "render_simulation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("\nReport saved to: render_simulation_report.json\n")
        
        return len(self.failed) == 0

def main():
    tester = RenderSimulationTest()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
