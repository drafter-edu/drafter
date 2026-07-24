import { DrafterHTMLElement } from "./drafterHTMLElement";
import { DRAFTER_PAGE_LOADED_EVENT } from "./events";

type TimerState = "running" | "finished" | "paused";
type ClockState = "running" | "paused";

const DEFAULT_RATE = 1000;
const DEFAULT_DURATION = 1000;

/**
 * Attribute the parking machinery (drafter.bridge.persistence) uses to select
 * elements that survive simulated page reloads. Mirrors PERSIST_FLAG_ATTR in
 * src/drafter/components/utilities/persistence.py.
 */
const PERSIST_FLAG_ATTR = "data-drafter-persistent";

/**
 * Whether the drafter-page-loaded event has already fired for the view that
 * is currently in the DOM. Tracked at module level (with a listener that is
 * registered at import time) so a timer or clock inserted into an
 * already-loaded page can start right away instead of waiting for a
 * page-loaded event that will never come. The flag is cleared when a timer
 * or clock is genuinely torn down (a real disconnect, not a persistence
 * move), which is what happens to a view's elements when navigation replaces
 * the page content — the next view's elements then wait for their own
 * page-loaded event.
 */
let pageLoadedForCurrentView = false;
window.addEventListener(DRAFTER_PAGE_LOADED_EVENT, () => {
	pageLoadedForCurrentView = true;
});

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
	private waitingForPageLoad = false;
	private startFallbackId: number | null = null;

	private handlePageLoaded = (_event: Event): void => {
		if (!this.isConnected || !this.waitingForPageLoad) {
			return;
		}

		this.waitingForPageLoad = false;
		this.beginRunning();
	};

	private formatTime(ms: number): string {
		const totalSeconds = Math.ceil(ms / 1000);
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

		if (this.startFallbackId !== null) {
			window.clearTimeout(this.startFallbackId);
			this.startFallbackId = null;
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

	private waitForPageLoadThenStart(): void {
		this.waitingForPageLoad = true;
		this.startedAt = null;
		this.clearTimers();
		this.updateDisplay();
		this.updateControls();
	}

	private startSoon(): void {
		// The current view has already loaded, so no page-loaded event is
		// guaranteed to arrive and start this element (it was inserted into
		// an already-loaded page). Start on the next task instead of
		// synchronously: an element inserted while a new page render is
		// still in progress may be replaced by its parked persistent twin
		// (or receive the new view's page-loaded event) first, and must not
		// tick mid-render. The fallback is cancelled by clearTimers on
		// disconnect, restart, or an earlier page-loaded start.
		this.waitingForPageLoad = true;
		this.startedAt = null;
		this.updateDisplay();
		this.updateControls();
		this.startFallbackId = window.setTimeout(() => {
			this.startFallbackId = null;
			if (this.waitingForPageLoad) {
				this.waitingForPageLoad = false;
				this.beginRunning();
			}
		}, 0);
	}

	private syncPersistenceFlag(): void {
		// Parking (drafter.bridge.persistence) selects the elements that
		// survive page reloads via the data-drafter-persistent attribute;
		// keep it in sync so runtime changes to `persistent` gate parking.
		// A persistence change must not restart the running timer.
		if (this.isPersistent()) {
			this.setAttribute(PERSIST_FLAG_ATTR, "true");
		} else {
			this.removeAttribute(PERSIST_FLAG_ATTR);
		}
	}

	private initializeTimer(startImmediately: boolean): void {
		this.clearTimers();

		this.resetState();

		this.renderStructure();
		if (this.state === "running") {
			if (!pageLoadedForCurrentView) {
				this.waitForPageLoadThenStart();
			} else if (startImmediately) {
				this.beginRunning();
			} else {
				this.startSoon();
			}
		} else {
			this.updateDisplay();
			this.updateControls();
		}
	}

	connectedCallback() {
		if (this.isMovingBetweenParents()) {
			// Persistence move in progress: keep running state untouched.
			return;
		}
		window.addEventListener(
			DRAFTER_PAGE_LOADED_EVENT,
			this.handlePageLoaded,
		);
		this.initializeTimer(false);
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

		if (name === "persistent") {
			this.syncPersistenceFlag();
			return;
		}

		this.initializeTimer(true);
	}

	disconnectedCallback() {
		if (this.isMovingBetweenParents()) {
			// Persistence move in progress: keep running state untouched.
			return;
		}
		// A real teardown, which is what happens to a view's elements when
		// navigation replaces the page content: the next view must wait for
		// its own page-loaded event.
		pageLoadedForCurrentView = false;
		window.removeEventListener(
			DRAFTER_PAGE_LOADED_EVENT,
			this.handlePageLoaded,
		);
		this.clearTimers();
		this.waitingForPageLoad = false;
		this.label = null;
		this.toggleButton = null;
		this.restartButton = null;
	}
}

class DrafterClock extends DrafterHTMLElement {
	static get observedAttributes() {
		return ["interval", "show", "controls", "persistent"];
	}

	private state: ClockState = "running";
	private intervalId: number | null = null;
	private startedAt: number | null = null;
	private elapsedMs = 0;
	private label: HTMLSpanElement | null = null;
	private toggleButton: HTMLButtonElement | null = null;
	private restartButton: HTMLButtonElement | null = null;
	private waitingForPageLoad = false;
	private startFallbackId: number | null = null;

	private handlePageLoaded = (_event: Event): void => {
		if (!this.isConnected || !this.waitingForPageLoad) {
			return;
		}

		this.waitingForPageLoad = false;
		this.beginRunning();
	};

	private formatTime(ms: number): string {
		const totalSeconds = Math.floor(ms / 1000);
		const minutes = Math.floor(totalSeconds / 60);
		const seconds = totalSeconds % 60;
		return `${minutes}:${seconds.toString().padStart(2, "0")}`;
	}

	private getInterval(): number {
		return Math.max(this.getNumberAttribute("interval", DEFAULT_RATE), 1);
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

	private clearIntervalTimer(): void {
		if (this.intervalId !== null) {
			window.clearInterval(this.intervalId);
			this.intervalId = null;
		}

		if (this.startFallbackId !== null) {
			window.clearTimeout(this.startFallbackId);
			this.startFallbackId = null;
		}
	}

	private computeElapsedMs(): number {
		if (this.state !== "running" || this.startedAt === null) {
			return this.elapsedMs;
		}

		return this.elapsedMs + (Date.now() - this.startedAt);
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
		this.elapsedMs = 0;
	}

	private emitTick(elapsed = this.computeElapsedMs()): void {
		this.dispatchEvent(
			new CustomEvent("tick", {
				detail: {
					elapsed,
					interval: this.getInterval(),
				},
			}),
		);
	}

	private updateDisplay(): void {
		if (this.label === null) {
			return;
		}

		this.label.textContent = this.formatTime(this.computeElapsedMs());
	}

	private updateControls(): void {
		if (this.toggleButton !== null) {
			this.toggleButton.textContent =
				this.state === "running" ? "⏸" : "▶";
			this.toggleButton.setAttribute(
				"aria-label",
				this.state === "running" ? "Pause clock" : "Resume clock",
			);
		}

		if (this.restartButton !== null) {
			this.restartButton.setAttribute("aria-label", "Restart clock");
		}
	}

	private handleIntervalTick(): void {
		if (this.state !== "running") {
			return;
		}

		this.updateDisplay();
		this.emitTick();
	}

	private beginRunning(): void {
		this.clearIntervalTimer();
		this.state = "running";
		this.startedAt = Date.now();
		this.intervalId = window.setInterval(() => {
			this.handleIntervalTick();
		}, this.getInterval());
		this.updateDisplay();
		this.updateControls();
		this.emitTick();
	}

	private pause(): void {
		if (this.state !== "running") {
			return;
		}

		this.elapsedMs = this.computeElapsedMs();
		this.state = "paused";
		this.startedAt = null;
		this.clearIntervalTimer();
		this.updateDisplay();
		this.updateControls();
	}

	private resume(): void {
		this.beginRunning();
	}

	private toggleRunningState(): void {
		if (this.state === "running") {
			this.pause();
		} else {
			this.resume();
		}
	}

	private restart(): void {
		this.clearIntervalTimer();
		this.resetState();
		this.beginRunning();
	}

	private waitForPageLoadThenStart(): void {
		this.waitingForPageLoad = true;
		this.startedAt = null;
		this.clearIntervalTimer();
		this.updateDisplay();
		this.updateControls();
	}

	private startSoon(): void {
		// See Timer.startSoon: the current view has already loaded, so start
		// on the next task rather than synchronously, letting persistence
		// adoption (or the new view's page-loaded event) win first. The
		// fallback is cancelled by clearIntervalTimer on disconnect,
		// restart, or an earlier page-loaded start.
		this.waitingForPageLoad = true;
		this.startedAt = null;
		this.updateDisplay();
		this.updateControls();
		this.startFallbackId = window.setTimeout(() => {
			this.startFallbackId = null;
			if (this.waitingForPageLoad) {
				this.waitingForPageLoad = false;
				this.beginRunning();
			}
		}, 0);
	}

	private syncPersistenceFlag(): void {
		// Parking (drafter.bridge.persistence) selects the elements that
		// survive page reloads via the data-drafter-persistent attribute;
		// keep it in sync so runtime changes to `persistent` gate parking.
		// A persistence change must not restart the running clock.
		if (this.isPersistent()) {
			this.setAttribute(PERSIST_FLAG_ATTR, "true");
		} else {
			this.removeAttribute(PERSIST_FLAG_ATTR);
		}
	}

	private initializeClock(startImmediately: boolean): void {
		this.clearIntervalTimer();

		this.resetState();

		this.renderStructure();
		if (this.state === "running") {
			if (!pageLoadedForCurrentView) {
				this.waitForPageLoadThenStart();
			} else if (startImmediately) {
				this.beginRunning();
			} else {
				this.startSoon();
			}
		} else {
			this.updateDisplay();
			this.updateControls();
		}
	}

	connectedCallback() {
		if (this.isMovingBetweenParents()) {
			// Persistence move in progress: keep running state untouched.
			return;
		}
		window.addEventListener(
			DRAFTER_PAGE_LOADED_EVENT,
			this.handlePageLoaded,
		);
		this.initializeClock(false);
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

		if (name === "persistent") {
			this.syncPersistenceFlag();
			return;
		}

		this.initializeClock(true);
	}

	disconnectedCallback() {
		if (this.isMovingBetweenParents()) {
			// Persistence move in progress: keep running state untouched.
			return;
		}
		// A real teardown, which is what happens to a view's elements when
		// navigation replaces the page content: the next view must wait for
		// its own page-loaded event.
		pageLoadedForCurrentView = false;
		window.removeEventListener(
			DRAFTER_PAGE_LOADED_EVENT,
			this.handlePageLoaded,
		);
		this.clearIntervalTimer();
		this.waitingForPageLoad = false;
		this.label = null;
		this.toggleButton = null;
		this.restartButton = null;
	}
}

customElements.define("drafter-timer", Timer);
customElements.define("drafter-clock", DrafterClock);
