"""Web Audio components for playing, analyzing, and recording sound.

Provides five components built on the browser's Web Audio API:

- :class:`Tone`: play a single pitch (a note name like ``"C4"`` or a
  frequency in Hz) with a chosen waveform.
- :class:`Melody`: play a sequence of notes at a tempo; a melody is just a
  Python list, so students can compose music with list operations.
- :class:`Sound`: play an audio file through an optional chain of effects
  (echo, reverb, muffle, sharpen, distortion) with volume/pan/speed control.
- :class:`Microphone`: monitor live microphone input, firing events when the
  room gets loud or quiet and providing an :class:`AudioLevel` snapshot on
  form submission.
- :class:`AudioRecorder`: record microphone audio and submit it as a
  :class:`Recording` that can be played back with :class:`Sound`.

The Python side only describes the components: each renders as a custom
element (``<drafter-tone>``, ``<drafter-melody>``, ``<drafter-sound>``,
``<drafter-microphone>``, ``<drafter-audio-recorder>``) whose behavior is
implemented in js/src/components/. A single shared AudioContext lives in
js/src/components/audioBroker.ts; because browsers require a user gesture
before sound can play, components rendered before any interaction show a
small "Enable sound" prompt (the audio analog of the geolocation permission
prompt).

Like :class:`~drafter.components.geolocation.CurrentLocation`, the
:class:`Microphone` and :class:`AudioRecorder` components keep a hidden form
field (named after the component) updated with JSON-encoded data;
converters registered below turn those payloads into :class:`AudioLevel`
and :class:`Recording` values when a matching route parameter is annotated
with them. Failures become ``status`` values rather than exceptions, so
routes can inspect problems without try/except.
"""

import json
from dataclasses import asdict, dataclass
from typing import ClassVar, List, Literal, Optional, Tuple, Union

from drafter.components.page_content import Component, ComponentArgument, UrlOrFunction
from drafter.components.utilities.contracts import (
    ComponentContract,
    EventPayloadFieldSpec,
    EventPayloadSpec,
)
from drafter.components.utilities.registry import (
    COMPONENT_CONTRACT_REGISTRY,
    CONVERTER_REGISTRY,
)
from drafter.components.utilities.validation import validate_parameter_name
from drafter.data.converter import ConversionContext, ConversionResult


WAVEFORMS = ("sine", "square", "triangle", "sawtooth")

VISUALIZATIONS = ("meter", "waveform", "bars")

MicrophoneStatus = Literal[
    "unavailable", "prompt", "pending", "granted", "denied", "error"
]
RecordingStatus = Literal[
    "unavailable", "prompt", "recording", "granted", "denied", "error"
]

#: Semitone offset of each letter name from C within an octave.
_NOTE_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

#: A note that plays silence for its beats in a Melody.
REST = "rest"

NoteValue = Union[str, Tuple[str, Union[int, float]]]


def note_to_frequency(note: str) -> float:
    """Convert a note name like ``"C4"``, ``"F#3"``, or ``"Bb2"`` to Hz.

    Uses equal temperament with A4 = 440 Hz. Note names are a letter A-G,
    an optional ``#`` (sharp) or ``b`` (flat), and an octave digit 0-9.

    Args:
        note: The note name to convert.

    Returns:
        The frequency in Hz.

    Raises:
        ValueError: If the note name is not recognized.
    """
    original = note
    note = note.strip()
    if len(note) < 2:
        raise ValueError(_bad_note_message(original))
    letter = note[0].upper()
    if letter not in _NOTE_SEMITONES:
        raise ValueError(_bad_note_message(original))
    rest = note[1:]
    accidental = 0
    if rest[0] in ("#", "♯"):
        accidental = 1
        rest = rest[1:]
    elif rest[0] in ("b", "♭") and len(rest) > 1:
        accidental = -1
        rest = rest[1:]
    if not rest.isdigit() or len(rest) != 1:
        raise ValueError(_bad_note_message(original))
    octave = int(rest)
    midi = (octave + 1) * 12 + _NOTE_SEMITONES[letter] + accidental
    return round(440.0 * 2 ** ((midi - 69) / 12), 4)


def _bad_note_message(note) -> str:
    return (
        f"Invalid note name: {note!r}. Notes are a letter (A-G), an optional"
        " # (sharp) or b (flat), and an octave digit (0-9), like 'C4',"
        " 'F#3', or 'Bb5'."
    )


def _validate_pitch(pitch, component_name: str) -> None:
    """Check that a pitch is a valid note name or a positive frequency."""
    if isinstance(pitch, str):
        note_to_frequency(pitch)
    elif isinstance(pitch, (int, float)) and not isinstance(pitch, bool):
        if pitch <= 0:
            raise ValueError(
                f"{component_name} pitch must be a positive frequency in Hz,"
                f" not {pitch!r}."
            )
    else:
        raise ValueError(
            f"{component_name} pitch must be a note name like 'C4' or a"
            f" frequency in Hz, not {pitch!r}."
        )


