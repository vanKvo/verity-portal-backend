import pytest

def test_register_user(client):
    response = client.post("/auth/register", json={"email": "newuser@corporate.com", "password": "password"})
    assert response.status_code == 201
    assert "access_token" in response.json()

def test_register_invalid_domain(client):
    response = client.post("/auth/register", json={"email": "newuser@gmail.com", "password": "password"})
    assert response.status_code == 400

def test_login_user(client):
    client.post("/auth/register", json={"email": "loginuser@corporate.com", "password": "password"})
    response = client.post("/auth/login", data={"username": "loginuser@corporate.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_password(client):
    client.post("/auth/register", json={"email": "loginuser2@corporate.com", "password": "password"})
    response = client.post("/auth/login", data={"username": "loginuser2@corporate.com", "password": "wrongpassword"})
    assert response.status_code == 401

def test_guest_login(client):
    response = client.post("/auth/guest-login")
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "guest" in response.json()["roles"]
