/**
 * Web Audio helpers shared by the audio components: note-name parsing and
 * building effect chains from the JSON configuration emitted by the Python
 * side (see src/drafter/components/audio.py, which validates the same
 * grammar and effect types).
 */

export const REST_NOTE = "rest";

const NOTE_SEMITONES: Record<string, number> = {
	C: 0,
	D: 2,
	E: 4,
	F: 5,
	G: 7,
	A: 9,
	B: 11,
};

/**
 * Convert a note name like "C4", "F#3", or "Bb2" to a frequency in Hz
 * (equal temperament, A4 = 440). Returns null for invalid names.
 */
export function noteToFrequency(note: string): number | null {
	const trimmed = note.trim();
	if (trimmed.length < 2) {
		return null;
	}
	const letter = trimmed[0].toUpperCase();
	const semitone = NOTE_SEMITONES[letter];
	if (semitone === undefined) {
		return null;
	}
	let rest = trimmed.slice(1);
	let accidental = 0;
	if (rest[0] === "#" || rest[0] === "♯") {
		accidental = 1;
		rest = rest.slice(1);
	} else if ((rest[0] === "b" || rest[0] === "♭") && rest.length > 1) {
		accidental = -1;
		rest = rest.slice(1);
	}
	if (rest.length !== 1 || rest < "0" || rest > "9") {
		return null;
	}
	const octave = Number(rest);
	const midi = (octave + 1) * 12 + semitone + accidental;
	return 440 * 2 ** ((midi - 69) / 12);
}

/**
 * Resolve a pitch attribute (note name or raw frequency string) to Hz.
 * Returns null if it cannot be understood.
 */
export function pitchToFrequency(pitch: string): number | null {
	const asNumber = Number(pitch);
	if (Number.isFinite(asNumber) && asNumber > 0) {
		return asNumber;
	}
	return noteToFrequency(pitch);
}

export type MelodyNote = {
	note: string;
	beats: number;
	frequency: number;
};

/**
 * Parse the JSON "notes" attribute of a Melody: a list of [note, beats]
 * pairs. Unparseable entries are skipped rather than crashing.
 */
export function parseMelodyNotes(raw: string | null): MelodyNote[] {
	if (raw === null || raw.trim() === "") {
		return [];
	}
	let parsed: unknown;
	try {
		parsed = JSON.parse(raw);
	} catch {
		return [];
	}
	if (!Array.isArray(parsed)) {
		return [];
	}
	const notes: MelodyNote[] = [];
	for (const item of parsed) {
		let note: unknown = item;
		let beats = 1;
		if (Array.isArray(item)) {
			if (item.length !== 2) {
				continue;
			}
			[note, beats] = item as [unknown, number];
		}
		if (typeof note !== "string") {
			continue;
		}
		if (typeof beats !== "number" || !Number.isFinite(beats) || beats <= 0) {
			beats = 1;
		}
		const normalized = note.trim().toLowerCase();
		if (normalized === REST_NOTE) {
			notes.push({ note: REST_NOTE, beats, frequency: 0 });
			continue;
		}
		const frequency = noteToFrequency(note);
		if (frequency === null) {
			continue;
		}
		notes.push({ note, beats, frequency });
	}
	return notes;
}

/**
 * Parse a numeric attribute value (which, unlike
 * DrafterHTMLElement.getNumberAttribute, may be fractional), clamped to
 * [min, max]. Returns the default when missing or unparseable.
 */
export function parseNumberAttribute(
	raw: string | null,
	defaultValue: number,
	min: number,
	max: number,
): number {
	if (raw === null || raw.trim() === "") {
		return defaultValue;
	}
	const parsed = Number(raw);
	if (!Number.isFinite(parsed)) {
		return defaultValue;
	}
	return Math.min(max, Math.max(min, parsed));
}

export type EffectConfig = {
	type: string;
	[key: string]: unknown;
};

export type EffectChain = {
	input: AudioNode;
	output: AudioNode;
};

function clamp(value: number, low: number, high: number): number {
	return Math.min(high, Math.max(low, value));
}

function readAmount(
	config: EffectConfig,
	key: string,
	defaultValue: number,
): number {
	const value = config[key];
	if (typeof value !== "number" || !Number.isFinite(value)) {
		return defaultValue;
	}
	return value;
}

/** Parse the JSON "effects" attribute into effect configurations. */
export function parseEffectConfigs(raw: string | null): EffectConfig[] {
	if (raw === null || raw.trim() === "") {
		return [];
	}
	let parsed: unknown;
	try {
		parsed = JSON.parse(raw);
	} catch {
		return [];
	}
	if (!Array.isArray(parsed)) {
		return [];
	}
	return parsed.filter(
		(item): item is EffectConfig =>
			typeof item === "object" &&
			item !== null &&
			typeof (item as EffectConfig).type === "string",
	);
}

