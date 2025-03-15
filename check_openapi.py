"""
Script to check the OpenAPI schema directly.
"""
import json
import requests

# Try to get the OpenAPI schema from the running application
try:
    response = requests.get("http://localhost:8000/openapi.json")
    schema = response.json()
    
    print("OpenAPI Schema:")
    print(json.dumps(schema, indent=2))
    
    print("\nPaths:")
    for path in schema.get("paths", {}).keys():
        print(f"  {path}")
except Exception as e:
    print(f"Error getting OpenAPI schema: {e}") 