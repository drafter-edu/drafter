import { describe, expect, jest, test } from "@jest/globals";

import {
	buildEffectsChain,
	noteToFrequency,
	parseEffectConfigs,
	parseMelodyNotes,
	pitchToFrequency,
} from "../components/audioGraph";

// ---------------------------------------------------------------------------
// Fake BaseAudioContext (jsdom has no Web Audio). Every node records what it
// connects to so the wiring of each effect chain can be asserted.
// ---------------------------------------------------------------------------

type FakeParam = { value: number };

class FakeNode {
	targets: FakeNode[] = [];

	connect = jest.fn((target: FakeNode) => {
		this.targets.push(target);
		return target;
	});

	disconnect = jest.fn();
}

class FakeGainNode extends FakeNode {
	gain: FakeParam = { value: 1 };
}

class FakeDelayNode extends FakeNode {
	delayTime: FakeParam = { value: 0 };

	constructor(public maxDelay: number) {
		super();
	}
}

class FakeBiquadFilterNode extends FakeNode {
	type = "";

	frequency: FakeParam = { value: 0 };
}

class FakeConvolverNode extends FakeNode {
	buffer: FakeAudioBuffer | null = null;
}

class FakeWaveShaperNode extends FakeNode {
	curve: Float32Array | null = null;

	oversample = "none";
}

class FakeAudioBuffer {
	private channels: Float32Array[];

	constructor(
		public numberOfChannels: number,
		public length: number,
		public sampleRate: number,
	) {
		this.channels = Array.from(
			{ length: numberOfChannels },
			() => new Float32Array(length),
		);
	}

	getChannelData(channel: number): Float32Array {
		return this.channels[channel];
	}
}

class FakeBaseAudioContext {
	// Small sample rate keeps generated reverb impulses tiny and fast.
	sampleRate = 8000;

	gains: FakeGainNode[] = [];

	delays: FakeDelayNode[] = [];

	filters: FakeBiquadFilterNode[] = [];

	convolvers: FakeConvolverNode[] = [];

	shapers: FakeWaveShaperNode[] = [];

	createGain(): FakeGainNode {
		const node = new FakeGainNode();
		this.gains.push(node);
		return node;
	}

	createDelay(maxDelay: number): FakeDelayNode {
		const node = new FakeDelayNode(maxDelay);
		this.delays.push(node);
		return node;
	}

	createBiquadFilter(): FakeBiquadFilterNode {
		const node = new FakeBiquadFilterNode();
		this.filters.push(node);
		return node;
	}

	createConvolver(): FakeConvolverNode {
		const node = new FakeConvolverNode();
		this.convolvers.push(node);
		return node;
	}

	createWaveShaper(): FakeWaveShaperNode {
		const node = new FakeWaveShaperNode();
		this.shapers.push(node);
		return node;
	}

	createBuffer(
		channels: number,
		length: number,
		sampleRate: number,
	): FakeAudioBuffer {
		return new FakeAudioBuffer(channels, length, sampleRate);
	}
}

function makeContext(): {
	context: BaseAudioContext;
	fake: FakeBaseAudioContext;
} {
	const fake = new FakeBaseAudioContext();
	return { context: fake as unknown as BaseAudioContext, fake };
}

