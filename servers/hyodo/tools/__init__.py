"""servers/hyodo/tools — 효도비서 Tool 등록 aggregator.

각 Tool은 자신의 모듈에 register(mcp) 함수를 노출.
register_all(mcp)가 모든 Tool register를 일괄 호출.

새 Tool 추가 절차:
1. servers/hyodo/tools/<tool_name>.py 작성 + register(mcp) 정의
2. 아래 _TOOL_MODULES 리스트에 모듈 import 추가
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from servers.hyodo.tools import compose_anbu, compose_parent_warning, save_to_memo_chat

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_TOOL_MODULES = [
    save_to_memo_chat,
    compose_parent_warning,
    compose_anbu,
]


def register_all(mcp: "FastMCP") -> None:
    """모든 효도비서 Tool을 FastMCP 인스턴스에 등록."""
    for mod in _TOOL_MODULES:
        mod.register(mcp)
