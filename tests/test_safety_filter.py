from shared.safety_filter import SafetyFilter


def test_medical_certainty_phrase_gets_disclaimer():
    sf = SafetyFilter()
    text = "이 약을 드시면 무릎이 나아요."
    result = sf.apply(text)
    assert "의료 진단·처방이 아닙니다" in result
    assert text in result  # 원문 유지


def test_financial_certainty_phrase_gets_disclaimer():
    sf = SafetyFilter()
    text = "100% 안전한 투자입니다."
    result = sf.apply(text)
    assert "투자 권유가 아닙니다" in result


def test_scam_certainty_gets_softened():
    sf = SafetyFilter()
    text = "100% 사기입니다."
    result = sf.apply(text)
    # 확정 표현이 약화되거나 disclaimer 부착
    assert "100% 사기" not in result or "참고용" in result


def test_clean_text_unchanged():
    sf = SafetyFilter()
    text = "엄마께 안부 한 줄 보내세요."
    result = sf.apply(text)
    assert result.strip() == text
