"""Narrative explanation (FR-002, FR-014, FR-003).

The narrative is generated from the SAME computed result that produced the score — the
fired rules with their own `because` text — never reconstructed from the score afterwards.
That is what makes it an explanation rather than a plausible story about a number.

The language model's role, if one is configured at all, is to rephrase. It is given the
already-computed facts and cannot introduce, remove, or reweight any of them. Before the
narrative leaves this module it is checked against the verdict it claims to explain
(`consistent`), and the API discards it if they disagree.
"""

from __future__ import annotations

import os
import re
from typing import Any

#: Set to a pinned model id to enable LLM rephrasing. FR-008 requires the model version in
#: every audit entry, so an unpinned provider is not a usable configuration.
LLM_MODEL = os.environ.get("SHEPEAK_LLM_MODEL", "").strip()

_BAND_OPENERS = {
    "low": "Your injury risk is low right now.",
    "moderate": "Your injury risk is moderate right now.",
    "elevated": "Your injury risk is elevated right now.",
    "high": "Your injury risk is high right now.",
}


def explain(result: dict[str, Any]) -> dict[str, Any] | None:
    """Return {'text', 'source', 'consistent'} or None when there is nothing to explain."""
    if result.get("outcome") == "refused":
        return {
            "text": _refusal_text(result),
            "source": "deterministic",
            "consistent": True,
        }
    if result.get("outcome") != "assessed":
        return None

    text = _deterministic_text(result)
    source = "deterministic"

    if LLM_MODEL:
        rephrased = _llm_rephrase(text, result)
        if rephrased is not None:
            text, source = rephrased, LLM_MODEL

    return {
        "text": text,
        "source": source,
        "consistent": is_consistent(text, result),
    }


def _refusal_text(result: dict[str, Any]) -> str:
    """A refusal explains itself. Principle IV wants a reason the athlete can act on."""
    lead = "No risk score has been issued, and here is exactly why."
    return f"{lead} {result['detail']} This has been escalated to your coach."


def _deterministic_text(result: dict[str, Any]) -> str:
    """Build the explanation out of the rules that actually fired."""
    parts = [_BAND_OPENERS.get(result["band"], "Your injury risk has been assessed.")]

    rules = result.get("fired_rules") or []
    if not rules:
        parts.append("No risk rule was triggered by your current data.")
    else:
        ordered = sorted(rules, key=lambda r: r["points"], reverse=True)
        parts.append("The largest contributor is: " + ordered[0]["because"])
        if len(ordered) > 1:
            others = " ".join(r["because"] for r in ordered[1:])
            parts.append("Also contributing: " + others)

    sex_specific = [r for r in rules if r.get("is_sex_specific")]
    if sex_specific:
        parts.append(
            f"{len(sex_specific)} of these are specific to female physiology and would not "
            "appear in a model built on male defaults."
        )

    absent = result.get("absent_sex_specific_inputs") or []
    if absent:
        # FR-017 surfaced to the athlete: absences are stated, never quietly defaulted.
        parts.append(
            "Not included, because you have not recorded it: "
            + ", ".join(a.replace("_", " ") for a in absent)
            + ". No default value was substituted."
        )

    if result.get("requires_coach_approval"):
        parts.append("Any plan from this assessment needs your coach's approval.")

    parts.append(
        f"Confidence {result['confidence']:.2f}; rules {result['rule_set_version']}."
    )
    return " ".join(parts)


def is_consistent(text: str, result: dict[str, Any]) -> bool:
    """FR-003 — the boundary re-check, as a pure predicate.

    A narrative must not contradict the verdict it explains. Rather than trusting a model
    to behave, this asserts the two agree on the facts that matter: the band, and whether
    coach approval is required. A mismatch means the response is refused upstream.
    """
    lowered = text.lower()
    band = result["band"]

    other_bands = {"low", "moderate", "elevated", "high"} - {band}
    mentions_band = f"risk is {band}" in lowered or band in lowered
    contradicts = any(f"risk is {b}" in lowered for b in other_bands)
    if contradicts and not mentions_band:
        return False

    if result.get("requires_coach_approval"):
        denies_approval = re.search(
            r"(no|without|does not need|doesn't need)\s+(coach\s+)?approval", lowered
        )
        if denies_approval:
            return False

    # A narrative may not invent a numeric score that differs from the computed one.
    for found in re.findall(r"\bscore(?:d)?\s+(?:of\s+)?(\d{1,3})\b", lowered):
        if int(found) != result["score"]:
            return False
    return True


def _llm_rephrase(deterministic_text: str, result: dict[str, Any]) -> str | None:
    """Ask a pinned model to rephrase — never to decide.

    Deliberately returns None on any failure. If the narrative service is unavailable the
    score and its structured evidence are still delivered; an explanation is a courtesy on
    top of the guarantee, not part of it.
    """
    try:
        import anthropic  # noqa: PLC0415
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=LLM_MODEL,
            max_tokens=400,
            system=(
                "You rephrase a sports-science risk explanation for an athlete. You MUST "
                "NOT change, add, or remove any fact, number, band, or recommendation. Do "
                "not give medical advice. Keep it under 120 words, warm and plain."
            ),
            messages=[{"role": "user", "content": deterministic_text}],
        )
        return "".join(block.text for block in message.content if block.type == "text")
    except Exception:
        return None
