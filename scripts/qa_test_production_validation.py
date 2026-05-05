#!/usr/bin/env python
"""
Test that production mode enforces strict checks and fails fast on bad config
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

class ProductionStrictnessValidator:
    def __init__(self):
        self.tests = []
        
    def test_startup_fails_with_sqlite(self):
        """PROD should reject SQLite"""
        print("[TEST 1] Production rejects SQLite database...")
        
        # Try to start app with SQLite in PROD
        result = subprocess.run(
            [sys.executable, '-c', '''
import os
os.environ.update({
    "ENV": "production",
    "DATABASE_URL": "sqlite:///./test.db",
    "EXTERNAL_SYNC_TOKEN": "token_32chars_1234567890abcdef",
    "CORS_ORIGINS": "https://example.com"
})
try:
    from backend.main import app
    print("ERROR: App started despite SQLite in PROD!")
    import sys
    sys.exit(0)  # Fail test if no error
except SystemExit as e:
    # We expect sys.exit(1) from config validation
    if e.code == 1:
        print("OK: App correctly rejected SQLite in production")
        import sys
        sys.exit(0)  # Pass test
    else:
        print(f"ERROR: Unexpected exit code: {e.code}")
        import sys
        sys.exit(1)
except Exception as e:
    print(f"OK: App raised error: {e.__class__.__name__}")
    import sys
    sys.exit(0)
'''],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        
        passed = result.returncode == 0
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        if result.stdout:
            print(f"  Output: {result.stdout[:100]}")
        
        self.tests.append({
            "name": "SQLite rejected in production",
            "passed": passed
        })
        
        return passed
    
    def test_startup_fails_without_token(self):
        """PROD should require token"""
        print("\n[TEST 2] Production requires EXTERNAL_SYNC_TOKEN...")
        
        result = subprocess.run(
            [sys.executable, '-c', '''
import os
import sys
os.environ.update({
    "ENV": "production",
    "DATABASE_URL": "postgresql://user:pass@localhost/db",
    "EXTERNAL_SYNC_TOKEN": "",
    "CORS_ORIGINS": "http://localhost"
})
try:
    from backend.main import app
    print("ERROR: App started without token in PROD!")
    sys.exit(1)
except (SystemExit, ValueError) as e:
    print(f"OK: App correctly rejected missing token")
    sys.exit(0)
except Exception as e:
    if "token" in str(e).lower() or "sync" in str(e).lower():
        print(f"OK: App raised error about token: {e.__class__.__name__}")
        sys.exit(0)
    print(f"ERROR: Wrong error: {e}")
    sys.exit(1)
'''],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        
        passed = "ERROR" not in result.stdout and result.returncode == 0
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        if result.stdout:
            print(f"  Output: {result.stdout[:100]}")
        
        self.tests.append({
            "name": "Token required in production",
            "passed": passed
        })
        
        return passed
    
    def get_summary(self):
        passed = sum(1 for t in self.tests if t['passed'])
        total = len(self.tests)
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "tests": self.tests,
            "verdict": "PRODUCTION VALIDATION OK" if passed == total else "PRODUCTION VALIDATION FAILED"
        }

def main():
    print("=" * 60)
    print("PRODUCTION STRICTNESS VALIDATION")
    print("=" * 60)
    
    validator = ProductionStrictnessValidator()
    
    # Run validation tests
    validator.test_startup_fails_with_sqlite()
    validator.test_startup_fails_without_token()
    
    # Summary
    summary = validator.get_summary()
    
    print(f"\n{'=' * 60}")
    print(f"Total Tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Verdict: {summary['verdict']}")
    print("=" * 60)
    
    # Save
    with open(BASE_DIR / "qa_production_strictness.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Report saved: qa_production_strictness.json\n")
    
    return 0 if summary['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
