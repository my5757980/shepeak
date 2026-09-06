"""T4.15 — submission accuracy review, as a test rather than a promise.

FR-010a (external chain anchoring) is deferred, so Principle V is only PARTIALLY met. Every
artifact that reaches a judge must therefore avoid claiming independent verifiability. A
review checklist would be forgotten under deadline pressure; this fails the build instead.

It also guards the opposite direction: the honesty caveats must actually be present, not
merely intended.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

#: Everything a judge, reader, or viewer could see.
AUDIENCE_FACING = sorted(
    p
    for p in [
        *(ROOT / "submission").glob("*.md"),
        ROOT / "README.md",
        *(ROOT / "frontend").rglob("*.html"),
        *(ROOT / "frontend" / "assets").glob("*.js"),
    ]
    if p.is_file()
)

#: Claims that are false while FR-010a is unbuilt. Matched only as positive assertions —
#: the artifacts are *required* to discuss the limitation, so the words themselves appear.
FORBIDDEN = [
    re.compile(r"\bis\s+independently\s+verifiab", re.I),
    re.compile(r"\bfully\s+auditable\b", re.I),
    re.compile(r"\btamper[-\s]?proof\b", re.I),
    re.compile(r"\bimmutable\s+audit\b", re.I),
    re.compile(r"\bcannot\s+be\s+(?:altered|tampered)\b", re.I),
]

#: Lines that legitimately contain the words while denying the claim.
NEGATING = re.compile(
    r"\b(?:not|never|isn'?t|no[t]?\s+yet|rather\s+than|instead\s+of|don'?t|"
    r"requires|needs|until|without|avoid|must\s+not|cannot\s+claim|"
    r"nothing\s+(?:here\s+)?(?:describes|claims))\b",
    re.I,
)


def _offending_lines(path: Path) -> list[tuple[int, str]]:
    hits = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if NEGATING.search(line):
            continue
        for pattern in FORBIDDEN:
            if pattern.search(line):
                hits.append((number, line.strip()))
                break
    return hits


def test_audience_facing_files_exist():
    assert AUDIENCE_FACING, "no audience-facing artifacts found — the guard would pass vacuously"


@pytest.mark.parametrize("path", AUDIENCE_FACING, ids=lambda p: p.name)
def test_no_overstated_audit_claim(path: Path):
    """FR-010a is deferred, so these claims would be false."""
    hits = _offending_lines(path)
    assert not hits, (
        f"{path.relative_to(ROOT)} overstates the audit guarantee while FR-010a is "
        f"unbuilt:\n"
        + "\n".join(f"  line {n}: {text}" for n, text in hits)
        + "\n  Accurate wording: 'append-only and tamper-evident against the application; "
        "independent anchoring is on the roadmap.'"
    )


class TestHonestyCaveatsArePresent:
    """The limitations must be stated, not merely not-overstated."""

    def test_readme_states_the_audit_limit(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        assert "tamper-evident" in text
        assert "not independently verifiable" in text or "not built" in text

    def test_readme_states_thresholds_are_provisional(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        assert "provisional" in text

    def test_readme_states_not_a_medical_device(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        assert "not a medical device" in text

    @pytest.mark.parametrize(
        "name", ["01-usp.md", "02-solution-overview.md", "03-pitch-deck.md"]
    )
    def test_each_submission_document_carries_the_caveats(self, name):
        path = ROOT / "submission" / name
        if not path.exists():
            pytest.skip(f"{name} not written yet")
        text = path.read_text(encoding="utf-8").lower()
        assert "tamper-evident" in text, f"{name} does not scope the audit claim"
        assert "provisional" in text, f"{name} does not flag provisional thresholds"

    def test_the_ui_shows_the_guarantee_scope_to_the_viewer(self):
        """The scope is on screen during the demo, not only in the documents."""
        text = (ROOT / "backend" / "src" / "api" / "main.py").read_text(encoding="utf-8")
        assert "tamper-evident against the application" in text
        assert "FR-010a" in text
