import { DrafterHTMLElement } from "./drafterHTMLElement";
import { DRAFTER_PAGE_LOADED_EVENT } from "./events";
import { audioBroker, AUDIO_UNSUPPORTED_ERROR } from "./audioBroker";
import {
	buildEffectsChain,
	parseEffectConfigs,
	parseMelodyNotes,
	parseNumberAttribute,
	type MelodyNote,
} from "./audioGraph";

type MelodyState =
	| "idle"
	| "locked"
	| "playing"
	| "paused"
	| "finished"
	| "unavailable";

type ScheduledNote = MelodyNote & {
	startSeconds: number;
	endSeconds: number;
	index: number;
};

const WAVEFORMS = ["sine", "square", "triangle", "sawtooth"];

//: Fraction of each beat that actually sounds, leaving a small gap that
//: keeps repeated notes distinct.
const ARTICULATION = 0.9;
const NOTE_ATTACK_SECONDS = 0.008;
const NOTE_RELEASE_SECONDS = 0.02;

class Melody extends DrafterHTMLElement {
	static get observedAttributes() {
		return [
			"notes",
			"tempo",
			"waveform",
			"volume",
			"auto-play",
			"controls",
			"show",
			"effects",
		];
	}

	private state: MelodyState = "idle";

	private label: HTMLSpanElement | null = null;

	private primaryButton: HTMLButtonElement | null = null;

	private restartButton: HTMLButtonElement | null = null;

	private activeNodes: Array<{ stop: () => void }> = [];

	private timeouts: number[] = [];

	private outputNode: AudioNode | null = null;

	private startedAtContextTime = 0;

	private offsetSeconds = 0;

	private waitingForPageLoad = false;

	private unsubscribeUnlock: (() => void) | null = null;

	private handlePageLoaded = (_event: Event): void => {
		if (!this.isConnected || !this.waitingForPageLoad) {
			return;
		}
		this.waitingForPageLoad = false;
		this.autoPlayWhenUnlocked();
	};

	private getNotes(): MelodyNote[] {
		return parseMelodyNotes(this.getAttribute("notes"));
	}

