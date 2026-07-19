import { DrafterHTMLElement } from "./drafterHTMLElement";
import { DRAFTER_PAGE_LOADED_EVENT } from "./events";
import { audioBroker } from "./audioBroker";
import {
	buildEffectsChain,
	parseEffectConfigs,
	parseNumberAttribute,
} from "./audioGraph";

type AudioWithPreservesPitch = HTMLAudioElement & {
	preservesPitch?: boolean;
	webkitPreservesPitch?: boolean;
};

const VISUALIZER_WIDTH = 300;
const VISUALIZER_HEIGHT = 60;

class Sound extends DrafterHTMLElement {
	static get observedAttributes() {
		return [
			"src",
			"volume",
			"pan",
			"speed",
			"loop",
			"effects",
			"auto-play",
			"controls",
			"visualize",
		];
	}

	private audio: HTMLAudioElement | null = null;

	private canvas: HTMLCanvasElement | null = null;

	private enableButton: HTMLButtonElement | null = null;

	private sourceNode: MediaElementAudioSourceNode | null = null;

	private gainNode: GainNode | null = null;

	private panNode: StereoPannerNode | null = null;

	private analyserNode: AnalyserNode | null = null;

	private chainOutput: AudioNode | null = null;

	private animationFrame: number | null = null;

	private waitingForPageLoad = false;

	private unsubscribeUnlock: (() => void) | null = null;

	private handlePageLoaded = (_event: Event): void => {
		if (!this.isConnected || !this.waitingForPageLoad) {
			return;
		}
		this.waitingForPageLoad = false;
		this.autoPlayWhenUnlocked();
	};

	private getSrc(): string {
		return this.getAttribute("src") ?? "";
	}

	private getVolume(): number {
		return parseNumberAttribute(this.getAttribute("volume"), 1, 0, 1);
	}

	private getPan(): number {
		return parseNumberAttribute(this.getAttribute("pan"), 0, -1, 1);
	}

	private getSpeed(): number {
		return parseNumberAttribute(this.getAttribute("speed"), 1, 0.0625, 16);
	}

	private isLoop(): boolean {
		return this.getBooleanAttribute("loop", false);
	}

	private isAutoPlay(): boolean {
		return this.getBooleanAttribute("auto-play", false);
	}

	private hasControls(): boolean {
		return this.getBooleanAttribute("controls", false);
	}

	private getVisualize(): string | null {
		const visualize = this.getAttribute("visualize");
		if (visualize === "waveform" || visualize === "bars") {
			return visualize;
		}
		return null;
	}

	private renderStructure(): void {
		const audio = document.createElement("audio");
		audio.src = this.getSrc();
		audio.controls = this.hasControls();
		audio.addEventListener("play", () => this.handlePlay());
		audio.addEventListener("pause", () => this.stopVisualizing());
		audio.addEventListener("ended", () => this.handleEnded());
		audio.addEventListener("error", () => this.handleError());

		const enableButton = document.createElement("button");
		enableButton.type = "button";
		enableButton.className = "drafter-audio-play-button";
		enableButton.textContent = "🔊 Enable sound";
		enableButton.hidden = true;
		enableButton.addEventListener("click", () => {
			void audioBroker.requestUnlock().then(() => {
				enableButton.hidden = true;
				this.startPlayback();
			});
		});

		const children: Node[] = [audio, enableButton];
		this.canvas = null;
		if (this.getVisualize() !== null) {
			const canvas = document.createElement("canvas");
			canvas.className = "drafter-audio-visualizer";
			canvas.width = VISUALIZER_WIDTH;
			canvas.height = VISUALIZER_HEIGHT;
			this.canvas = canvas;
			children.push(canvas);
		}

		this.audio = audio;
		this.enableButton = enableButton;
		this.replaceChildren(...children);
		this.applyPlaybackSettings();
	}

