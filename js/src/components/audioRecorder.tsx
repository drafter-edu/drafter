import { DrafterHTMLElement } from "./drafterHTMLElement";
import { audioBroker, MICROPHONE_UNSUPPORTED_ERROR } from "./audioBroker";
import { parseNumberAttribute } from "./audioGraph";

type RecorderStatus =
	| "unavailable"
	| "prompt"
	| "pending"
	| "recording"
	| "granted"
	| "denied"
	| "error";

type RecordingData = {
	status: RecorderStatus;
	message?: string;
	data_url?: string;
	duration?: number;
	size?: number;
};

const ELAPSED_UPDATE_MS = 250;

function paragraph(className: string, text: string): HTMLParagraphElement {
	const element = document.createElement("p");
	if (className) {
		element.className = className;
	}
	element.textContent = text;
	return element;
}

function formatSeconds(totalSeconds: number): string {
	const seconds = Math.floor(totalSeconds % 60);
	const minutes = Math.floor(totalSeconds / 60);
	return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

class AudioRecorder extends DrafterHTMLElement {
	static get observedAttributes() {
		return ["name", "max-duration", "show"];
	}

	private input: HTMLInputElement | null = null;

	private statusArea: HTMLDivElement | null = null;

	private elapsedLabel: HTMLSpanElement | null = null;

	private recorder: MediaRecorder | null = null;

	private chunks: Blob[] = [];

	private status: RecorderStatus = "prompt";

	private recordingStartedAt = 0;

	private elapsedIntervalId: number | null = null;

	private maxDurationTimeoutId: number | null = null;

	private hasAcquiredMicrophone = false;

	private lastRecording: RecordingData | null = null;

	private getName(): string {
		return this.getAttribute("name") ?? "";
	}

	private getMaxDuration(): number {
		return parseNumberAttribute(
			this.getAttribute("max-duration"),
			30000,
			100,
			3600000,
		);
	}

	private shouldShow(): boolean {
		return this.getBooleanAttribute("show", true);
	}

	private syncVisibility(): void {
		this.hidden = !this.shouldShow();
	}

	private isSupported(): boolean {
		return (
			audioBroker.isMicrophoneSupported() &&
			typeof MediaRecorder !== "undefined"
		);
	}

	// The hidden input is what actually enters the form payload: its value
	// is the JSON-encoded Recording, and data-transform "json-decode"
	// tells the bridge to decode it before the router converts it to a
	// Recording.
	private renderStructure(): void {
		const input = document.createElement("input");
		input.type = "hidden";
		input.name = this.getName();
		input.setAttribute("data-transform", "json-decode");

		const statusArea = document.createElement("div");
		statusArea.className = "drafter-recorder-status";

		this.input = input;
		this.statusArea = statusArea;
		this.replaceChildren(input, statusArea);
		this.syncVisibility();
	}

	private setData(data: RecordingData): void {
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
		this.elapsedLabel = null;

		if (this.status === "prompt") {
			const button = document.createElement("button");
			button.type = "button";
			button.className = "drafter-recorder-record-button";
			button.textContent = "⏺ Record";
			button.addEventListener("click", () => {
				void audioBroker.requestUnlock();
				this.startRecording();
			});
			children.push(button);
		} else if (this.status === "pending") {
			const spinner = document.createElement("div");
			spinner.className = "drafter-microphone-spinner";
			children.push(
				spinner,
				paragraph("", message ?? "Requesting permission..."),
			);
		} else if (this.status === "recording") {
			const elapsed = document.createElement("span");
			elapsed.className = "drafter-recorder-elapsed";
			elapsed.textContent = "⏺ 0:00";
			this.elapsedLabel = elapsed;

			const stopButton = document.createElement("button");
			stopButton.type = "button";
			stopButton.className = "drafter-recorder-stop-button";
			stopButton.textContent = "⏹ Stop";
			stopButton.addEventListener("click", () => {
				this.stopRecording();
			});
			children.push(elapsed, stopButton);
		} else if (this.status === "granted") {
			const preview = document.createElement("audio");
			preview.controls = true;
			if (this.lastRecording?.data_url !== undefined) {
				preview.src = this.lastRecording.data_url;
			}
			const redoButton = document.createElement("button");
			redoButton.type = "button";
			redoButton.className = "drafter-recorder-record-button";
			redoButton.textContent = "⏺ Re-record";
			redoButton.addEventListener("click", () => {
				void audioBroker.requestUnlock();
				this.startRecording();
			});
			children.push(preview, redoButton);
		} else if (this.status === "denied") {
			children.push(
				paragraph("drafter-microphone-error-icon", "⚠️"),
				paragraph(
					"drafter-microphone-error-message",
					message ?? "Microphone access denied",
				),
			);
		} else if (this.status === "unavailable") {
			children.push(
				paragraph("drafter-microphone-error-icon", "ℹ️"),
				paragraph(
					"",
					message ?? "Audio recording is not supported by your browser",
				),
			);
		} else {
			children.push(
				paragraph("drafter-microphone-error-icon", "⚠️"),
				paragraph(
					"drafter-microphone-error-message",
					message ?? "Could not record audio",
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

	private startRecording(): void {
		if (this.status === "recording") {
			return;
		}
		if (!this.isSupported()) {
			this.emitFailure(
				"unavailable",
				"Audio recording is not supported by your browser",
			);
			return;
		}
		this.setData({ status: "pending", message: "Requesting permission..." });
		this.renderStatus();
		this.hasAcquiredMicrophone = true;
		audioBroker
			.acquireMicrophone()
			.then((stream) => {
				if (!this.isConnected) {
					this.releaseMicrophone();
					return;
				}
				this.beginRecording(stream);
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
		const name = error instanceof Error ? error.name : "";
		const message = error instanceof Error ? error.message : "";
		if (name === "NotAllowedError" || name === "SecurityError") {
			this.emitFailure("denied", "Microphone access denied");
		} else if (name === "NotFoundError") {
			this.emitFailure("error", "No microphone was found");
		} else if (message === MICROPHONE_UNSUPPORTED_ERROR) {
			this.emitFailure("unavailable", MICROPHONE_UNSUPPORTED_ERROR);
		} else {
			this.emitFailure("error", message || "Could not record audio");
		}
	}

	private beginRecording(stream: MediaStream): void {
		let recorder: MediaRecorder;
		try {
			recorder = new MediaRecorder(stream);
		} catch (error) {
			this.releaseMicrophone();
			this.handleCaptureError(error);
			return;
		}
		this.recorder = recorder;
		this.chunks = [];
		recorder.ondataavailable = (event: BlobEvent) => {
			if (event.data.size > 0) {
				this.chunks.push(event.data);
			}
		};
		recorder.onerror = () => {
			this.clearRecordingTimers();
			this.releaseMicrophone();
			this.emitFailure("error", "Recording failed");
		};
		recorder.onstop = () => {
			this.finishRecording();
		};

		recorder.start();
		this.recordingStartedAt = Date.now();
		this.setData({ status: "recording", message: "Recording..." });
		this.renderStatus();
		this.elapsedIntervalId = window.setInterval(() => {
			if (this.elapsedLabel !== null) {
				const seconds = (Date.now() - this.recordingStartedAt) / 1000;
				this.elapsedLabel.textContent = `⏺ ${formatSeconds(seconds)}`;
			}
		}, ELAPSED_UPDATE_MS);
		this.maxDurationTimeoutId = window.setTimeout(() => {
			this.stopRecording();
		}, this.getMaxDuration());
	}

	private stopRecording(): void {
		this.clearRecordingTimers();
		if (this.recorder !== null && this.recorder.state !== "inactive") {
			this.recorder.stop();
		}
	}

	private finishRecording(): void {
		this.clearRecordingTimers();
		const recorder = this.recorder;
		this.recorder = null;
		const durationSeconds =
			Math.round(((Date.now() - this.recordingStartedAt) / 1000) * 100) /
			100;
		const mimeType = recorder?.mimeType || "audio/webm";
		const blob = new Blob(this.chunks, { type: mimeType });
		this.chunks = [];
		this.releaseMicrophone();

		const reader = new FileReader();
		reader.onerror = () => {
			this.emitFailure("error", "Could not read the recording");
		};
		reader.onload = () => {
			if (!this.isConnected) {
				return;
			}
			const recording: RecordingData = {
				status: "granted",
				message: "Recording available",
				data_url: String(reader.result),
				duration: durationSeconds,
				size: blob.size,
			};
			this.lastRecording = recording;
			this.setData(recording);
			this.renderStatus();
			this.dispatchEvent(
				new CustomEvent("record", {
					detail: { duration: durationSeconds, size: blob.size },
				}),
			);
		};
		reader.readAsDataURL(blob);
	}

	private clearRecordingTimers(): void {
		if (this.elapsedIntervalId !== null) {
			window.clearInterval(this.elapsedIntervalId);
			this.elapsedIntervalId = null;
		}
		if (this.maxDurationTimeoutId !== null) {
			window.clearTimeout(this.maxDurationTimeoutId);
			this.maxDurationTimeoutId = null;
		}
	}

	private releaseMicrophone(): void {
		if (this.hasAcquiredMicrophone) {
			this.hasAcquiredMicrophone = false;
			audioBroker.releaseMicrophone();
		}
	}

	connectedCallback() {
		this.renderStructure();
		if (!this.isSupported()) {
			this.setData({
				status: "unavailable",
				message: "Audio recording is not supported by your browser",
			});
			this.renderStatus();
			return;
		}
		this.setData({
			status: "prompt",
			message: "Nothing has been recorded yet",
		});
		this.renderStatus();
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
		}
	}

	disconnectedCallback() {
		this.clearRecordingTimers();
		if (this.recorder !== null && this.recorder.state !== "inactive") {
			this.recorder.onstop = null;
			this.recorder.stop();
		}
		this.recorder = null;
		this.chunks = [];
		this.releaseMicrophone();
		this.input = null;
		this.statusArea = null;
		this.elapsedLabel = null;
	}
}

customElements.define("drafter-audio-recorder", AudioRecorder);
