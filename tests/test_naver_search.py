import pytest
from pytest_httpx import HTTPXMock

from shared.http_client import HttpClient
from shared.naver_search import NaverSearch


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from shared.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_search_blog(httpx_mock: HTTPXMock, monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "test_id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    from shared.config import get_settings
    get_settings.cache_clear()

    httpx_mock.add_response(
        json={
            "total": 100,
            "items": [
                {
                    "title": "<b>수면 안마기</b> 후기",
                    "link": "https://blog.naver.com/x/1",
                    "description": "써본 결과 좋아요",
                    "bloggername": "ㅇㅇ",
                },
                {
                    "title": "엄마 환갑 선물",
                    "link": "https://blog.naver.com/y/2",
                    "description": "마사지건 추천",
                    "bloggername": "ㅁㅁ",
                },
            ],
        },
    )

    client = HttpClient()
    try:
        naver = NaverSearch(http=client)
        results = await naver.search("수면 안마기", source="blog", max_results=5)

        assert len(results) == 2
        assert results[0]["link"] == "https://blog.naver.com/x/1"
        assert "<b>" not in results[0]["title"]
        assert results[0]["title"] == "수면 안마기 후기"
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_search_does_not_cache(httpx_mock: HTTPXMock, monkeypatch):
    """약관 준수 — 같은 query 두 번 호출 시 HTTP 요청도 두 번."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "test_id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    from shared.config import get_settings
    get_settings.cache_clear()

    httpx_mock.add_response(json={"items": []})
    httpx_mock.add_response(json={"items": []})

    client = HttpClient()
    try:
        naver = NaverSearch(http=client)
        await naver.search("test", source="blog")
        await naver.search("test", source="blog")

        assert len(httpx_mock.get_requests()) == 2
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_search_sends_auth_headers(httpx_mock: HTTPXMock, monkeypatch):
    """네이버 인증 헤더가 실제로 전송되는지."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "my_id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "my_secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    from shared.config import get_settings
    get_settings.cache_clear()

    httpx_mock.add_response(json={"items": []})

    client = HttpClient()
    try:
        naver = NaverSearch(http=client)
        await naver.search("test", source="cafe")
        req = httpx_mock.get_requests()[0]
        assert req.headers["X-Naver-Client-Id"] == "my_id"
        assert req.headers["X-Naver-Client-Secret"] == "my_secret"
        assert "cafearticle" in str(req.url)
    finally:
        await client.aclose()
