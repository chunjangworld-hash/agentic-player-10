from datetime import date

from servers.hyodo.tools.compose_anbu import ComposeAnbuInput, compose_anbu


def test_basic_anbu_returns_parent_profile_and_season():
    inp = ComposeAnbuInput(
        parent_brief="엄마 60대 허리 안 좋음 등산 시작",
        tone="warm_polite",
    )
    result = compose_anbu(inp)
    assert "엄마" in result
    assert "60대" in result or "허리" in result
    # 시즌 컨텍스트 어떤 식으로든 반영 (월/계절/절기 중 하나)
    assert any(kw in result for kw in ["시즌", "절기", "계절", "월"])


def test_with_occasion():
    inp = ComposeAnbuInput(
        parent_brief="아빠 70대",
        occasion="비 오는 날",
        tone="brief",
    )
    result = compose_anbu(inp)
    # occasion이 결과에 반영
    assert "비" in result or "장마" in result or "비 오는 날" in result


def test_response_within_safe_limit():
    inp = ComposeAnbuInput(parent_brief="엄마 60대")
    result = compose_anbu(inp)
    # ResponseBuilder 22000자 안전 한계
    assert len(result) < 22000


def test_invalid_tone_raises():
    import pytest
    with pytest.raises(Exception):  # pydantic ValidationError or ValueError
        ComposeAnbuInput(parent_brief="엄마", tone="invalid_tone")