def _validate_fraction(value, parameter_name: str, component_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(
            f"{component_name} {parameter_name} must be a number between"
            f" 0.0 and 1.0, not {value!r}."
        )
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{component_name} {parameter_name} must be between 0.0 and 1.0,"
            f" not {value!r}."
        )


def _validate_waveform(waveform, component_name: str) -> None:
    if waveform not in WAVEFORMS:
        raise ValueError(
            f"{component_name} waveform must be one of"
            f" {', '.join(repr(w) for w in WAVEFORMS)}, not {waveform!r}."
        )


@dataclass
class AudioLevel:
    """A snapshot of microphone input from a :class:`Microphone` component.

    Attributes:
        status: Current permission/availability state.
        message: Optional descriptive message about the status.
        volume: Loudness from 0.0 (silence) to 1.0 (as loud as the
            microphone can measure) at the moment the form was submitted,
            based on the peak signal level (None if unavailable).
        peak_volume: The loudest volume heard since the page loaded
            (None if unavailable).
        pitch: The dominant frequency in Hz of the sound being heard
            (None if unavailable or too quiet to estimate).
    """

    status: MicrophoneStatus
    message: Optional[str] = None
    volume: Optional[float] = None
    peak_volume: Optional[float] = None
    pitch: Optional[float] = None


@dataclass
class Recording:
    """A completed audio recording from an :class:`AudioRecorder` component.

    The ``data_url`` can be handed directly to :class:`Sound` (or
    :class:`~drafter.components.media.Audio`) to play the recording back.

    Attributes:
        status: Current permission/recording state.
        message: Optional descriptive message about the status.
        data_url: The recorded audio as a data URL (None if nothing has
            been recorded).
        duration: Length of the recording in seconds (None if unavailable).
        size: Size of the recorded audio in bytes (None if unavailable).
    """

    status: RecordingStatus
    message: Optional[str] = None
    data_url: Optional[str] = None
    duration: Optional[float] = None
    size: Optional[int] = None


def _is_audio_level_type(target) -> bool:
    return target is AudioLevel


def _is_recording_type(target) -> bool:
    return target is Recording


def _convert_json_dataclass(ctx: ConversionContext, dataclass_type, label: str):
    """Shared conversion logic: JSON string or dict payload into a dataclass.

    An unparseable payload becomes a status of ``"error"`` rather than a
    crash, so routes can inspect the problem without try/except.
    """
    value = ctx.raw_value
    if isinstance(value, dataclass_type):
        return ConversionResult(ok=True, value=value)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            return ConversionResult(
                ok=True,
                value=dataclass_type(
                    status="error",
                    message=f"Failed to parse {label} data: {error}",
                ),
            )
    if isinstance(value, dict):
        try:
            return ConversionResult(ok=True, value=dataclass_type(**value))
        except TypeError as error:
            return ConversionResult(
                ok=True,
                value=dataclass_type(
                    status="error",
                    message=f"Failed to parse {label} data: {error}",
                ),
            )
    return None


def convert_audio_level(ctx: ConversionContext) -> Optional[ConversionResult]:
    """Convert a JSON string or dict payload into an :class:`AudioLevel`."""
    return _convert_json_dataclass(ctx, AudioLevel, "microphone")


def convert_recording(ctx: ConversionContext) -> Optional[ConversionResult]:
    """Convert a JSON string or dict payload into a :class:`Recording`."""
    return _convert_json_dataclass(ctx, Recording, "recording")


CONVERTER_REGISTRY.register_predicate(
    _is_audio_level_type, convert_audio_level, priority=20, name="AudioLevel"
)
CONVERTER_REGISTRY.register_predicate(
    _is_recording_type, convert_recording, priority=20, name="Recording"
)


@dataclass
class AudioEffect:
    """Base class for audio effects that can be chained onto sound.

    Effects are plain values, not components: pass a list of them as the
    ``effects`` parameter of :class:`Sound`, :class:`Tone`, or
    :class:`Melody`, and they are applied in order.
    """

    EFFECT_TYPE: ClassVar[str] = ""

    def to_config(self) -> dict:
        """Serialize this effect to the JSON configuration the JS side reads."""
        config = {"type": self.EFFECT_TYPE}
        config.update(asdict(self))
        return config


@dataclass
class Echo(AudioEffect):
    """Repeats the sound after a delay, quieter each time.

    Attributes:
        delay: Seconds between repeats. Defaults to 0.3.
        strength: How loud each repeat is relative to the one before,
            from 0.0 (no echo) to 1.0 (repeats forever). Defaults to 0.4.
    """

    EFFECT_TYPE: ClassVar[str] = "echo"
    delay: float = 0.3
    strength: float = 0.4


@dataclass
class Reverb(AudioEffect):
    """Makes the sound ring out as if played in a large room.

    Attributes:
        amount: How much reverberation to add, from 0.0 (none) to 1.0
            (cavernous). Defaults to 0.5.
    """

    EFFECT_TYPE: ClassVar[str] = "reverb"
    amount: float = 0.5


@dataclass
class Muffle(AudioEffect):
    """Removes high frequencies, like hearing sound through a wall.

    Attributes:
        amount: How muffled the sound is, from 0.0 (unchanged) to 1.0
            (very muffled). Defaults to 0.5.
    """

    EFFECT_TYPE: ClassVar[str] = "muffle"
    amount: float = 0.5