describe("buildEffectsChain", () => {
	test("no effects: input and output are one passthrough gain", () => {
		const { context, fake } = makeContext();
		const chain = buildEffectsChain(context, []);
		expect(chain.input).toBe(chain.output);
		expect(fake.gains).toHaveLength(1);
		expect(chain.input).toBe(fake.gains[0] as unknown as AudioNode);
	});

	test("unknown effect types are skipped entirely", () => {
		const { context, fake } = makeContext();
		const chain = buildEffectsChain(context, [
			{ type: "chorus" },
			{ type: "" },
		]);
		expect(chain.input).toBe(chain.output);
		expect(fake.gains).toHaveLength(1);
		expect(fake.gains[0].connect).not.toHaveBeenCalled();
	});

	test("echo: wires input -> {dry, delay -> feedback loop} -> output", () => {
		const { context, fake } = makeContext();
		const chain = buildEffectsChain(context, [
			{ type: "echo", delay: 0.25, strength: 0.6 },
		]);

		// Nodes created in order: passthrough, echo input, echo output.
		const [passthrough, input, output] = fake.gains.slice(0, 3);
		const feedback = fake.gains[3];
		const delay = fake.delays[0];

		expect(chain.input).toBe(passthrough as unknown as AudioNode);
		expect(chain.output).toBe(output as unknown as AudioNode);
		expect(passthrough.targets).toEqual([input]);

		expect(delay.maxDelay).toBe(10);
		expect(delay.delayTime.value).toBeCloseTo(0.25, 6);
		expect(feedback.gain.value).toBeCloseTo(0.6, 6);

		expect(input.targets).toEqual([output, delay]);
		expect(delay.targets).toEqual([feedback, output]);
		expect(feedback.targets).toEqual([delay]);
	});

	test("echo clamps delay to [0.01, 10] and strength to [0, 0.95]", () => {
		const { fake, context } = makeContext();
		buildEffectsChain(context, [{ type: "echo", delay: 99, strength: 2 }]);
		buildEffectsChain(context, [{ type: "echo", delay: 0, strength: -1 }]);
		expect(fake.delays[0].delayTime.value).toBe(10);
		expect(fake.gains[3].gain.value).toBe(0.95);
		expect(fake.delays[1].delayTime.value).toBe(0.01);
		expect(fake.gains[7].gain.value).toBe(0);
	});

	test("echo defaults: delay 0.3, strength 0.4 for missing or junk values", () => {
		const { fake, context } = makeContext();
		buildEffectsChain(context, [
			{ type: "echo", delay: "soon", strength: null },
		]);
		expect(fake.delays[0].delayTime.value).toBeCloseTo(0.3, 6);
		expect(fake.gains[3].gain.value).toBeCloseTo(0.4, 6);
	});

	test("reverb: convolver gets a generated stereo impulse, dry/wet mix follows amount", () => {
		const { context, fake } = makeContext();
		const chain = buildEffectsChain(context, [
			{ type: "reverb", amount: 0.5 },
		]);

		const [passthrough, input, output, dry, wet] = fake.gains;
		const convolver = fake.convolvers[0];

		expect(chain.input).toBe(passthrough as unknown as AudioNode);
		expect(chain.output).toBe(output as unknown as AudioNode);
		expect(passthrough.targets).toEqual([input]);
		expect(input.targets).toEqual([dry, convolver]);
		expect(dry.targets).toEqual([output]);
		expect(convolver.targets).toEqual([wet]);
		expect(wet.targets).toEqual([output]);

		expect(dry.gain.value).toBeCloseTo(0.75, 6);
		expect(wet.gain.value).toBeCloseTo(0.5, 6);

		const buffer = convolver.buffer as FakeAudioBuffer;
		expect(buffer).not.toBeNull();
		expect(buffer.numberOfChannels).toBe(2);
		// 0.3 + 0.5 * 2.7 seconds at the fake sample rate.
		expect(buffer.length).toBe(Math.floor(1.65 * fake.sampleRate));
		// The impulse is a decaying noise burst: early samples carry energy,
		// everything stays within [-1, 1], and the tail decays to zero.
		const data = buffer.getChannelData(0);
		const head = Array.from(data.slice(0, 32));
		expect(head.some((sample) => sample !== 0)).toBe(true);
		expect(
			Array.from(data).every((sample) => sample >= -1 && sample <= 1),
		).toBe(true);
		expect(Math.abs(data[data.length - 1])).toBeLessThan(1e-6);
	});

	test("reverb clamps amount to [0, 1]", () => {
		const { context, fake } = makeContext();
		buildEffectsChain(context, [{ type: "reverb", amount: 5 }]);
		const wet = fake.gains[4];
		const dry = fake.gains[3];
		expect(wet.gain.value).toBe(1);
		expect(dry.gain.value).toBeCloseTo(0.5, 6);
		expect((fake.convolvers[0].buffer as FakeAudioBuffer).length).toBe(
			Math.floor(3 * fake.sampleRate),
		);
	});

	test("muffle is a lowpass filter swept from 18 kHz down to 250 Hz", () => {
		const { context, fake } = makeContext();
		buildEffectsChain(context, [{ type: "muffle", amount: 0 }]);
		buildEffectsChain(context, [{ type: "muffle", amount: 1 }]);
		buildEffectsChain(context, [{ type: "muffle", amount: 0.5 }]);
		expect(fake.filters[0].type).toBe("lowpass");
		expect(fake.filters[0].frequency.value).toBeCloseTo(18000, 3);
		expect(fake.filters[1].frequency.value).toBeCloseTo(250, 3);
		expect(fake.filters[2].frequency.value).toBeCloseTo(
			18000 * (250 / 18000) ** 0.5,
			3,
		);
	});

	test("sharpen is a highpass filter swept from 20 Hz up to 3 kHz", () => {
		const { context, fake } = makeContext();
		buildEffectsChain(context, [{ type: "sharpen", amount: 0 }]);
		buildEffectsChain(context, [{ type: "sharpen", amount: 1 }]);
		expect(fake.filters[0].type).toBe("highpass");
		expect(fake.filters[0].frequency.value).toBeCloseTo(20, 3);
		expect(fake.filters[1].frequency.value).toBeCloseTo(3000, 3);
	});

	test("filter effects use the filter itself as both input and output", () => {
		const { context, fake } = makeContext();
		const chain = buildEffectsChain(context, [{ type: "muffle" }]);
		const filter = fake.filters[0];
		expect(fake.gains[0].targets).toEqual([filter]);
		expect(chain.output).toBe(filter as unknown as AudioNode);
	});

	test("distortion: 256-sample curve, 4x oversampling, clamped amount", () => {
		const { context, fake } = makeContext();
		const chain = buildEffectsChain(context, [
			{ type: "distortion", amount: 0 },
		]);
		const shaper = fake.shapers[0];
		expect(chain.output).toBe(shaper as unknown as AudioNode);
		expect(shaper.oversample).toBe("4x");
		const curve = shaper.curve as Float32Array;
		expect(curve).toHaveLength(256);
		// With amount 0 (k = 0) the curve is linear: 3 * x * 20 * (pi/180) / pi
		// which is x / 3; at i = 0, x = -1.
		expect(curve[0]).toBeCloseTo(-1 / 3, 5);
		expect(curve[128]).toBeCloseTo(0, 5);
		expect(Array.from(curve).every((y) => Number.isFinite(y))).toBe(true);

		buildEffectsChain(context, [{ type: "distortion", amount: 42 }]);
		const clamped = fake.shapers[1].curve as Float32Array;
		// amount clamps to 1 (k = 100): identical to an explicit amount of 1.
		buildEffectsChain(context, [{ type: "distortion", amount: 1 }]);
		const explicit = fake.shapers[2].curve as Float32Array;
		expect(Array.from(clamped)).toEqual(Array.from(explicit));
	});

	test("multiple effects chain in order: passthrough -> echo -> muffle", () => {
		const { context, fake } = makeContext();
		const chain = buildEffectsChain(context, [
			{ type: "echo" },
			{ type: "muffle" },
		]);
		const passthrough = fake.gains[0];
		const echoInput = fake.gains[1];
		const echoOutput = fake.gains[2];
		const filter = fake.filters[0];

		expect(chain.input).toBe(passthrough as unknown as AudioNode);
		expect(passthrough.targets).toEqual([echoInput]);
		expect(echoOutput.targets).toContain(filter);
		expect(chain.output).toBe(filter as unknown as AudioNode);
	});

	test("invalid entries between valid effects do not break the chain", () => {
		const { context, fake } = makeContext();
		const chain = buildEffectsChain(context, [
			{ type: "mystery" },
			{ type: "sharpen", amount: 1 },
			{ type: "wat" },
		]);
		expect(chain.output).toBe(fake.filters[0] as unknown as AudioNode);
	});
});

