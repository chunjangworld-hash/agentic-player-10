"""환경 변수 로딩 + 설정 객체."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # 외부 API 키는 옵셔널 — 사용 시점(NaverSearch/TavilySearch 호출)에 검증.
    # 효도비서처럼 외부 API를 안 쓰는 서버도 부팅 가능해야 함 (KC 배포 호환).
    naver_client_id: str = ""
    naver_client_secret: str = ""
    tavily_api_key: str = ""
    log_level: str = "INFO"
    naver_max_per_query: int = 10
    tavily_max_results: int = 5
    response_max_chars: int = 22000  # 24k 한계 - 2k 버퍼
    external_call_timeout: float = 5.0
    external_call_concurrency: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            naver_client_id=os.environ.get("NAVER_CLIENT_ID", ""),
            naver_client_secret=os.environ.get("NAVER_CLIENT_SECRET", ""),
            tavily_api_key=os.environ.get("TAVILY_API_KEY", ""),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """모듈 전역 캐시된 Settings."""
    return Settings.from_env()
