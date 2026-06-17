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

# In-product verifier (improvement #2) — re-checks each finding to cut false
# positives. Distinct from the finding-producing agents (quality/security/
# test_gap) AND from the eval judge, so the eval stays an independent measure.
VERIFIER_MODEL = os.getenv("VERIFIER_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507")

# Eval judge — deliberately a DIFFERENT model family than any reviewer OR the
# verifier above, to avoid self-grading bias when scoring precision.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")

# ── LangSmith tracing ─────────────────────────────────────────────────────
# LangChain auto-traces when these env vars are set (loaded above via .env):
# LANGCHAIN_TRACING_V2=true, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT. Exposed here
# so startup can report status.
LANGSMITH_ENABLED: bool = (
    os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    and bool(os.getenv("LANGCHAIN_API_KEY"))
)
LANGSMITH_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "code-review-agent")


def log_tracing_status() -> None:
    if LANGSMITH_ENABLED:
        print(f"[langsmith] tracing ON → project {LANGSMITH_PROJECT!r}")
    else:
        print("[langsmith] tracing OFF "
              "(set LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY to enable)")


def require_nebius_key() -> str:
    return _require("NEBIUS_API_KEY")
