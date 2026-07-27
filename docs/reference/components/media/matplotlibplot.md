---
page_type: component
title: MatPlotLibPlot
level: L4
audience: S
priority: P1
prereqs: []
symbols:
  - MatPlotLibPlot
outcome: Show a matplotlib figure.
---

# MatPlotLibPlot

Group: [Media](../index.md#media)

## Description

`MatPlotLibPlot` puts a chart on your page. You draw the chart with
the matplotlib library's usual commands (`plt.plot`, `plt.bar`, and
so on), then place `MatPlotLibPlot()` in the page where the picture
should appear. The component captures whatever figure matplotlib
currently has open and embeds it as an image.

## Syntax

```python
MatPlotLibPlot()
MatPlotLibPlot(extra_matplotlib_settings)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --------- | ---- | ------- | ------- |
| `extra_matplotlib_settings` | `dict` | `{}` | Settings passed to matplotlib when saving the figure, like `{"format": "svg"}`. The format must be `"png"` (the default) or `"svg"`. |
| `close_automatically` | `bool` | `True` | Close the figure after rendering, so the next chart starts fresh. |

## Examples

Draw first, then place the component:

```python drafter height=420
from drafter import *
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    plt.plot([12, 15, 11, 18, 16, 20])
    plt.title("Treats eaten by Ada this week")
    return Page(state, [
        Header("Treat Tracker"),
        MatPlotLibPlot()
    ])


start_server(State())
```

The chart can be driven by state, so it changes as the data does:

```python drafter height=480
from drafter import *
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class State:
    naps: list[int]


@route
def index(state: State) -> Page:
    plt.bar(range(len(state.naps)), state.naps)
    plt.title("Captain's naps per day")
    return Page(state, [
        Header("Nap Chart"),
        MatPlotLibPlot(),
        Button("Record a lazy day", "lazy_day")
    ])


@route
def lazy_day(state: State) -> Page:
    state.naps.append(state.naps[-1] + 1)
    return index(state)


start_server(State([3, 4, 2]))
```

## Notes

- The component shows the figure that is open at the moment the
  page renders, so run your `plt.` commands inside the route,
  before returning the `Page`.
- The first page that uses matplotlib in the browser takes a while
  to appear: the library is downloaded and installed on demand.
  Later pages reuse it.
- By default the figure closes after rendering. If you draw one
  figure and show it twice on the same page, pass
  `close_automatically=False` to the first `MatPlotLibPlot`.
- The chart is a picture: visitors cannot hover or zoom it.
- To store a chart in state or offer it as a download, call the
  component's `to_picture()` method to get a
  [Picture](../../data-types/picture.md) value.

## Related components

- [Image](image.md): show a picture that is not a chart.
- [Download](../input/download.md): let visitors save the chart
  file.

## External links

- [Third-party libraries in Drafter](../../../extend/packages.md)
- [Matplotlib's beginner tutorial](https://matplotlib.org/stable/tutorials/pyplot.html)
