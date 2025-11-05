from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_query_unknown_nation():
    """测试当nation参数为"Unknown"时，API不再返回500错误"""
    response = client.get("/api/query?nation=Unknown")
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"