// ---------------------------------------------------------------------------
// Pure parsing helpers: complements audio.test.ts, which covers the basics
// (equal temperament, invalid names, pair parsing, clamping). Only gaps here.
// ---------------------------------------------------------------------------

describe("audioGraph parsing complements", () => {
	test("noteToFrequency understands flats and unicode accidentals", () => {
		expect(noteToFrequency("Bb3")).toBeCloseTo(
			noteToFrequency("A#3") as number,
			6,
		);
		expect(noteToFrequency("C♯4")).toBeCloseTo(
			noteToFrequency("C#4") as number,
			6,
		);
		expect(noteToFrequency("D♭4")).toBeCloseTo(
			noteToFrequency("C#4") as number,
			6,
		);
		// A bare "b" with nothing after cannot be a flat marker.
		expect(noteToFrequency("Bb")).toBeNull();
	});

	test("noteToFrequency trims surrounding whitespace", () => {
		expect(noteToFrequency("  A4  ")).toBeCloseTo(440, 3);
	});

	test("pitchToFrequency rejects zero and non-finite numbers", () => {
		expect(pitchToFrequency("0")).toBeNull();
		expect(pitchToFrequency("Infinity")).toBeNull();
		expect(pitchToFrequency("NaN")).toBeNull();
	});

	test("parseMelodyNotes accepts bare note strings with one beat", () => {
		const notes = parseMelodyNotes(JSON.stringify(["C4", "rest", 17]));
		expect(notes).toHaveLength(2);
		expect(notes[0]).toMatchObject({ note: "C4", beats: 1 });
		expect(notes[1]).toMatchObject({ note: "rest", frequency: 0 });
	});

	test("parseMelodyNotes rejects non-array JSON and wrong-length pairs", () => {
		expect(parseMelodyNotes('{"note": "C4"}')).toEqual([]);
		expect(parseMelodyNotes(JSON.stringify([["C4", 1, "extra"]]))).toEqual(
			[],
		);
	});

	test("parseEffectConfigs handles null and non-array JSON", () => {
		expect(parseEffectConfigs(null)).toEqual([]);
		expect(parseEffectConfigs("   ")).toEqual([]);
		expect(parseEffectConfigs('{"type": "echo"}')).toEqual([]);
	});
});
