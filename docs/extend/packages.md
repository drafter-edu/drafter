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

## Wheels Drafter hosts

A few libraries students ask for exist on PyPI only as source code,
which a browser cannot build. ChemPy is one. Others can be installed
themselves but need a library like that: qmsolve needs `progressbar`,
which is source-only. For these, Drafter keeps a **wheel index** at
`https://drafter-edu.github.io/packages/wheels.json`: pure-Python
wheels built for the browser, listed in a small JSON file. When PyPI
cannot supply a package, or something the package needs, Drafter
checks the index. Nothing to configure: `import chempy` and
`import qmsolve` work.

Only what your program needs is installed. Drafter installs the
package, then each library the package says it needs: from the same
index when the index has it, since an index's wheels are built to go
together, and otherwise from the browser's own Python (`sympy`, for
example) or PyPI. A requirement that nothing can supply is skipped,
since not every dependency a package lists is needed in the browser.
If the package turns out to need it after all, its `import` fails
with a `ModuleNotFoundError` that names the missing library.

Courses can host their own index the same way: a `wheels.json`
listing wheel file names next to a `wheels/` folder, on any server
that allows cross-origin requests (GitHub Pages does). Add it with
`--package-index`:

```console
drafter my_app.py --package-index https://my-course.github.io/wheels/wheels.json
```

Extra indexes are searched first, in the order given, and Drafter's
own index last; `--no-default-package-index` leaves Drafter's out.
The same settings exist as `DRAFTER_PACKAGE_INDEXES` (several URLs
separated by `;`) and `DRAFTER_USE_DEFAULT_PACKAGE_INDEX`, and as
`package_indexes` and `use_default_package_index` in a config file.
The index format is the one produced by the
[drafter-edu/packages](https://github.com/drafter-edu/packages)
repository, which you can copy to build your own.

## Libraries that draw their own charts

Some libraries built on matplotlib draw a chart for you and then call
`plt.show()` themselves. qmsolve's `plot_eigenstate` is one. The
chart is still an ordinary matplotlib figure, so put `MatPlotLibPlot()`
on the page right after the library draws it.

The `plt.show()` call needs one extra step, because it means
different things in the two places your program runs:

- **In the browser** it does nothing. The figure stays open, and
  `MatPlotLibPlot()` picks it up.
- **On your own computer** it opens the chart in a separate window
  and waits for you to close it. Drafter builds your first page on
  your computer before the site opens, so the site does not start
  until the window is closed.

To stop the window from opening, tell matplotlib to draw off screen.
Put these two lines at the top of your program, above the import of
the library that draws the chart:

```python
import matplotlib
matplotlib.use("Agg")

from dataclasses import dataclass

from drafter import *
from qmsolve import Hamiltonian, SingleParticle, init_visualization, Å, eV


@dataclass
class State:
    level: int


def harmonic_oscillator(particle):
    k = 100 * eV / Å**2
    return 0.5 * k * particle.x**2


@route
def index(state: State) -> Page:
    hamiltonian = Hamiltonian(
        particles=SingleParticle(),
        potential=harmonic_oscillator,
        spatial_ndim=1,
        N=512,
        extent=20 * Å
    )
    eigenstates = hamiltonian.solve(max_states=5)
    # plot_eigenstate draws the chart and calls plt.show() itself.
    init_visualization(eigenstates).plot_eigenstate(state.level)
    return Page(state, [
        Header("Harmonic oscillator"),
        "Showing energy level " + str(state.level),
        MatPlotLibPlot(),
        Button("Next level", next_level)
    ])


@route
def next_level(state: State) -> Page:
    state.level = (state.level + 1) % 5
    return index(state)


start_server(State(0))
```

(This one is not a live demo: its libraries take a while to download.
Copy it into your own editor to try it, after installing qmsolve on
your computer.)

With those two lines, your terminal may print `UserWarning:
FigureCanvasAgg is non-interactive, and thus cannot be shown` each
time the library calls `plt.show()`. That is matplotlib saying it
skipped the window, which is what you asked for.

If the `plt.show()` is in your own code, delete it instead. A Drafter
page shows a chart with `MatPlotLibPlot()`, so the call is never
needed.

Only charts that are a single picture carry over. A library's
sliders, animations, and other controls that live in a matplotlib
window do not work on a Drafter page; use Drafter's own buttons and
inputs to choose what to draw, as the example does.

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
- **`ModuleNotFoundError` for a library that is only on PyPI as source**:
  if Drafter's wheel index does not have it, you can build a wheel and
  host your own index; see [Wheels Drafter hosts](#wheels-drafter-hosts).
  The same goes for a library you never imported yourself: one of
  your libraries needs it, and it is only on PyPI as source.
- **A chart opens in its own window and the site does not start**:
  something called `plt.show()`; see
  [Libraries that draw their own charts](#libraries-that-draw-their-own-charts).
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
