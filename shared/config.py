"""환경 변수 로딩 + 설정 객체."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    naver_client_id: str
    naver_client_secret: str
    tavily_api_key: str
    log_level: str = "INFO"
    naver_max_per_query: int = 10
    tavily_max_results: int = 5
    response_max_chars: int = 22000  # 24k 한계 - 2k 버퍼
    external_call_timeout: float = 5.0
    external_call_concurrency: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        required = ["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET", "TAVILY_API_KEY"]
        for key in required:
            if not os.environ.get(key):
                raise ValueError(
                    f"필수 환경 변수 누락: {key}. .env 파일 또는 환경 변수에 설정해주세요."
                )

        return cls(
            naver_client_id=os.environ["NAVER_CLIENT_ID"],
            naver_client_secret=os.environ["NAVER_CLIENT_SECRET"],
            tavily_api_key=os.environ["TAVILY_API_KEY"],
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """모듈 전역 캐시된 Settings."""
    return Settings.from_env()
