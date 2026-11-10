from datetime import date

import pytest

from nldate import parse

REF = date(2026, 11, 10)


# Simple relative dates


def test_today():
    assert parse("today", today=REF) == REF


def test_tomorrow():
    assert parse("tomorrow", today=REF) == date(2026, 11, 11)


def test_yesterday():
    assert parse("yesterday", today=REF) == date(2026, 11, 9)


# Days and weeks


def test_in_five_days():
    assert parse("in 5 days", today=REF) == date(2026, 11, 15)


def test_three_days_ago():
    assert parse("3 days ago", today=REF) == date(2026, 11, 7)


def test_two_weeks_from_tomorrow():
    assert parse("two weeks from tomorrow", today=REF) == date(2026, 11, 25)


# Weekdays


def test_next_tuesday():
    assert parse("next Tuesday", today=REF) == date(2026, 11, 17)


def test_last_friday():
    assert parse("last Friday", today=REF) == date(2026, 11, 6)


# Absolute dates


def test_month_day_year():
    assert parse("December 1, 2025") == date(2025, 12, 1)


def test_ordinal_date():
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_iso_date():
    assert parse("2025-12-01") == date(2025, 12, 1)


def test_slash_date():
    assert parse("12/01/2025") == date(2025, 12, 1)


# More complex expressions


def test_days_before_date():
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_year_and_month_after_yesterday():
    assert parse("1 year and 2 months after yesterday", today=REF) == date(2028, 1, 9)


# Edge cases


def test_capitalization_and_spaces():
    assert parse("  TOMORROW  ", today=REF) == date(2026, 11, 11)


def test_leap_year():
    assert parse("February 29, 2024") == date(2024, 2, 29)


# Invalid inputs


def test_empty_string():
    with pytest.raises(ValueError):
        parse("")


def test_invalid_text():
    with pytest.raises(ValueError):
        parse("hello world")


def test_invalid_calendar_date():
    with pytest.raises(ValueError):
        parse("February 30, 2025")

def test_day_after_tomorrow():
    assert parse("the day after tomorrow", today=REF) == date(2026, 11, 12)

def test_day_before_yesterday():
    assert parse("the day before yesterday", today=REF) == date(2026, 11, 8)
