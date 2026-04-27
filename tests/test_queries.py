import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db

@pytest.fixture
def db():
    engine = create_engine("sqlite:///./test_queries.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    from fastapi.testclient import TestClient
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_get_drawing_query_integration(client):
    # 1. Register and login
    client.post("/auth/register", json={"email": "q@test.com", "nickname": "q", "password": "pass"})
    login_res = client.post("/auth/login", data={"username": "q", "password": "pass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create drawing
    client.post("/drawings/", json={"title": "Query Test", "first_layer_data": "data1"}, headers=headers)
    
    # 3. Query drawing
    res = client.get("/drawings/1", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Query Test"
    assert len(data["layers"]) == 1
    assert data["layers"][0]["image_data"] == "data1"

def test_feed_query_integration(client):
    # Setup two users
    client.post("/auth/register", json={"email": "u1@test.com", "nickname": "u1", "password": "pass"})
    client.post("/auth/register", json={"email": "u2@test.com", "nickname": "u2", "password": "pass"})
    
    # Login as u1
    login_res = client.post("/auth/login", data={"username": "u1", "password": "pass"})
    u1_token = login_res.json()["access_token"]
    u1_headers = {"Authorization": f"Bearer {u1_token}"}
    
    # Login as u2
    login_res = client.post("/auth/login", data={"username": "u2", "password": "pass"})
    u2_token = login_res.json()["access_token"]
    u2_headers = {"Authorization": f"Bearer {u2_token}"}
    
    # u2 creates a drawing
    client.post("/drawings/", json={"title": "U2 Art", "first_layer_data": "data2"}, headers=u2_headers)
    
    # u1 follows u2
    client.post("/drawings/users/2/follow", headers=u1_headers)
    
    # u1 checks feed
    res = client.get("/drawings/feed", headers=u1_headers)
    assert res.status_code == 200
    feed = res.json()
    assert len(feed) == 1
    assert feed[0]["title"] == "U2 Art"
