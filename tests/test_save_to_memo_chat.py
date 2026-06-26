import pytest

from servers.hyodo.tools.save_to_memo_chat import (
    SaveToMemoChatInput,
    save_to_memo_chat,
)


def test_basic_format():
    inp = SaveToMemoChatInput(
        content="엄마 6월 안부: 장마철 허리 조심",
        category="anbu",
        label="엄마 6월 안부",
    )
    result = save_to_memo_chat(inp)
    assert "효도비서" in result
    assert "엄마 6월 안부" in result  # label
    assert "엄마 6월 안부: 장마철 허리 조심" in result  # content


def test_empty_content_raises():
    with pytest.raises(ValueError):
        SaveToMemoChatInput(content="", category="general")


def test_long_content_within_limit():
    inp = SaveToMemoChatInput(
        content="x" * 5000,
        category="general",
    )
    result = save_to_memo_chat(inp)
    # max_chars=22000 안전 한계 안
    assert len(result) < 22000


def test_warning_category_korean_label():
    inp = SaveToMemoChatInput(content="사기 의심 카톡 발견", category="warning")
    result = save_to_memo_chat(inp)
    assert "[카테고리: 경고]" in result


def test_event_category_with_no_label():
    """label=None branch."""
    inp = SaveToMemoChatInput(content="추석 D-30 알림", category="event", label=None)
    result = save_to_memo_chat(inp)
    assert "[카테고리: 이벤트]" in result
    assert "[라벨:" not in result  # label part omitted when None
