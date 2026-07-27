/**
 * Shared Web Audio infrastructure for the audio components.
 *
 * A single AudioContext is shared by every audio component on the page.
 * Browsers keep an AudioContext suspended until a user gesture occurs, so
 * the broker installs document-level gesture listeners and notifies
 * subscribers once the context is running ("unlocked"). Because Drafter
 * swaps pages client-side, one unlock lasts for the whole session.
 *
 * The broker also owns the shared microphone MediaStream, so that a
 * Microphone meter and an AudioRecorder on the same page trigger a single
 * permission prompt and share the stream.
 */

type WebkitWindow = Window & {
	webkitAudioContext?: typeof AudioContext;
};

const GESTURE_EVENTS: Array<keyof DocumentEventMap> = [
	"pointerdown",
	"keydown",
];

export const AUDIO_UNSUPPORTED_ERROR =
	"Audio is not supported by your browser";
export const MICROPHONE_UNSUPPORTED_ERROR =
	"Microphone access is not supported by your browser";

function getAudioContextConstructor(): typeof AudioContext | undefined {
	if (typeof window === "undefined") {
		return undefined;
	}
	return window.AudioContext ?? (window as WebkitWindow).webkitAudioContext;
}

export class AudioBroker {
	private context: AudioContext | null = null;

	private unlockCallbacks = new Set<() => void>();

	private gestureListenersInstalled = false;

	private micStream: MediaStream | null = null;

	private micRequest: Promise<MediaStream> | null = null;

	private micConsumers = 0;

	isSupported(): boolean {
		return getAudioContextConstructor() !== undefined;
	}

	/** Lazily create (or return) the shared AudioContext. */
	getContext(): AudioContext | null {
		if (this.context !== null) {
			return this.context;
		}
		const AudioContextConstructor = getAudioContextConstructor();
		if (AudioContextConstructor === undefined) {
			return null;
		}
		this.context = new AudioContextConstructor();
		this.context.addEventListener?.("statechange", () => {
			if (this.isUnlocked()) {
				this.notifyUnlocked();
			}
		});
		return this.context;
	}

	isUnlocked(): boolean {
		return this.context !== null && this.context.state === "running";
	}

	/**
	 * Try to resume the shared context. Call this from within a user
	 * gesture (e.g. a click handler); resolves true once running.
	 */
	requestUnlock(): Promise<boolean> {
		const context = this.getContext();
		if (context === null) {
			return Promise.resolve(false);
		}
		if (context.state === "running") {
			this.notifyUnlocked();
			return Promise.resolve(true);
		}
		return context
			.resume()
			.then(() => {
				const unlocked = this.isUnlocked();
				if (unlocked) {
					this.notifyUnlocked();
				}
				return unlocked;
			})
			.catch(() => false);
	}

	/**
	 * Subscribe to the moment the context becomes unlocked. If it is
	 * already unlocked, the callback fires immediately (synchronously).
	 * Returns an unsubscribe function.
	 */
	onUnlocked(callback: () => void): () => void {
		if (this.isUnlocked()) {
			callback();
			return () => {};
		}
		this.unlockCallbacks.add(callback);
		this.installGestureListeners();
		return () => {
			this.unlockCallbacks.delete(callback);
		};
	}

	isMicrophoneSupported(): boolean {
		return (
			typeof navigator !== "undefined" &&
			navigator.mediaDevices !== undefined &&
			typeof navigator.mediaDevices.getUserMedia === "function"
		);
	}

	/**
	 * Request (or reuse) the shared microphone stream. Concurrent callers
	 * share one getUserMedia request, and a live stream is reused so the
	 * user is only prompted once.
	 */
	getMicrophone(): Promise<MediaStream> {
		if (!this.isMicrophoneSupported()) {
			return Promise.reject(new Error(MICROPHONE_UNSUPPORTED_ERROR));
		}
		if (this.micStream !== null && this.isStreamLive(this.micStream)) {
			return Promise.resolve(this.micStream);
		}
		if (this.micRequest !== null) {
			return this.micRequest;
		}
		const request = navigator.mediaDevices
			.getUserMedia({ audio: true })
			.then((stream) => {
				this.micStream = stream;
				if (this.micConsumers === 0) {
					this.stopMicrophoneTracks();
				}
				return stream;
			})
			.finally(() => {
				if (this.micRequest === request) {
					this.micRequest = null;
				}
			});
		this.micRequest = request;
		return request;
	}

	/**
	 * Like getMicrophone, but counted: the microphone stays live until
	 * every acquirer has called releaseMicrophone, at which point the
	 * tracks are stopped (turning off the browser's recording indicator).
	 */
	acquireMicrophone(): Promise<MediaStream> {
		this.micConsumers += 1;
		return this.getMicrophone().catch((error) => {
			this.releaseMicrophone();
			throw error;
		});
	}

	releaseMicrophone(): void {
		this.micConsumers = Math.max(0, this.micConsumers - 1);
		if (this.micConsumers === 0) {
			this.stopMicrophoneTracks();
		}
	}

	peekMicrophone(): MediaStream | null {
		if (this.micStream !== null && this.isStreamLive(this.micStream)) {
			return this.micStream;
		}
		return null;
	}

	resetForTests(): void {
		if (this.context !== null) {
			this.context.close?.().catch?.(() => {});
		}
		this.context = null;
		this.unlockCallbacks.clear();
		this.micStream = null;
		this.micRequest = null;
		this.micConsumers = 0;
	}

	private stopMicrophoneTracks(): void {
		if (this.micStream === null) {
			return;
		}
		for (const track of this.micStream.getTracks()) {
			track.stop();
		}
		this.micStream = null;
	}

	private isStreamLive(stream: MediaStream): boolean {
		const tracks = stream.getAudioTracks();
		return tracks.length > 0 && tracks.some((track) => track.readyState === "live");
	}

	private installGestureListeners(): void {
		if (this.gestureListenersInstalled || typeof document === "undefined") {
			return;
		}
		this.gestureListenersInstalled = true;
		const handleGesture = () => {
			if (this.unlockCallbacks.size === 0) {
				return;
			}
			void this.requestUnlock();
		};
		for (const eventName of GESTURE_EVENTS) {
			document.addEventListener(eventName, handleGesture, {
				capture: true,
				passive: true,
			});
		}
	}

	private notifyUnlocked(): void {
		const callbacks = Array.from(this.unlockCallbacks);
		this.unlockCallbacks.clear();
		for (const callback of callbacks) {
			callback();
		}
	}
}

export const audioBroker = new AudioBroker();

export function resetAudioBrokerForTests(): void {
	audioBroker.resetForTests();
}
