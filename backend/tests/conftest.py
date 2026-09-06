"""Root fixtures. Shared builders live in tests/helpers.py to avoid conftest shadowing."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers import NOW  # noqa: E402


@pytest.fixture
def now() -> datetime:
    return NOW
