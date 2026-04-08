import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.core.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_register(client):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "nickname": "tester", "password": "password123"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert response.json()["nickname"] == "tester"

def test_login(client):
    # First register
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "nickname": "tester", "password": "password123"}
    )
    # Login with email
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Login with nickname
    response = client.post(
        "/auth/login",
        data={"username": "tester", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_drawing(client):
    # Register and login
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "nickname": "tester", "password": "password123"}
    )
    login_res = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create drawing
    response = client.post(
        "/drawings/",
        json={"title": "My Drawing", "first_layer_data": "base64data"},
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["title"] == "My Drawing"
    assert len(response.json()["layers"]) == 1

def test_add_layer(client):
    # Setup: User 1 creates drawing, User 2 adds layer
    client.post("/auth/register", json={"email": "user1@example.com", "nickname": "u1", "password": "password"})
    client.post("/auth/register", json={"email": "user2@example.com", "nickname": "u2", "password": "password"})
    
    token1 = client.post("/auth/login", data={"username": "user1@example.com", "password": "password"}).json()["access_token"]
    token2 = client.post("/auth/login", data={"username": "user2@example.com", "password": "password"}).json()["access_token"]
    
    # User 1 creates drawing
    res = client.post("/drawings/", json={"title": "D1", "first_layer_data": "L1"}, headers={"Authorization": f"Bearer {token1}"})
    drawing_id = res.json()["id"]
    
    # User 2 adds layer
    res = client.post(f"/drawings/{drawing_id}/layers", json={"image_data": "L2"}, headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 201
    
    # Check drawing
    res = client.get(f"/drawings/{drawing_id}")
    assert len(res.json()["layers"]) == 2
    assert res.json()["layers"][0]["image_data"] == "L1"
    assert res.json()["layers"][1]["image_data"] == "L2"

def test_like_drawing(client):
    client.post("/auth/register", json={"email": "u1@ex.com", "nickname": "u1", "password": "p"})
    token = client.post("/auth/login", data={"username": "u1@ex.com", "password": "p"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.post("/drawings/", json={"title": "T", "first_layer_data": "D"}, headers=headers)
    d_id = res.json()["id"]
    
    # Like
    res = client.post(f"/drawings/{d_id}/like", headers=headers)
    assert res.status_code == 200
    
    # Double like should fail
    res = client.post(f"/drawings/{d_id}/like", headers=headers)
    assert res.status_code == 409
    
    # Check count
    res = client.get(f"/drawings/{d_id}")
    assert res.json()["likes_count"] == 1

def test_follow_and_feed(client):
    client.post("/auth/register", json={"email": "u1@ex.com", "nickname": "u1", "password": "p"})
    client.post("/auth/register", json={"email": "u2@ex.com", "nickname": "u2", "password": "p"})
    
    t1 = client.post("/auth/login", data={"username": "u1@ex.com", "password": "p"}).json()["access_token"]
    t2 = client.post("/auth/login", data={"username": "u2@ex.com", "password": "p"}).json()["access_token"]
    
    # Get u2 id
    u2_id = 2 # Assuming it is 2, but let's be safer in real app.
    
    # u2 creates drawing
    client.post("/drawings/", json={"title": "U2 Drawing", "first_layer_data": "data"}, headers={"Authorization": f"Bearer {t2}"})
    
    # u1 feed should be empty
    res = client.get("/drawings/feed", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 0
    
    # u1 follows u2
    client.post(f"/drawings/users/{u2_id}/follow", headers={"Authorization": f"Bearer {t1}"})
    
    # Check u1 feed should have u2 drawing
    res = client.get("/drawings/feed", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "U2 Drawing"

def test_unfollow(client):
    client.post("/auth/register", json={"email": "u1@ex.com", "nickname": "u1", "password": "p"})
    client.post("/auth/register", json={"email": "u2@ex.com", "nickname": "u2", "password": "p"})
    
    t1 = client.post("/auth/login", data={"username": "u1@ex.com", "password": "p"}).json()["access_token"]
    u2_id = 2
    
    # Follow
    client.post(f"/drawings/users/{u2_id}/follow", headers={"Authorization": f"Bearer {t1}"})
    
    # Check status
    res = client.get(f"/drawings/users/{u2_id}/is_following", headers={"Authorization": f"Bearer {t1}"})
    assert res.json()["is_following"] is True
    
    # Unfollow
    res = client.delete(f"/drawings/users/{u2_id}/unfollow", headers={"Authorization": f"Bearer {t1}"})
    assert res.status_code == 200
    
    # Check status again
    res = client.get(f"/drawings/users/{u2_id}/is_following", headers={"Authorization": f"Bearer {t1}"})
    assert res.json()["is_following"] is False

def test_user_profile_drawings(client):
    # Setup users
    client.post("/auth/register", json={"email": "u1@ex.com", "nickname": "u1", "password": "p"})
    client.post("/auth/register", json={"email": "u2@ex.com", "nickname": "u2", "password": "p"})
    
    t1 = client.post("/auth/login", data={"username": "u1@ex.com", "password": "p"}).json()["access_token"]
    t2 = client.post("/auth/login", data={"username": "u2@ex.com", "password": "p"}).json()["access_token"]
    
    # Get u1 and u2 IDs
    u1_id = client.get("/auth/me", headers={"Authorization": f"Bearer {t1}"}).json()["id"]
    u2_id = client.get("/auth/me", headers={"Authorization": f"Bearer {t2}"}).json()["id"]
    
    # u1 creates D1
    client.post("/drawings/", json={"title": "D1", "first_layer_data": "L1"}, headers={"Authorization": f"Bearer {t1}"})
    # u2 creates D2
    res = client.post("/drawings/", json={"title": "D2", "first_layer_data": "L2"}, headers={"Authorization": f"Bearer {t2}"})
    d2_id = res.json()["id"]
    
    # u1 contributes to D2
    client.post(f"/drawings/{d2_id}/layers", json={"image_data": "L3"}, headers={"Authorization": f"Bearer {t1}"})
    
    # Check u1 owned drawings
    res = client.get(f"/drawings/users/{u1_id}/drawings", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "D1"
    
    # Check u1 contributed drawings
    res = client.get(f"/drawings/users/{u1_id}/contributed", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "D2"
    
    # Check u2 owned drawings
    res = client.get(f"/drawings/users/{u2_id}/drawings", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "D2"
    
    # Check u2 contributed drawings (should be 0 since he owns D2)
    res = client.get(f"/drawings/users/{u2_id}/contributed", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 0

def test_search_drawings(client):
    # Setup users
    client.post("/auth/register", json={"email": "alice@example.com", "nickname": "alice", "password": "password"})
    client.post("/auth/register", json={"email": "bob@example.com", "nickname": "bob", "password": "password"})
    
    t1 = client.post("/auth/login", data={"username": "alice", "password": "password"}).json()["access_token"]
    t2 = client.post("/auth/login", data={"username": "bob", "password": "password"}).json()["access_token"]
    
    # Create drawings
    client.post("/drawings/", json={"title": "Sunset Landscape", "first_layer_data": "data1"}, headers={"Authorization": f"Bearer {t1}"})
    client.post("/drawings/", json={"title": "Mountain View", "first_layer_data": "data2"}, headers={"Authorization": f"Bearer {t2}"})
    client.post("/drawings/", json={"title": "City at Night", "first_layer_data": "data3"}, headers={"Authorization": f"Bearer {t2}"})
    
    # Search by painting name
    res = client.get("/drawings/feed?q=Sunset", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "Sunset Landscape"
    
    # Search by author nickname
    res = client.get("/drawings/feed?q=bob", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 2
    titles = [d["title"] for d in res.json()]
    assert "Mountain View" in titles
    assert "City at Night" in titles
    
    # Search by author email
    res = client.get("/drawings/feed?q=alice@example.com", headers={"Authorization": f"Bearer {t2}"})
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "Sunset Landscape"
    
    # Search with no results
    res = client.get("/drawings/feed?q=Nonexistent", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 0

    # Search case-insensitive
    res = client.get("/drawings/feed?q=SUNSET", headers={"Authorization": f"Bearer {t1}"})
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "Sunset Landscape"

def test_dedicated_search_endpoint(client):
    # Setup users
    client.post("/auth/register", json={"email": "alice@example.com", "nickname": "alice", "password": "password"})
    client.post("/auth/register", json={"email": "bob@example.com", "nickname": "bob", "password": "password"})
    
    t1 = client.post("/auth/login", data={"username": "alice", "password": "password"}).json()["access_token"]
    
    # Create drawings
    client.post("/drawings/", json={"title": "Sunset Landscape", "first_layer_data": "data1"}, headers={"Authorization": f"Bearer {t1}"})
    
    # Search
    res = client.get("/drawings/search?q=alice", headers={"Authorization": f"Bearer {t1}"})
    assert res.status_code == 200
    data = res.json()
    assert "users" in data
    assert "drawings" in data
    assert len(data["users"]) == 1
    assert data["users"][0]["nickname"] == "alice"
    assert len(data["drawings"]) == 1
    assert data["drawings"][0]["title"] == "Sunset Landscape"

