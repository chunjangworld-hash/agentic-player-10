import pytest
from pytest_httpx import HTTPXMock

from shared.http_client import HttpClient
from shared.tavily_search import TavilySearch


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from shared.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_tavily_search(httpx_mock: HTTPXMock, monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    from shared.config import get_settings
    get_settings.cache_clear()

    httpx_mock.add_response(
        json={
            "results": [
                {"title": "Result 1", "url": "https://x.com/1", "content": "snippet"},
            ],
        },
    )

    client = HttpClient()
    try:
        tavily = TavilySearch(http=client)
        results = await tavily.search("수면 안마기 후기", max_results=5)

        assert len(results) == 1
        assert results[0]["url"] == "https://x.com/1"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_tavily_caches_for_5min(httpx_mock: HTTPXMock, monkeypatch):
    """Tavily는 캐싱 OK — 같은 query 두 번째 호출은 캐시."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    from shared.config import get_settings
    get_settings.cache_clear()

    httpx_mock.add_response(json={"results": []})

    client = HttpClient()
    try:
        tavily = TavilySearch(http=client)
        await tavily.search("test")
        await tavily.search("test")

        assert len(httpx_mock.get_requests()) == 1
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_tavily_sends_api_key_in_params(httpx_mock: HTTPXMock, monkeypatch):
    """Tavily는 인증을 URL 파라미터로 보냄 (헤더 X)."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-secret-123")
    from shared.config import get_settings
    get_settings.cache_clear()

    httpx_mock.add_response(json={"results": []})

    client = HttpClient()
    try:
        tavily = TavilySearch(http=client)
        await tavily.search("auth check")
        req = httpx_mock.get_requests()[0]
        assert "api_key=tvly-secret-123" in str(req.url)
        assert "query=auth+check" in str(req.url) or "query=auth%20check" in str(req.url)
    finally:
        await client.aclose()
