import { DrafterHTMLElement } from "./drafterHTMLElement";

type CameraStatus =
	| "unavailable"
	| "prompt"
	| "pending"
	| "live"
	| "granted"
	| "denied"
	| "error";

type PhotoData = {
	status: CameraStatus;
	message?: string;
	data_url?: string;
	width?: number;
	height?: number;
};

const CAMERA_UNSUPPORTED_ERROR = "Camera is not supported by your browser";

function paragraph(className: string, text: string): HTMLParagraphElement {
	const element = document.createElement("p");
	if (className) {
		element.className = className;
	}
	element.textContent = text;
	return element;
}

class Camera extends DrafterHTMLElement {
	static get observedAttributes() {
		return ["name", "width", "height", "facing", "mirror", "show"];
	}

	private input: HTMLInputElement | null = null;

	private statusArea: HTMLDivElement | null = null;

	private video: HTMLVideoElement | null = null;

	private stream: MediaStream | null = null;

	private status: CameraStatus = "prompt";

	private lastPhoto: PhotoData | null = null;

	private getName(): string {
		return this.getAttribute("name") ?? "";
	}

	private getFacing(): "user" | "environment" {
		return this.getAttribute("facing") === "environment"
			? "environment"
			: "user";
	}

	private shouldMirror(): boolean {
		return this.getBooleanAttribute("mirror", true);
	}

	private shouldShow(): boolean {
		return this.getBooleanAttribute("show", true);
	}

	private syncVisibility(): void {
		this.hidden = !this.shouldShow();
	}

	private isSupported(): boolean {
		return typeof navigator.mediaDevices?.getUserMedia === "function";
	}

	// The captured photo is never mirrored; mirroring is only a preview
	// affordance so the user's movements match what they see, like a mirror.
	private syncMirror(): void {
		if (this.video !== null) {
			this.video.style.transform = this.shouldMirror()
				? "scaleX(-1)"
				: "";
		}
	}

	// The hidden input is what actually enters the form payload: its value
	// is the JSON-encoded Photo, and data-transform "json-decode" tells the
	// bridge to decode it before the router converts it to a Photo.
	private renderStructure(): void {
		const input = document.createElement("input");
		input.type = "hidden";
		input.name = this.getName();
		input.setAttribute("data-transform", "json-decode");

		const statusArea = document.createElement("div");
		statusArea.className = "drafter-camera-status";

		this.input = input;
		this.statusArea = statusArea;
		this.replaceChildren(input, statusArea);
		this.syncVisibility();
	}

