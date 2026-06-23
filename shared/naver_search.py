"""네이버 검색 API 클라이언트 (블로그/카페).

⚠️ 약관:
- 검색 결과 캐싱 금지 (무단 복제·저장 금지 조항)
- 출처 표기 의무 — 응답 호출처에서 '네이버 검색 기반' 표기 필수
"""
from __future__ import annotations

import re
from typing import Any, Literal

from shared.config import get_settings
from shared.http_client import HttpClient
from shared.logging import setup_logger

logger = setup_logger("naver_search")

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html_tags(text: str) -> str:
    return _TAG_RE.sub("", text)


class NaverSearch:
    BLOG_URL = "https://openapi.naver.com/v1/search/blog.json"
    CAFE_URL = "https://openapi.naver.com/v1/search/cafearticle.json"

    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self._settings = get_settings()

    async def search(
        self,
        query: str,
        *,
        source: Literal["blog", "cafe"] = "blog",
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        url = self.BLOG_URL if source == "blog" else self.CAFE_URL
        headers = {
            "X-Naver-Client-Id": self._settings.naver_client_id,
            "X-Naver-Client-Secret": self._settings.naver_client_secret,
        }
        params = {"query": query, "display": min(max_results, 10)}

        # 약관 준수 — cache_ttl=0 명시 (HttpClient 기본값이지만 의도 명확화)
        data = await self._http.get(url, headers=headers, params=params, cache_ttl=0)

        items = data.get("items", [])
        for item in items:
            item["title"] = _strip_html_tags(item.get("title", ""))
            item["description"] = _strip_html_tags(item.get("description", ""))

        logger.info("naver_search", extra={"query": query, "source": source, "count": len(items)})
        return items
