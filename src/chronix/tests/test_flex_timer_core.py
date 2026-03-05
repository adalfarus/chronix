from datetime import timedelta

import pytest

from chronix import FlexTimer, PreciseTimeDelta, PreciseTimeFormat


class DummyLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def timer(monkeypatch):
    monkeypatch.setattr("chronix.threading.Lock", DummyLock)
    t = FlexTimer(start_now=False)
    return t


def _set_times(monkeypatch, values):
    it = iter(values)
    monkeypatch.setattr(FlexTimer, "_time", staticmethod(lambda: next(it)))


def test_start_get_pause_resume_stop_end(timer, monkeypatch):
    _set_times(monkeypatch, [1000.0, 1400.0, 1600.0, 2000.0, 2500.0, 3000.0])

    timer.start(0)
    got = timer.get(0)
    assert isinstance(got, PreciseTimeDelta)
    assert got.nanoseconds() == 400.0

    timer.pause(0)
    timer.resume(0)
    timer.stop(0)

    td = timer.end(0, return_type="timedelta")
    assert isinstance(td, timedelta)
    assert td >= timedelta(0)


def test_start_existing_running_index_raises(timer, monkeypatch):
    _set_times(monkeypatch, [1000.0, 1100.0])
    timer.start(0)
    with pytest.raises(Exception, match="already running"):
        timer.start(0)


def test_get_delete_restart_elapsed_lap_tally_average(timer, monkeypatch):
    _set_times(monkeypatch, [
        1000.0,  # start
        1200.0,  # elapsed
        1400.0,  # lap
        1600.0,  # lap
        2000.0,  # get
        2200.0,  # restart
        2400.0,  # start called by restart
        2600.0,  # delete
    ])

    timer.start(0)
    elapsed = timer.elapsed(0)
    assert elapsed.nanoseconds() == 200.0

    lap1 = timer.lap(0, return_type="timedelta")
    assert lap1 == timedelta(microseconds=200.0 / 1000)

    lap2 = timer.lap(0)
    assert lap2.nanoseconds() == 200.0

    current = timer.get(0, return_type="timedelta")
    assert isinstance(current, timedelta)

    restarted = timer.restart(0)
    assert isinstance(restarted, PreciseTimeDelta)

    deleted = timer.delete(0)
    assert isinstance(deleted, PreciseTimeDelta)

    assert timer.tally(0).nanoseconds() == 0
    assert timer.average(0).nanoseconds() == 0


def test_multiple_indices_return_list(timer, monkeypatch):
    _set_times(monkeypatch, [1000.0, 2000.0, 2300.0, 2600.0])
    timer.start(0, 1)
    values = timer.get(0, 1)
    assert isinstance(values, list)
    assert len(values) == 2


def test_index_errors_and_pause_resume_value_errors(timer, monkeypatch):
    _set_times(monkeypatch, [1000.0, 1200.0, 1300.0, 1400.0, 1500.0, 1600.0])

    with pytest.raises(IndexError):
        timer.get(0)

    timer.start(0)
    with pytest.raises(IndexError):
        timer.pause(1)

    timer.pause(0)
    with pytest.raises(ValueError, match="already paused"):
        timer.pause(0)

    timer.resume(0)
    with pytest.raises(ValueError, match="isn't paused"):
        timer.resume(0)


def test_elapsed_and_lap_error_when_time_goes_backwards(timer, monkeypatch):
    _set_times(monkeypatch, [1000.0, 900.0, 800.0])
    timer.start(0)
    with pytest.raises(ValueError, match="don't tick"):
        timer.elapsed(0)
    with pytest.raises(ValueError, match="don't tock"):
        timer.lap(0)


def test_show_laps_and_get_readable(timer, monkeypatch):
    _set_times(monkeypatch, [1000.0, 1300.0, 1600.0])
    timer.start(1)
    timer.lap(1)
    timer.lap(1)

    laps = timer.show_laps(1, format_to=PreciseTimeFormat.NANOSECS)
    assert "Lap 1" in laps
    assert "Lap 2" in laps

    readable = timer.get_readable(1, format_to=PreciseTimeFormat.NANOSECS)
    assert "nanosecond" in readable


def test_warmup_start_end_cycle(monkeypatch):
    monkeypatch.setattr("chronix.threading.Lock", DummyLock)
    _set_times(monkeypatch, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    t = FlexTimer(start_now=False)
    t._warmup(rounds=2)
    assert t._times == []
    assert t._tick_tocks == []


def test_state_save_load_static(timer, monkeypatch):
    _set_times(monkeypatch, [1000.0, 1200.0])
    timer.start(0)
    timer.stop(0)

    blob = timer.save_state()
    assert isinstance(blob, bytes)

    t2 = FlexTimer(start_now=False)
    with pytest.raises(AttributeError):
        t2.load_state(blob)

    with pytest.raises(AttributeError):
        FlexTimer.load_state_static(blob)


def test_at_and_from_class_tracking(monkeypatch):
    monkeypatch.setattr("chronix.threading.Lock", DummyLock)
    FlexTimer._tracked_timers = []

    t = FlexTimer.at(2, start_now=False)
    assert isinstance(t, FlexTimer)
    assert FlexTimer.from_(2) is t

    with pytest.raises(IndexError):
        FlexTimer.from_(3)


def test_context_manager_and_enter_exit(monkeypatch):
    monkeypatch.setattr("chronix.threading.Lock", DummyLock)
    _set_times(monkeypatch, [1000.0, 1200.0])

    printed = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: printed.append(args[0]))

    t = FlexTimer(start_now=False)
    t.enter(index=0)
    t.__exit__(None, None, None)
    assert any("Codeblock" in line for line in printed)

    t2 = FlexTimer(start_now=False)
    t2.__exit__(None, None, None)
    assert any("exit index not found" in line for line in printed)


def test_system_time_format():
    assert len(FlexTimer.system_time().split(":")) == 3


def test_test_delay_and_wait_wrappers(monkeypatch):
    calls = []
    monkeypatch.setattr(FlexTimer, "wait_static", classmethod(lambda cls, s=0: calls.append(("s", s)) or cls))
    monkeypatch.setattr(FlexTimer, "wait_ms_static", classmethod(lambda cls, ms=0: calls.append(("ms", ms)) or cls))

    t = FlexTimer(start_now=False)
    assert t.wait(2) is t
    assert t.wait_ms(3) is t

    d1 = FlexTimer.test_delay(0, return_type="timedelta")
    d2 = FlexTimer.test_delay_ms(0, return_type="timedelta")
    assert isinstance(d1, timedelta)
    assert isinstance(d2, timedelta)
    assert ("s", 2) in calls
    assert ("ms", 3) in calls


def test_wait_ms_static_uses_sleep_for_large_gap(monkeypatch):
    timeline = iter([0.0, 0.0, 500_000.0, 2_100_000.0])
    monkeypatch.setattr(FlexTimer, "_time", staticmethod(lambda: next(timeline)))
    sleeps = []
    monkeypatch.setattr("chronix.time.sleep", lambda s: sleeps.append(s))

    FlexTimer.wait_ms_static(2)
    assert sleeps == [0.001]