	private getTempo(): number {
		return parseNumberAttribute(this.getAttribute("tempo"), 120, 1, 2000);
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

	private isAutoPlay(): boolean {
		return this.getBooleanAttribute("auto-play", false);
	}

	private hasControls(): boolean {
		return this.getBooleanAttribute("controls", false);
	}

	private shouldShow(): boolean {
		return this.getBooleanAttribute("show", true);
	}

	private syncVisibility(): void {
		this.hidden = !this.shouldShow();
	}

	private schedule(): ScheduledNote[] {
		const beatSeconds = 60 / this.getTempo();
		const scheduled: ScheduledNote[] = [];
		let cursor = 0;
		let index = 0;
		for (const note of this.getNotes()) {
			const length = note.beats * beatSeconds;
			scheduled.push({
				...note,
				startSeconds: cursor,
				endSeconds: cursor + length,
				index,
			});
			cursor += length;
			index += 1;
		}
		return scheduled;
	}

	private totalSeconds(): number {
		const scheduled = this.schedule();
		if (scheduled.length === 0) {
			return 0;
		}
		return scheduled[scheduled.length - 1].endSeconds;
	}

	private renderStructure(): void {
		const label = document.createElement("span");
		label.className = "drafter-audio-status";

		const primaryButton = document.createElement("button");
		primaryButton.type = "button";
		primaryButton.className = "drafter-audio-play-button";
		primaryButton.addEventListener("click", () => {
			this.handlePrimaryClick();
		});

		const children: Node[] = [primaryButton, label];
		this.restartButton = null;
		if (this.hasControls()) {
			const restartButton = document.createElement("button");
			restartButton.type = "button";
			restartButton.textContent = "🔄";
			restartButton.setAttribute("aria-label", "Restart melody");
			restartButton.addEventListener("click", () => {
				void audioBroker.requestUnlock().then(() => this.restart());
			});
			this.restartButton = restartButton;
			children.push(restartButton);
		}

		this.label = label;
		this.primaryButton = primaryButton;
		this.replaceChildren(...children);
		this.syncVisibility();
		this.updateControls();
	}

	private updateControls(): void {
		if (this.primaryButton === null || this.label === null) {
			return;
		}
		const button = this.primaryButton;
		button.hidden = false;
		button.disabled = false;
		if (this.state === "unavailable") {
			button.hidden = true;
			this.label.textContent = AUDIO_UNSUPPORTED_ERROR;
		} else if (this.state === "locked") {
			button.textContent = "🔊 Enable sound";
		} else if (this.state === "playing") {
			if (this.hasControls()) {
				button.textContent = "⏸";
				button.setAttribute("aria-label", "Pause melody");
			} else if (this.isAutoPlay()) {
				button.hidden = true;
			} else {
				button.textContent = "♪";
				button.disabled = true;
			}
		} else {
			button.textContent = "▶";
			button.setAttribute("aria-label", "Play melody");
			if (this.state !== "paused") {
				this.label.textContent = "";
			}
		}
	}

	private handlePrimaryClick(): void {
		void audioBroker.requestUnlock().then(() => {
			if (!this.isConnected) {
				return;
			}
			if (this.state === "playing") {
				if (this.hasControls()) {
					this.pause();
				}
				return;
			}
			if (this.state === "paused") {
				this.play(this.offsetSeconds);
				return;
			}
			this.play(0);
		});
	}

	private clearPlayback(): void {
		for (const node of this.activeNodes) {
			node.stop();
		}
		this.activeNodes = [];
		for (const timeout of this.timeouts) {
			window.clearTimeout(timeout);
		}
		this.timeouts = [];
		if (this.outputNode !== null) {
			this.outputNode.disconnect();
			this.outputNode = null;
		}
	}

	private play(offsetSeconds: number): void {
		if (!this.isConnected || this.state === "playing") {
			return;
		}
		const context = audioBroker.getContext();
		if (context === null) {
			this.state = "unavailable";
			this.updateControls();
			return;
		}
		const scheduled = this.schedule();
		const count = scheduled.length;
		const total = this.totalSeconds();
		if (count === 0 || offsetSeconds >= total) {
			this.finish(count);
			return;
		}
		this.clearPlayback();

		const masterGain = context.createGain();
		masterGain.gain.value = this.getVolume();
		const effects = buildEffectsChain(
			context,
			parseEffectConfigs(this.getAttribute("effects")),
		);
		masterGain.connect(effects.input);
		effects.output.connect(context.destination);
		this.outputNode = effects.output;

		const now = context.currentTime;
		const waveform = this.getWaveform();
		this.startedAtContextTime = now;
		this.offsetSeconds = offsetSeconds;
		this.state = "playing";

		for (const note of scheduled) {
			if (note.endSeconds <= offsetSeconds) {
				continue;
			}
			const startAt = now + Math.max(0, note.startSeconds - offsetSeconds);
			const soundingEnd = Math.min(
				note.endSeconds,
				note.startSeconds +
					(note.endSeconds - note.startSeconds) * ARTICULATION,
			);
			const stopAt = now + Math.max(0, soundingEnd - offsetSeconds);

			if (note.frequency > 0 && stopAt > now) {
				const oscillator = context.createOscillator();
				oscillator.type = waveform;
				oscillator.frequency.value = note.frequency;
				const envelope = context.createGain();
				envelope.gain.setValueAtTime(0, startAt);
				envelope.gain.linearRampToValueAtTime(
					1,
					startAt + NOTE_ATTACK_SECONDS,
				);
				envelope.gain.setValueAtTime(
					1,
					Math.max(startAt, stopAt - NOTE_RELEASE_SECONDS),
				);
				envelope.gain.linearRampToValueAtTime(0.0001, stopAt);
				oscillator.connect(envelope);
				envelope.connect(masterGain);
				oscillator.start(startAt);
				oscillator.stop(stopAt);
				this.activeNodes.push({
					stop: () => {
						oscillator.onended = null;
						try {
							oscillator.stop();
						} catch {
							// Already stopped.
						}
						oscillator.disconnect();
						envelope.disconnect();
					},
				});
			}

			if (note.startSeconds >= offsetSeconds) {
				const delayMs = (note.startSeconds - offsetSeconds) * 1000;
				this.timeouts.push(
					window.setTimeout(() => {
						this.announceNote(note, count);
					}, delayMs),
				);
			}
		}

		this.timeouts.push(
			window.setTimeout(
				() => {
					this.finish(count);
				},
				(total - offsetSeconds) * 1000,
			),
		);
		this.updateControls();
	}

	private announceNote(note: ScheduledNote, count: number): void {
		if (this.label !== null) {
			this.label.textContent =
				note.frequency > 0 ? `♪ ${note.note}` : "♪";
		}
		this.dispatchEvent(
			new CustomEvent("note", {
				detail: {
					note: note.note,
					frequency: note.frequency,
					index: note.index,
					count,
				},
			}),
		);
	}

	private pause(): void {
		if (this.state !== "playing") {
			return;
		}
		const context = audioBroker.getContext();
		const elapsed =
			context === null
				? 0
				: context.currentTime - this.startedAtContextTime;
		this.offsetSeconds += elapsed;
		this.clearPlayback();
		this.state = "paused";
		this.updateControls();
	}

	private restart(): void {
		this.clearPlayback();
		this.offsetSeconds = 0;
		this.state = "idle";
		this.play(0);
	}

	private finish(count: number): void {
		this.clearPlayback();
		this.offsetSeconds = 0;
		this.state = "finished";
		this.updateControls();
		this.dispatchEvent(new CustomEvent("finish", { detail: { count } }));
	}

	private autoPlayWhenUnlocked(): void {
		if (!audioBroker.isSupported()) {
			this.state = "unavailable";
			this.updateControls();
			return;
		}
		if (audioBroker.isUnlocked()) {
			this.play(0);
			return;
		}
		this.state = "locked";
		this.updateControls();
		this.unsubscribeUnlock = audioBroker.onUnlocked(() => {
			this.unsubscribeUnlock = null;
			if (this.state === "locked") {
				this.state = "idle";
				this.play(0);
			}
		});
	}

	connectedCallback() {
		this.state = "idle";
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
		// Any musical change restarts playback from a clean state.
		this.clearPlayback();
		this.offsetSeconds = 0;
		this.state = "idle";
		this.renderStructure();
	}

	disconnectedCallback() {
		window.removeEventListener(
			DRAFTER_PAGE_LOADED_EVENT,
			this.handlePageLoaded,
		);
		this.clearPlayback();
		if (this.unsubscribeUnlock !== null) {
			this.unsubscribeUnlock();
			this.unsubscribeUnlock = null;
		}
		this.waitingForPageLoad = false;
		this.label = null;
		this.primaryButton = null;
		this.restartButton = null;
	}
}

customElements.define("drafter-melody", Melody);