@dataclass
class Sharpen(AudioEffect):
    """Removes low frequencies, like a tinny phone speaker.

    Attributes:
        amount: How thinned-out the sound is, from 0.0 (unchanged) to 1.0
            (very tinny). Defaults to 0.5.
    """

    EFFECT_TYPE: ClassVar[str] = "sharpen"
    amount: float = 0.5


@dataclass
class Distortion(AudioEffect):
    """Overdrives the sound for a gritty, fuzzy character.

    Attributes:
        amount: How distorted the sound is, from 0.0 (clean) to 1.0
            (heavily distorted). Defaults to 0.3.
    """

    EFFECT_TYPE: ClassVar[str] = "distortion"
    amount: float = 0.3


def _validate_effects(effects, component_name: str) -> None:
    if effects is None:
        return
    if not isinstance(effects, list):
        raise ValueError(
            f"{component_name} effects must be a list of effects like"
            f" [Echo(), Reverb()], not {effects!r}."
        )
    for index, effect in enumerate(effects):
        if not isinstance(effect, AudioEffect):
            raise ValueError(
                f"{component_name} effects must all be effects (Echo, Reverb,"
                f" Muffle, Sharpen, or Distortion), but item {index} was"
                f" {effect!r}."
            )
        for field_name, field_value in asdict(effect).items():
            if not isinstance(field_value, (int, float)) or isinstance(
                field_value, bool
            ):
                raise ValueError(
                    f"{component_name} effects: {type(effect).__name__}"
                    f" {field_name} must be a number, not {field_value!r}."
                )


def _serialize_effects(effects: List[AudioEffect]) -> str:
    return json.dumps([effect.to_config() for effect in effects])


