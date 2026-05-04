#!/usr/bin/env python3
import requests
import json

r = requests.get("http://127.0.0.1:8000/api/distribution/category", timeout=5)
print(json.dumps(r.json(), indent=2))
