"""A tour of the Web Audio components: tones, melodies, microphone
monitoring, and recording with playback effects."""

from drafter import *


@dataclass
class State:
    claps: int
    last_note: str


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            Header("Audio Playground"),
            "Play a single note:",
            Tone("C4"),
            Tone(
                "E4",
                waveform="square",
                volume=0.5,
            ),
            Tone(440, duration=1000, effects=[Echo()]),
            "Play a melody (it's just a list!):",
            Melody(
                ["C4", "E4", "G4", ("C5", 2), "rest", "G4", ("C5", 2)],
                tempo=180,
                controls=True,
                on_note=heard_note,
            ),
            Span(f"Last note played: {state.last_note}", id="last-note"),
            Button("Clap counter", clap_page),
            Button("Recording booth", recording_page),
        ],
    )


@route
def heard_note(state: State, note: str) -> Fragment:
    # A full Page here would re-render everything and stop the melody after
    # its first note; a Fragment only updates the "last note" text.
    state.last_note = note
    return Fragment(state, [f"Last note played: {note}"], target="#last-note")


@route
def clap_page(state: State) -> Page:
    return Page(
        state,
        [
            Header("Clap Counter"),
            Span(f"👏 Claps so far: {state.claps}", id="clap-count"),
            Microphone("mic", threshold=0.1, on_loud=clapped),
            Button("Check the room", check_room),
            Button("Back", index),
        ],
    )


@route
def clapped(state: State, volume: float) -> Fragment:
    # Updating just the counter keeps the microphone meter running.
    state.claps += 1
    return Fragment(state, [f"👏 Claps so far: {state.claps}"], target="#clap-count")


@route
def check_room(state: State, mic: AudioLevel) -> Page:
    if mic.status != "granted":
        message = f"Microphone not available: {mic.message}"
    else:
        message = f"Room volume is {mic.volume:.0%} (peak {mic.peak_volume:.0%})"
    return Page(state, [message, Button("Back", clap_page)])


@route
def recording_page(state: State) -> Page:
    return Page(
        state,
        [
            Header("Recording Booth"),
            "Record yourself, then hear it back with effects:",
            AudioRecorder("voice"),
            Button("Play it spooky", play_spooky),
            Button("Back", index),
        ],
    )


@route
def play_spooky(state: State, voice: Recording) -> Page:
    if voice.status != "granted":
        return Page(
            state,
            [
                f"No recording yet: {voice.message}",
                Button("Back", recording_page),
            ],
        )
    return Page(
        state,
        [
            "Here you are, but spookier:",
            Sound(
                voice.data_url,
                speed=0.8,
                effects=[Reverb(0.8), Echo(delay=0.4, strength=0.3)],
                auto_play=True,
            ),
            Button("Back", recording_page),
        ],
    )


start_server(State(0, "none"))
