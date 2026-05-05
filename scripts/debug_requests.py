#!/usr/bin/env python3
"""Debug requests to local backend and print status + response body."""
import os
import urllib.request
import urllib.error
import json

BASE = os.getenv("BASE_URL", "http://localhost:8000")
ENDPOINTS = [
    "/api/overview?period=all&category=all&status=all&search=",
    "/api/external-products?period=all&category=all&status=all&search=&page=1&page_size=8&sort_by=date&sort_order=desc",
    "/api/filters",
    "/api/sales/monthly?period=all&category=all&status=all&search=",
    "/api/metrics/ticket-average?period=all&category=all&status=all&search=",
    "/api/distribution/category",
    "/api/top/products",
    "/api/sales/trend?period=all&category=all&status=all&search=&range=30d",
]


def fetch(path):
    url = BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": "debug-client/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            body = resp.read()
            ct = resp.headers.get('Content-Type', '')
            try:
                if 'application/json' in ct:
                    parsed = json.loads(body.decode('utf-8'))
                    pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
                else:
                    pretty = body.decode('utf-8', errors='replace')
            except Exception:
                pretty = body.decode('utf-8', errors='replace')
            print(f"=== {url} ===\nStatus: {status}\nContent-Type: {ct}\nBody:\n{pretty}\n")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"=== {url} ===\nHTTPError: {e.code} {e.reason}\nBody:\n{body}\n")
    except urllib.error.URLError as e:
        print(f"=== {url} ===\nURLError: {e}\n")
    except Exception as e:
        print(f"=== {url} ===\nUnexpected error: {e}\n")


if __name__ == '__main__':
    for ep in ENDPOINTS:
        fetch(ep)
