import pytest
from pytest_httpx import HTTPXMock

from servers.gift_curator.tools.evaluate_gift_idea import (
    EvaluateGiftIdeaInput,
    evaluate_gift_idea,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from shared.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_evaluate_with_reviews(httpx_mock: HTTPXMock, monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": [
        {"title": "마사지건 추천", "link": "https://blog.b.com/2", "description": "재구매했습니다."},
    ]})
    httpx_mock.add_response(json={"results": [
        {"title": "마사지건 후기", "url": "https://x.com/1", "content": "직접 구매. 한 달 사용."},
    ]})

    inp = EvaluateGiftIdeaInput(
        gift_idea="마사지건",
        recipient_brief="엄마 환갑 20만원",
        user_budget=130000,
    )
    result = await evaluate_gift_idea(inp)
    assert "마사지건" in result
    assert "엄마" in result or "환갑" in result
    assert "네이버 검색 기반" in result  # Naver 사용 → footer


@pytest.mark.asyncio
async def test_evaluate_without_budget(httpx_mock: HTTPXMock, monkeypatch):
    """user_budget 미입력 시도 정상 동작."""
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": []})
    httpx_mock.add_response(json={"results": []})

    inp = EvaluateGiftIdeaInput(
        gift_idea="와인 세트",
        recipient_brief="친구 집들이",
    )
    result = await evaluate_gift_idea(inp)
    assert "와인 세트" in result
    assert "친구" in result or "집들이" in result


@pytest.mark.asyncio
async def test_evaluate_filters_ads(httpx_mock: HTTPXMock, monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": [
        {"title": "클린", "link": "https://x.com/1", "description": "직접 구매했습니다."},
        {"title": "광고", "link": "https://x.com/2", "description": "유료광고 포함 후기."},
    ]})
    httpx_mock.add_response(json={"results": []})

    inp = EvaluateGiftIdeaInput(
        gift_idea="제품X",
        recipient_brief="엄마 60대",
    )
    result = await evaluate_gift_idea(inp)
    # 광고 제거된 후 통계 노출
    assert "제품X" in result
    # 광고는 결과에 나오지 않아야
    assert "유료광고" not in result
