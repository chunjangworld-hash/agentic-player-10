from servers.hyodo.tools.compose_parent_warning import (
    ComposeParentWarningInput,
    compose_parent_warning,
)


def test_loan_scam_warning():
    inp = ComposeParentWarningInput(scam_type="대출 사기", urgency="high")
    result = compose_parent_warning(inp)
    assert "절대" in result  # 강한 행동 지침
    assert "링크" in result
    assert "신고" in result


def test_unknown_scam_type_falls_back():
    inp = ComposeParentWarningInput(scam_type="외계인 사칭", urgency="medium")
    result = compose_parent_warning(inp)
    # fallback 템플릿 적용
    assert "사기" in result or "주의" in result


def test_high_urgency_emphasizes_action():
    inp = ComposeParentWarningInput(scam_type="택배 사칭", urgency="high")
    result = compose_parent_warning(inp)
    assert "즉시" in result or "당장" in result or "절대" in result