	private applyPlaybackSettings(): void {
		if (this.audio === null) {
			return;
		}
		const audio = this.audio as AudioWithPreservesPitch;
		audio.loop = this.isLoop();
		audio.playbackRate = this.getSpeed();
		audio.defaultPlaybackRate = this.getSpeed();
		// Let speed changes shift pitch (the classic tape-speed effect),
		// which is what students expect from "speed".
		if ("preservesPitch" in audio) {
			audio.preservesPitch = false;
		}
		if ("webkitPreservesPitch" in audio) {
			audio.webkitPreservesPitch = false;
		}
		if (this.gainNode !== null) {
			this.gainNode.gain.value = this.getVolume();
		} else {
			audio.volume = this.getVolume();
		}
		if (this.panNode !== null) {
			this.panNode.pan.value = this.getPan();
		}
	}

	/**
	 * Route the audio element through the shared Web Audio graph. Without
	 * Web Audio support the element still plays natively (no effects).
	 * A MediaElementSourceNode can only be created once per element, so
	 * the source persists and only the downstream chain is rebuilt.
	 */
	private buildGraph(): void {
		if (this.audio === null || this.sourceNode !== null) {
			return;
		}
		const context = audioBroker.getContext();
		if (context === null) {
			return;
		}
		try {
			this.sourceNode = context.createMediaElementSource(this.audio);
		} catch {
			return;
		}
		this.connectChain(context);
	}

	private connectChain(context: AudioContext): void {
		if (this.sourceNode === null) {
			return;
		}
		if (this.chainOutput !== null) {
			this.chainOutput.disconnect();
		}
		this.sourceNode.disconnect();

		const effects = buildEffectsChain(
			context,
			parseEffectConfigs(this.getAttribute("effects")),
		);
		this.sourceNode.connect(effects.input);
		let tail: AudioNode = effects.output;

		if (typeof context.createStereoPanner === "function") {
			this.panNode = context.createStereoPanner();
			tail.connect(this.panNode);
			tail = this.panNode;
		}

		this.gainNode = context.createGain();
		tail.connect(this.gainNode);
		tail = this.gainNode;

		if (this.getVisualize() !== null) {
			this.analyserNode = context.createAnalyser();
			this.analyserNode.fftSize = 2048;
			tail.connect(this.analyserNode);
			tail = this.analyserNode;
		}

		tail.connect(context.destination);
		this.chainOutput = tail;
		// The audio element's own volume stays at 1; loudness is handled
		// by the gain node once the graph exists.
		this.audio!.volume = 1;
		this.applyPlaybackSettings();
	}

	private handlePlay(): void {
		// Clicking the native play control is a user gesture, so use it to
		// unlock the shared context; otherwise a locked context would
		// swallow the media element's output silently.
		void audioBroker.requestUnlock();
		this.buildGraph();
		this.startVisualizing();
		this.dispatchEvent(
			new CustomEvent("play", { detail: { src: this.getSrc() } }),
		);
	}

	private handleEnded(): void {
		this.stopVisualizing();
		const detail: { src: string; duration?: number } = {
			src: this.getSrc(),
		};
		const duration = this.audio?.duration;
		if (duration !== undefined && Number.isFinite(duration)) {
			detail.duration = duration;
		}
		this.dispatchEvent(new CustomEvent("finish", { detail }));
	}

	private handleError(): void {
		this.stopVisualizing();
		this.dispatchEvent(
			new CustomEvent("error", {
				detail: {
					status: "error",
					message: `Could not play audio: ${this.getSrc()}`,
				},
			}),
		);
	}

	private startPlayback(): void {
		if (this.audio === null) {
			return;
		}
		this.buildGraph();
		this.audio.play()?.catch?.(() => {
			// Autoplay was blocked: reveal the enable-sound prompt so the
			// user can start playback with a gesture.
			if (this.enableButton !== null) {
				this.enableButton.hidden = false;
			}
		});
	}

	private autoPlayWhenUnlocked(): void {
		if (!audioBroker.isSupported()) {
			// No Web Audio at all: try native playback anyway.
			this.startPlayback();
			return;
		}
		if (audioBroker.isUnlocked()) {
			this.startPlayback();
			return;
		}
		if (this.enableButton !== null) {
			this.enableButton.hidden = false;
		}
		this.unsubscribeUnlock = audioBroker.onUnlocked(() => {
			this.unsubscribeUnlock = null;
			if (this.enableButton !== null) {
				this.enableButton.hidden = true;
			}
			this.startPlayback();
		});
	}

