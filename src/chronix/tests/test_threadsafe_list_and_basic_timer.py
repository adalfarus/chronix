from datetime import timedelta

import pytest

from chronix import _ThreadSafeList, BasicTimer, PreciseTimeFormat


def test_thread_safe_list_full_mutation_and_access_cycle():
    values = _ThreadSafeList([1, 2])

    values.append(3)
    values.extend([4, 5])
    values.insert(0, 0)
    values.remove(2)
    popped = values.pop()
    assert popped == 5

    assert values.index(3) == 2
    assert values.count(4) == 1

    values.reverse()
    values.sort()

    snapshot = values.copy()
    assert snapshot == [0, 1, 3, 4]

    assert values[1] == 1
    values[1] = 11
    del values[0]

    assert len(values) == 3
    assert 11 in values
    assert list(iter(values)) == [11, 3, 4]
    assert list(values) == [11, 3, 4]
    values.clear()
    assert list(values) == []


def test_basic_timer_happy_path(monkeypatch):
    timeline = iter([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
    monkeypatch.setattr("chronix.time.time", lambda: next(timeline))

    timer = BasicTimer().start()
    timer.split_start()
    timer.split_end()

    assert timer.get_times() == [(10.0, 11.0), (10.0, 12.0)]
    assert timer.tally() == 3.0
    assert timer.average() == timedelta(seconds=1.5)

    timer.pause()
    timer.resume()

    current = timer.get()
    assert current == timedelta(seconds=1.0)

    timer.stop()
    assert timer.is_stopped is True


def test_basic_timer_auto_start_and_readable(monkeypatch):
    timeline = iter([1.0, 2.0])
    monkeypatch.setattr("chronix.time.time", lambda: next(timeline))
    timer = BasicTimer(auto_start=True)
    assert timer.get_readable(PreciseTimeFormat.SECONDS).startswith("1 second")


def test_basic_timer_errors(monkeypatch):
    monkeypatch.setattr("chronix.time.time", lambda: 1.0)

    timer = BasicTimer()
    with pytest.raises(RuntimeError, match="not been started"):
        timer.stop()
    with pytest.raises(RuntimeError, match="not been started"):
        timer.pause()
    with pytest.raises(RuntimeError, match="not paused"):
        timer.resume()
    with pytest.raises(RuntimeError, match="not been started"):
        timer.split_start()
    with pytest.raises(RuntimeError, match="not been started"):
        timer.split_end()
    with pytest.raises(ValueError, match="need to start"):
        timer.get_readable()

    timer.start()
    with pytest.raises(RuntimeError, match="already running"):
        timer.start()

    timer.pause()
    with pytest.raises(RuntimeError, match="already paused"):
        timer.pause()

    timer.resume()
    timer.stop()

    with pytest.raises(RuntimeError, match="already stopped"):
        timer.stop()
    with pytest.raises(RuntimeError, match="stopped"):
        timer.pause()

    timer.end()
    with pytest.raises(RuntimeError, match="ended"):
        timer.start()
    with pytest.raises(RuntimeError, match="not paused"):
        timer.resume()
    with pytest.raises(RuntimeError, match="ended"):
        timer.split_start()


def test_basic_timer_average_none_when_no_ticks(monkeypatch):
    monkeypatch.setattr("chronix.time.time", lambda: 1.0)
    timer = BasicTimer(auto_start=True)
    assert timer.average() is None
