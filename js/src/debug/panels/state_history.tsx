import { Panel } from "./panel";
import type { SpecificRepresentation } from "../telemetry/state";
import { renderRepresentation } from "./state";

/**
 * The State History panel keeps a timeline of every state snapshot the
 * server reports (one per UpdatedState event), newest first, so students
 * can see how their state evolved across page visits. Each entry expands
 * into the same rich typed rendering the Current State panel uses.
 */
export class StateHistoryPanel extends Panel {
	private entryCount = 0;
	/** Oldest entries are dropped beyond this bound to keep the DOM light. */
	private readonly maxEntries = 50;

	constructor(containerId: string, instanceId: number, root: ParentNode = document) {
		super(
			containerId,
			instanceId,
			"drafter-debug-state-history",
			"State History",
			root,
		);
	}

	protected get initialContent() {
		return (
			<div>
				<div class="drafter-debug-state-history-empty">
					No state updates yet.
				</div>
				<div
					class={`drafter-debug-state-history-list drafter-debug-state-history-list-${this.instanceId}`}
				></div>
			</div>
		);
	}

	private getListElement(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-state-history-list"),
			"DebugPanel: State history list not found.",
		);
	}

	/** Record one state snapshot (newest first). */
	public addSnapshot(
		representation: SpecificRepresentation,
		route: string = "",
	): void {
		this.entryCount++;
		const empty = this.getContentElement().querySelector(
			".drafter-debug-state-history-empty",
		);
		empty?.remove();

		const time = new Date().toLocaleTimeString();
		const entry = (
			<details class="drafter-debug-state-history-entry">
				<summary>
					#{this.entryCount}
					{route ? ` after ${route}` : ""} at {time}
				</summary>
				{renderRepresentation(representation)}
			</details>
		);

		const list = this.getListElement();
		list.prepend(entry);
		while (list.children.length > this.maxEntries) {
			list.lastElementChild?.remove();
		}
	}

	public getEntryCount(): number {
		return this.entryCount;
	}
}
