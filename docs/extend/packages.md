---
page_type: how-to
title: Third-party libraries
level: L4
audience: S
priority: P1
prereqs: []
symbols: []
outcome: Use pandas, matplotlib, and other libraries.
---

# Third-party libraries

## Goal

Use libraries beyond Drafter (matplotlib, pandas, requests, and
others) inside an app that runs in the browser.

## Before you start

You should have read
[Python in the browser](pyodide.md): the key fact is that your
app runs in Pyodide, so a library must be installable *there*,
not only on your computer. You also need the library installed
locally (with pip or Thonny) so the first run on your own
machine works.

## Importing is usually all it takes

When your program runs in the browser, Drafter reads its `import`
lines and installs what they name before running it. Libraries built
for the browser, such as `matplotlib` and `pandas`, come from the
browser's own Python distribution. Anything else, such as `seaborn`,
is fetched from PyPI, the same place `pip` gets it. For most
libraries there is nothing to configure:

```python drafter height=420
from drafter import *
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    plt.plot([1, 4, 2, 8, 5])
    plt.title("A chart from a third-party library")
    return Page(state, [
        Header("It works"),
        MatPlotLibPlot()
    ])


start_server(State())
```

The first page load that needs a library pays a download cost:
matplotlib is several megabytes, pandas more. Later loads are
faster because the browser caches the download.

## What works and what cannot

Three tiers, from best to impossible:

- **Built for Pyodide.** The scientific stack (numpy, pandas,
  matplotlib, pillow, scipy, scikit-learn) has versions compiled
  specifically for the browser. These work well.
- **Pure Python.** Any package on PyPI written in plain Python
  (no compiled parts) installs fine. Most small utility
  libraries fall here.
- **Cannot work.** Packages that need things browsers forbid:
  raw network sockets, other processes, real threads, or
  compiled code with no Pyodide build. Database drivers, game
  engines, and web scrapers with browser automation are typical
  casualties. No flag fixes these; the browser is the limit.

The quick test: search the package name in
[Pyodide's built-in package list](https://pyodide.org/en/stable/usage/packages-in-pyodide.html),
and if it is absent but pure Python, it will install from PyPI
automatically.

## Fetching data from the internet

`requests` works in the browser, with one big caveat: the
browser's rules apply, so the other website must allow
cross-origin requests (CORS). Public data APIs usually do;
ordinary websites usually do not, and there is nothing your code
can change about a refusal.

```python
import requests

from drafter import *


@dataclass
class State:
    weather: str


URL = ("https://forecast.weather.gov/MapClick.php"
       "?lat=39.68&lon=-75.75&FcstType=json")


@route
def index(state: State) -> Page:
    data = requests.get(URL).json()
    state.weather = data["currentobservation"]["Weather"]
    return Page(state, [
        "The weather in Newark right now: " + state.weather
    ])


start_server(State(""))
```

(This one is not embedded as a live demo because it depends on an
external service; copy it into your own editor to try it. It also
uses a dictionary, which your course may not have covered.)

## Declaring packages explicitly

Automatic installation works from the `import` lines in your main
file, and it looks each library up by the name you import. Three
situations fall outside that:

- **The install name differs from the import name.** You write
  `import sklearn`, but the library is installed as `scikit-learn`.
  The common ones built for the browser are handled, but a less
  common library needs its install name declared.
- **The import is not in your main file.** One of your own modules
  imports the library, or the name is built at run time.
- **You want a particular version.**

In those cases, declare packages on the command line:

```console
drafter my_app.py --project-packages wordfreq --project-packages emoji
```

Declared packages load in addition to automatic detection, not
instead of it. `--system-packages` similarly controls the base
set Drafter itself loads, and `--no-load-packages-automatically`
turns the detection off entirely if you want full manual
control.

## Common problems

- **Works locally, fails deployed**: the library is probably in
  the cannot-work tier, or you imported it somewhere detection
  cannot see; try declaring it with `--project-packages`.
- **`ModuleNotFoundError` in the browser for a library you did
  import**: Drafter looked for a library with that exact name and
  could not install one. Check the spelling first. If the library
  installs under a different name, declare that name with
  `--project-packages`.
- **Your own file has the same name as a library**: your file wins.
  Drafter only goes to PyPI for names that nothing next to your
  program can provide, so a `utils.py` of your own is never replaced
  by a stranger's package.
- **`ModuleNotFoundError` when building or deploying**: that is the
  computer doing the build, not the browser. The library has to be
  installed there too; see
  [Building for deployment](../reference/cli.md#building-for-deployment).
- **A long first load**: normal for heavy libraries. Warn your
  users on the page, or trim the dependency.
- **`requests` raises about the connection**: check the browser
  console for a CORS message; if the API does not allow browser
  requests, no client-side fix exists.
- **A friendly error names the missing package**: see the
  [package import error entry](../help/errors/package-import-error.md).

## Related

- [MatPlotLibPlot](../reference/components/media/matplotlibplot.md):
  the component that puts charts on pages.
- [Python in the browser](pyodide.md): why these constraints
  exist.
