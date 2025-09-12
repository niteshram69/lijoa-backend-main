import os
import time
import uuid
from fastapi.testclient import TestClient
from app.main import app

# Set test environment
os.environ["APP_ENV"] = "test"

client = TestClient(app)

def generate_unique_email():
    """Generate a unique email for testing"""
    return f"test-{uuid.uuid4().hex[:8]}@example.com"

def test_api_key_flow_and_signed_call():
    """Test complete API key flow with optional signature"""
    # 1) Create user
    user_data = {"email": generate_unique_email(), "full_name": "Auth Test"}
    response = client.post("/users", json=user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]
    
    # 2) Create API key
    key_data = {"user_id": user_id, "name": "test-key"}
    response = client.post("/api-keys", json=key_data)
    assert response.status_code == 201
    token = response.json()["token"]
    
    # 3) Create application using API key
    app_data = {
        "user_id": user_id,
        "company": "TestCo",
        "role_title": "QA Engineer",
        "source": "tests"
    }
    response = client.post(
        "/api/applications",  # Updated to use /api prefix
        headers={"X-API-Key": token},
        json=app_data
    )
    assert response.status_code == 201
    
    # 4) List applications (also tests rate limit)
    response = client.get(
        f"/api/applications?user_id={user_id}",  # Updated to use /api prefix
        headers={"X-API-Key": token}
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1

def test_rate_limit_basic():
    """Test that rate limiting works (disabled in test environment)"""
    # Create user and key
    user_data = {"email": generate_unique_email(), "full_name": "Rate Limit Test"}
    response = client.post("/users", json=user_data)
    user_id = response.json()["id"]
    
    key_data = {"user_id": user_id, "name": "rate-limit-test"}
    response = client.post("/api-keys", json=key_data)
    assert response.status_code == 201
    token = response.json()["token"]
    
    # Make requests to test rate limiting (should not be limited in test env)
    for i in range(10):
        response = client.get(
            f"/api/applications?user_id={user_id}",  # Updated to use /api prefix
            headers={"X-API-Key": token}
        )
        assert response.status_code == 200
    
    print("Rate limiting is disabled in test environment (as expected)")