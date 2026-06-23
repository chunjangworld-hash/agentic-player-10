from datetime import date

from servers.hyodo.tools.find_upcoming_events import (
    FindUpcomingEventsInput,
    find_upcoming_events,
)


def test_finds_seasonal_events():
    inp = FindUpcomingEventsInput(parent_brief="엄마 60대", upcoming_days=60)
    result = find_upcoming_events(inp)
    assert "D-" in result  # 카운트다운 표시


def test_extracts_personal_date_from_brief():
    inp = FindUpcomingEventsInput(
        parent_brief="엄마 60대 생신 8월 15일",
        upcoming_days=90,
    )
    result = find_upcoming_events(inp)
    # 개인 생신 D-X 어떤 식으로든 반영
    assert "생신" in result or "8월" in result


def test_short_window():
    inp = FindUpcomingEventsInput(parent_brief="아빠", upcoming_days=7)
    result = find_upcoming_events(inp)
    assert "다가오는" in result or "챙길" in result or "이벤트" in result


def test_no_events_in_tiny_window():
    """upcoming_days=7 + 아무 키워드 없을 때 — 빈 결과여도 graceful."""
    inp = FindUpcomingEventsInput(parent_brief="엄마", upcoming_days=7)
    result = find_upcoming_events(inp)
    # 결과가 비어있어도 placeholder 메시지 또는 일반 안부 안내 있어야
    assert len(result) > 50


def test_invalid_upcoming_days_raises():
    """upcoming_days < 7 (validator min)."""
    import pytest
    with pytest.raises(Exception):
        FindUpcomingEventsInput(parent_brief="엄마", upcoming_days=3)
