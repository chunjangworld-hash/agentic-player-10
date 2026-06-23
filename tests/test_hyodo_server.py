from servers.hyodo.server import mcp


def test_mcp_instance_exists():
    assert mcp is not None


def test_mcp_name_uses_english_korean_pair():
    """PlayMCP 규정: description에 영문+국문 병기 필수."""
    assert mcp.name == "Hyodo Secretary(효도비서)"


def test_mcp_instructions_describe_service():
    """instructions가 서버 역할 설명을 포함해야 호출 에이전트가 올바르게 활용."""
    instructions = getattr(mcp, "instructions", "") or ""
    assert "효도비서" in instructions
