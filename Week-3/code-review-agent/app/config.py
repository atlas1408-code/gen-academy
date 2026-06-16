"""Environment loading and app settings."""
import os

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "postgresql://cra:cra@localhost:5433/code_review"
)

# ── Nebius Token Factory ──────────────────────────────────────────────────
NEBIUS_API_KEY: str = os.getenv("NEBIUS_API_KEY", "")
NEBIUS_BASE_URL: str = os.getenv(
    "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"
)

# Model id per agent (verified against the Token Factory /models catalog).
MODELS = {
    "quality": os.getenv("MODEL_QUALITY", "moonshotai/Kimi-K2.6"),
    "security": os.getenv("MODEL_SECURITY", "deepseek-ai/DeepSeek-V3.2"),
    "test_gap": os.getenv("MODEL_TEST_GAP", "meta-llama/Llama-3.3-70B-Instruct"),
    "consolidate": os.getenv(
        "MODEL_CONSOLIDATE", "Qwen/Qwen3-235B-A22B-Instruct-2507"
    ),
}


def require_nebius_key() -> str:
    return _require("NEBIUS_API_KEY")
