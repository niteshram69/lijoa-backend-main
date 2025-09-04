from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthz():
    """Test the health check endpoint"""
    # Test the endpoint
    response = client.get("/healthz")
    
    # Print response for debugging if it fails
    if response.status_code != 200:
        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        print(f"Available routes: {[route.path for route in app.routes]}")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "db" in data
    
    # Verify the response structure
    if data["status"] == "ok":
        assert data["db"] == "ok"
    else:
        assert "error" in data["db"]

def test_healthz_with_debug():
    """Debug version that prints more information"""
    print("\n=== Debugging Health Endpoint ===")
    print(f"App routes: {[route.path for route in app.routes if hasattr(route, 'path')]}")
    
    response = client.get("/healthz")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # This test will always pass but provides debugging info
    assert True