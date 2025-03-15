"""
Script to print the OpenAPI schema of the main application.
"""
import json
from main import app

# Get the OpenAPI schema
openapi_schema = app.openapi()

# Print the schema
print(json.dumps(openapi_schema, indent=2))

# Print the paths
print("\nPaths:")
for path in openapi_schema.get("paths", {}).keys():
    print(f"  {path}") 