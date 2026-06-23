import pytest

from shared.response_builder import ResponseBuilder, ResponseTooLargeError


def test_build_simple_markdown():
    rb = ResponseBuilder()
    result = rb.build([
        ("# 제목", 1),
        ("본문 내용", 2),
    ])
    assert "# 제목" in result
    assert "본문 내용" in result


def test_respects_max_chars():
    rb = ResponseBuilder(max_chars=100)
    sections = [(f"section {i}: " + ("x" * 50), 1) for i in range(10)]
    result = rb.build(sections)
    # truncation marker 길이까지 포함한 안전 여유
    assert len(result) <= 100 + len(ResponseBuilder.TRUNCATION_MARKER)


def test_truncates_with_marker():
    rb = ResponseBuilder(max_chars=200)
    sections = [(f"section {i}: " + ("x" * 100), 1) for i in range(10)]
    result = rb.build(sections)
    assert "더 보기" in result or "..." in result


def test_priority_keeps_important_sections():
    """priority 낮은(숫자 큰) 섹션이 먼저 잘림."""
    rb = ResponseBuilder(max_chars=150)
    sections = [
        ("핵심 정보", 1),
        ("덜 중요한 정보" + ("y" * 100), 3),
        ("중간 정보" + ("z" * 50), 2),
    ]
    result = rb.build(sections)
    assert "핵심 정보" in result
    # priority 3 (덜 중요)이 가장 먼저 잘림 — 100자 padding이 빠져야 함
    assert "y" * 100 not in result


def test_within_default_limit_no_truncation():
    """기본 22000자 한계 안이면 marker 없음."""
    rb = ResponseBuilder()
    result = rb.build([("짧은 본문", 1)])
    assert "더 보기" not in result
    assert result.strip() == "짧은 본문"


def test_empty_sections_returns_empty():
    rb = ResponseBuilder()
    assert rb.build([]) == ""


def test_mandatory_footer_always_present():
    """약관 출처 표기는 본문이 truncate돼도 항상 포함."""
    rb = ResponseBuilder(max_chars=200)
    sections = [(f"section {i}: " + ("x" * 100), 1) for i in range(10)]
    result = rb.build(sections, mandatory_footer="네이버 검색 기반")
    assert result.endswith("네이버 검색 기반")
    assert "이하 생략" in result  # truncate된 상태 (TRUNCATION_MARKER)
    assert len(result) <= 200 + len(ResponseBuilder.TRUNCATION_MARKER)


def test_mandatory_footer_within_limit():
    """본문이 한계 안일 때도 footer 정상 부착."""
    rb = ResponseBuilder()
    result = rb.build([("짧은 본문", 1)], mandatory_footer="네이버 검색 기반")
    assert "짧은 본문" in result
    assert result.endswith("네이버 검색 기반")
    assert "더 보기" not in result


def test_mandatory_footer_too_large_raises():
    """footer가 max_chars 자체보다 크면 명확한 에러."""
    rb = ResponseBuilder(max_chars=10)
    with pytest.raises(ResponseTooLargeError, match="mandatory_footer"):
        rb.build([("x", 1)], mandatory_footer="x" * 100)
