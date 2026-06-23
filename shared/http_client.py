"""비동기 HTTP 클라이언트 — 호출별 캐싱 정책 + 타임아웃 + 동시처리 제한."""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging import setup_logger

logger = setup_logger("http_client")


class HttpClient:
    """httpx.AsyncClient 래퍼.

    - 기본 타임아웃: settings.external_call_timeout (5초)
    - cache_ttl=0 (기본): 캐싱 안 함 — 네이버 약관 준수
    - cache_ttl>0: 해당 초 동안 in-memory 캐싱 — Tavily 등 캐싱 허용 API용
    - 동시 호출 제한: settings.external_call_concurrency (5)
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._client = httpx.AsyncClient(timeout=settings.external_call_timeout)
        self._semaphore = asyncio.Semaphore(settings.external_call_concurrency)
        self._cache: dict[str, tuple[float, Any]] = {}

    def _cache_key(self, url: str, params: dict | None) -> str:
        if not params:
            return url
        items = sorted(params.items())
        return url + "?" + "&".join(f"{k}={v}" for k, v in items)

    def _cache_get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        expire_at, value = entry
        if time.time() > expire_at:
            del self._cache[key]
            return None
        return value

    def _cache_set(self, key: str, value: Any, ttl: float) -> None:
        self._cache[key] = (time.time() + ttl, value)

    async def get(
        self,
        url: str,
        *,
        headers: dict | None = None,
        params: dict | None = None,
        timeout: float | None = None,
        cache_ttl: float = 0,
    ) -> dict:
        """GET 요청. cache_ttl=0 이면 캐싱 안 함."""
        if cache_ttl > 0:
            key = self._cache_key(url, params)
            cached = self._cache_get(key)
            if cached is not None:
                logger.info("http_cache_hit", extra={"url": url})
                return cached

        async with self._semaphore:
            response = await self._client.get(
                url, headers=headers, params=params, timeout=timeout
            )
            response.raise_for_status()
            data = response.json()

        if cache_ttl > 0:
            self._cache_set(self._cache_key(url, params), data, cache_ttl)

        return data

    async def aclose(self) -> None:
        await self._client.aclose()
