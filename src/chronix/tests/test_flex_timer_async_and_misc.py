import types
import math

import pytest

from chronix import (
    CPUFTimer,
    CPUFTimerNS,
    DateTimeFTimer,
    FlexTimer,
    MonotonicFTimer,
    MonotonicFTimerNS,
    PerfFTimer,
    PerfFTimerNS,
    ThreadFTimer,
    ThreadFTimerNS,
    TimeFTimer,
    TimeFTimerNS,
)


class FakeEvent:
    def __init__(self):
        self._set = False

    def set(self):
        self._set = True

    def is_set(self):
        return self._set


class FakeThread:
    created = []

    def __init__(self, target=None, kwargs=None, daemon=False):
        self.target = target
        self.kwargs = kwargs or {}
        self.daemon = daemon
        self.started = False
        self.joined = False
        FakeThread.created.append(self)

    def start(self):
        self.started = True

    def join(self):
        self.joined = True


class FakeTimer:
    created = []

    def __init__(self, interval, function, args=(), kwargs=None):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs or {}
        self.started = False
        FakeTimer.created.append(self)

    def start(self):
        self.started = True


def test_trigger_variants(monkeypatch):
    calls = []

    monkeypatch.setattr(FlexTimer, "wait_static", classmethod(lambda cls, s=0: cls))
    monkeypatch.setattr(FlexTimer, "wait_ms_static", classmethod(lambda cls, ms=0: cls))

    FlexTimer._trigger(1, lambda x: calls.append(x), (1,), {}, iterations=2)
    FlexTimer._trigger_ms(1, lambda x: calls.append(x), (2,), {}, iterations=2)

    monkeypatch.setattr("chronix.threading.Timer", FakeTimer)
    FlexTimer._trigger_long(1, lambda x: calls.append(x), (3,), {}, iterations=1)
    FakeTimer.created[-1].function()

    assert calls == [1, 1, 2, 2, 3]


def test_trigger_catches_callback_exceptions(monkeypatch):
    monkeypatch.setattr(FlexTimer, "wait_static", classmethod(lambda cls, s=0: cls))
    printed = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: printed.append(args[0]))

    FlexTimer._trigger(1, lambda: (_ for _ in ()).throw(RuntimeError("x")), (), {}, 1)
    assert any("Error in _trigger thread" in p for p in printed)


def test_single_shot_repeat_and_ms_wrappers(monkeypatch):
    FakeThread.created = []
    monkeypatch.setattr("chronix.threading.Thread", FakeThread)

    FlexTimer.single_shot(1, lambda: None, daemon=True)
    FlexTimer.single_shot_ms(2, lambda: None)
    FlexTimer.repeat(3, lambda: None, iterations=2)
    FlexTimer.repeat_ms(4, lambda: None, iterations=2)

    assert len(FakeThread.created) == 4
    assert FakeThread.created[0].target == FlexTimer._trigger
    assert FakeThread.created[1].target == FlexTimer._trigger_ms
    # current implementation sends the callback under "functions" in single_shot_ms
    assert "functions" in FakeThread.created[1].kwargs


def test_single_shot_long_and_repeat_long(monkeypatch):
    calls = []
    monkeypatch.setattr(
        FlexTimer,
        "_trigger_long",
        classmethod(lambda cls, *args, **kwargs: calls.append(kwargs if kwargs else args)),
    )

    FlexTimer.single_shot_long(1, lambda: None)
    FlexTimer.repeat_long(2, lambda: None, iterations=3)

    assert calls[0][-1] == 1
    assert calls[1]["iterations"] == 3


