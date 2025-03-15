"""
Script to test direct HTTP requests to your API.
"""
import requests

BASE_URL = "http://localhost:8001"

def test_endpoint(endpoint):
    """Test an endpoint and print the response."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTesting: {url}")
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test endpoints
test_endpoint("/")
test_endpoint("/health")
test_endpoint("/api/test/hello")
test_endpoint("/api/test/echo/test")
test_endpoint("/api/auth/login/google")

# Print OpenAPI schema
print("\nTesting OpenAPI schema:")
try:
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        schema = response.json()
        print("Paths in OpenAPI schema:")
        for path in schema.get("paths", {}).keys():
            print(f"  {path}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}") 