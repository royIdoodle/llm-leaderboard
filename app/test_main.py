import pytest
import httpx
from app.main import app


@pytest.mark.asyncio
async def test_model_across_benches_non_numeric_version():
    """测试模型名称以非数字结尾的情况（如gpt-turbo）"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/models/gpt-turbo/benches")
    assert response.status_code == 200
    assert "total" in response.json()
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_model_across_benches_numeric_version():
    """测试模型名称以数字结尾的情况（如gpt-4）"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/models/gpt-4/benches")
    assert response.status_code == 200
    assert "total" in response.json()
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_model_across_benches_latest_only_false():
    """测试latest_only参数为False的情况"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/models/gpt-turbo/benches?latest_only=false")
    assert response.status_code == 200
    assert "total" in response.json()
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_model_across_benches_latest_only_true():
    """测试latest_only参数为True的情况"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/models/gpt-turbo/benches?latest_only=true")
    assert response.status_code == 200
    assert "total" in response.json()
    assert "items" in response.json()