function buildEcho(context: BaseAudioContext, config: EffectConfig): EffectChain {
	const input = context.createGain();
	const output = context.createGain();
	const delay = context.createDelay(10);
	delay.delayTime.value = clamp(readAmount(config, "delay", 0.3), 0.01, 10);
	const feedback = context.createGain();
	feedback.gain.value = clamp(readAmount(config, "strength", 0.4), 0, 0.95);
	input.connect(output);
	input.connect(delay);
	delay.connect(feedback);
	feedback.connect(delay);
	delay.connect(output);
	return { input, output };
}

function buildReverbImpulse(
	context: BaseAudioContext,
	amount: number,
): AudioBuffer {
	// A generated noise burst with exponential decay stands in for a room
	// impulse response; larger amounts decay more slowly (bigger room).
	const seconds = 0.3 + amount * 2.7;
	const sampleRate = context.sampleRate;
	const length = Math.max(1, Math.floor(seconds * sampleRate));
	const impulse = context.createBuffer(2, length, sampleRate);
	for (let channel = 0; channel < impulse.numberOfChannels; channel += 1) {
		const data = impulse.getChannelData(channel);
		for (let i = 0; i < length; i += 1) {
			const decay = (1 - i / length) ** (2 + (1 - amount) * 4);
			data[i] = (Math.random() * 2 - 1) * decay;
		}
	}
	return impulse;
}

function buildReverb(
	context: BaseAudioContext,
	config: EffectConfig,
): EffectChain {
	const amount = clamp(readAmount(config, "amount", 0.5), 0, 1);
	const input = context.createGain();
	const output = context.createGain();
	const convolver = context.createConvolver();
	convolver.buffer = buildReverbImpulse(context, amount);
	const dry = context.createGain();
	dry.gain.value = 1 - amount * 0.5;
	const wet = context.createGain();
	wet.gain.value = amount;
	input.connect(dry);
	dry.connect(output);
	input.connect(convolver);
	convolver.connect(wet);
	wet.connect(output);
	return { input, output };
}

function buildFilter(
	context: BaseAudioContext,
	config: EffectConfig,
	kind: "lowpass" | "highpass",
): EffectChain {
	const amount = clamp(readAmount(config, "amount", 0.5), 0, 1);
	const filter = context.createBiquadFilter();
	filter.type = kind;
	if (kind === "lowpass") {
		// amount 0 -> 18 kHz (unchanged), amount 1 -> ~250 Hz (very muffled)
		filter.frequency.value = 18000 * (250 / 18000) ** amount;
	} else {
		// amount 0 -> 20 Hz (unchanged), amount 1 -> ~3 kHz (very tinny)
		filter.frequency.value = 20 * (3000 / 20) ** amount;
	}
	return { input: filter, output: filter };
}

function buildDistortion(
	context: BaseAudioContext,
	config: EffectConfig,
): EffectChain {
	const amount = clamp(readAmount(config, "amount", 0.3), 0, 1);
	const shaper = context.createWaveShaper();
	const k = amount * 100;
	const samples = 256;
	const curve = new Float32Array(samples);
	for (let i = 0; i < samples; i += 1) {
		const x = (i * 2) / samples - 1;
		curve[i] = ((3 + k) * x * 20 * (Math.PI / 180)) / (Math.PI + k * Math.abs(x));
	}
	shaper.curve = curve;
	shaper.oversample = "4x";
	return { input: shaper, output: shaper };
}

/**
 * Build a linear chain of effects. Returns input/output nodes to splice
 * into an audio graph; with no (valid) effects, input === output.
 */
export function buildEffectsChain(
	context: BaseAudioContext,
	configs: EffectConfig[],
): EffectChain {
	const passthrough = context.createGain();
	let input: AudioNode = passthrough;
	let output: AudioNode = passthrough;
	for (const config of configs) {
		let stage: EffectChain | null = null;
		if (config.type === "echo") {
			stage = buildEcho(context, config);
		} else if (config.type === "reverb") {
			stage = buildReverb(context, config);
		} else if (config.type === "muffle") {
			stage = buildFilter(context, config, "lowpass");
		} else if (config.type === "sharpen") {
			stage = buildFilter(context, config, "highpass");
		} else if (config.type === "distortion") {
			stage = buildDistortion(context, config);
		}
		if (stage === null) {
			continue;
		}
		output.connect(stage.input);
		output = stage.output;
	}
	return { input, output };
}
