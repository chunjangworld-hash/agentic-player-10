"""servers/gift_curator/tools — 선물고민러 Tool 등록 aggregator.

각 Tool은 자신의 모듈에 register(mcp) 함수를 노출.
register_all(mcp)가 모든 Tool register를 일괄 호출.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from servers.gift_curator.tools import compose_gift_message

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

_TOOL_MODULES: list = [
    compose_gift_message,
]


def register_all(mcp: "FastMCP") -> None:
    """모든 선물고민러 Tool을 FastMCP 인스턴스에 등록."""
    for mod in _TOOL_MODULES:
        mod.register(mcp)
