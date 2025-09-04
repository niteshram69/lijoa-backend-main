import os
import uuid
from fastapi.testclient import TestClient
from app.main import app

# Set test environment
os.environ["APP_ENV"] = "test"

client = TestClient(app)

def generate_unique_email():
    """Generate a unique email for testing"""
    return f"test-{uuid.uuid4().hex[:8]}@example.com"

def test_create_user_and_application_and_list():
    """Test the complete workflow"""
    # Create a user with unique email
    user_data = {"email": generate_unique_email(), "full_name": "API Test User"}
    response = client.post("/users", json=user_data)
    
    # Should always succeed with unique email
    assert response.status_code == 201
    user_id = response.json()["id"]
    print(f"Created new user with ID: {user_id}")
    
    # Create API key for the user
    key_data = {"user_id": user_id, "name": "test-key"}
    response = client.post("/api-keys", json=key_data)
    assert response.status_code == 201
    token = response.json()["token"]
    print(f"Created API key: {token[:20]}...")
    
    # Create an application for the user using the API key
    app_data = {
        "user_id": user_id,
        "company": "OpenAI",
        "role_title": "ML Engineer",
        "source": "linkedin",
        "status": "applied",
        "job_url": "https://example.com/job",
        "notes": "Created by test"
    }
    response = client.post("/api/applications", json=app_data, headers={"X-API-Key": token})
    assert response.status_code == 201
    
    app_response = response.json()
    assert app_response["company"] == "OpenAI"
    assert app_response["status"] == "applied"
    assert app_response["user_id"] == user_id
    print(f"Created application with ID: {app_response['id']}")
    
    # List applications for this user
    response = client.get(f"/api/applications?user_id={user_id}&limit=10&offset=0", headers={"X-API-Key": token})
    assert response.status_code == 200
    
    list_response = response.json()
    assert "items" in list_response
    assert isinstance(list_response["items"], list)
    assert list_response["total"] >= 1
    assert list_response["limit"] == 10
    assert list_response["offset"] == 0
    print(f"Found {list_response['total']} applications for user {user_id}")

def test_create_user_duplicate_email():
    """Test that creating a user with duplicate email returns 409"""
    # Create first user with unique email
    email = generate_unique_email()
    user_data = {"email": email, "full_name": "First User"}
    response = client.post("/users", json=user_data)
    assert response.status_code == 201
    
    # Try to create user with same email
    response = client.post("/users", json=user_data)
    assert response.status_code == 409
    assert "Email already exists" in response.json()["detail"]
    print("Correctly rejected duplicate email")

def test_create_application_invalid_user():
    """Test creating application with non-existent user ID returns 404"""
    # First create a user and API key
    user_data = {"email": generate_unique_email(), "full_name": "Test User"}
    response = client.post("/users", json=user_data)
    user_id = response.json()["id"]
    
    key_data = {"user_id": user_id, "name": "test-key"}
    response = client.post("/api-keys", json=key_data)
    token = response.json()["token"]
    
    # Try to create application with non-existent user ID
    app_data = {
        "user_id": 99999,  # Non-existent user ID
        "company": "Test Company",
        "role_title": "Test Role"
    }
    response = client.post("/api/applications", json=app_data, headers={"X-API-Key": token})
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
    print("Correctly rejected application for non-existent user")

def test_list_applications_with_filters():
    """Test listing applications with various filters"""
    # Create a user with unique email
    email = generate_unique_email()
    user_data = {"email": email, "full_name": "Filter Test"}
    response = client.post("/users", json=user_data)
    user_id = response.json()["id"]
    
    # Create API key
    key_data = {"user_id": user_id, "name": "test-key"}
    response = client.post("/api-keys", json=key_data)
    token = response.json()["token"]
    
    # Create multiple applications with different statuses
    applications = [
        {"user_id": user_id, "company": "Company A", "role_title": "Role A", "status": "applied"},
        {"user_id": user_id, "company": "Company B", "role_title": "Role B", "status": "interviewing"},
        {"user_id": user_id, "company": "Company C", "role_title": "Role C", "status": "applied"},
    ]
    
    for app in applications:
        response = client.post("/api/applications", json=app, headers={"X-API-Key": token})
        assert response.status_code == 201
    
    # Test filtering by user
    response = client.get(f"/api/applications?user_id={user_id}", headers={"X-API-Key": token})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    
    # Test filtering by status
    response = client.get(f"/api/applications?user_id={user_id}&status=applied", headers={"X-API-Key": token})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2  # At least 2 applied applications
    for app in data["items"]:
        assert app["status"] == "applied"
    
    # Test pagination
    response = client.get(f"/api/applications?user_id={user_id}&limit=1&offset=1", headers={"X-API-Key": token})
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 1
    assert data["offset"] == 1
    assert len(data["items"]) <= 1
    
    print("Successfully tested application filters and pagination")

def test_application_validation():
    """Test application input validation"""
    # Create a user with unique email
    email = generate_unique_email()
    user_data = {"email": email, "full_name": "Validation Test"}
    response = client.post("/users", json=user_data)
    user_id = response.json()["id"]
    
    # Create API key
    key_data = {"user_id": user_id, "name": "test-key"}
    response = client.post("/api-keys", json=key_data)
    token = response.json()["token"]
    
    # Test empty company name
    app_data = {
        "user_id": user_id,
        "company": "",  # Empty company
        "role_title": "Valid Role"
    }
    response = client.post("/api/applications", json=app_data, headers={"X-API-Key": token})
    assert response.status_code == 422  # Validation error
    
    # Test empty role title
    app_data = {
        "user_id": user_id,
        "company": "Valid Company",
        "role_title": ""  # Empty role
    }
    response = client.post("/api/applications", json=app_data, headers={"X-API-Key": token})
    assert response.status_code == 422  # Validation error
    
    # Test invalid status
    app_data = {
        "user_id": user_id,
        "company": "Valid Company",
        "role_title": "Valid Role",
        "status": "invalid_status"  # Invalid status
    }
    response = client.post("/api/applications", json=app_data, headers={"X-API-Key": token})
    assert response.status_code == 422  # Validation error
    
    print("Successfully tested application input validation")