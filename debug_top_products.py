#!/usr/bin/env python3
import requests

r = requests.get("http://127.0.0.1:8000/api/top/products?limit=3", timeout=5)
import json
print(json.dumps(r.json(), indent=2))
