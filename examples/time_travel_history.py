"""
Demonstrates browser-history time travel: every navigation stores a snapshot
of the state as it was when that page was visited, so the browser's back and
forward buttons genuinely rewind (and re-advance) the application instead of
replaying routes against the newest state.

Things to try:

1. March onward and dig for treasure a few times, watching the day, gold,
   and expedition log grow.
2. Press the browser's BACK button: the whole state rewinds to how it was
   on that page (the day and gold shrink back, log entries vanish). FORWARD
   re-advances. Backing all the way to the first page restores the very
   first state, Day 1 with 10 gold.
3. Now pick up the Boulder of Regret. It stuffs about 1.5 million
   characters into the state, which is over the snapshot size limit
   (BrowserHistory.MAX_STATE_JSON_LENGTH, one million JSON characters), so
   every navigation made while carrying it records a history entry WITHOUT
   a snapshot and reports a `bridge.history_state_too_large` warning (watch
   the debug panel / console). Pressing back over those entries falls back
   to the old behavior: the page is replayed with the CURRENT state, so the
   day and gold no longer rewind.
4. Drop the boulder and navigate again: snapshots resume, and new entries
   time-travel normally, while the boulder-era entries stay replay-only.
"""

from dataclasses import dataclass, field

from drafter import *

# Big enough to push the state's JSON past the one-million-character
# snapshot limit, small enough to stay quick to copy around.
BOULDER_WEIGHT = 1_500_000


@dataclass
class State:
    day: int
    gold: int
    log: list[str] = field(default_factory=list)
    # Empty normally; BOULDER_WEIGHT characters of granite while carrying
    # the boulder.
    boulder: str = ""


def carrying_boulder(state: State) -> bool:
    return len(state.boulder) > 0


@route
def index(state: State) -> Page:
    if carrying_boulder(state):
        pack_status = (
            f"You are lugging the Boulder of Regret ({len(state.boulder):,} "
            "characters of solid granite). The state is now too large to "
            "snapshot into browser history, so the back button will only "
            "REPLAY these pages with the current state instead of rewinding "
            "it. A warning appears in the debug panel on each navigation."
        )
        boulder_button = Button("Drop the boulder", drop_boulder)
    else:
        pack_status = (
            "Your pack is light, so every page you visit snapshots the "
            "state into browser history. Press the browser's back button "
            "at any time to rewind the expedition."
        )
        boulder_button = Button("Pick up the Boulder of Regret", pick_up_boulder)
    return Page(
        state,
        [
            Header("The Time-Traveling Expedition"),
            f"Day {state.day}, with {state.gold} gold.",
            Div(pack_status),
            Button("March onward", march),
            Button("Dig for treasure", dig),
            boulder_button,
            Header("Expedition log", 2),
            BulletedList(state.log if state.log else ["Nothing has happened yet."]),
        ],
    )


@route
def march(state: State) -> Page:
    state.day += 1
    state.gold -= 1
    state.log.append(f"Day {state.day}: marched onward, spent 1 gold on rations.")
    return index(state)


@route
def dig(state: State) -> Page:
    found = 3 + state.day % 5
    state.gold += found
    state.log.append(f"Day {state.day}: dug for treasure and found {found} gold.")
    return index(state)


@route
def pick_up_boulder(state: State) -> Page:
    state.boulder = "granite " * (BOULDER_WEIGHT // 8)
    state.log.append(
        f"Day {state.day}: picked up the Boulder of Regret "
        f"({len(state.boulder):,} characters). History snapshots now fail!"
    )
    return index(state)


@route
def drop_boulder(state: State) -> Page:
    state.boulder = ""
    state.log.append(f"Day {state.day}: dropped the boulder. History snapshots resume.")
    return index(state)


start_server(State(day=1, gold=10))
