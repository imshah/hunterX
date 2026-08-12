from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Kimi (Moonshot AI) — uses the Anthropic-compatible Messages API
    kimi_api_token: SecretStr = Field(
        default=SecretStr(""), description="Moonshot/Kimi API token"
    )
    kimi_base_url: str = Field(
        default="https://api.moonshot.ai/anthropic",
        description="Kimi Anthropic-compatible API base URL",
    )
    kimi_model: str = Field(default="kimi-k2.6")
    # Extended-thinking budget in tokens. 0 disables thinking (recommended: the
    # optimizer's max_tokens budgets assume direct output, and thinking tokens
    # would otherwise consume that budget before any answer is produced).
    kimi_thinking_budget: int = Field(default=0, ge=0)

    # Optimizer
    optimization_rounds: int = Field(default=5, ge=1, le=10)
    target_score: int = Field(default=95, ge=50, le=100)

    # Paths
    output_dir: Path = Field(default=Path("output"))

    @property
    def thinking_param(self) -> dict:
        """Anthropic-style `thinking` argument for messages.create calls."""
        if self.kimi_thinking_budget > 0:
            return {"type": "enabled", "budget_tokens": self.kimi_thinking_budget}
        return {"type": "disabled"}

    def create_llm_client(self):
        token = self.kimi_api_token.get_secret_value()
        if not token:
            raise ValueError(
                "KIMI_API_TOKEN is required for LLM calls. Set it in your .env file."
            )
        import anthropic

        return anthropic.Anthropic(
            api_key=token,
            base_url=self.kimi_base_url,
        )


@lru_cache
def get_settings(**kwargs) -> Settings:
    return Settings(**kwargs)
