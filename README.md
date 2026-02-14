[![Active Development](https://img.shields.io/badge/Maintenance%20Level-Actively%20Developed-brightgreen.svg)](https://gist.github.com/cheerfulstoic/d107229326a01ff0f333a1d3476e068d)
[![CI Test Status](https://github.com/Adalfarus/chronokit/actions/workflows/test-package.yml/badge.svg)](https://github.com/Adalfarus/chronokit/actions)
[![License: LGPL-2.1](https://img.shields.io/github/license/Adalfarus/chronokit)](https://github.com/Adalfarus/chronokit/blob/main/LICENSE)
[![PyPI Downloads](https://static.pepy.tech/badge/chronokit)](https://pepy.tech/projects/chronokit)
![coverage](https://raw.githubusercontent.com/Adalfarus/chronokit/refs/heads/main/coverage-badge.svg)

# chronokit

chronokit is a small timer utility that has all the helpful features you could ever want.

## Compatibility
🟩 (Works perfectly); 🟨 (Untested); 🟧 (Some Issues); 🟥 (Unusable)

| OS                       |   |
|--------------------------|---|
| Windows                  | 🟩 |
| MacOS                    | 🟩 |
| Linux (Ubuntu 22.04 LTS) | 🟩 |

## Features

- Easy to use for beginners, but not lacking for experts
- Efficient
- Fully cross-platform
- Regular updates and support
- Comprehensive documentation

## Installation

You can install chronokit via pip:

```sh
pip install chronokit --pre --upgrade
```

Or clone the repository and install manually:

```sh
git clone https://github.com/Adalfarus/chronokit.git
cd chronokit
python -m pip install .
```

If you have problems with the package please use `py -m pip install chronokit --pre --upgrade --user`

## 📦 Usage

Here are a few quick examples of how to use `chronokit`.

---

## ⏱ Basic Timing (`aplustools.package.chronokit`)

Measure elapsed time with nanosecond resolution.

---

### ⏲ Use `BasicTimer` for simple measurements

```python
from aplustools.package.chronokit import BasicTimer
import time

timer = BasicTimer(auto_start=True)
time.sleep(0.123)
timer.stop()

print(timer.get())          # timedelta
print(timer.get_readable()) # Human-readable
```

---

### 📏 Create precise deltas

```python
from aplustools.package.chronokit import PreciseTimeDelta

delta = PreciseTimeDelta(seconds=1.5, microseconds=250)
print(str(delta))           # 0:00:01.500250
print(delta.to_readable())  # "1.500s"
```

---

## ⏱ Flexible Timing with `FlexTimer`

Advanced control for performance tracking, interval measurements, and benchmarking.

---

### 🧪 Measure CPU-only time (ignores sleep)

```python
from aplustools.package.chronokit import CPUFTimer

with CPUFTimer():
    sum(i * i for i in range(100_000))
```

> Ideal for benchmarking with minimal system interference.

---

### 🔄 Manual start/stop and waiting

```python
from aplustools.package.chronokit import FlexTimer

t = FlexTimer(start_now=False)
t.start(start_at=1.2)
t.wait(0.8)
t.stop()

print(t.get().to_clock_string())  # e.g., 00:00:02.00
```

---

### ⏱ Record laps (interval checkpoints)

```python
t = FlexTimer()
# ... task 1 ...
t.lap()
# ... task 2 ...
t.lap()

print(t.show_laps())  # List of lap durations
```

---

### 🪄 Time entire functions with a decorator

```python
@FlexTimer().time()
def compute():
    return [x**2 for x in range(1_000_000)]

compute()  # Prints execution time
```

---

### 🕒 Schedule callbacks after a delay

```python
def on_done():
    print("Finished!")

FlexTimer().after(2, on_done)
```

---

### 🧵 Run functions at intervals

```python
def tick():
    print("Tick!")

FlexTimer().interval(1, count=5, callback=tick)
```

---

### 📈 Estimate time complexity of a function

```python
def fn(n):
    return [i ** 2 for i in range(n)]

def gen_inputs():
    for i in range(1000, 50000, 1000):
        yield ((i,), {})

from aplustools.package.chronokit import FlexTimer
print(FlexTimer.complexity(fn, gen_inputs()))  # e.g., "O(N)"
```

### chrono cli
Can currently run tests with ```chrono tests run tests/ -minimal``` and show a basic help using ```chrono help```.

For more detailed usage and examples, check out our [documentation](https://github.com/adalfarus/chronokit/wiki).

## Naming convention, dependencies and library information
[PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions)

For modules I use 'lowercase', classes are 'CapitalizedWords' and functions and methods are 'lower_case_with_underscores'.

## Contributing

We welcome contributions! Please see our [contributing guidelines](https://github.com/adalfarus/chronokit/blob/main/CONTRIBUTING.md) for more details on how you can contribute to chronokit.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

### Aps Build master

You can use the aps_build_master script for your os to make your like a lot easier.
It supports running tests, installing, building and much more as well as chaining together as many commands as you like.

This example runs test, build the project and then installs it
````commandline
call .\aps_build_master.bat 234
````

````shell
sudo apt install python3-pip
sudo apt install python3-venv
chmod +x ./aps_build_master.sh
./aps_build_master.sh 234
````

## License

chronokit is licensed under the LGPL-2.1 License - see the [LICENSE](https://github.com/adalfarus/chronokit/blob/main/LICENSE) file for details.
