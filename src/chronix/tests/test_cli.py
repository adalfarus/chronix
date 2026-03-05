import importlib
import types

import pytest


@pytest.fixture
def cli_module(monkeypatch):
    class DummyInterface:
        def __init__(self, _name):
            self.paths = {}

        def path(self, name, fn):
            self.paths[name] = fn

        def parse_cli(self):
            return None

    monkeypatch.setitem(__import__("sys").modules, "argumint", types.SimpleNamespace(Interface=DummyInterface))
    import chronix._cli as cli

    importlib.reload(cli)
    return cli


def test_change_working_dir_to_script_location_non_frozen(cli_module, monkeypatch):
    changed = []

    class Frame:
        f_back = types.SimpleNamespace(f_globals={"__file__": "/tmp/app/main.py"})

    monkeypatch.setattr(cli_module.inspect, "currentframe", lambda: Frame())
    monkeypatch.setattr(cli_module.os, "chdir", lambda p: changed.append(p))

    cli_module._change_working_dir_to_script_location()
    assert changed[-1].endswith("/tmp/app")


def test_change_working_dir_to_script_location_frozen(cli_module, monkeypatch):
    changed = []
    monkeypatch.setattr(cli_module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(cli_module.sys, "executable", "/tmp/bin/chronix")
    monkeypatch.setattr(cli_module.os, "chdir", lambda p: changed.append(p))

    cli_module._change_working_dir_to_script_location()
    assert changed[-1].endswith("/tmp/bin")


def test_change_working_dir_to_script_location_errors(cli_module, monkeypatch):
    monkeypatch.setattr(cli_module.inspect, "currentframe", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    with pytest.raises(RuntimeError):
        cli_module._change_working_dir_to_script_location()


def test_execute_silent_python_command(cli_module, monkeypatch):
    called = []

    class Result:
        returncode = 0

    monkeypatch.setattr(cli_module.subprocess, "run", lambda cmd, stdout=None, stderr=None: called.append(cmd) or Result())
    out = cli_module._execute_silent_python_command(["-V"])
    assert out.returncode == 0
    assert called[0][0] == cli_module.sys.executable


def test_cli_run_tests_and_help(cli_module, monkeypatch):
    recorded = {"mkdir": [], "rmtree": [], "pytest": []}

    monkeypatch.setattr(cli_module, "_change_working_dir_to_script_location", lambda: None)
    monkeypatch.setattr(cli_module.os, "chdir", lambda _p: None)
    monkeypatch.setattr(cli_module, "_execute_silent_python_command", lambda _cmd: None)
    monkeypatch.setattr(cli_module.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(cli_module.shutil, "rmtree", lambda p: recorded["rmtree"].append(p))
    monkeypatch.setattr(cli_module.os, "mkdir", lambda p: recorded["mkdir"].append(p))

    class R:
        def __init__(self, code):
            self.returncode = code

    run_count = {"count": 0}

    def fake_run(cmd):
        if cmd and cmd[0] == "pytest":
            run_count["count"] += 1
            recorded["pytest"].append(cmd)
            return R(1 if run_count["count"] == 1 else 0)
        return R(0)

    monkeypatch.setattr(cli_module.subprocess, "run", fake_run)

    paths = {}

    class Interface:
        def __init__(self, _name):
            pass

        def path(self, name, fn):
            paths[name] = fn

        def parse_cli(self):
            paths["tests.run"](None, debug=True, minimal=False)
            paths["tests.run"](["tests"], debug=False, minimal=True)
            paths["help"]()

    monkeypatch.setattr(cli_module, "Interface", Interface)

    printed = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: printed.append(args[0]))

    cli_module._cli()

    assert recorded["rmtree"] == ["test_data", "test_data"]
    assert recorded["mkdir"] == ["test_data", "test_data"]
    assert len(recorded["pytest"]) == 2
    assert any("Please use this command" in p for p in printed)
    assert any("Tests failed for chronix/all." in p for p in printed)