@dataclass(repr=False)
class Tone(Component):
    """Plays a single pitch using the browser's Web Audio API.

    The pitch can be a note name like ``"C4"`` or ``"F#3"``, or a raw
    frequency in Hz like ``440``. By default the component renders a small
    play button; with ``auto_play=True`` it plays as soon as the page loads
    (browsers require at least one interaction with the page first, so a
    tone on the very first page shows an "Enable sound" prompt instead).

    Attributes:
        pitch: Note name (``"C4"``) or frequency in Hz (``440``).
        duration: How long the tone plays, in milliseconds. Defaults to 500.
        waveform: The shape of the sound wave: "sine" (smooth), "square"
            (buzzy), "triangle" (mellow), or "sawtooth" (bright).
        volume: Loudness from 0.0 to 1.0. Defaults to 0.8.
        attack: Milliseconds to fade in (prevents clicks). Defaults to 10.
        release: Milliseconds to fade out. Defaults to 50.
        auto_play: Whether to play as soon as the page loads instead of
            showing a play button. Defaults to False.
        show: Whether to display the component. Defaults to True.
        effects: Optional list of effects (like :class:`Echo`) applied in order.
        on_start: Function or URL to call when the tone starts playing.
        on_finish: Function or URL to call when the tone finishes playing.
        on_error: Function or URL to call if the tone cannot be played.
    """

    pitch: Union[str, int, float]
    duration: int = 500
    waveform: str = "sine"
    volume: float = 0.8
    attack: int = 10
    release: int = 50
    auto_play: bool = False
    show: bool = True
    effects: Optional[List[AudioEffect]] = None
    on_start: Optional[UrlOrFunction] = None
    on_finish: Optional[UrlOrFunction] = None
    on_error: Optional[UrlOrFunction] = None

    tag = "drafter-tone"

    KNOWN_ATTRS = [
        "pitch",
        "duration",
        "waveform",
        "volume",
        "attack",
        "release",
        "auto-play",
        "show",
        "effects",
    ]
    ARGUMENTS = [
        ComponentArgument("pitch", "positional"),
        ComponentArgument("duration", "keyword", 500),
        ComponentArgument("waveform", "keyword", "sine"),
        ComponentArgument("volume", "keyword", 0.8),
        ComponentArgument("attack", "keyword", 10),
        ComponentArgument("release", "keyword", 50),
        ComponentArgument("auto_play", "keyword", False),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("effects", "keyword", None),
        ComponentArgument("on_start", "keyword", None, is_event=True),
        ComponentArgument("on_finish", "keyword", None, is_event=True),
        ComponentArgument("on_error", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["start", "finish", "error"]

    #: What this component emits: the JS implementation (js/src/components/
    #: tone.tsx) must match this contract, and the router uses it to reason
    #: about event payload fields.
    CONTRACT = ComponentContract(
        component_name="Tone",
        html_tag="drafter-tone",
        emitted_events=[
            EventPayloadSpec(
                event_name="start",
                fields=[
                    EventPayloadFieldSpec(
                        "frequency", float, "The pitch being played, in Hz."
                    ),
                    EventPayloadFieldSpec(
                        "duration", int, "How long the tone plays, in milliseconds."
                    ),
                    EventPayloadFieldSpec(
                        "waveform", str, "The waveform being played."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "note", str, "The note name, if a note name was given."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="finish",
                fields=[
                    EventPayloadFieldSpec(
                        "frequency", float, "The pitch that was played, in Hz."
                    ),
                    EventPayloadFieldSpec(
                        "duration", int, "How long the tone played, in milliseconds."
                    ),
                    EventPayloadFieldSpec(
                        "waveform", str, "The waveform that was played."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "note", str, "The note name, if a note name was given."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="error",
                fields=[
                    EventPayloadFieldSpec(
                        "status", str, "Failure state: unavailable or error."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the failure."
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        pitch: Union[str, int, float],
        duration: int = 500,
        waveform: str = "sine",
        volume: float = 0.8,
        attack: int = 10,
        release: int = 50,
        auto_play: bool = False,
        show: bool = True,
        effects: Optional[List[AudioEffect]] = None,
        on_start: Optional[UrlOrFunction] = None,
        on_finish: Optional[UrlOrFunction] = None,
        on_error: Optional[UrlOrFunction] = None,
        **extra_settings,
    ):
        """Initialize the Tone component.

        Args:
            pitch: Note name ("C4") or frequency in Hz (440).
            duration: How long the tone plays, in milliseconds.
            waveform: "sine", "square", "triangle", or "sawtooth".
            volume: Loudness from 0.0 to 1.0.
            attack: Milliseconds to fade in.
            release: Milliseconds to fade out.
            auto_play: Whether to play on page load instead of showing a button.
            show: Whether to display the component.
            effects: Optional list of effects applied in order.
            on_start: Function or URL to call when the tone starts.
            on_finish: Function or URL to call when the tone finishes.
            on_error: Function or URL to call if the tone cannot play.
            **extra_settings: Additional HTML attributes.
        """
        _validate_pitch(pitch, "Tone")
        _validate_waveform(waveform, "Tone")
        _validate_fraction(volume, "volume", "Tone")
        _validate_effects(effects, "Tone")
        self.pitch = pitch
        self.duration = duration
        self.waveform = waveform
        self.volume = volume
        self.attack = attack
        self.release = release
        self.auto_play = auto_play
        self.show = show
        self.effects = effects
        self.on_start = on_start
        self.on_finish = on_finish
        self.on_error = on_error
        self.extra_settings = extra_settings

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        if isinstance(attributes.get("effects"), list):
            attributes["effects"] = _serialize_effects(attributes["effects"])
        return attributes


COMPONENT_CONTRACT_REGISTRY.register(Tone.CONTRACT)


def _normalize_notes(notes) -> List[List]:
    """Validate a Melody note list and normalize it to [note, beats] pairs."""
    if not isinstance(notes, list) or not notes:
        raise ValueError(
            "Melody notes must be a non-empty list of note names like"
            " ['C4', 'E4', 'G4'], optionally with beats like [('C4', 2)]."
        )
    normalized = []
    for index, item in enumerate(notes):
        beats = 1
        note = item
        if isinstance(item, (tuple, list)):
            if len(item) != 2:
                raise ValueError(
                    f"Melody notes: item {index} should be a (note, beats)"
                    f" pair, but had {len(item)} parts: {item!r}."
                )
            note, beats = item
            if (
                not isinstance(beats, (int, float))
                or isinstance(beats, bool)
                or beats <= 0
            ):
                raise ValueError(
                    f"Melody notes: item {index} has beats {beats!r}, but"
                    " beats must be a positive number."
                )
        if note is None:
            note = REST
        if not isinstance(note, str):
            raise ValueError(
                f"Melody notes: item {index} should be a note name like 'C4'"
                f" or 'rest', not {note!r}."
            )
        if note.strip().lower() == REST:
            note = REST
        else:
            note_to_frequency(note)
        normalized.append([note, beats])
    return normalized


@dataclass(repr=False)
class Melody(Component):
    """Plays a sequence of notes at a tempo using the Web Audio API.

    A melody is just a list: each item is a note name like ``"C4"`` (played
    for one beat), a ``(note, beats)`` pair like ``("C4", 2)``, or
    ``"rest"`` for silence. Notes are scheduled with sample-accurate Web
    Audio timing, so melodies stay in rhythm.

    Note:
        An ``on_note`` handler that returns a full :class:`~drafter.Page`
        re-renders the whole page, which stops and resets this melody after
        its very first note. To react to notes while the melody keeps
        playing, return an ``Update`` (change state only) or a ``Fragment``
        targeting another element; save full pages for ``on_finish``.

    Attributes:
        notes: The notes to play, in order.
        tempo: Speed in beats per minute. Defaults to 120.
        waveform: The shape of the sound wave: "sine", "square", "triangle",
            or "sawtooth". Defaults to "sine".
        volume: Loudness from 0.0 to 1.0. Defaults to 0.8.
        auto_play: Whether to play as soon as the page loads instead of
            showing a play button. Defaults to False.
        controls: Whether to show play/pause and restart buttons. Defaults
            to False.
        show: Whether to display the component. Defaults to True.
        effects: Optional list of effects (like :class:`Echo`) applied in order.
        on_note: Function or URL to call as each note starts.
        on_finish: Function or URL to call when the melody finishes.
    """

    notes: List[NoteValue]
    tempo: Union[int, float] = 120
    waveform: str = "sine"
    volume: float = 0.8
    auto_play: bool = False
    controls: bool = False
    show: bool = True
    effects: Optional[List[AudioEffect]] = None
    on_note: Optional[UrlOrFunction] = None
    on_finish: Optional[UrlOrFunction] = None

    tag = "drafter-melody"

    KNOWN_ATTRS = [
        "notes",
        "tempo",
        "waveform",
        "volume",
        "auto-play",
        "controls",
        "show",
        "effects",
    ]
    ARGUMENTS = [
        ComponentArgument("notes", "positional"),
        ComponentArgument("tempo", "keyword", 120),
        ComponentArgument("waveform", "keyword", "sine"),
        ComponentArgument("volume", "keyword", 0.8),
        ComponentArgument("auto_play", "keyword", False),
        ComponentArgument("controls", "keyword", False),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("effects", "keyword", None),
        ComponentArgument("on_note", "keyword", None, is_event=True),
        ComponentArgument("on_finish", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["note", "finish"]

    #: What this component emits: the JS implementation (js/src/components/
    #: melody.tsx) must match this contract, and the router uses it to reason
    #: about event payload fields.
    CONTRACT = ComponentContract(
        component_name="Melody",
        html_tag="drafter-melody",
        emitted_events=[
            EventPayloadSpec(
                event_name="note",
                fields=[
                    EventPayloadFieldSpec(
                        "note", str, "The note name now playing (or 'rest')."
                    ),
                    EventPayloadFieldSpec(
                        "frequency",
                        float,
                        "The frequency now playing in Hz (0 for a rest).",
                    ),
                    EventPayloadFieldSpec(
                        "index", int, "The position of this note in the melody."
                    ),
                    EventPayloadFieldSpec(
                        "count", int, "The total number of notes in the melody."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="finish",
                fields=[
                    EventPayloadFieldSpec(
                        "count", int, "The total number of notes that played."
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        notes: List[NoteValue],
        tempo: Union[int, float] = 120,
        waveform: str = "sine",
        volume: float = 0.8,
        auto_play: bool = False,
        controls: bool = False,
        show: bool = True,
        effects: Optional[List[AudioEffect]] = None,
        on_note: Optional[UrlOrFunction] = None,
        on_finish: Optional[UrlOrFunction] = None,
        **extra_settings,
    ):
        """Initialize the Melody component.

        Args:
            notes: List of note names like 'C4', (note, beats) pairs, or 'rest'.
            tempo: Speed in beats per minute.
            waveform: "sine", "square", "triangle", or "sawtooth".
            volume: Loudness from 0.0 to 1.0.
            auto_play: Whether to play on page load instead of showing a button.
            controls: Whether to show play/pause and restart buttons.
            show: Whether to display the component.
            effects: Optional list of effects applied in order.
            on_note: Function or URL to call as each note starts.
            on_finish: Function or URL to call when the melody finishes.
            **extra_settings: Additional HTML attributes.
        """
        _normalize_notes(notes)
        _validate_waveform(waveform, "Melody")
        _validate_fraction(volume, "volume", "Melody")
        _validate_effects(effects, "Melody")
        if not isinstance(tempo, (int, float)) or isinstance(tempo, bool) or tempo <= 0:
            raise ValueError(
                f"Melody tempo must be a positive number of beats per minute,"
                f" not {tempo!r}."
            )
        self.notes = notes
        self.tempo = tempo
        self.waveform = waveform
        self.volume = volume
        self.auto_play = auto_play
        self.controls = controls
        self.show = show
        self.effects = effects
        self.on_note = on_note
        self.on_finish = on_finish
        self.extra_settings = extra_settings

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        attributes["notes"] = json.dumps(_normalize_notes(self.notes))
        if isinstance(attributes.get("effects"), list):
            attributes["effects"] = _serialize_effects(attributes["effects"])
        return attributes


COMPONENT_CONTRACT_REGISTRY.register(Melody.CONTRACT)


@dataclass(repr=False)
class Sound(Component):
    """Plays an audio file through the Web Audio API with optional effects.

    Unlike the plain :class:`~drafter.components.media.Audio` component,
    Sound routes the audio through a processing chain, so it can change
    volume, stereo position, and playback speed, and apply effects like
    :class:`Echo` or :class:`Reverb`. The ``data_url`` of a
    :class:`Recording` can be played back this way, too.

    Attributes:
        src: URL (or data URL) of the audio to play.
        volume: Loudness from 0.0 to 1.0. Defaults to 1.0.
        pan: Stereo position from -1.0 (left) to 1.0 (right). Defaults to 0.0.
        speed: Playback speed multiplier; below 1.0 is slower and deeper,
            above 1.0 is faster and higher. Defaults to 1.0.
        loop: Whether to repeat forever. Defaults to False.
        effects: Optional list of effects (like :class:`Echo`) applied in order.
        auto_play: Whether to start playing as soon as the page loads.
            Defaults to False.
        controls: Whether to show playback controls. Defaults to True.
        visualize: Optional live visualization drawn while playing:
            "waveform" or "bars". Defaults to None.
        on_play: Function or URL to call when playback starts.
        on_finish: Function or URL to call when playback finishes.
        on_error: Function or URL to call if the audio cannot be played.
    """

    src: str
    volume: float = 1.0
    pan: float = 0.0
    speed: float = 1.0
    loop: bool = False
    effects: Optional[List[AudioEffect]] = None
    auto_play: bool = False
    controls: bool = True
    visualize: Optional[str] = None
    on_play: Optional[UrlOrFunction] = None
    on_finish: Optional[UrlOrFunction] = None
    on_error: Optional[UrlOrFunction] = None

    tag = "drafter-sound"

    DEFAULT_ATTRS = {"controls": True}
    KNOWN_ATTRS = [
        "src",
        "volume",
        "pan",
        "speed",
        "loop",
        "effects",
        "auto-play",
        "controls",
        "visualize",
    ]
    ARGUMENTS = [
        ComponentArgument("src", "positional"),
        ComponentArgument("volume", "keyword", 1.0),
        ComponentArgument("pan", "keyword", 0.0),
        ComponentArgument("speed", "keyword", 1.0),
        ComponentArgument("loop", "keyword", False),
        ComponentArgument("effects", "keyword", None),
        ComponentArgument("auto_play", "keyword", False),
        ComponentArgument("controls", "keyword", True),
        ComponentArgument("visualize", "keyword", None),
        ComponentArgument("on_play", "keyword", None, is_event=True),
        ComponentArgument("on_finish", "keyword", None, is_event=True),
        ComponentArgument("on_error", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["play", "finish", "error"]

    #: What this component emits: the JS implementation (js/src/components/
    #: sound.tsx) must match this contract, and the router uses it to reason
    #: about event payload fields.
    CONTRACT = ComponentContract(
        component_name="Sound",
        html_tag="drafter-sound",
        emitted_events=[
            EventPayloadSpec(
                event_name="play",
                fields=[
                    EventPayloadFieldSpec(
                        "src", str, "The URL of the audio being played."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="finish",
                fields=[
                    EventPayloadFieldSpec(
                        "src", str, "The URL of the audio that finished."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "duration", float, "Length of the audio in seconds."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="error",
                fields=[
                    EventPayloadFieldSpec(
                        "status", str, "Failure state: unavailable or error."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the failure."
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        src: str,
        volume: float = 1.0,
        pan: float = 0.0,
        speed: float = 1.0,
        loop: bool = False,
        effects: Optional[List[AudioEffect]] = None,
        auto_play: bool = False,
        controls: bool = True,
        visualize: Optional[str] = None,
        on_play: Optional[UrlOrFunction] = None,
        on_finish: Optional[UrlOrFunction] = None,
        on_error: Optional[UrlOrFunction] = None,
        **extra_settings,
    ):
        """Initialize the Sound component.

        Args:
            src: URL (or data URL) of the audio to play.
            volume: Loudness from 0.0 to 1.0.
            pan: Stereo position from -1.0 (left) to 1.0 (right).
            speed: Playback speed multiplier.
            loop: Whether to repeat forever.
            effects: Optional list of effects applied in order.
            auto_play: Whether to start playing on page load.
            controls: Whether to show playback controls.
            visualize: Optional visualization: "waveform" or "bars".
            on_play: Function or URL to call when playback starts.
            on_finish: Function or URL to call when playback finishes.
            on_error: Function or URL to call if the audio cannot play.
            **extra_settings: Additional HTML attributes.
        """
        _validate_fraction(volume, "volume", "Sound")
        _validate_effects(effects, "Sound")
        if (
            not isinstance(pan, (int, float))
            or isinstance(pan, bool)
            or not (-1.0 <= pan <= 1.0)
        ):
            raise ValueError(
                f"Sound pan must be between -1.0 (left) and 1.0 (right), not {pan!r}."
            )
        if not isinstance(speed, (int, float)) or isinstance(speed, bool) or speed <= 0:
            raise ValueError(f"Sound speed must be a positive number, not {speed!r}.")
        if visualize is not None and visualize not in ("waveform", "bars"):
            raise ValueError(
                f"Sound visualize must be 'waveform', 'bars', or None,"
                f" not {visualize!r}."
            )
        self.src = src
        self.volume = volume
        self.pan = pan
        self.speed = speed
        self.loop = loop
        self.effects = effects
        self.auto_play = auto_play
        self.controls = controls
        self.visualize = visualize
        self.on_play = on_play
        self.on_finish = on_finish
        self.on_error = on_error
        self.extra_settings = extra_settings

    def get_attributes(self, context) -> dict:
        attributes = super().get_attributes(context)
        if isinstance(attributes.get("effects"), list):
            attributes["effects"] = _serialize_effects(attributes["effects"])
        return attributes


COMPONENT_CONTRACT_REGISTRY.register(Sound.CONTRACT)


@dataclass(repr=False)
class Microphone(Component):
    """Monitors live microphone input and reports how loud the room is.

    This component follows the same permission workflow as
    :class:`~drafter.components.geolocation.CurrentLocation`: it shows an
    "Enable microphone" prompt, and once permission is granted it displays a
    live level meter. It keeps a hidden form field (named ``name``) updated
    with the latest :class:`AudioLevel` snapshot, so a route parameter with
    the same name annotated as :class:`AudioLevel` receives the converted
    value on any form submission.

    The ``on_loud`` event is the easiest way to react to sound: it fires
    when the volume crosses ``threshold`` (a clap, a shout), and then not
    again until ``cooldown`` milliseconds have passed. Volume is measured
    as the peak signal level, so brief sounds like claps register at their
    full loudness.

    Note:
        An ``on_loud``/``on_quiet``/``on_level`` handler that returns a
        full :class:`~drafter.Page` re-renders the whole page, briefly
        resetting this component (it re-enables itself, but the meter and
        ``peak_volume`` restart). For frequent events, prefer returning an
        ``Update`` (change state only) or a ``Fragment`` targeting another
        element.

    Attributes:
        name: The form field name that will contain the AudioLevel data.
        threshold: The loudness (0.0 to 1.0) that counts as "loud".
            Defaults to 0.5.
        cooldown: Minimum milliseconds between on_loud events. Defaults
            to 1000.
        rate: Milliseconds between on_level events, or 0 to never fire
            them. Defaults to 0.
        show: Whether to display the permission UI and meter. Defaults
            to True.
        visualize: The live display once granted: "meter", "waveform",
            or "bars". Defaults to "meter".
        on_loud: Function or URL to call when the volume rises past threshold.
        on_quiet: Function or URL to call when the volume falls back below
            threshold.
        on_level: Function or URL to call every ``rate`` milliseconds with
            the current volume.
        on_denied: Function or URL to call when microphone permission is denied.
        on_error: Function or URL to call when the microphone fails.
    """

    name: str
    threshold: float = 0.5
    cooldown: int = 1000
    rate: int = 0
    show: bool = True
    visualize: str = "meter"
    on_loud: Optional[UrlOrFunction] = None
    on_quiet: Optional[UrlOrFunction] = None
    on_level: Optional[UrlOrFunction] = None
    on_denied: Optional[UrlOrFunction] = None
    on_error: Optional[UrlOrFunction] = None

    tag = "drafter-microphone"

    KNOWN_ATTRS = [
        "name",
        "threshold",
        "cooldown",
        "rate",
        "show",
        "visualize",
    ]
    ARGUMENTS = [
        ComponentArgument("name", "positional"),
        ComponentArgument("threshold", "keyword", 0.5),
        ComponentArgument("cooldown", "keyword", 1000),
        ComponentArgument("rate", "keyword", 0),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("visualize", "keyword", "meter"),
        ComponentArgument("on_loud", "keyword", None, is_event=True),
        ComponentArgument("on_quiet", "keyword", None, is_event=True),
        ComponentArgument("on_level", "keyword", None, is_event=True),
        ComponentArgument("on_denied", "keyword", None, is_event=True),
        ComponentArgument("on_error", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["loud", "quiet", "level", "denied", "error"]

    #: What this component emits: the JS implementation (js/src/components/
    #: microphone.tsx) must match this contract, and the router uses it to
    #: reason about event payload fields.
    CONTRACT = ComponentContract(
        component_name="Microphone",
        html_tag="drafter-microphone",
        emitted_events=[
            EventPayloadSpec(
                event_name="loud",
                fields=[
                    EventPayloadFieldSpec(
                        "volume", float, "The loudness (0.0-1.0) that was heard."
                    ),
                    EventPayloadFieldSpec(
                        "threshold", float, "The configured loudness threshold."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="quiet",
                fields=[
                    EventPayloadFieldSpec(
                        "volume", float, "The loudness (0.0-1.0) that was heard."
                    ),
                    EventPayloadFieldSpec(
                        "threshold", float, "The configured loudness threshold."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="level",
                fields=[
                    EventPayloadFieldSpec(
                        "volume", float, "The current loudness (0.0-1.0)."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "pitch",
                        float,
                        "The dominant frequency in Hz, if one was detected.",
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="denied",
                fields=[
                    EventPayloadFieldSpec(
                        "status", str, "Always denied when permission is rejected."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the denial."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="error",
                fields=[
                    EventPayloadFieldSpec(
                        "status", str, "Failure state: denied, unavailable, or error."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the failure."
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        name: str,
        threshold: float = 0.5,
        cooldown: int = 1000,
        rate: int = 0,
        show: bool = True,
        visualize: str = "meter",
        on_loud: Optional[UrlOrFunction] = None,
        on_quiet: Optional[UrlOrFunction] = None,
        on_level: Optional[UrlOrFunction] = None,
        on_denied: Optional[UrlOrFunction] = None,
        on_error: Optional[UrlOrFunction] = None,
        **extra_settings,
    ):
        """Initialize the Microphone component.

        Args:
            name: The form field name for the AudioLevel data.
            threshold: The loudness (0.0 to 1.0) that counts as "loud".
            cooldown: Minimum milliseconds between on_loud events.
            rate: Milliseconds between on_level events (0 disables them).
            show: Whether to display the permission UI and meter.
            visualize: "meter", "waveform", or "bars".
            on_loud: Function or URL to call when volume rises past threshold.
            on_quiet: Function or URL to call when volume falls below threshold.
            on_level: Function or URL to call on each level report.
            on_denied: Function or URL to call when permission is denied.
            on_error: Function or URL to call when the microphone fails.
            **extra_settings: Additional HTML attributes.
        """
        validate_parameter_name(name, "Microphone")
        _validate_fraction(threshold, "threshold", "Microphone")
        if visualize not in VISUALIZATIONS:
            raise ValueError(
                f"Microphone visualize must be one of"
                f" {', '.join(repr(v) for v in VISUALIZATIONS)},"
                f" not {visualize!r}."
            )
        self.name = name
        self.threshold = threshold
        self.cooldown = cooldown
        self.rate = rate
        self.show = show
        self.visualize = visualize
        self.on_loud = on_loud
        self.on_quiet = on_quiet
        self.on_level = on_level
        self.on_denied = on_denied
        self.on_error = on_error
        self.extra_settings = extra_settings


COMPONENT_CONTRACT_REGISTRY.register(Microphone.CONTRACT)


@dataclass(repr=False)
class AudioRecorder(Component):
    """Records microphone audio and submits it with the form.

    Shows a record button; after asking for microphone permission (shared
    with :class:`Microphone`), it records until stopped or until
    ``max_duration`` milliseconds pass. The completed recording is kept in
    a hidden form field (named ``name``) as a data URL, so a route
    parameter with the same name annotated as :class:`Recording` receives
    the converted value. Play a recording back by passing its ``data_url``
    to :class:`Sound`.

    Attributes:
        name: The form field name that will contain the Recording data.
        max_duration: Maximum recording length in milliseconds. Defaults
            to 30000 (30 seconds).
        show: Whether to display the recorder UI. Defaults to True.
        on_record: Function or URL to call when a recording completes.
        on_denied: Function or URL to call when microphone permission is denied.
        on_error: Function or URL to call when recording fails.
    """

    name: str
    max_duration: int = 30000
    show: bool = True
    on_record: Optional[UrlOrFunction] = None
    on_denied: Optional[UrlOrFunction] = None
    on_error: Optional[UrlOrFunction] = None

    tag = "drafter-audio-recorder"

    KNOWN_ATTRS = [
        "name",
        "max-duration",
        "show",
    ]
    ARGUMENTS = [
        ComponentArgument("name", "positional"),
        ComponentArgument("max_duration", "keyword", 30000),
        ComponentArgument("show", "keyword", True),
        ComponentArgument("on_record", "keyword", None, is_event=True),
        ComponentArgument("on_denied", "keyword", None, is_event=True),
        ComponentArgument("on_error", "keyword", None, is_event=True),
    ]
    EXTRA_SUPPORTED_EVENTS = ["record", "denied", "error"]

    #: What this component emits: the JS implementation (js/src/components/
    #: audioRecorder.tsx) must match this contract, and the router uses it to
    #: reason about event payload fields.
    CONTRACT = ComponentContract(
        component_name="AudioRecorder",
        html_tag="drafter-audio-recorder",
        emitted_events=[
            EventPayloadSpec(
                event_name="record",
                fields=[
                    EventPayloadFieldSpec(
                        "duration", float, "Length of the recording in seconds."
                    ),
                    EventPayloadFieldSpec(
                        "size", int, "Size of the recording in bytes."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="denied",
                fields=[
                    EventPayloadFieldSpec(
                        "status", str, "Always denied when permission is rejected."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the denial."
                    ),
                ],
            ),
            EventPayloadSpec(
                event_name="error",
                fields=[
                    EventPayloadFieldSpec(
                        "status", str, "Failure state: denied, unavailable, or error."
                    ),
                ],
                optional_fields=[
                    EventPayloadFieldSpec(
                        "message", str, "Descriptive message about the failure."
                    ),
                ],
            ),
        ],
    )

    def __init__(
        self,
        name: str,
        max_duration: int = 30000,
        show: bool = True,
        on_record: Optional[UrlOrFunction] = None,
        on_denied: Optional[UrlOrFunction] = None,
        on_error: Optional[UrlOrFunction] = None,
        **extra_settings,
    ):
        """Initialize the AudioRecorder component.

        Args:
            name: The form field name for the Recording data.
            max_duration: Maximum recording length in milliseconds.
            show: Whether to display the recorder UI.
            on_record: Function or URL to call when a recording completes.
            on_denied: Function or URL to call when permission is denied.
            on_error: Function or URL to call when recording fails.
            **extra_settings: Additional HTML attributes.
        """
        validate_parameter_name(name, "AudioRecorder")
        self.name = name
        self.max_duration = max_duration
        self.show = show
        self.on_record = on_record
        self.on_denied = on_denied
        self.on_error = on_error
        self.extra_settings = extra_settings


COMPONENT_CONTRACT_REGISTRY.register(AudioRecorder.CONTRACT)
