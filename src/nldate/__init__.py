"""Parse common English date expressions using calendar-aware arithmetic."""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

_NUMBERS = dict(
    zip(
        [
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
            "twenty",
        ],
        range(21),
    )
)
_NUMBERS.update(
    thirty=30, forty=40, fifty=50, sixty=60, seventy=70, eighty=80, ninety=90
)
_MONTHS = {
    name.lower(): number
    for number in range(1, 13)
    for name in (calendar.month_name[number], calendar.month_abbr[number])
}
_WEEKDAYS = {
    name.lower(): number
    for number in range(7)
    for name in (calendar.day_name[number], calendar.day_abbr[number])
}
_AMOUNT = r"(?:\d+|[a-z]+(?:[- ][a-z]+)?)"
_TERM = re.compile(rf"({_AMOUNT})\s+(days?|weeks?|months?|years?)\b")


def _number(text: str) -> int:
    if text.isdecimal():
        return int(text)
    if text in ("a", "an"):
        return 1
    if text in _NUMBERS:
        return _NUMBERS[text]
    parts = text.replace("-", " ").split()
    if (
        len(parts) == 2
        and parts[0] in _NUMBERS
        and _NUMBERS[parts[0]] >= 20
        and 1 <= _NUMBERS.get(parts[1], 0) <= 9
    ):
        return _NUMBERS[parts[0]] + _NUMBERS[parts[1]]
    raise ValueError(f"Invalid number: {text!r}")


def _duration(text: str) -> tuple[int, int]:
    """Return calendar months and fixed-length days for a whole duration."""
    months = days = 0
    position = 0
    for match in _TERM.finditer(text):
        gap = text[position : match.start()]
        if gap not in (("",) if position == 0 else (" ", " and ", ", ", ", and ")):
            raise ValueError(f"Invalid duration: {text!r}")
        amount = _number(match[1])
        unit = match[2].rstrip("s")
        if unit in ("year", "month"):
            months += amount * (12 if unit == "year" else 1)
        else:
            days += amount * (7 if unit == "week" else 1)
        position = match.end()
    if position == 0 or position != len(text):
        raise ValueError(f"Invalid duration: {text!r}")
    return months, days


def _shift(base: date, duration: str, direction: int) -> date:
    months, days = _duration(duration)
    index = base.year * 12 + base.month - 1 + direction * months
    year, month = divmod(index, 12)
    month += 1
    if not 1 <= year <= 9999:
        raise ValueError("Date arithmetic exceeds the supported calendar")
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day) + timedelta(days=direction * days)


def _parse(text: str, reference: date) -> date:
    if text in ("today", "now", "tomorrow", "yesterday"):
        return reference + timedelta(
            days={"today": 0, "now": 0, "tomorrow": 1, "yesterday": -1}[text]
        )

    match = re.fullmatch(r"(.+?) (before|after|from) (.+)", text)
    if match:
        duration = re.sub(r"^the (day|week|month|year)$", r"1 \1", match[1])
        return _shift(
            _parse(match[3], reference), duration, -1 if match[2] == "before" else 1
        )
    if text.startswith("in "):
        return _shift(reference, text[3:], 1)
    if text.endswith(" ago"):
        return _shift(reference, text[:-4], -1)

    match = re.fullmatch(r"(next|last|this) (day|week|month|year)", text)
    if match:
        direction = {"next": 1, "last": -1, "this": 0}[match[1]]
        return _shift(reference, f"1 {match[2]}", direction)

    match = re.fullmatch(r"(?:(next|last|this) )?([a-z]+)", text)
    if match and match[2] in _WEEKDAYS:
        delta = (_WEEKDAYS[match[2]] - reference.weekday()) % 7
        if match[1] == "last":
            delta = delta - 7 if delta else -7
        elif match[1] == "next" and delta == 0:
            delta = 7
        return reference + timedelta(days=delta)

    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return date(int(match[1]), int(match[2]), int(match[3]))
    match = re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", text)
    if match:
        return date(int(match[1]), int(match[2]), int(match[3]))
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        return date(int(match[3]), int(match[1]), int(match[2]))

    # Strip English ordinal suffixes before matching named-month formats.
    text = re.sub(r"\b(\d{1,2})(?:st|nd|rd|th)\b", r"\1", text)
    match = re.fullmatch(r"([a-z]+)\.? (\d{1,2})(?:,? (\d{4}))?", text)
    if match and match[1] in _MONTHS:
        return date(
            int(match[3]) if match[3] else reference.year,
            _MONTHS[match[1]],
            int(match[2]),
        )
    match = re.fullmatch(r"(\d{1,2}) ([a-z]+)\.?(?:,? (\d{4}))?", text)
    if match and match[2] in _MONTHS:
        return date(
            int(match[3]) if match[3] else reference.year,
            _MONTHS[match[2]],
            int(match[1]),
        )
    raise ValueError(f"Unrecognized date expression: {text!r}")


def parse(s: str, today: date | None = None) -> date:
    """Parse an English date, relative to ``today`` (default: the local date).

    Slash dates use month/day/year or year/month/day (with a four-digit year).
    Hyphenated ISO dates use year-month-day. Bare weekdays mean the next occurrence,
    including today; next/last weekdays are strictly future/past. Missing years
    use the reference year. Arithmetic applies combined years/months first,
    clamping the day to the destination month, then applies weeks/days.
    """
    if not isinstance(s, str) or not s.strip():
        raise ValueError("A nonempty date expression is required")
    text = " ".join(s.lower().split())
    try:
        return _parse(text, today if today is not None else date.today())
    except (OverflowError, RecursionError) as error:
        raise ValueError(f"Date expression exceeds supported limits: {s!r}") from error


def main() -> None:
    print("Hello from nldate!")
