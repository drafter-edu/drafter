import { DrafterHTMLElement } from "./drafterHTMLElement";
import {
	audioBroker,
	AUDIO_UNSUPPORTED_ERROR,
	MICROPHONE_UNSUPPORTED_ERROR,
} from "./audioBroker";
import { parseNumberAttribute } from "./audioGraph";

type MicrophoneStatus =
	| "unavailable"
	| "prompt"
	| "pending"
	| "granted"
	| "denied"
	| "error";

type MicrophoneData = {
	status: MicrophoneStatus;
	message?: string;
	volume?: number;
	peak_volume?: number;
	pitch?: number | null;
};

const ANALYSIS_INTERVAL_MS = 50;
//: Below this volume, pitch estimates are noise and are omitted.
const PITCH_VOLUME_FLOOR = 0.02;
const VISUALIZER_WIDTH = 300;
const VISUALIZER_HEIGHT = 60;

const DENIED_HELP_INSTRUCTIONS = [
	"To enable microphone access:",
	"",
	"1. Click the lock or info icon in your browser's address bar",
	"2. Find Microphone permissions",
	"3. Change to 'Allow'",
	"4. Refresh this page",
].join("\n");

function paragraph(className: string, text: string): HTMLParagraphElement {
	const element = document.createElement("p");
	if (className) {
		element.className = className;
	}
	element.textContent = text;
	return element;
}

class Microphone extends DrafterHTMLElement {
	static get observedAttributes() {
		return ["name", "threshold", "cooldown", "rate", "show", "visualize"];
	}

	private input: HTMLInputElement | null = null;

	private statusArea: HTMLDivElement | null = null;

	private meterFill: HTMLDivElement | null = null;

	private canvas: HTMLCanvasElement | null = null;

	private analyser: AnalyserNode | null = null;

	private sourceNode: MediaStreamAudioSourceNode | null = null;

	private intervalId: number | null = null;

	private status: MicrophoneStatus = "prompt";

	private peakVolume = 0;

	private isLoud = false;

	private lastLoudAt = 0;

	private lastLevelAt = 0;

	private hasAcquiredMicrophone = false;

	private getName(): string {
		return this.getAttribute("name") ?? "";
	}

	private getThreshold(): number {
		return parseNumberAttribute(this.getAttribute("threshold"), 0.5, 0, 1);
	}

	private getCooldown(): number {
		return parseNumberAttribute(
			this.getAttribute("cooldown"),
			1000,
			0,
			3600000,
		);
	}

	private getRate(): number {
		return parseNumberAttribute(this.getAttribute("rate"), 0, 0, 3600000);
	}

	private getVisualize(): string {
		const visualize = this.getAttribute("visualize") ?? "meter";
		if (visualize === "waveform" || visualize === "bars") {
			return visualize;
		}
		return "meter";
	}

	private shouldShow(): boolean {
		return this.getBooleanAttribute("show", true);
	}

	private syncVisibility(): void {
		this.hidden = !this.shouldShow();
	}

	// The hidden input is what actually enters the form payload: its value
	// is the JSON-encoded AudioLevel snapshot, and data-transform
	// "json-decode" tells the bridge to decode it before the router
	// converts it to an AudioLevel.
	private renderStructure(): void {
		const input = document.createElement("input");
		input.type = "hidden";
		input.name = this.getName();
		input.setAttribute("data-transform", "json-decode");

		const statusArea = document.createElement("div");
		statusArea.className = "drafter-microphone-status";

		this.input = input;
		this.statusArea = statusArea;
		this.replaceChildren(input, statusArea);
		this.syncVisibility();
	}

	private setData(data: MicrophoneData): void {
		this.status = data.status;
		if (this.input !== null) {
			this.input.value = JSON.stringify(data);
		}
	}

