import pytest
from pytest_httpx import HTTPXMock

from servers.gift_curator.tools.curate_gifts import CurateGiftsInput, curate_gifts


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from shared.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_curate_returns_recipient_and_budget(httpx_mock: HTTPXMock, monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": [
        {"title": "수면 안마기 후기", "link": "https://blog.a.com/1",
         "description": "엄마 매일 쓰세요. 재구매했습니다."},
    ]})
    httpx_mock.add_response(json={"results": [
        {"title": "환갑 선물 추천", "url": "https://x.com/1", "content": "수면 안마기 좋아요"},
    ]})

    inp = CurateGiftsInput(
        recipient_brief="엄마 환갑 20만원 등산 시작 허리 안 좋음",
        budget_max=200000,
    )
    result = await curate_gifts(inp)

    assert "엄마" in result
    assert "20만" in result or "200,000" in result
    # SearchGift 파라미터 포함 (호출 에이전트가 카카오 MCP에 전달)
    assert "SearchGift" in result or "query" in result.lower() or "minPrice" in result
    assert "네이버 검색 기반" in result


@pytest.mark.asyncio
async def test_curate_extracts_budget_from_brief(httpx_mock: HTTPXMock, monkeypatch):
    """budget_max 미입력 시 brief에서 추출."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": []})
    httpx_mock.add_response(json={"results": []})

    inp = CurateGiftsInput(recipient_brief="아빠 생신 10만원 책")
    result = await curate_gifts(inp)
    # 10만원 추출 확인
    assert "10만" in result or "100,000" in result


@pytest.mark.asyncio
async def test_curate_avoid_categories(httpx_mock: HTTPXMock, monkeypatch):
    """avoid_categories가 출력에 명시되어 호출 에이전트가 참고."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": []})
    httpx_mock.add_response(json={"results": []})

    inp = CurateGiftsInput(
        recipient_brief="엄마 생신",
        budget_max=100000,
        avoid_categories=["향수", "건강식품"],
    )
    result = await curate_gifts(inp)
    assert "향수" in result and "건강식품" in result


@pytest.mark.asyncio
async def test_curate_recent_gifts_hint(httpx_mock: HTTPXMock, monkeypatch):
    """recent_gifts_hint 중복 회피 명시."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": []})
    httpx_mock.add_response(json={"results": []})

    inp = CurateGiftsInput(
        recipient_brief="엄마 추석",
        recent_gifts_hint=["한우 세트", "건강즙"],
    )
    result = await curate_gifts(inp)
    assert "한우" in result and "건강즙" in result