def test_after_and_interval_route_to_expected_methods(monkeypatch):
    t = FlexTimer(start_now=False)
    called = []

    monkeypatch.setattr(t, "single_shot", lambda *a, **k: called.append("single"))
    monkeypatch.setattr(t, "single_shot_ms", lambda *a, **k: called.append("single_ms"))
    monkeypatch.setattr(t, "single_shot_long", lambda *a, **k: called.append("single_long"))
    monkeypatch.setattr(t, "loop", lambda *a, **k: called.append("loop"))
    monkeypatch.setattr(t, "loop_ms", lambda *a, **k: called.append("loop_ms"))
    monkeypatch.setattr(t, "loop_long", lambda *a, **k: called.append("loop_long"))
    monkeypatch.setattr(t, "repeat", lambda *a, **k: called.append("repeat"))
    monkeypatch.setattr(t, "repeat_ms", lambda *a, **k: called.append("repeat_ms"))
    monkeypatch.setattr(t, "repeat_long", lambda *a, **k: called.append("repeat_long"))

    t.after(1, lambda: None)
    t.after(1, lambda: None, ms=True)
    t.after(1, lambda: None, long=True)

    t.interval(1, "inf", lambda: None)
    t.interval(1, "inf", lambda: None, ms=True)
    t.interval(1, "inf", lambda: None, long=True)
    t.interval(1, 2, lambda: None)
    t.interval(1, 2, lambda: None, ms=True)
    t.interval(1, 2, lambda: None, long=True)

    assert called == [
        "single",
        "single_ms",
        "single_long",
        "loop",
        "loop_ms",
        "loop_long",
        "repeat",
        "repeat_ms",
        "repeat_long",
    ]


def test_loop_loop_ms_loop_long_and_stop(monkeypatch):
    monkeypatch.setattr("chronix.threading.Thread", FakeThread)
    monkeypatch.setattr("chronix.threading.Event", FakeEvent)

    t = FlexTimer(start_now=False)
    t.loop(1, lambda: None, index=0)
    t.loop_ms(1, lambda: None, index=1)

    monkeypatch.setattr(FlexTimer, "_trigger_long", classmethod(lambda cls, **kwargs: None))
    t.loop_long(1, lambda: None, index=2)

    assert len(t._loops) == 3
    t.stop_loop(index=0)
    t.stop_loops(0, 0, not_exists_okay=True)


def test_schedule_task_at_formats_and_invalid(monkeypatch):
    started = []

    class D:
        @staticmethod
        def now():
            class T:
                def time(self):
                    return types.SimpleNamespace()

            return T()

        @staticmethod
        def strptime(value, fmt):
            class DT:
                @staticmethod
                def time():
                    return types.SimpleNamespace()

            return DT()

        @staticmethod
        def today():
            return types.SimpleNamespace()

        @staticmethod
        def combine(_a, _b):
            class C:
                def __lt__(self, other):
                    return False

                def __sub__(self, other):
                    class Delta:
                        @staticmethod
                        def total_seconds():
                            return 1

                    return Delta()

            return C()

    class Tmr:
        def __init__(self, *args, **kwargs):
            started.append((args, kwargs))

        def start(self):
            started.append("started")

    monkeypatch.setattr("chronix._datetime", D)
    monkeypatch.setattr("chronix.threading.Timer", Tmr)

    FlexTimer.schedule_task_at("10:30", lambda: None)
    FlexTimer.schedule_task_at("10:30:20", lambda: None)
    assert "started" in started

    with pytest.raises(TypeError):
        FlexTimer.schedule_task_at("10")


def test_complexity_import_error(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"sklearn.linear_model", "scipy.optimize", "numpy"}:
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="Optional library"):
        FlexTimer.complexity(lambda x: x, [((1,), {})])


