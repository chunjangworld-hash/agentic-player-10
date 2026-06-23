import pytest
from pytest_httpx import HTTPXMock

from servers.gift_curator.tools.refine_recommendation import (
    RefineRecommendationInput,
    refine_recommendation,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from shared.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_cheaper_direction(httpx_mock: HTTPXMock, monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": []})
    httpx_mock.add_response(json={"results": []})

    inp = RefineRecommendationInput(
        previous_keywords=["안마의자"],
        feedback_direction="cheaper",
        recipient_brief="엄마 환갑",
        new_budget_max=50000,
    )
    result = await refine_recommendation(inp)
    assert "엄마" in result
    # 새 예산 적용
    assert "50,000" in result or "5만" in result
    # 회피 카테고리에 이전 키워드
    assert "안마의자" in result
    # 방향 표시
    assert "cheaper" in result or "재추천" in result


@pytest.mark.asyncio
async def test_different_category_direction(httpx_mock: HTTPXMock, monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")

    httpx_mock.add_response(json={"items": []})
    httpx_mock.add_response(json={"results": []})

    inp = RefineRecommendationInput(
        previous_keywords=["디퓨저", "향초"],
        feedback_direction="different_category",
        recipient_brief="엄마 선물",
    )
    result = await refine_recommendation(inp)
    assert "디퓨저" in result and "향초" in result
    assert "different_category" in result or "재추천" in result


@pytest.mark.asyncio
async def test_invalid_feedback_direction_raises():
    """feedback_direction Literal validation."""
    import pytest
    with pytest.raises(Exception):
        RefineRecommendationInput(
            previous_keywords=["A"],
            feedback_direction="invalid_dir",  # not in Literal
            recipient_brief="엄마",
        )
