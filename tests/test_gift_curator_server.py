from servers.gift_curator.server import mcp


def test_mcp_instance_exists():
    assert mcp is not None


def test_mcp_name_uses_english_korean_pair():
    """PlayMCP 규정: description에 영문+국문 병기 필수."""
    assert mcp.name == "Gift Curator(선물고민러)"


def test_mcp_instructions_describe_service():
    instructions = getattr(mcp, "instructions", "") or ""
    assert "선물고민러" in instructions