def test_complexity_with_fake_optional_modules_and_plot(monkeypatch):
    class FakeArray:
        def __init__(self, data):
            self.data = list(data)

        def reshape(self, *_args):
            return self

        def __len__(self):
            return len(self.data)

        def __iter__(self):
            return iter(self.data)

        def __getitem__(self, key):
            if isinstance(key, FakeArray):
                return FakeArray([v for v, keep in zip(self.data, key.data) if keep])
            return self.data[key]

        def __le__(self, other):
            return FakeArray([v <= other for v in self.data])

        def __sub__(self, other):
            return FakeArray([a - b for a, b in zip(self.data, other.data)])

        def __pow__(self, p):
            return FakeArray([v**p for v in self.data])

        def __mul__(self, other):
            if isinstance(other, FakeArray):
                return FakeArray([a * b for a, b in zip(self.data, other.data)])
            return FakeArray([v * other for v in self.data])

        __rmul__ = __mul__

        def __add__(self, other):
            if isinstance(other, FakeArray):
                return FakeArray([a + b for a, b in zip(self.data, other.data)])
            return FakeArray([v + other for v in self.data])

        __radd__ = __add__

    fake_np = types.SimpleNamespace(
        inf=float("inf"),
        array=lambda x: FakeArray(x),
        any=lambda x: any(x.data),
        ones_like=lambda n: FakeArray([1 for _ in n.data]),
        log=lambda n: FakeArray([math.log(v) for v in n.data]),
        sqrt=lambda n: FakeArray([math.sqrt(v) for v in n.data]),
        mean=lambda x: sum(x.data) / len(x.data),
        linspace=lambda a, b, c: FakeArray([a, (a + b) / 2, b]),
    )

    class FakeRansac:
        def fit(self, x, _y):
            self.inlier_mask_ = FakeArray([True] * len(x))

    fake_sklearn = types.SimpleNamespace(RANSACRegressor=FakeRansac)
    fake_scipy = types.SimpleNamespace(
        curve_fit=lambda fn, _x, _y, maxfev=0: ((1,) * (fn.__code__.co_argcount - 1),)
    )

    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "numpy":
            return fake_np
        if name == "scipy.optimize":
            return fake_scipy
        if name == "sklearn.linear_model":
            return fake_sklearn
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    times = iter([1_000_000_000.0, 2_000_000_000.0, 2_000_000_000.0, 3_000_000_000.0])
    monkeypatch.setattr(FlexTimer, "_time", staticmethod(lambda: next(times)))

    plotted = []
    fake_plt = types.SimpleNamespace(
        scatter=lambda *a, **k: plotted.append("scatter"),
        plot=lambda *a, **k: plotted.append("plot"),
        xlabel=lambda *a, **k: plotted.append("xlabel"),
        ylabel=lambda *a, **k: plotted.append("ylabel"),
        title=lambda *a, **k: plotted.append("title"),
        legend=lambda *a, **k: plotted.append("legend"),
        show=lambda *a, **k: plotted.append("show"),
    )

    best = FlexTimer.complexity(lambda n: n, [((1,), {}), ((2,), {})], matplotlib_pyplt=fake_plt)
    assert best in {"O(1)", "O(log N)", "O(N)", "O(N log N)", "O(N^2)", "O(N^3)", "O(sqrt(N))"}
    assert "show" in plotted


def test_complexity_insufficient_data(monkeypatch):
    fake_np = types.SimpleNamespace(array=lambda x: x, any=lambda x: False)
    fake_sklearn = types.SimpleNamespace(RANSACRegressor=object)
    fake_scipy = types.SimpleNamespace(curve_fit=lambda *a, **k: ((1,),))

    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "numpy":
            return fake_np
        if name == "scipy.optimize":
            return fake_scipy
        if name == "sklearn.linear_model":
            return fake_sklearn
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(FlexTimer, "_time", staticmethod(lambda: 1.0))

    assert FlexTimer.complexity(lambda n: n, [((1,), {})]) == "Insufficient data"


def test_time_decorator_and_system_timers(monkeypatch):
    printed = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: printed.append(args[0]))

    @FlexTimer.time()
    def fn(x):
        return x + 1

    assert fn(4) == 5
    assert any("Function fn took" in line for line in printed)

    timer_types = [
        TimeFTimer,
        TimeFTimerNS,
        PerfFTimer,
        PerfFTimerNS,
        CPUFTimer,
        CPUFTimerNS,
        MonotonicFTimer,
        MonotonicFTimerNS,
        ThreadFTimer,
        ThreadFTimerNS,
        DateTimeFTimer,
    ]
    for t in timer_types:
        v = t._time() if t is not DateTimeFTimer else t(start_now=False)._time()
        assert isinstance(v, (int, float))


def test_enter_internal_branch_calls_start(monkeypatch):
    t = FlexTimer(start_now=False)
    called = []
    monkeypatch.setattr(t, "start", lambda index=None, **kwargs: called.append(index) or t)
    t._thread_data.entry_index = 1
    t.__enter__()
    assert called == [1]


def test_destructor_stops_all_loops(monkeypatch):
    t = FlexTimer(start_now=False)
    t._loops = [(None, None), (None, None)]

    called = []
    monkeypatch.setattr(t, "stop_loop", lambda **kwargs: called.append(kwargs))
    t.__del__()

    assert called == [{"amount": 2}]
