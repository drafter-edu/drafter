"""Tests for the Web Audio components (Tone, Melody, Sound, Microphone,
AudioRecorder), their effect values, note parsing, attribute serialization,
and the AudioLevel/Recording converters."""

import json

import pytest

from drafter.components.audio import (
    AudioLevel,
    AudioRecorder,
    Distortion,
    Echo,
    Melody,
    Microphone,
    Muffle,
    Recording,
    Reverb,
    Sharpen,
    Sound,
    Tone,
    note_to_frequency,
)
from drafter.components.utilities.registry import COMPONENT_CONTRACT_REGISTRY
from drafter.data.converter import ConversionContext

# Loading the router conversion module installs the shared converters and is
# how the app guarantees component converters are registered too.
from drafter.router.parameters.conversion import CONVERTER_REGISTRY


def convert(value, expected_type, param_name="value"):
    """Convert one value through the shared registry."""
    return CONVERTER_REGISTRY.convert(
        ConversionContext(
            param_name=param_name,
            expected_type=expected_type,
            raw_value=value,
        )
    )


class TestNoteToFrequency:
    def test_a4_is_concert_pitch(self):
        assert note_to_frequency("A4") == 440.0

    def test_middle_c(self):
        assert note_to_frequency("C4") == pytest.approx(261.6256, abs=0.001)

    def test_sharps_and_flats_are_enharmonic(self):
        assert note_to_frequency("F#3") == note_to_frequency("Gb3")

    def test_case_insensitive_letter(self):
        assert note_to_frequency("c4") == note_to_frequency("C4")

    def test_octave_doubles_frequency(self):
        assert note_to_frequency("A5") == pytest.approx(880.0, abs=0.001)

    @pytest.mark.parametrize(
        "bad_note", ["H4", "C", "#4", "C#", "Cb", "C44", "rest", "", "4C"]
    )
    def test_invalid_notes_raise(self, bad_note):
        with pytest.raises(ValueError):
            note_to_frequency(bad_note)


class TestToneValidation:
    def test_accepts_note_name_and_frequency(self):
        Tone("C4")
        Tone(440)
        Tone(261.63)

    def test_rejects_bad_pitch(self):
        with pytest.raises(ValueError):
            Tone("H9")
        with pytest.raises(ValueError):
            Tone(-10)
        with pytest.raises(ValueError):
            Tone(None)

    def test_rejects_bad_waveform(self):
        with pytest.raises(ValueError):
            Tone("C4", waveform="wobbly")

    def test_rejects_bad_volume(self):
        with pytest.raises(ValueError):
            Tone("C4", volume=1.5)

    def test_rejects_bad_effects(self):
        with pytest.raises(ValueError):
            Tone("C4", effects=Echo())
        with pytest.raises(ValueError):
            Tone("C4", effects=["echo"])
        with pytest.raises(ValueError):
            Tone("C4", effects=[Echo(delay="soon")])


class TestMelodyValidation:
    def test_accepts_notes_beats_and_rests(self):
        Melody(["C4", "E4", "G4"])
        Melody([("C4", 2), ("E4", 0.5), "rest", None])

    def test_rejects_empty_or_non_list(self):
        with pytest.raises(ValueError):
            Melody([])
        with pytest.raises(ValueError):
            Melody("C4 E4 G4")

    def test_rejects_bad_notes(self):
        with pytest.raises(ValueError):
            Melody(["C4", "X2"])
        with pytest.raises(ValueError):
            Melody([("C4", 0)])
        with pytest.raises(ValueError):
            Melody([("C4", 1, 2)])
        with pytest.raises(ValueError):
            Melody([3.5])

    def test_rejects_bad_tempo(self):
        with pytest.raises(ValueError):
            Melody(["C4"], tempo=0)


class TestSoundValidation:
    def test_rejects_bad_pan(self):
        with pytest.raises(ValueError):
            Sound("song.mp3", pan=2.0)

    def test_rejects_bad_speed(self):
        with pytest.raises(ValueError):
            Sound("song.mp3", speed=0)

    def test_rejects_bad_visualize(self):
        with pytest.raises(ValueError):
            Sound("song.mp3", visualize="sparkles")


class TestMicrophoneValidation:
    def test_rejects_bad_name(self):
        with pytest.raises(ValueError):
            Microphone("not a name!")

    def test_rejects_bad_threshold(self):
        with pytest.raises(ValueError):
            Microphone("mic", threshold=2.0)

    def test_rejects_bad_visualize(self):
        with pytest.raises(ValueError):
            Microphone("mic", visualize="sparkles")


