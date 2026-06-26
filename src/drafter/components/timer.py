""" "
Components for simulating timers that count down or clocks that count up.


"""

import json
from dataclasses import dataclass
from typing import Optional, Literal

from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction
from drafter.components.planning.render_plan import RenderPlan, AssetBundle
from drafter.components.utilities.validation import validate_parameter_name


@dataclass(repr=False)
class Timer(Component):
    """Timer component that simulates a clock ticking down.
    Provides the ability to call a function when the timer runs out.

    Internally uses setTimeout to trigger the callback when the timer runs out.

    Attributes:
        duration (int): Duration of the timer in milliseconds.
        on_finish (UrlOrFunction): Function or URL to call when the timer runs out.
        show (bool): Whether to display the timer. Defaults to True.
        controls (bool): Whether to show timer controls. Defaults to False.
        persistent (bool): Whether the timer persists across page transitions. Defaults to False.
        rate (int): Interval between timer ticks in milliseconds. Defaults to 1000.
        on_tick (UrlOrFunction, optional): Function or URL to call on each tick. Defaults to None.
    """

    duration: int
    on_finish: UrlOrFunction
    show: bool = True
    controls: bool = False
    persistent: bool = False
    rate: int = 1000
    on_tick: Optional[UrlOrFunction] = None

    tag = "drafter-timer"

    DEFAULT_ATTRS = {"role": "timer"}
    KNOWN_ATTRS = [
        "duration",
        "onfinish",
        "show",
        "controls",
        "persistent",
        "rate",
        "on_tick",
    ]
    ARGUMENTS = [
        ComponentArgument("duration", "positional", 1000),
        ComponentArgument("on_finish", "positional", None, is_event=True),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("controls", "keyword", False),
        ComponentArgument("persistent", "keyword", False),
        ComponentArgument("rate", "keyword", 1000),
        ComponentArgument("on_tick", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["finish", "tick"]

    def __init__(
        self,
        duration: int,
        on_finish: UrlOrFunction,
        show: bool = True,
        controls: bool = False,
        persistent: bool = False,
        rate: int = 1000,
        on_tick: Optional[UrlOrFunction] = None,
        **kwargs,
    ):
        self.duration = duration
        self.on_finish = on_finish
        self.show = show
        self.controls = controls
        self.persistent = persistent
        self.rate = rate
        self.on_tick = on_tick
        self.extra_settings = kwargs


@dataclass(repr=False)
class Clock(Component):
    """Clock component that simulates a clock ticking up.
    Provides the ability to call a function on each tick.

    Note that if the function takes more than the tick interval to execute,
    ticks may be delayed.

    Internally uses setInterval to trigger the callback on each tick.

    Attributes:
        interval (int): Interval between ticks in milliseconds.
        route (UrlOrFunction): Function or URL to call on each tick.
        show (bool): Whether to display the clock. Defaults to True.
    """

    interval: int
    route: UrlOrFunction
    show: bool = True
