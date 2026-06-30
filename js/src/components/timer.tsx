import { DrafterHTMLElement } from "./drafterHTMLElement";

type TimerState = "running" | "finished" | "paused";

type PersistedTimerState = {
	duration: number;
	rate: number;
	remainingMs: number;
	state: TimerState;
};

const DEFAULT_RATE = 1000;
const DEFAULT_DURATION = 1000;
const persistedTimers = new Map<string, PersistedTimerState>();

class Timer extends DrafterHTMLElement {
	static get observedAttributes() {
		return ["duration", "rate", "show", "controls", "persistent"];
	}

	private state: TimerState = "running";
	private timerId: number | null = null;
	private intervalId: number | null = null;
	private startedAt: number | null = null;
	private remainingMs = DEFAULT_DURATION;
	private label: HTMLSpanElement | null = null;
	private toggleButton: HTMLButtonElement | null = null;
	private restartButton: HTMLButtonElement | null = null;

	private formatTime(ms: number): string {
		const totalSeconds = Math.floor(ms / 1000);
		const minutes = Math.floor(totalSeconds / 60);
		const seconds = totalSeconds % 60;
		return `${minutes}:${seconds.toString().padStart(2, "0")}`;
	}

	private getDuration(): number {
		return this.getNumberAttribute("duration", DEFAULT_DURATION);
	}

	private getRate(): number {
		return Math.max(this.getNumberAttribute("rate", DEFAULT_RATE), 1);
	}

	private shouldShow(): boolean {
		return this.getBooleanAttribute("show", true);
	}

	private hasControls(): boolean {
		return this.getBooleanAttribute("controls", false);
	}

	private isPersistent(): boolean {
		return this.getBooleanAttribute("persistent", false);
	}

	private clearTimers(): void {
		if (this.timerId !== null) {
			window.clearTimeout(this.timerId);
			this.timerId = null;
		}

		if (this.intervalId !== null) {
			window.clearInterval(this.intervalId);
			this.intervalId = null;
		}
	}

	private computeRemainingMs(): number {
		if (this.state !== "running" || this.startedAt === null) {
			return this.remainingMs;
		}

		return Math.max(this.remainingMs - (Date.now() - this.startedAt), 0);
	}

	private syncVisibility(): void {
		this.hidden = !this.shouldShow();
	}

	private renderStructure(): void {
		const label = document.createElement("span");
		const children: Node[] = [label];

		this.label = label;
		this.toggleButton = null;
		this.restartButton = null;

		if (this.hasControls()) {
			const toggleButton = document.createElement("button");
			toggleButton.type = "button";
			toggleButton.addEventListener("click", () => {
				this.toggleRunningState();
			});

			const restartButton = document.createElement("button");
			restartButton.type = "button";
			restartButton.textContent = "🔄";
			restartButton.addEventListener("click", () => {
				this.restart();
			});

			this.toggleButton = toggleButton;
			this.restartButton = restartButton;
			children.push(toggleButton, restartButton);
		}

		this.replaceChildren(...children);
		this.syncVisibility();
		this.updateDisplay();
		this.updateControls();
	}

	private resetState(): void {
		this.state = "running";
		this.startedAt = null;
		this.remainingMs = this.getDuration();
	}

	private emitTick(remaining = this.computeRemainingMs()): void {
		this.dispatchEvent(
			new CustomEvent("tick", {
				detail: {
					remaining,
					duration: this.getDuration(),
				},
			}),
		);
	}

	private emitFinish(): void {
		this.dispatchEvent(
			new CustomEvent("finish", {
				detail: {
					remaining: 0,
					duration: this.getDuration(),
				},
			}),
		);
	}

	private updateDisplay(): void {
		if (this.label === null) {
			return;
		}

		this.label.textContent = this.formatTime(this.computeRemainingMs());
	}

	private updateControls(): void {
		if (this.toggleButton !== null) {
			this.toggleButton.textContent =
				this.state === "running" ? "⏸" : "▶";
			this.toggleButton.setAttribute(
				"aria-label",
				this.state === "running" ? "Pause timer" : "Resume timer",
			);
		}

		if (this.restartButton !== null) {
			this.restartButton.setAttribute("aria-label", "Restart timer");
		}
	}

	private handleIntervalTick(): void {
		if (this.state !== "running") {
			return;
		}

		const remaining = this.computeRemainingMs();
		if (remaining <= 0) {
			this.finish();
			return;
		}

		this.updateDisplay();
		this.emitTick(remaining);
	}

	private beginRunning(): void {
		this.clearTimers();
		if (this.remainingMs <= 0) {
			this.finish();
			return;
		}

		this.state = "running";
		this.startedAt = Date.now();
		this.timerId = window.setTimeout(() => {
			this.finish();
		}, this.remainingMs);
		this.intervalId = window.setInterval(() => {
			this.handleIntervalTick();
		}, this.getRate());
		this.updateDisplay();
		this.updateControls();
		this.emitTick();
	}

	private pause(): void {
		if (this.state !== "running") {
			return;
		}

		this.remainingMs = this.computeRemainingMs();
		this.state = "paused";
		this.startedAt = null;
		this.clearTimers();
		this.updateDisplay();
		this.updateControls();
	}

	private resume(): void {
		if (this.state === "finished") {
			this.restart();
			return;
		}

		this.beginRunning();
	}

	private toggleRunningState(): void {
		if (this.state === "running") {
			this.pause();
		} else {
			this.resume();
		}
	}

	private finish(): void {
		if (this.state === "finished") {
			return;
		}

		this.clearTimers();
		this.state = "finished";
		this.startedAt = null;
		this.remainingMs = 0;
		this.updateDisplay();
		this.updateControls();
		this.emitTick(0);
		this.emitFinish();
	}

	private restart(): void {
		this.clearTimers();
		this.resetState();
		this.beginRunning();
	}

	private initializeTimer(preferPersistedState: boolean): void {
		this.clearTimers();

		this.resetState();

		this.renderStructure();
		if (this.state === "running") {
			this.beginRunning();
		} else {
			this.updateDisplay();
			this.updateControls();
		}
	}

	connectedCallback() {
		this.initializeTimer(true);
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

		if (name === "controls") {
			this.renderStructure();
			return;
		}

		this.initializeTimer(false);
	}

	disconnectedCallback() {
		this.clearTimers();
		this.label = null;
		this.toggleButton = null;
		this.restartButton = null;
	}
}

customElements.define("drafter-timer", Timer);
