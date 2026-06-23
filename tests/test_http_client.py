import httpx
import pytest
from pytest_httpx import HTTPXMock

from shared.http_client import HttpClient


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from shared.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"hello": "world"})
    client = HttpClient()
    try:
        result = await client.get("https://example.com/api")
        assert result == {"hello": "world"}
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_get_with_timeout(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
    client = HttpClient()
    try:
        with pytest.raises(httpx.TimeoutException):
            await client.get("https://example.com/slow", timeout=0.5)
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_get_cache_hit_when_ttl_set(httpx_mock: HTTPXMock):
    """cache_ttl > 0 일 때 두 번째 호출은 캐시 적중."""
    httpx_mock.add_response(json={"value": 1})
    client = HttpClient()
    try:
        r1 = await client.get("https://example.com/cacheable", cache_ttl=60)
        r2 = await client.get("https://example.com/cacheable", cache_ttl=60)

        assert r1 == r2 == {"value": 1}
        assert len(httpx_mock.get_requests()) == 1
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_get_no_cache_by_default(httpx_mock: HTTPXMock):
    """cache_ttl=0 (기본) 일 때 매번 호출."""
    httpx_mock.add_response(json={"value": 1})
    httpx_mock.add_response(json={"value": 2})
    client = HttpClient()
    try:
        r1 = await client.get("https://example.com/no-cache")
        r2 = await client.get("https://example.com/no-cache")

        assert r1 == {"value": 1}
        assert r2 == {"value": 2}
        assert len(httpx_mock.get_requests()) == 2
    finally:
        await client.aclose()
