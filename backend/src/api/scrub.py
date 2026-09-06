"""Log, trace, and error scrubbing (FR-018, Constitution: Data classification).

Athlete health data must never appear raw in a log line, a trace, or an error message. The
risk is not malice — it is an exception handler that helpfully includes the row it choked on,
or a debug line left in during a deadline.

So scrubbing is applied as a logging filter at the boundary rather than trusted to every call
site remembering. A call site that forgets is the normal case; the filter is what makes
forgetting safe.
"""

from __future__ import annotations

import logging
import re
from typing import Any

REDACTED = "[redacted:health]"

#: Metric names whose VALUES are health data. The name may be logged; the value may not.
_SENSITIVE_KEYS = (
    "cycle_phase", "contraception_status", "iron_status", "soreness", "sleep",
    "training_load", "bowling_load", "ferritin", "menstrual",
)

#: key=value / "key": value / key: value, in logs, JSON fragments and repr() output.
_PATTERNS = tuple(
    re.compile(
        rf'(?P<prefix>["\']?\b{key}\b["\']?\s*[:=]\s*)(?P<value>"[^"]*"|\'[^\']*\'|[^\s,;}}\)\]]+)',
        re.IGNORECASE,
    )
    for key in _SENSITIVE_KEYS
)


#: dataclass repr form: Metric(kind='sleep', value=5.9). Here the sensitive metric name is
#: the VALUE of `kind`, and the number to redact sits under a generic `value` key — so the
#: key-based patterns above miss it entirely. This is the shape an exception handler
#: including the offending row would actually produce, which is why it is handled explicitly.
_REPR_PATTERN = re.compile(
    r"(?P<kind>kind\s*=\s*[\"']?(?:" + "|".join(_SENSITIVE_KEYS) + r")[\"']?\s*,\s*"
    r"value\s*=\s*)(?P<value>\"[^\"]*\"|'[^']*'|[^\s,;}\)\]]+)",
    re.IGNORECASE,
)


def scrub(text: str) -> str:
    """Replace health metric values with a redaction marker, keeping the key readable.

    The key is deliberately preserved: an engineer debugging a stale-data bug needs to know
    *which* metric was involved. They do not need the athlete's ferritin level to fix it.
    """
    if not text:
        return text
    text = _REPR_PATTERN.sub(lambda m: m.group("kind") + REDACTED, text)
    for pattern in _PATTERNS:
        text = pattern.sub(lambda m: m.group("prefix") + REDACTED, text)
    return text


def scrub_obj(obj: Any) -> Any:
    """Recursively redact sensitive values in a dict/list structure."""
    if isinstance(obj, dict):
        return {
            k: (REDACTED if str(k).lower() in _SENSITIVE_KEYS else scrub_obj(v))
            for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        return type(obj)(scrub_obj(v) for v in obj)
    if isinstance(obj, str):
        return scrub(obj)
    return obj


class HealthDataFilter(logging.Filter):
    """Scrub every record on its way out, including the arguments and any exception text."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = scrub(str(record.msg))
            if record.args:
                if isinstance(record.args, dict):
                    record.args = scrub_obj(record.args)
                else:
                    record.args = tuple(scrub_obj(a) for a in record.args)
        except Exception:
            # A scrubbing failure must never swallow the log line entirely, but it must not
            # emit unscrubbed content either. Replace it wholesale.
            record.msg = "[log scrubbing failed; message withheld]"
            record.args = ()
        return True


def install() -> None:
    """Attach the filter to the root logger and every existing handler."""
    handler_filter = HealthDataFilter()
    root = logging.getLogger()
    root.addFilter(handler_filter)
    for handler in root.handlers:
        handler.addFilter(handler_filter)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(name)
        logger.addFilter(handler_filter)
        for handler in logger.handlers:
            handler.addFilter(handler_filter)
