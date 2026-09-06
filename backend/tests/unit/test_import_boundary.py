"""T0.12 — Risk Engine purity, enforced automatically (Constitution Principle I).

Principle I erodes by import creep, not by decision. Nobody ever decides to make the safety
core depend on the network; someone adds one convenient import during a deadline. This test
is the guardrail, and it is deliberately a test rather than a code-review convention.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parents[2] / "src" / "risk_engine"

#: Packages the deterministic core must never reach for.
FORBIDDEN_PREFIXES = (
    # Application layers — the engine must not know they exist
    "orchestrator", "api", "audit", "consent", "explanation", "models",
    # Network and I/O
    "requests", "httpx", "urllib", "socket", "aiohttp", "http",
    # Databases
    "sqlalchemy", "asyncpg", "psycopg", "psycopg2", "sqlite3",
    # LLM clients — the engine may never consult a model (FR-002)
    "anthropic", "openai", "langchain", "litellm", "transformers",
    # Non-determinism
    "random", "secrets", "uuid",
)

ENGINE_FILES = sorted(p for p in ENGINE_DIR.glob("*.py"))


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                found.add(node.module)
    return found


def test_engine_directory_is_not_empty():
    assert ENGINE_FILES, "no engine modules found — the guard would pass vacuously"


@pytest.mark.parametrize("path", ENGINE_FILES, ids=lambda p: p.name)
def test_no_forbidden_imports(path: Path):
    for module in _imported_modules(path):
        root = module.split(".")[0]
        assert root not in FORBIDDEN_PREFIXES, (
            f"{path.name} imports '{module}'. The risk engine must stay pure "
            f"(Constitution Principle I) — safety-critical scoring cannot depend on the "
            f"network, a database, or a model."
        )


@pytest.mark.parametrize("path", ENGINE_FILES, ids=lambda p: p.name)
def test_no_wall_clock_reads(path: Path):
    """`now` is always passed in, so the engine's output is reproducible (SC-008)."""
    source = path.read_text(encoding="utf-8")
    for banned in ("datetime.now(", "datetime.utcnow(", "time.time(", "date.today("):
        assert banned not in source, (
            f"{path.name} reads the clock via {banned}. Time must be an argument, or "
            f"identical inputs stop producing identical scores."
        )
