from servers.gift_curator.tools.compose_gift_message import (
    ComposeGiftMessageInput,
    compose_gift_message,
)


def test_parent_birthday_returns_three_tones():
    inp = ComposeGiftMessageInput(
        gift_name="핸드크림",
        recipient_relationship="parent",
        occasion="환갑",
    )
    result = compose_gift_message(inp)
    assert "정중" in result or "formal" in result.lower()
    assert "따뜻" in result or "heartfelt" in result.lower()
    assert "캐주얼" in result or "casual" in result.lower()
    assert "핸드크림" in result


def test_specific_tone_only():
    inp = ComposeGiftMessageInput(
        gift_name="와인",
        recipient_relationship="friend",
        occasion="집들이",
        tone_preference="casual",
    )
    result = compose_gift_message(inp)
    # 톤 선호 지정 시 그 톤 강조
    assert "캐주얼" in result or "casual" in result.lower()


def test_unknown_combination_falls_back():
    """관계+행사 조합이 templates JSON에 없으면 fallback."""
    inp = ComposeGiftMessageInput(
        gift_name="책",
        recipient_relationship="other",
        occasion="이상한특별일",
    )
    result = compose_gift_message(inp)
    # fallback 동작 → 결과는 비어있지 않아야 함
    assert "이상한특별일" in result or len(result) > 100
