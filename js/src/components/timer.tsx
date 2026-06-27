import { getHandlers } from "./utils";

class Timer extends HTMLElement {
	DEFAULT_RATE = 1000;
	DEFAULT_DURATION = 1000;
	DEFAULT_LABEL = "⏰";

	static get observedAttributes() {
		return ["duration", "rate"];
	}
	private state: "running" | "finished" | "paused" = "running";
	private timerId: number | null = null;
	private intervalId: number | null = null;
	private tick: number = 0;

	constructor() {
		super();
	}

	private formatTime(ms: number): string {
		const totalSeconds = Math.floor(ms / 1000);
		const minutes = Math.floor(totalSeconds / 60);
		const seconds = totalSeconds % 60;
		return `${minutes}:${seconds.toString().padStart(2, "0")}`;
	}

	connectedCallback() {
		console.log("Timer connected");

		// Get the duration and rate
		const duration = parseInt(
			this.getAttribute("duration") || `${this.DEFAULT_DURATION}`,
			10,
		);
		const rate = parseInt(
			this.getAttribute("rate") || `${this.DEFAULT_RATE}`,
			10,
		);

		const handlers = getHandlers(this);

		// Get whether there are controls
		const hasControls = this.hasAttribute("controls");

		// Create the timer label
		const label = document.createElement("span");
		if (handlers["tick"]) {
			this.dispatchEvent(
				new CustomEvent("tick", {
					detail: {
						remaining: duration,
						duration: duration,
					},
				}),
			);
		} else {
			label.textContent = this.formatTime(duration);
		}
		this.appendChild(label);

		if (hasControls) {
			const pauseButton = document.createElement("button");
			pauseButton.textContent = "⏸";
			pauseButton.addEventListener("click", () => {
				if (this.state === "running") {
					this.state = "paused";
					if (this.timerId !== null) {
						clearTimeout(this.timerId);
						this.timerId = null;
					}
				} else if (this.state === "paused") {
					this.state = "running";
					const remaining = Math.max(duration - this.tick * rate, 0);
					this.timerId = window.setTimeout(() => {
						this.state = "finished";
						console.log("Timer finished");
						this.dispatchEvent(
							new CustomEvent("finish", { detail: { duration } }),
						);
					}, remaining);
				}
			});
			this.appendChild(pauseButton);
		}

		// Start the timer
		this.timerId = window.setTimeout(() => {
			this.state = "finished";
			//label.textContent = this.DEFAULT_LABEL;
			console.log("Timer finished");
			this.dispatchEvent(
				new CustomEvent("finish", { detail: { duration } }),
			);
			if (hasControls) {
				// Add restart button
				const restartButton = document.createElement("button");
				restartButton.textContent = "🔄";
				restartButton.addEventListener("click", () => {
					this.state = "running";
					this.tick = 0;
					label.textContent = this.formatTime(duration);
					this.timerId = window.setTimeout(() => {
						this.state = "finished";
						console.log("Timer finished");
						this.dispatchEvent(
							new CustomEvent("finish", { detail: { duration } }),
						);
					}, duration);
				});
				this.appendChild(restartButton);
			}
		}, duration);
		// Start the interval
		this.intervalId = window.setInterval(() => {
			console.log("Interval:", duration, rate, duration - rate);
			if (this.state === "finished") {
				clearInterval(this.intervalId!);
				this.intervalId = null;
			} else {
				this.tick += 1;
				if (handlers["tick"]) {
					this.dispatchEvent(
						new CustomEvent("tick", {
							detail: {
								remaining: Math.max(
									duration - this.tick * rate,
									0,
								),
								duration: duration,
							},
						}),
					);
				} else {
					label.textContent = this.formatTime(
						Math.max(duration - this.tick * rate, 0),
					);
				}
			}
		}, rate);
	}

	disconnectedCallback() {
		if (this.timerId !== null) {
			clearTimeout(this.timerId);
			this.timerId = null;
		}
		if (this.intervalId !== null) {
			clearInterval(this.intervalId);
			this.intervalId = null;
		}
	}
}

customElements.define("drafter-timer", Timer);
