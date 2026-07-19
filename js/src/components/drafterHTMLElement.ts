const DRAFTER_EVENT_HANDLER = "data--drafter-handlers";

export class DrafterHTMLElement extends HTMLElement {
	private drafterMoving = false;

	/**
	 * Called by the bridge before reparenting this element (persistence
	 * parking/adoption) in browsers without Element.moveBefore. While the
	 * move is in progress, connected/disconnected callbacks must not tear
	 * down or reset the element's running state.
	 */
	public _drafterBeginMove(): void {
		this.drafterMoving = true;
	}

	public _drafterEndMove(): void {
		this.drafterMoving = false;
	}

	protected isMovingBetweenParents(): boolean {
		return this.drafterMoving;
	}

	/**
	 * Atomic moves (Element.moveBefore) invoke this instead of the
	 * disconnected/connected pair; an empty body means all running state
	 * (timers, listeners, playback) is preserved through the move.
	 */
	connectedMoveCallback(): void {}

	protected getHandlers(): Record<string, string> {
		const handlers = this.getAttribute(DRAFTER_EVENT_HANDLER);
		return handlers ? JSON.parse(handlers) : {};
	}

	protected getNumberAttribute(name: string, defaultValue: number): number {
		const rawValue = this.getAttribute(name);
		const parsedValue =
			rawValue === null ? defaultValue : parseInt(rawValue, 10);
		if (!Number.isFinite(parsedValue)) {
			return defaultValue;
		}

		return Math.max(parsedValue, 0);
	}

	protected getBooleanAttribute(
		name: string,
		defaultValue: boolean,
	): boolean {
		const rawValue = this.getAttribute(name);
		if (rawValue === null) {
			return defaultValue;
		}

		const normalizedValue = rawValue.trim().toLowerCase();
		if (normalizedValue === "" || normalizedValue === name.toLowerCase()) {
			return true;
		}
		if (["false", "0", "no", "off", "none"].includes(normalizedValue)) {
			return false;
		}
		if (["true", "1", "yes", "on"].includes(normalizedValue)) {
			return true;
		}

		return defaultValue;
	}
}
