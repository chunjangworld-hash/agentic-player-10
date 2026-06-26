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


def test_tone_changes_output():
    """톤이 다르면 출력의 추천 톤 섹션이 다르게 표시되어야."""
    inp_warm = ComposeAnbuInput(parent_brief="엄마 60대", tone="warm_polite")
    inp_brief = ComposeAnbuInput(parent_brief="엄마 60대", tone="brief")
    inp_playful = ComposeAnbuInput(parent_brief="엄마 60대", tone="playful")
    out_warm = compose_anbu(inp_warm)
    out_brief = compose_anbu(inp_brief)
    out_playful = compose_anbu(inp_playful)
    # 셋이 모두 달라야
    assert out_warm != out_brief
    assert out_brief != out_playful
    assert "warm_polite" in out_warm
    assert "brief" in out_brief
    assert "playful" in out_playful


def test_image_base64_accepted_as_forward_compat():
    """image_base64는 현재 무시되지만 input으로 받아들여져야 (forward compat)."""
    inp = ComposeAnbuInput(
        parent_brief="엄마 60대",
        image_base64="dGVzdA==",  # base64 of 'test'
    )
    result = compose_anbu(inp)
    assert len(result) > 100  # 정상 응답 생성됨
    # image_base64 내용이 결과에 노출되지 않아야 (현재는 무시)
    assert "dGVzdA==" not in result


def test_occasion_omitted_when_none():
    """occasion=None이면 '특별 occasion' 섹션 없음."""
    inp = ComposeAnbuInput(parent_brief="엄마 60대")
    result = compose_anbu(inp)
    assert "특별 occasion" not in result
