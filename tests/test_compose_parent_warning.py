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


def test_parent_brief_affects_output_when_provided():
    """parent_brief가 결과에 반영되는지 검증."""
    inp_with = ComposeParentWarningInput(
        scam_type="대출 사기",
        urgency="high",
        parent_brief="엄마 70대 시골 거주",
    )
    inp_without = ComposeParentWarningInput(
        scam_type="대출 사기",
        urgency="high",
    )
    result_with = compose_parent_warning(inp_with)
    result_without = compose_parent_warning(inp_without)
    # parent_brief가 제공되면 결과에 그 정보가 어떤 식으로든 반영되어야 함
    # (브리프 텍스트 직접 포함 OR 차별화된 톤 안내)
    assert result_with != result_without, (
        "parent_brief가 결과에 영향을 주지 않음 — 사용 안 되거나 효과 없는 듯"
    )
