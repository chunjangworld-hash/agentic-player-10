import pytest
from pytest_httpx import HTTPXMock

from servers.gift_curator.tools.find_real_recommendations import (
    FindRealRecommendationsInput,
    find_real_recommendations,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from shared.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_filters_ads_and_returns_clean(httpx_mock: HTTPXMock, monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    # Naver blog: 1 clean + 1 ad
    httpx_mock.add_response(json={
        "items": [
            {"title": "수면 안마기 후기", "link": "https://blog.a.com/1",
             "description": "직접 구매했습니다. 한 달 써보고 만족."},
            {"title": "체험단 수면 안마기", "link": "https://blog.b.com/2",
             "description": "체험단으로 받았어요. 광고 포함."},
        ],
    })
    # Naver cafe: empty
    httpx_mock.add_response(json={"items": []})
    # Tavily: 1 clean
    httpx_mock.add_response(json={
        "results": [
            {"title": "Real review", "url": "https://x.com/1", "content": "매일 사용 중"},
        ],
    })

    inp = FindRealRecommendationsInput(keyword="수면 안마기", max_results=5)
    result = await find_real_recommendations(inp)

    assert "수면 안마기" in result
    assert "blog.a.com" in result   # 클린 살아남음
    assert "체험단" not in result    # 광고 제거
    assert "네이버 검색 기반" in result  # mandatory_footer


@pytest.mark.asyncio
async def test_source_blog_only(httpx_mock: HTTPXMock, monkeypatch):
    """source_preference='blog'면 Naver blog만 호출."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": [
        {"title": "후기", "link": "https://x.com/1", "description": "재구매했습니다."},
    ]})

    inp = FindRealRecommendationsInput(
        keyword="홍삼", max_results=3, source_preference="blog",
    )
    result = await find_real_recommendations(inp)
    assert "홍삼" in result
    # 1번만 호출 (blog만)
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_empty_results_graceful(httpx_mock: HTTPXMock, monkeypatch):
    """모든 결과가 광고로 제거되어도 깨지지 않음."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": [
        {"title": "체험단 광고", "link": "https://x.com/1", "description": "유료광고 포함."},
    ]})
    httpx_mock.add_response(json={"items": []})
    httpx_mock.add_response(json={"results": []})

    inp = FindRealRecommendationsInput(keyword="공구 마감", max_results=5)
    result = await find_real_recommendations(inp)
    # 결과가 비어도 정상 응답 (메시지로)
    assert len(result) > 100
    assert "수면 안마기" not in result  # 다른 키워드 무관