	private startVisualizing(): void {
		if (
			this.canvas === null ||
			this.analyserNode === null ||
			this.animationFrame !== null ||
			typeof window.requestAnimationFrame !== "function"
		) {
			return;
		}
		const draw = () => {
			this.animationFrame = window.requestAnimationFrame(draw);
			this.drawVisualization();
		};
		draw();
	}

	private stopVisualizing(): void {
		if (this.animationFrame !== null) {
			window.cancelAnimationFrame(this.animationFrame);
			this.animationFrame = null;
		}
	}

	private drawVisualization(): void {
		if (this.canvas === null || this.analyserNode === null) {
			return;
		}
		const context2d = this.canvas.getContext("2d");
		if (context2d === null) {
			return;
		}
		const width = this.canvas.width;
		const height = this.canvas.height;
		context2d.clearRect(0, 0, width, height);
		context2d.fillStyle = "#3e3e9e";

		if (this.getVisualize() === "bars") {
			const data = new Uint8Array(this.analyserNode.frequencyBinCount);
			this.analyserNode.getByteFrequencyData(data);
			const barCount = 48;
			const step = Math.floor(data.length / barCount) || 1;
			const barWidth = width / barCount;
			for (let i = 0; i < barCount; i += 1) {
				const value = data[i * step] / 255;
				const barHeight = value * height;
				context2d.fillRect(
					i * barWidth,
					height - barHeight,
					barWidth * 0.8,
					barHeight,
				);
			}
		} else {
			const data = new Uint8Array(this.analyserNode.fftSize);
			this.analyserNode.getByteTimeDomainData(data);
			context2d.strokeStyle = "#3e3e9e";
			context2d.lineWidth = 2;
			context2d.beginPath();
			for (let i = 0; i < data.length; i += 1) {
				const x = (i / data.length) * width;
				const y = (data[i] / 255) * height;
				if (i === 0) {
					context2d.moveTo(x, y);
				} else {
					context2d.lineTo(x, y);
				}
			}
			context2d.stroke();
		}
	}

	connectedCallback() {
		this.renderStructure();
		window.addEventListener(DRAFTER_PAGE_LOADED_EVENT, this.handlePageLoaded);
		if (this.isAutoPlay()) {
			this.waitingForPageLoad = true;
		}
	}

	attributeChangedCallback(
		name: string,
		oldValue: string | null,
		newValue: string | null,
	) {
		if (oldValue === newValue || !this.isConnected) {
			return;
		}
		if (name === "src" && this.audio !== null) {
			this.audio.src = newValue ?? "";
			return;
		}
		if (name === "controls" && this.audio !== null) {
			this.audio.controls = this.hasControls();
			return;
		}
		if (name === "effects") {
			const context = audioBroker.getContext();
			if (context !== null && this.sourceNode !== null) {
				this.connectChain(context);
			}
			return;
		}
		this.applyPlaybackSettings();
	}

	disconnectedCallback() {
		window.removeEventListener(
			DRAFTER_PAGE_LOADED_EVENT,
			this.handlePageLoaded,
		);
		this.stopVisualizing();
		if (this.unsubscribeUnlock !== null) {
			this.unsubscribeUnlock();
			this.unsubscribeUnlock = null;
		}
		if (this.audio !== null) {
			this.audio.pause();
		}
		if (this.chainOutput !== null) {
			this.chainOutput.disconnect();
			this.chainOutput = null;
		}
		if (this.sourceNode !== null) {
			this.sourceNode.disconnect();
			this.sourceNode = null;
		}
		this.waitingForPageLoad = false;
		this.audio = null;
		this.canvas = null;
		this.enableButton = null;
		this.gainNode = null;
		this.panNode = null;
		this.analyserNode = null;
	}
}

customElements.define("drafter-sound", Sound);
