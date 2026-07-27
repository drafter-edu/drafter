"""Custom-element components for time-based callbacks.

Provides the `Timer` component (counts down from a duration, firing an event
when it finishes and optionally on each tick) and the `Clock` component
(counts up indefinitely, firing an event on each tick). Both render as custom
elements (`drafter-timer` and `drafter-clock`) implemented in
js/src/components/timer.tsx, and register contracts describing the payloads
of the events they emit.
"""

from dataclasses import dataclass

from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction
from drafter.components.utilities.contracts import (
    ComponentContract,
    EventPayloadFieldSpec,
    EventPayloadSpec,
)
from drafter.components.utilities.registry import COMPONENT_CONTRACT_REGISTRY


@dataclass(repr=False)
class Timer(Component):
    """Timer component that simulates a clock ticking down.
    Provides the ability to call a function when the timer runs out,
    and optionally on each tick along the way.

    Attributes:
        duration: Duration of the timer in milliseconds.
        on_finish: Function or URL to call when the timer runs out.
        show: Whether to display the timer. Defaults to True.
        controls: Whether to show timer controls. Defaults to False.
        persistent: Whether the timer persists across page transitions. Defaults to False.
        rate: Interval between timer ticks in milliseconds. Defaults to 1000.
        on_tick: Optional function or URL to call on each tick. Defaults to None.
    """

    duration: int
    on_finish: UrlOrFunction
    show: bool = True
    controls: bool = False
    persistent: bool = False
    rate: int = 1000
    on_tick: UrlOrFunction | None = None

    tag = "drafter-timer"

    PERSISTABLE = True
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

    #: What this component emits: the JS implementation (js/src/components/
    #: timer.tsx) must match this contract, and the router uses it to reason
    #: about event payload fields.
    CONTRACT = ComponentContract(
        component_name="Timer",
        html_tag="drafter-timer",
        emitted_events=[
            EventPayloadSpec(
                event_name="tick",
                fields=[
                    EventPayloadFieldSpec(
                        "remaining",
                        int,
                        "Milliseconds left before the timer finishes.",
                    ),
                    EventPayloadFieldSpec(
                        "duration",
                        int,
                        "Total duration of the timer in milliseconds.",
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="finish",
                fields=[
                    EventPayloadFieldSpec(
                        "remaining",
                        int,
                        "Always 0 when the timer finishes.",
                    ),
                    EventPayloadFieldSpec(
                        "duration",
                        int,
                        "Total duration of the timer in milliseconds.",
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        duration: int,
        on_finish: UrlOrFunction,
        show: bool = True,
        controls: bool = False,
        persistent: bool = False,
        rate: int = 1000,
        on_tick: UrlOrFunction | None = None,
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


COMPONENT_CONTRACT_REGISTRY.register(Timer.CONTRACT)


@dataclass(repr=False)
class Clock(Component):
    """Clock component that simulates a clock ticking up.
    Provides the ability to call a function on each tick.

    Note that if the function takes more than the tick interval to execute,
    ticks may be delayed.

    Internally uses setInterval to trigger the callback on each tick.

    Note:
        The `route` field is rendered as the `on_tick` attribute (via
        `RENAME_ATTRS`), so `route` is effectively an alias for `on_tick`;
        both trigger the same tick event handling.

    Attributes:
        interval: Interval between ticks in milliseconds.
        route: Function or URL to call on each tick.
        show: Whether to display the elapsed time. Defaults to True.
        controls: Whether to show pause/restart controls. Defaults to False.
        persistent: Whether the clock keeps running across page transitions.
            Defaults to False.
        on_tick: Optional function or URL to call on each tick; alternative
            keyword spelling of `route`. Defaults to None.
    """

    interval: int
    route: UrlOrFunction
    show: bool = True
    controls: bool = False
    persistent: bool = False
    on_tick: UrlOrFunction | None = None

    tag = "drafter-clock"

    PERSISTABLE = True
    DEFAULT_ATTRS = {"role": "clock"}
    RENAME_ATTRS = {"route": "on_tick"}
    KNOWN_ATTRS = [
        "interval",
        "on_tick",
        "show",
        "controls",
        "persistent",
    ]
    ARGUMENTS = [
        ComponentArgument("interval", "positional", 1000),
        ComponentArgument("route", "positional", None, is_event=True),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("controls", "keyword", False),
        ComponentArgument("persistent", "keyword", False),
        ComponentArgument("on_tick", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["tick"]

    #: What this component emits: the JS implementation (js/src/components/
    #: timer.tsx) must match this contract, and the router uses it to reason
    #: about event payload fields.
    CONTRACT = ComponentContract(
        component_name="Clock",
        html_tag="drafter-clock",
        emitted_events=[
            EventPayloadSpec(
                event_name="tick",
                fields=[
                    EventPayloadFieldSpec(
                        "elapsed",
                        int,
                        "Milliseconds elapsed since the clock started.",
                    ),
                    EventPayloadFieldSpec(
                        "interval",
                        int,
                        "Current interval in milliseconds between ticks.",
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        interval: int,
        route: UrlOrFunction,
        show: bool = True,
        controls: bool = False,
        persistent: bool = False,
        on_tick: UrlOrFunction | None = None,
        **kwargs,
    ):
        self.interval = interval
        self.route = route
        self.show = show
        self.controls = controls
        self.persistent = persistent
        self.on_tick = on_tick
        self.extra_settings = kwargs


COMPONENT_CONTRACT_REGISTRY.register(Clock.CONTRACT)