class TestAudioRecorderValidation:
    def test_rejects_bad_name(self):
        with pytest.raises(ValueError):
            AudioRecorder("not a name!")


class TestAttributeSerialization:
    def test_tone_renders_pitch_and_handlers(self):
        def tone_done(state):
            pass

        attributes = Tone("C4", on_finish=tone_done).get_attributes(None)
        assert attributes["pitch"] == "C4"
        handlers = json.loads(attributes["data--drafter-handlers"])
        assert handlers == {"finish": "tone_done"}

    def test_tone_effects_serialize_to_json(self):
        attributes = Tone(
            "C4", effects=[Echo(delay=0.2, strength=0.5), Distortion()]
        ).get_attributes(None)
        assert json.loads(attributes["effects"]) == [
            {"type": "echo", "delay": 0.2, "strength": 0.5},
            {"type": "distortion", "amount": 0.3},
        ]

    def test_melody_notes_normalize_to_json_pairs(self):
        attributes = Melody(
            ["C4", ("E4", 2), "rest", None], tempo=90
        ).get_attributes(None)
        assert json.loads(attributes["notes"]) == [
            ["C4", 1],
            ["E4", 2],
            ["rest", 1],
            ["rest", 1],
        ]
        assert attributes["tempo"] == 90

    def test_sound_controls_default_on(self):
        attributes = Sound("song.mp3").get_attributes(None)
        assert attributes["controls"] is True

    def test_sound_controls_can_be_disabled(self):
        attributes = Sound("song.mp3", controls=False).get_attributes(None)
        assert attributes["controls"] is False

    def test_all_effects_have_distinct_types(self):
        effect_types = {
            effect().to_config()["type"]
            for effect in (Echo, Reverb, Muffle, Sharpen, Distortion)
        }
        assert len(effect_types) == 5


class TestContractsRegistered:
    @pytest.mark.parametrize(
        "component_name,html_tag",
        [
            ("Tone", "drafter-tone"),
            ("Melody", "drafter-melody"),
            ("Sound", "drafter-sound"),
            ("Microphone", "drafter-microphone"),
            ("AudioRecorder", "drafter-audio-recorder"),
        ],
    )
    def test_contract_registered(self, component_name, html_tag):
        contract = COMPONENT_CONTRACT_REGISTRY.get(component_name)
        assert contract is not None
        assert contract.html_tag == html_tag


class TestAudioLevelConversion:
    def test_json_string_converts(self):
        payload = json.dumps(
            {
                "status": "granted",
                "message": "Microphone active",
                "volume": 0.25,
                "peak_volume": 0.9,
                "pitch": 440.0,
            }
        )
        result = convert(payload, AudioLevel, param_name="mic")
        assert result.ok
        assert result.value == AudioLevel(
            status="granted",
            message="Microphone active",
            volume=0.25,
            peak_volume=0.9,
            pitch=440.0,
        )

    def test_dict_converts(self):
        result = convert({"status": "denied"}, AudioLevel)
        assert result.ok
        assert result.value.status == "denied"

    def test_malformed_json_becomes_error_status(self):
        result = convert("{not json", AudioLevel)
        assert result.ok
        assert result.value.status == "error"
        assert "Failed to parse" in result.value.message

    def test_unknown_fields_become_error_status(self):
        result = convert(json.dumps({"status": "granted", "extra": 1}), AudioLevel)
        assert result.ok
        assert result.value.status == "error"

    def test_existing_instance_passes_through(self):
        level = AudioLevel(status="granted", volume=0.5)
        result = convert(level, AudioLevel)
        assert result.ok
        assert result.value is level


class TestRecordingConversion:
    def test_json_string_converts(self):
        payload = json.dumps(
            {
                "status": "granted",
                "message": "Recording available",
                "data_url": "data:audio/webm;base64,AAAA",
                "duration": 2.5,
                "size": 1024,
            }
        )
        result = convert(payload, Recording, param_name="voice")
        assert result.ok
        assert result.value.data_url == "data:audio/webm;base64,AAAA"
        assert result.value.duration == 2.5
        assert result.value.size == 1024

    def test_malformed_json_becomes_error_status(self):
        result = convert("{not json", Recording)
        assert result.ok
        assert result.value.status == "error"

    def test_prompt_status_converts(self):
        result = convert(
            json.dumps({"status": "prompt", "message": "Nothing yet"}),
            Recording,
        )
        assert result.ok
        assert result.value.status == "prompt"
        assert result.value.data_url is None
