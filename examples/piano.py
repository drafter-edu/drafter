from drafter import *

# Two musical scales
C_MAJOR = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]

G_MAJOR = ["G4", "A4", "B4", "C5", "D5", "E5", "F#5", "G5"]

# Piano keys
WHITE_KEYS = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5"]

BLACK_KEYS = ["C#4", "D#4", "F#4", "G#4", "A#4", "C#5", "D#5", "F#5"]


def piano_key(note, black=False):
    return Button(
        note,
        "play_note",
        [Argument("note", note)],
        style_background_color="black" if black else "white",
        style_color="white" if black else "black",
        style_height="90px" if black else "150px",
        style_width="55px",
        style_border="1px solid gray",
    )


@route
def index() -> Page:
    return Page(
        [
            Header("My Piano"),
            Header("Play a Scale", level=2),
            Row(
                Button("Play C Major", "play_c_major"),
                Button("Play G Major", "play_g_major"),
            ),
            Header("Piano Keyboard", level=2),
            Row(*[piano_key(note, True) for note in BLACK_KEYS], style_gap="4px"),
            Row(*[piano_key(note) for note in WHITE_KEYS], style_gap="4px"),
            Output("sound_area", ["Click a key or play a scale"]),
        ]
    )


@route
def play_note(note: str) -> Fragment:
    return Fragment(
        [Tone(note, duration=400, waveform="triangle", auto_play=True, show=False)],
        target="#sound_area",
    )


@route
def play_c_major() -> Fragment:
    return Fragment(
        [Melody(C_MAJOR, tempo=140, waveform="triangle", auto_play=True, show=False)],
        target="#sound_area",
    )


@route
def play_g_major() -> Fragment:
    return Fragment(
        [Melody(G_MAJOR, tempo=140, waveform="triangle", auto_play=True, show=False)],
        target="#sound_area",
    )


start_server()
