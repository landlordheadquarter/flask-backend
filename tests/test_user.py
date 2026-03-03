import pytest
from landlordhq.app import create_app
from landlordhq.extensions import db

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_register_user(client):
    # Define the payload
    payload = {
        "name": "John Doe",
        "email": "johndoe211@example.com",
        "password": "securepassword"
    }

    # Send a POST request
    response = client.post("/api/account/register", json=payload)

    # Assert the response
    assert response.status_code == 201
    assert response.get_json() == {"message": "User registered successfully"}
    
    
def test_account_login(client):
    # Step 1: Register a user first
    register_payload = {
        "name": "John Doe",
        "email": "johndoe4@example.com",
        "password": "securepassword"
    }
    register_response = client.post("/api/account/register", json=register_payload)
    assert register_response.status_code == 201
    assert register_response.get_json()["message"] == "User registered successfully"

    # Step 2: Login with the registered user
    login_payload = {
        "email": "johndoe4@example.com",
        "password": "securepassword"
    }
    login_response = client.post("/api/account/login", json=login_payload)

    # Step 3: Assert the login response
    assert login_response.status_code == 200
    response_data = login_response.get_json()
    assert response_data["message"] == "Login successful"
    assert response_data["user"]["name"] == "John Doe"
    assert response_data["user"]["email"] == "johndoe4@example.com"

    # Step 4: Test invalid login (wrong password)
    invalid_login_payload = {
        "email": "johndoe4@example.com",
        "password": "wrongpassword"
    }
    invalid_login_response = client.post("/api/account/login", json=invalid_login_payload)
    assert invalid_login_response.status_code == 401
    assert invalid_login_response.get_json()["error"] == "Invalid password"

    # Step 5: Test invalid login (non-existent user)
    non_existent_user_payload = {
        "email": "nonexistent@example.com",
        "password": "somepassword"
    }
    non_existent_user_response = client.post("/api/account/login", json=non_existent_user_payload)
    assert non_existent_user_response.status_code == 404
    assert non_existent_user_response.get_json()["error"] == "User not found"