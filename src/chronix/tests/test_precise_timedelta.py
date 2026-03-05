from datetime import timedelta

import pytest

from chronix import PreciseTimeDelta, PreciseTimeFormat


def test_parse_timedelta_string_and_to_timedelta_roundtrip():
    td = PreciseTimeDelta.parse_timedelta_string("01:02:03.4")
    assert td.nanoseconds() == 3723_400_000_000
    assert td.to_timedelta() == timedelta(seconds=3723, microseconds=400000)


def test_parse_timedelta_string_invalid_format_raises():
    with pytest.raises(ValueError, match="Invalid time format"):
        PreciseTimeDelta.parse_timedelta_string("01:02")


def test_from_timedelta_roundtrip_seconds():
    original = timedelta(seconds=3.5)
    parsed = PreciseTimeDelta.from_timedelta(original)
    assert parsed.seconds() == 3.5


@pytest.mark.parametrize(
    ("fmt", "expected"),
    [
        (PreciseTimeFormat.YEARS, "1 year, 0 months"),
        (PreciseTimeFormat.MONTHS, "11 months, 30.41 days"),
        (PreciseTimeFormat.WEEKS, "52 weeks, 1.25 days"),
        (PreciseTimeFormat.DAYS, "365 days, 6 hours"),
        (PreciseTimeFormat.HOURS, "8766 hours, 0 minutes"),
        (PreciseTimeFormat.MINUTES, "525960 minutes, 0 second(s)"),
        (PreciseTimeFormat.SECONDS, "31557600 seconds, 0 millisecond(s)"),
        (PreciseTimeFormat.MILLISECS, "31557600000 milliseconds, 0 microsecond(s)"),
        (PreciseTimeFormat.MICROSECS, "31557600000000 microseconds"),
        (PreciseTimeFormat.NANOSECS, "31557600000000000 nanoseconds"),
        (PreciseTimeFormat.PICOSECS, "31557600000000000000 picoseconds"),
        (PreciseTimeFormat.FEMTOSECS, "31557600000000001048576 femtoseconds"),
        (PreciseTimeFormat.ATTOSECS, "31557599999999999135973376 attoseconds"),
    ],
)
def test_to_readable_all_formats(fmt, expected):
    td = PreciseTimeDelta(years=1)
    assert td.to_readable(fmt) == expected


def test_to_readable_auto_format_selects_highest_unit():
    td = PreciseTimeDelta(seconds=2)
    assert td.to_readable() == "2 seconds, 0 millisecond(s)"


def test_to_clock_string_with_large_units():
    td = PreciseTimeDelta(years=1, months=1, days=2, hours=3, minutes=4, seconds=5)
    value = td.to_clock_string()
    assert "year" in value
    assert "month" in value
    assert "day" in value
    assert value.endswith("03:04:05.000000000")


def test_str_and_negative_str_repr():
    positive = PreciseTimeDelta(seconds=1.25)
    negative = PreciseTimeDelta(seconds=-2.5)
    assert str(positive) == "0:00:01.25"
    assert str(negative).startswith("-")
    assert repr(positive).startswith("PreciseTimeDelta(nanoseconds=")


def test_division_with_number_and_timedelta_and_errors():
    td = PreciseTimeDelta(seconds=10)
    result = td / 2
    assert isinstance(result, PreciseTimeDelta)
    assert result.seconds() == 5

    ratio = td / PreciseTimeDelta(seconds=5)
    assert ratio == 2

    with pytest.raises(ZeroDivisionError):
        _ = td / 0
    with pytest.raises(ZeroDivisionError):
        _ = td / PreciseTimeDelta()
    with pytest.raises(TypeError):
        _ = td / "bad"


def test_scalar_accessors_return_expected_values():
    td = PreciseTimeDelta(days=1)
    assert td.days() == 1
    assert td.hours() == 24
    assert td.minutes() == 1440
    assert td.seconds() == 86400
    assert td.milliseconds() == 86_400_000
    assert td.microseconds() == 86_400_000_000
    assert td.nanoseconds() == 86_400_000_000_000
    assert td.picoseconds() == 86_400_000_000_000_000
    assert td.femtoseconds() == 86_400_000_000_000_000_000
    assert td.attoseconds() == 86_400_000_000_000_000_000_000


def test_pluralize_and_format_value_helpers():
    assert PreciseTimeDelta._pluralize(1, "x", "xs") == "1 x"
    assert PreciseTimeDelta._pluralize(2, "x", "xs") == "2 xs"
    assert PreciseTimeDelta._format_value(2.0, 3) == 2
    assert PreciseTimeDelta._format_value(2.3456, 2) == 2.35
