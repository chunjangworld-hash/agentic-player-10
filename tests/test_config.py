import pytest

from shared.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """get_settings는 lru_cache라 monkeypatch와 충돌 — 각 테스트 전후로 비움."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "test_id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    settings = Settings.from_env()

    assert settings.naver_client_id == "test_id"
    assert settings.naver_client_secret == "test_secret"
    assert settings.tavily_api_key == "tvly-test"
    assert settings.log_level == "INFO"
    assert settings.response_max_chars == 22000


def test_settings_missing_keys_defaults_to_empty(monkeypatch):
    """외부 API 키는 옵셔널 — 누락 시 부팅은 통과, 사용 시점에서 검증."""
    monkeypatch.delenv("NAVER_CLIENT_ID", raising=False)
    monkeypatch.delenv("NAVER_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    settings = Settings.from_env()

    assert settings.naver_client_id == ""
    assert settings.naver_client_secret == ""
    assert settings.tavily_api_key == ""
    assert settings.log_level == "INFO"


def test_get_settings_caches(monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "id1")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "s1")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-1")

    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2  # 캐싱 확인
