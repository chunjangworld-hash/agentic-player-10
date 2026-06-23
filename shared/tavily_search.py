"""Tavily 검색 클라이언트 — 글로벌 보강 + 한국 부스팅. 5분 캐싱 OK."""
from __future__ import annotations

from typing import Any

from shared.config import get_settings
from shared.http_client import HttpClient
from shared.logging import setup_logger

logger = setup_logger("tavily_search")


class TavilySearch:
    URL = "https://api.tavily.com/search"
    CACHE_TTL = 300  # 5분

    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self._settings = get_settings()

    async def search(
        self,
        query: str,
        *,
        max_results: int | None = None,
        country: str = "south korea",
    ) -> list[dict[str, Any]]:
        max_n = max_results or self._settings.tavily_max_results

        params = {
            "api_key": self._settings.tavily_api_key,
            "query": query,
            "max_results": max_n,
            "country": country,
            "search_depth": "basic",
        }
        data = await self._http.get(self.URL, params=params, cache_ttl=self.CACHE_TTL)
        results = data.get("results", [])
        logger.info("tavily_search", extra={"query": query, "count": len(results)})
        return results
