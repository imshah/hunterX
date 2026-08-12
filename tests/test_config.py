import pytest

from hunterx.config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("KIMI_API_TOKEN", "sk-test-token")
    monkeypatch.setenv("KIMI_BASE_URL", "https://api.moonshot.cn/anthropic")
    monkeypatch.setenv("KIMI_MODEL", "kimi-k2.5")

    settings = Settings()
    assert settings.kimi_api_token.get_secret_value() == "sk-test-token"
    assert settings.kimi_base_url == "https://api.moonshot.cn/anthropic"
    assert settings.kimi_model == "kimi-k2.5"


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("KIMI_API_TOKEN", "sk-test-token")
    monkeypatch.delenv("OPTIMIZATION_ROUNDS", raising=False)
    monkeypatch.delenv("TARGET_SCORE", raising=False)
    monkeypatch.delenv("KIMI_MODEL", raising=False)
    monkeypatch.delenv("KIMI_BASE_URL", raising=False)

    settings = Settings(_env_file=None)
    assert settings.optimization_rounds == 5
    assert settings.target_score == 95
    assert settings.kimi_model == "kimi-k2.6"
    assert settings.kimi_base_url == "https://api.moonshot.ai/anthropic"


def test_settings_override(monkeypatch):
    monkeypatch.setenv("KIMI_API_TOKEN", "sk-test-token")

    settings = Settings(optimization_rounds=5, target_score=90)
    assert settings.optimization_rounds == 5
    assert settings.target_score == 90


def test_settings_validation_rounds(monkeypatch):
    monkeypatch.setenv("KIMI_API_TOKEN", "sk-test-token")

    with pytest.raises(Exception):
        Settings(optimization_rounds=0)

    with pytest.raises(Exception):
        Settings(optimization_rounds=11)


def test_create_llm_client_requires_token(monkeypatch):
    monkeypatch.delenv("KIMI_API_TOKEN", raising=False)

    settings = Settings(_env_file=None)
    with pytest.raises(ValueError, match="KIMI_API_TOKEN"):
        settings.create_llm_client()