	private renderStatus(message?: string): void {
		if (this.statusArea === null) {
			return;
		}
		const children: Node[] = [];
		this.meterFill = null;
		this.canvas = null;

		if (this.status === "prompt") {
			const button = document.createElement("button");
			button.type = "button";
			button.className = "drafter-microphone-prompt";
			button.textContent = "🎤 Enable microphone";
			button.addEventListener("click", () => {
				// This click is the user gesture that both grants the
				// microphone and unlocks the shared audio context.
				void audioBroker.requestUnlock();
				this.beginCapture();
			});
			children.push(button);
		} else if (this.status === "pending") {
			const spinner = document.createElement("div");
			spinner.className = "drafter-microphone-spinner";
			children.push(
				spinner,
				paragraph("", message ?? "Requesting permission..."),
			);
		} else if (this.status === "granted") {
			if (this.getVisualize() === "meter") {
				const meter = document.createElement("div");
				meter.className = "drafter-microphone-meter";
				const fill = document.createElement("div");
				fill.className = "drafter-microphone-meter-fill";
				meter.appendChild(fill);
				this.meterFill = fill;
				children.push(meter);
			} else {
				const canvas = document.createElement("canvas");
				canvas.className = "drafter-audio-visualizer";
				canvas.width = VISUALIZER_WIDTH;
				canvas.height = VISUALIZER_HEIGHT;
				this.canvas = canvas;
				children.push(canvas);
			}
			children.push(
				paragraph(
					"drafter-microphone-live-message",
					message ?? "🎤 Microphone active",
				),
			);
		} else if (this.status === "denied") {
			const helpButton = document.createElement("button");
			helpButton.type = "button";
			helpButton.className = "drafter-microphone-help-link";
			helpButton.textContent = "How to enable microphone access";
			helpButton.addEventListener("click", () => {
				window.alert(DENIED_HELP_INSTRUCTIONS);
			});
			children.push(
				paragraph("drafter-microphone-error-icon", "⚠️"),
				paragraph(
					"drafter-microphone-error-message",
					message ?? "Microphone access denied",
				),
				helpButton,
			);
		} else if (this.status === "unavailable") {
			children.push(
				paragraph("drafter-microphone-error-icon", "ℹ️"),
				paragraph("", message ?? MICROPHONE_UNSUPPORTED_ERROR),
			);
		} else {
			children.push(
				paragraph("drafter-microphone-error-icon", "⚠️"),
				paragraph(
					"drafter-microphone-error-message",
					message ?? "Could not access the microphone",
				),
			);
		}

		this.statusArea.dataset.status = this.status;
		this.statusArea.replaceChildren(...children);
	}

	private emitFailure(
		status: "denied" | "error" | "unavailable",
		message: string,
	): void {
		this.setData({ status, message });
		this.renderStatus(message);
		const detail = { status, message };
		this.dispatchEvent(new CustomEvent("error", { detail: { ...detail } }));
		if (status === "denied") {
			this.dispatchEvent(
				new CustomEvent("denied", { detail: { ...detail } }),
			);
		}
	}

	private beginCapture(): void {
		this.setData({ status: "pending", message: "Requesting permission..." });
		this.renderStatus();
		this.hasAcquiredMicrophone = true;
		audioBroker
			.acquireMicrophone()
			.then((stream) => {
				if (!this.isConnected) {
					return;
				}
				this.startAnalysis(stream);
			})
			.catch((error) => {
				this.hasAcquiredMicrophone = false;
				if (!this.isConnected) {
					return;
				}
				this.handleCaptureError(error);
			});
	}

	private handleCaptureError(error: unknown): void {
		const name =
			error instanceof Error ? error.name : "";
		const message = error instanceof Error ? error.message : "";
		if (name === "NotAllowedError" || name === "SecurityError") {
			this.emitFailure("denied", "Microphone access denied");
		} else if (name === "NotFoundError") {
			this.emitFailure("error", "No microphone was found");
		} else if (message === MICROPHONE_UNSUPPORTED_ERROR) {
			this.emitFailure("unavailable", MICROPHONE_UNSUPPORTED_ERROR);
		} else {
			this.emitFailure(
				"error",
				message || "Could not access the microphone",
			);
		}
	}

	private startAnalysis(stream: MediaStream): void {
		const context = audioBroker.getContext();
		if (context === null) {
			this.emitFailure("unavailable", AUDIO_UNSUPPORTED_ERROR);
			return;
		}
		// If permission was granted without a fresh gesture (e.g. it was
		// remembered), the context may still be suspended; the broker's
		// gesture listeners will resume it on the next interaction.
		audioBroker.onUnlocked(() => {});
		void audioBroker.requestUnlock();

		this.sourceNode = context.createMediaStreamSource(stream);
		this.analyser = context.createAnalyser();
		// 4096 samples (~85ms at 48kHz) overlaps consecutive 50ms polls, so
		// a short transient cannot fall between two reads.
		this.analyser.fftSize = 4096;
		this.sourceNode.connect(this.analyser);

		this.peakVolume = 0;
		this.isLoud = false;
		this.lastLoudAt = 0;
		this.lastLevelAt = 0;
		this.setData({
			status: "granted",
			message: "Microphone active",
			volume: 0,
			peak_volume: 0,
		});
		this.renderStatus();
		this.intervalId = window.setInterval(() => {
			this.analyze();
		}, ANALYSIS_INTERVAL_MS);
	}

	private measureVolume(): number {
		if (this.analyser === null) {
			return 0;
		}
		const data = new Uint8Array(this.analyser.fftSize);
		this.analyser.getByteTimeDomainData(data);
		// Peak amplitude, not RMS: transients like claps last only a few
		// milliseconds, so averaging over the analysis window would dilute
		// them below any usable threshold.
		let peak = 0;
		for (let i = 0; i < data.length; i += 1) {
			const sample = Math.abs(data[i] - 128) / 128;
			if (sample > peak) {
				peak = sample;
			}
		}
		return Math.min(1, peak);
	}

