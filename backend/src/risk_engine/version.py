"""Rule set identity by content hash.

Constitution Principle I requires version-pinned rules. A declared version string can drift
from the rules it names; a content hash cannot. The version is derived from the source of the
rule modules themselves, so editing a threshold changes the version by construction.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

#: Modules whose content defines the deterministic behaviour of the engine.
_RULE_SOURCES = ("rules.py", "factors.py", "freshness.py", "confidence.py", "types.py")


@lru_cache(maxsize=1)
def rule_set_version() -> str:
    """Return a stable short hash identifying the current rule set.

    Deterministic across processes and machines: it hashes file bytes with normalised line
    endings, so a Windows checkout and a Linux CI runner agree.
    """
    digest = hashlib.sha256()
    here = Path(__file__).parent
    for name in _RULE_SOURCES:
        content = (here / name).read_bytes().replace(b"\r\n", b"\n")
        digest.update(name.encode("utf-8"))
        digest.update(content)
    return f"rs-{digest.hexdigest()[:16]}"