	private setData(data: PhotoData): void {
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
		this.video = null;

		if (this.status === "prompt") {
			const button = document.createElement("button");
			button.type = "button";
			button.className = "drafter-camera-start-button";
			button.textContent = "📷 Enable camera";
			button.addEventListener("click", () => {
				this.startCamera();
			});
			children.push(button);
		} else if (this.status === "pending") {
			const spinner = document.createElement("div");
			spinner.className = "drafter-microphone-spinner";
			children.push(
				spinner,
				paragraph("", message ?? "Requesting permission..."),
			);
		} else if (this.status === "live") {
			const video = document.createElement("video");
			video.className = "drafter-camera-preview";
			video.autoplay = true;
			video.muted = true;
			video.setAttribute("playsinline", "");
			if (this.stream !== null) {
				video.srcObject = this.stream;
			}
			this.video = video;
			this.syncMirror();

			const captureButton = document.createElement("button");
			captureButton.type = "button";
			captureButton.className = "drafter-camera-capture-button";
			captureButton.textContent = "📷 Take photo";
			captureButton.addEventListener("click", () => {
				this.capturePhoto();
			});

			const stopButton = document.createElement("button");
			stopButton.type = "button";
			stopButton.className = "drafter-camera-stop-button";
			stopButton.textContent = "⏹ Stop";
			stopButton.addEventListener("click", () => {
				this.stopCamera();
			});

			const buttonRow = document.createElement("div");
			buttonRow.className = "drafter-camera-buttons";
			buttonRow.append(captureButton, stopButton);
			children.push(video, buttonRow);
		} else if (this.status === "granted") {
			const photo = document.createElement("img");
			photo.className = "drafter-camera-photo";
			photo.alt = "Captured photo";
			if (this.lastPhoto?.data_url !== undefined) {
				photo.src = this.lastPhoto.data_url;
			}
			const retakeButton = document.createElement("button");
			retakeButton.type = "button";
			retakeButton.className = "drafter-camera-start-button";
			retakeButton.textContent = "📷 Retake";
			retakeButton.addEventListener("click", () => {
				this.startCamera();
			});
			children.push(photo, retakeButton);
		} else if (this.status === "denied") {
			children.push(
				paragraph("drafter-microphone-error-icon", "⚠️"),
				paragraph(
					"drafter-microphone-error-message",
					message ?? "Camera access denied",
				),
			);
		} else if (this.status === "unavailable") {
			children.push(
				paragraph("drafter-microphone-error-icon", "ℹ️"),
				paragraph("", message ?? CAMERA_UNSUPPORTED_ERROR),
			);
		} else {
			children.push(
				paragraph("drafter-microphone-error-icon", "⚠️"),
				paragraph(
					"drafter-microphone-error-message",
					message ?? "Could not use the camera",
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

	private startCamera(): void {
		if (this.status === "live" || this.status === "pending") {
			return;
		}
		if (!this.isSupported()) {
			this.emitFailure("unavailable", CAMERA_UNSUPPORTED_ERROR);
			return;
		}
		this.setData({ status: "pending", message: "Requesting permission..." });
		this.renderStatus();
		const constraints: MediaStreamConstraints = {
			video: {
				width: { ideal: this.getNumberAttribute("width", 640) },
				height: { ideal: this.getNumberAttribute("height", 480) },
				facingMode: this.getFacing(),
			},
			audio: false,
		};
		navigator.mediaDevices
			.getUserMedia(constraints)
			.then((stream) => {
				if (!this.isConnected) {
					stopStream(stream);
					return;
				}
				this.stream = stream;
				this.setData({ status: "live", message: "Camera is on" });
				this.renderStatus();
			})
			.catch((error) => {
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
			this.emitFailure("denied", "Camera access denied");
		} else if (name === "NotFoundError" || name === "OverconstrainedError") {
			this.emitFailure("error", "No camera was found");
		} else if (name === "NotReadableError") {
			this.emitFailure("error", "The camera is already in use");
		} else {
			this.emitFailure("error", message || "Could not use the camera");
		}
	}

	private capturePhoto(): void {
		const video = this.video;
		if (video === null || this.stream === null) {
			return;
		}
		const width = video.videoWidth || this.getNumberAttribute("width", 640);
		const height =
			video.videoHeight || this.getNumberAttribute("height", 480);
		const canvas = document.createElement("canvas");
		canvas.width = width;
		canvas.height = height;
		const context = canvas.getContext("2d");
		if (context === null) {
			this.emitFailure("error", "Could not capture the photo");
			return;
		}
		context.drawImage(video, 0, 0, width, height);
		let dataUrl: string;
		try {
			dataUrl = canvas.toDataURL("image/png");
		} catch {
			this.emitFailure("error", "Could not capture the photo");
			return;
		}
		// Stop the stream after capturing so the camera light turns off;
		// "Retake" starts a fresh stream.
		this.releaseStream();
		const photo: PhotoData = {
			status: "granted",
			message: "Photo captured",
			data_url: dataUrl,
			width,
			height,
		};
		this.lastPhoto = photo;
		this.setData(photo);
		this.renderStatus();
		this.dispatchEvent(
			new CustomEvent("capture", { detail: { width, height } }),
		);
	}

	private stopCamera(): void {
		this.releaseStream();
		if (this.lastPhoto !== null) {
			this.setData(this.lastPhoto);
		} else {
			this.setData({
				status: "prompt",
				message: "No photo has been taken yet",
			});
		}
		this.renderStatus();
	}

	private releaseStream(): void {
		if (this.stream !== null) {
			stopStream(this.stream);
			this.stream = null;
		}
	}

	connectedCallback() {
		this.renderStructure();
		if (!this.isSupported()) {
			this.setData({
				status: "unavailable",
				message: CAMERA_UNSUPPORTED_ERROR,
			});
			this.renderStatus();
			return;
		}
		this.setData({
			status: "prompt",
			message: "No photo has been taken yet",
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
		if (name === "mirror") {
			this.syncMirror();
			return;
		}
		if (name === "facing" && this.status === "live") {
			// Switch cameras by restarting the stream with the new facing.
			this.releaseStream();
			this.status = "prompt";
			this.startCamera();
			return;
		}
		if (name === "show") {
			this.syncVisibility();
		}
	}

	disconnectedCallback() {
		this.releaseStream();
		this.video = null;
		this.input = null;
		this.statusArea = null;
	}
}

function stopStream(stream: MediaStream): void {
	for (const track of stream.getTracks()) {
		track.stop();
	}
}

customElements.define("drafter-camera", Camera);