	private measurePitch(): number | null {
		if (this.analyser === null) {
			return null;
		}
		const context = audioBroker.getContext();
		if (context === null) {
			return null;
		}
		const data = new Uint8Array(this.analyser.frequencyBinCount);
		this.analyser.getByteFrequencyData(data);
		let bestIndex = 0;
		let bestValue = 0;
		for (let i = 1; i < data.length; i += 1) {
			if (data[i] > bestValue) {
				bestValue = data[i];
				bestIndex = i;
			}
		}
		if (bestValue === 0 || bestIndex === 0) {
			return null;
		}
		const frequency =
			(bestIndex * context.sampleRate) / this.analyser.fftSize;
		return Math.round(frequency * 10) / 10;
	}

	private analyze(): void {
		const volume = Math.round(this.measureVolume() * 1000) / 1000;
		this.peakVolume = Math.max(this.peakVolume, volume);
		const pitch = volume >= PITCH_VOLUME_FLOOR ? this.measurePitch() : null;
		const threshold = this.getThreshold();
		const now = Date.now();

		const data: MicrophoneData = {
			status: "granted",
			message: "Microphone active",
			volume,
			peak_volume: this.peakVolume,
		};
		if (pitch !== null) {
			data.pitch = pitch;
		}
		this.setData(data);
		this.updateVisualization(volume);

		if (!this.isLoud && volume >= threshold) {
			if (now - this.lastLoudAt >= this.getCooldown()) {
				this.isLoud = true;
				this.lastLoudAt = now;
				this.dispatchEvent(
					new CustomEvent("loud", { detail: { volume, threshold } }),
				);
			}
		} else if (this.isLoud && volume < threshold) {
			this.isLoud = false;
			this.dispatchEvent(
				new CustomEvent("quiet", { detail: { volume, threshold } }),
			);
		}

		const rate = this.getRate();
		if (rate > 0 && now - this.lastLevelAt >= rate) {
			this.lastLevelAt = now;
			const detail: { volume: number; pitch?: number } = { volume };
			if (pitch !== null) {
				detail.pitch = pitch;
			}
			this.dispatchEvent(new CustomEvent("level", { detail }));
		}
	}

	private updateVisualization(volume: number): void {
		if (this.meterFill !== null) {
			this.meterFill.style.width = `${Math.round(volume * 100)}%`;
			this.meterFill.classList.toggle(
				"drafter-microphone-meter-loud",
				volume >= this.getThreshold(),
			);
			return;
		}
		if (this.canvas === null || this.analyser === null) {
			return;
		}
		const context2d = this.canvas.getContext("2d");
		if (context2d === null) {
			return;
		}
		const width = this.canvas.width;
		const height = this.canvas.height;
		context2d.clearRect(0, 0, width, height);
		if (this.getVisualize() === "bars") {
			const data = new Uint8Array(this.analyser.frequencyBinCount);
			this.analyser.getByteFrequencyData(data);
			context2d.fillStyle = "#3e3e9e";
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
			const data = new Uint8Array(this.analyser.fftSize);
			this.analyser.getByteTimeDomainData(data);
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

	private stopAnalysis(): void {
		if (this.intervalId !== null) {
			window.clearInterval(this.intervalId);
			this.intervalId = null;
		}
		if (this.sourceNode !== null) {
			this.sourceNode.disconnect();
			this.sourceNode = null;
		}
		this.analyser = null;
		if (this.hasAcquiredMicrophone) {
			this.hasAcquiredMicrophone = false;
			audioBroker.releaseMicrophone();
		}
	}

	private checkExistingPermission(): void {
		if (!navigator.permissions) {
			return;
		}
		navigator.permissions
			.query({ name: "microphone" as PermissionName })
			.then((result) => {
				if (!this.isConnected) {
					return;
				}
				if (result.state === "granted") {
					this.beginCapture();
				} else if (result.state === "denied") {
					this.setData({
						status: "denied",
						message: "Microphone access denied",
					});
					this.renderStatus();
				}
				// If "prompt", leave the initial button visible.
			})
			.catch(() => {
				// Permissions API not fully supported; leave the prompt.
			});
	}

	connectedCallback() {
		this.renderStructure();
		if (!audioBroker.isMicrophoneSupported() || !audioBroker.isSupported()) {
			this.setData({
				status: "unavailable",
				message: MICROPHONE_UNSUPPORTED_ERROR,
			});
			this.renderStatus();
			return;
		}
		this.setData({
			status: "prompt",
			message: "Microphone permission has not been requested yet",
		});
		this.renderStatus();
		this.checkExistingPermission();
	}

	attributeChangedCallback(
		name: string,
		oldValue: string | null,
		newValue: string | null,
	) {
		if (oldValue === newValue || !this.isConnected) {
			return;
		}
		if (name === "name") {
			if (this.input !== null) {
				this.input.name = newValue ?? "";
			}
			return;
		}
		if (name === "show") {
			this.syncVisibility();
			return;
		}
		if (name === "visualize" && this.status === "granted") {
			this.renderStatus();
		}
	}

	disconnectedCallback() {
		this.stopAnalysis();
		this.input = null;
		this.statusArea = null;
		this.meterFill = null;
		this.canvas = null;
	}
}

customElements.define("drafter-microphone", Microphone);
