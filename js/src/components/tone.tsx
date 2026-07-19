import { DrafterHTMLElement } from "./drafterHTMLElement";
import { DRAFTER_PAGE_LOADED_EVENT } from "./events";
import { audioBroker, AUDIO_UNSUPPORTED_ERROR } from "./audioBroker";
import {
	buildEffectsChain,
	noteToFrequency,
	parseEffectConfigs,
	parseNumberAttribute,
	pitchToFrequency,
} from "./audioGraph";

type ToneDetail = {
	frequency: number;
	duration: number;
	waveform: string;
	note?: string;
};

const WAVEFORMS = ["sine", "square", "triangle", "sawtooth"];

class Tone extends DrafterHTMLElement {
	static get observedAttributes() {
		return [
			"pitch",
			"duration",
			"waveform",
			"volume",
			"attack",
			"release",
			"auto-play",
			"show",
			"effects",
		];
	}

	private button: HTMLButtonElement | null = null;

	private statusArea: HTMLSpanElement | null = null;

	private playing = false;

	private waitingForPageLoad = false;

	private unsubscribeUnlock: (() => void) | null = null;

	private handlePageLoaded = (_event: Event): void => {
		if (!this.isConnected || !this.waitingForPageLoad) {
			return;
		}
		this.waitingForPageLoad = false;
		this.autoPlayWhenUnlocked();
	};

	private getFrequency(): number | null {
		const pitch = this.getAttribute("pitch");
		if (pitch === null) {
			return null;
		}
		return pitchToFrequency(pitch);
	}

	private getNoteName(): string | undefined {
		const pitch = this.getAttribute("pitch") ?? "";
		return noteToFrequency(pitch) !== null ? pitch : undefined;
	}

	private getDuration(): number {
		return parseNumberAttribute(this.getAttribute("duration"), 500, 1, 600000);
	}

	private getWaveform(): OscillatorType {
		const waveform = (this.getAttribute("waveform") ?? "sine").toLowerCase();
		return (
			WAVEFORMS.includes(waveform) ? waveform : "sine"
		) as OscillatorType;
	}

	private getVolume(): number {
		return parseNumberAttribute(this.getAttribute("volume"), 0.8, 0, 1);
	}

	private getAttack(): number {
		return parseNumberAttribute(this.getAttribute("attack"), 10, 0, 10000);
	}

	private getRelease(): number {
		return parseNumberAttribute(this.getAttribute("release"), 50, 0, 10000);
	}

	private isAutoPlay(): boolean {
		return this.getBooleanAttribute("auto-play", false);
	}

	private shouldShow(): boolean {
		return this.getBooleanAttribute("show", true);
	}

	private syncVisibility(): void {
		this.hidden = !this.shouldShow();
	}

	private buttonLabel(): string {
		const note = this.getNoteName();
		return note !== undefined ? `▶ ${note}` : "▶";
	}

	private renderStructure(): void {
		const button = document.createElement("button");
		button.type = "button";
		button.className = "drafter-audio-play-button";
		button.textContent = this.buttonLabel();
		button.addEventListener("click", () => {
			void audioBroker.requestUnlock().then(() => this.play());
		});

		const statusArea = document.createElement("span");
		statusArea.className = "drafter-audio-status";

		this.button = button;
		this.statusArea = statusArea;
		this.replaceChildren(button, statusArea);
		button.hidden = this.isAutoPlay();
		this.syncVisibility();
	}

	private setStatus(message: string): void {
		if (this.statusArea !== null) {
			this.statusArea.textContent = message;
		}
	}

	private emitError(status: string, message: string): void {
		this.setStatus(message);
		this.dispatchEvent(
			new CustomEvent("error", { detail: { status, message } }),
		);
	}

	private buildDetail(frequency: number): ToneDetail {
		const detail: ToneDetail = {
			frequency,
			duration: this.getDuration(),
			waveform: this.getWaveform(),
		};
		const note = this.getNoteName();
		if (note !== undefined) {
			detail.note = note;
		}
		return detail;
	}

	private play(): void {
		if (this.playing || !this.isConnected) {
			return;
		}
		const context = audioBroker.getContext();
		if (context === null) {
			this.emitError("unavailable", AUDIO_UNSUPPORTED_ERROR);
			return;
		}
		const frequency = this.getFrequency();
		if (frequency === null) {
			this.emitError(
				"error",
				`Could not understand the pitch: ${this.getAttribute("pitch")}`,
			);
			return;
		}

		const durationSeconds = this.getDuration() / 1000;
		const attackSeconds = Math.min(this.getAttack() / 1000, durationSeconds);
		const releaseSeconds = Math.min(
			this.getRelease() / 1000,
			durationSeconds - attackSeconds,
		);
		const now = context.currentTime;

		const oscillator = context.createOscillator();
		oscillator.type = this.getWaveform();
		oscillator.frequency.value = frequency;

		const envelope = context.createGain();
		envelope.gain.setValueAtTime(0, now);
		envelope.gain.linearRampToValueAtTime(
			this.getVolume(),
			now + attackSeconds,
		);
		envelope.gain.setValueAtTime(
			this.getVolume(),
			now + durationSeconds - releaseSeconds,
		);
		envelope.gain.linearRampToValueAtTime(0.0001, now + durationSeconds);

		const effects = buildEffectsChain(
			context,
			parseEffectConfigs(this.getAttribute("effects")),
		);
		oscillator.connect(envelope);
		envelope.connect(effects.input);
		effects.output.connect(context.destination);

		const detail = this.buildDetail(frequency);
		this.playing = true;
		if (this.button !== null) {
			this.button.disabled = true;
		}
		this.setStatus("♪");
		this.dispatchEvent(new CustomEvent("start", { detail: { ...detail } }));

		oscillator.onended = () => {
			this.playing = false;
			effects.output.disconnect();
			if (this.button !== null) {
				this.button.disabled = false;
			}
			this.setStatus("");
			this.dispatchEvent(
				new CustomEvent("finish", { detail: { ...detail } }),
			);
		};
		oscillator.start(now);
		oscillator.stop(now + durationSeconds);
	}

	private autoPlayWhenUnlocked(): void {
		if (!audioBroker.isSupported()) {
			this.emitError("unavailable", AUDIO_UNSUPPORTED_ERROR);
			return;
		}
		if (audioBroker.isUnlocked()) {
			this.play();
			return;
		}
		// The context is still locked: any interaction with the page (or
		// this prompt button) will unlock it and start the tone.
		if (this.button !== null) {
			this.button.hidden = false;
			this.button.textContent = "🔊 Enable sound";
		}
		this.unsubscribeUnlock = audioBroker.onUnlocked(() => {
			this.unsubscribeUnlock = null;
			if (this.button !== null) {
				this.button.hidden = true;
			}
			this.play();
		});
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
		if (name === "show") {
			this.syncVisibility();
			return;
		}
		if (this.button !== null && !this.playing) {
			this.button.textContent = this.buttonLabel();
		}
	}

	disconnectedCallback() {
		window.removeEventListener(
			DRAFTER_PAGE_LOADED_EVENT,
			this.handlePageLoaded,
		);
		if (this.unsubscribeUnlock !== null) {
			this.unsubscribeUnlock();
			this.unsubscribeUnlock = null;
		}
		this.waitingForPageLoad = false;
		this.button = null;
		this.statusArea = null;
	}
}

customElements.define("drafter-tone", Tone);
