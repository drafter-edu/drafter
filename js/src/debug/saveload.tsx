import { showDialog } from "../dialogs";
import { t } from "../i18n";
import { getConfigurationOverridesStorageKey } from "../config_overrides";
import { appStorageKey } from "../storage_keys";
import type { StateSnapshotEvent } from "./telemetry/snapshot";

/**
 * Name of the snapshot slots within an app's stored values (see
 * storage_keys.ts); the slot name follows. Slots saved before they were
 * kept per app live under `drafter.debug.snapshot.v1.*`. Those are not
 * read here, because nothing says which app saved them, but they remain in
 * storage and the Browser Storage section still lists them.
 */
const SNAPSHOT_STORAGE_NAME = "debug.snapshot.v2.";
const MOST_RECENT_SLOT_KEY = "most-recent";
export const QUICK_SLOT = "quick";
export const SLOT_COUNT = 10;

/** The JSON shape stored in localStorage slots and downloaded files. */
export interface StoredSnapshot {
	kind: "drafter-state-snapshot";
	version: number;
	created: string;
	route: string;
	kwargs_json: string;
	/**
	 * JSON-encoded plain data of the saved state (opaque to JS): the state
	 * as it was when saving, after `route` ran.
	 */
	state_json: string;
	/**
	 * The state as it was just before `route` ran, encoded the same way.
	 * Loading restores this one, so that running the route again arrives at
	 * the saved page rather than one step past it. Absent from snapshots
	 * saved in format version 1 (and from later ones whose earlier state
	 * could not be captured); those load from `state_json` as they always
	 * did.
	 */
	state_before_json?: string;
	/** The state's class name at save time (labels/diagnostics). */
	state_type: string;
	app_title: string;
}

function slotNames(): string[] {
	return [
		QUICK_SLOT,
		...Array.from({ length: SLOT_COUNT }, (_, i) => `slot-${i + 1}`),
	];
}

function slotLabel(slot: string): string {
	return slot === QUICK_SLOT
		? t("saveload.quick_slot")
		: `${t("saveload.slot")} ${slot.replace("slot-", "")}`;
}

/** Student-friendly "how long ago" description of an ISO timestamp. */
export function formatRelativeTime(
	isoTimestamp: string,
	now: Date = new Date(),
): string | null {
	const then = new Date(isoTimestamp);
	if (isNaN(then.getTime())) {
		return null;
	}
	const seconds = Math.max(0, (now.getTime() - then.getTime()) / 1000);
	if (seconds < 60) {
		return t("time.just_now");
	}
	const minutes = Math.floor(seconds / 60);
	if (minutes < 60) {
		return t("time.minutes_ago", { n: minutes });
	}
	const hours = Math.floor(minutes / 60);
	if (hours < 24) {
		return t("time.hours_ago", { n: hours });
	}
	return t("time.days_ago", { n: Math.floor(hours / 24) });
}

function safeGetItem(key: string): string | null {
	try {
		return window.localStorage.getItem(key);
	} catch {
		return null;
	}
}

function safeSetItem(key: string, value: string): boolean {
	try {
		window.localStorage.setItem(key, value);
		return true;
	} catch {
		return false;
	}
}

/** Parse and validate a stored snapshot; null when absent or malformed. */
export function parseStoredSnapshot(raw: string | null): StoredSnapshot | null {
	if (!raw) {
		return null;
	}
	try {
		const parsed = JSON.parse(raw) as StoredSnapshot;
		if (
			parsed &&
			parsed.kind === "drafter-state-snapshot" &&
			typeof parsed.version === "number" &&
			typeof parsed.state_json === "string" &&
			parsed.state_json.length > 0 &&
			typeof parsed.route === "string"
		) {
			return parsed;
		}
	} catch {
		// Malformed JSON — treat as absent.
	}
	return null;
}

/** Trigger a JSON file download (no-op in environments without Blob URLs). */
export function downloadJson(filename: string, payload: unknown): void {
	if (typeof URL === "undefined" || !URL.createObjectURL) {
		console.warn("Downloads are not supported in this environment.");
		return;
	}
	const blob = new Blob([JSON.stringify(payload, null, 2)], {
		type: "application/json",
	});
	const url = URL.createObjectURL(blob);
	const anchor = (
		<a href={url} download={filename} hidden></a>
	) as HTMLAnchorElement;
	document.body.appendChild(anchor);
	anchor.click();
	anchor.remove();
	URL.revokeObjectURL(url);
}

/** Close the dialog that contains `element` (used by slot-row buttons). */
function closeContainingDialog(element: HTMLElement): void {
	const closeButton = element
		.closest(".drafter-dialog")
		?.querySelector(".drafter-dialog-close") as HTMLButtonElement | null;
	closeButton?.click();
}

/**
 * Owns the Save/Load menu behaviors: requesting snapshots from Python
 * (drafter-save-state), storing them in localStorage slots (quick + 10
 * named), downloading/uploading them as files, and asking Python to
 * restore one (drafter-load-state).
 *
 * Save is Python-authoritative: the menu dispatches drafter-save-state,
 * Python reduces the state to plain JSON data and publishes StateSnapshot
 * telemetry, and handleSnapshot() (called from DebugPanel.handleEvent)
 * completes the store/download here.
 *
 * The slots belong to one app: their keys carry the app's storage scope
 * (page address and main file, see storage_keys.ts), so two programs
 * served at the same address do not see each other's saves.
 */
export class SaveLoadManager {
	private readonly keyPrefix: string;

	/**
	 * @param storageWindow The window the app renders into, which decides
	 *   whose slots these are (an embedded instance passes its iframe's
	 *   window).
	 */
	constructor(storageWindow: Window = window) {
		this.keyPrefix = appStorageKey(SNAPSHOT_STORAGE_NAME, storageWindow);
	}

	/** The localStorage key of a slot (or of the most-recent pointer). */
	private slotKey(slot: string): string {
		return this.keyPrefix + slot;
	}

	/** Ask Python to capture the current state + route invocation. */
	public requestSave(reason: "save" | "download", slot: string): void {
		window.dispatchEvent(
			new CustomEvent("drafter-save-state", {
				detail: { reason, slot },
			}),
		);
	}

	/** Complete a snapshot round-trip (called for StateSnapshot telemetry). */
	public handleSnapshot(event: StateSnapshotEvent): void {
		const stored: StoredSnapshot = {
			kind: "drafter-state-snapshot",
			version: event.version,
			created: new Date().toISOString(),
			route: event.route,
			kwargs_json: event.kwargs_json,
			state_json: event.state_json,
			state_type: event.state_type,
			app_title: event.app_title,
		};
		if (event.state_before_json) {
			stored.state_before_json = event.state_before_json;
		}
		if (event.reason === "download") {
			const stamp = stored.created.replace(/[:.]/g, "-");
			downloadJson(`drafter-snapshot-${event.route}-${stamp}.json`, stored);
			return;
		}
		if (safeSetItem(this.slotKey(event.slot), JSON.stringify(stored))) {
			safeSetItem(this.slotKey(MOST_RECENT_SLOT_KEY), event.slot);
		}
	}

	public getSlot(slot: string): StoredSnapshot | null {
		return parseStoredSnapshot(safeGetItem(this.slotKey(slot)));
	}

	public getMostRecentSlot(): string | null {
		const slot = safeGetItem(this.slotKey(MOST_RECENT_SLOT_KEY));
		return slot && this.getSlot(slot) ? slot : null;
	}

	/**
	 * How long ago the most recent save happened (e.g. "5 minutes ago"),
	 * or null when nothing has been saved — drives the Save/Load menu's
	 * "Load Most Recent (…)" suffix and its greyed-out state.
	 */
	public describeMostRecentAge(): string | null {
		const slot = this.getMostRecentSlot();
		if (!slot) {
			return null;
		}
		const snapshot = this.getSlot(slot);
		return snapshot ? formatRelativeTime(snapshot.created) : null;
	}

	/**
	 * Ask Python to restore a snapshot's state and replay its route. A
	 * snapshot that carries the state from before its route ran sends it
	 * along; Python then restores that earlier state, the way the Back
	 * button does. Without it (an older snapshot), Python restores
	 * `state_json` and runs the route on top of it, as it always did.
	 */
	public dispatchLoad(snapshot: StoredSnapshot): void {
		const detail: {
			state_json: string;
			route: string;
			kwargs_json: string;
			state_before_json?: string;
		} = {
			state_json: snapshot.state_json,
			route: snapshot.route,
			kwargs_json: snapshot.kwargs_json,
		};
		if (
			typeof snapshot.state_before_json === "string" &&
			snapshot.state_before_json.length > 0
		) {
			detail.state_before_json = snapshot.state_before_json;
		}
		window.dispatchEvent(new CustomEvent("drafter-load-state", { detail }));
	}

	public loadSlot(slot: string): boolean {
		const snapshot = this.getSlot(slot);
		if (!snapshot) {
			return false;
		}
		this.dispatchLoad(snapshot);
		return true;
	}

	public loadMostRecent(): boolean {
		const slot = this.getMostRecentSlot();
		if (!slot) {
			void showDialog({
				title: t("saveload.load_dialog.title"),
				content: t("saveload.nothing_saved"),
				buttons: [{ label: t("saveload.close"), variant: "primary" }],
			});
			return false;
		}
		return this.loadSlot(slot);
	}

	private describeSlot(slot: string): string {
		const snapshot = this.getSlot(slot);
		if (!snapshot) {
			return t("saveload.slot_empty");
		}
		const created = new Date(snapshot.created);
		const when = isNaN(created.getTime())
			? snapshot.created
			: created.toLocaleString();
		return `${snapshot.route} — ${when}`;
	}

	/** Dialog listing every slot with a Save button per row. */
	public openSaveDialog(): void {
		void showDialog({
			title: t("saveload.save_dialog.title"),
			content: this.createSlotList((slot) =>
				this.requestSave("save", slot),
			),
			width: "420px",
			buttons: [{ label: t("saveload.close"), variant: "secondary" }],
		});
	}

	/** Dialog listing the filled slots with a Load button per row. */
	public openLoadDialog(): void {
		void showDialog({
			title: t("saveload.load_dialog.title"),
			content: this.createSlotList(
				(slot) => this.loadSlot(slot),
				/* onlyFilled= */ true,
			),
			width: "420px",
			buttons: [{ label: t("saveload.close"), variant: "secondary" }],
		});
	}

	private createSlotList(
		onPick: (slot: string) => void,
		onlyFilled: boolean = false,
	): HTMLElement {
		const list = (
			<div class="drafter-saveload-slots"></div>
		) as HTMLDivElement;
		let anyRow = false;
		slotNames().forEach((slot) => {
			const filled = this.getSlot(slot) !== null;
			if (onlyFilled && !filled) {
				return;
			}
			anyRow = true;
			const pick = (
				<button
					type="button"
					class={`drafter-saveload-slot drafter-saveload-slot-${slot}`}
				>
					<span class="drafter-saveload-slot-name">
						{slotLabel(slot)}
					</span>
					<span class="drafter-saveload-slot-meta">
						{this.describeSlot(slot)}
					</span>
				</button>
			) as HTMLButtonElement;
			pick.addEventListener("click", () => {
				onPick(slot);
				closeContainingDialog(pick);
			});
			list.appendChild(pick);
		});
		if (!anyRow) {
			list.appendChild(
				(
					<p class="drafter-saveload-empty">
						{t("saveload.nothing_saved")}
					</p>
				) as HTMLElement,
			);
		}
		return list;
	}

	/** Dialog with a file input for restoring a downloaded snapshot. */
	public openUploadDialog(): void {
		const errorMessage = (
			<p class="drafter-saveload-upload-error" hidden></p>
		) as HTMLParagraphElement;
		const input = (
			<input type="file" accept="application/json,.json" />
		) as HTMLInputElement;
		const container = (
			<div class="drafter-saveload-upload">
				<p>{t("saveload.upload.instructions")}</p>
				{input}
				{errorMessage}
			</div>
		) as HTMLDivElement;

		input.addEventListener("change", () => {
			const file = input.files?.[0];
			if (!file) {
				return;
			}
			const reader = new FileReader();
			reader.onload = () => {
				const snapshot = parseStoredSnapshot(String(reader.result));
				if (!snapshot) {
					errorMessage.textContent = t("saveload.upload.invalid");
					errorMessage.hidden = false;
					return;
				}
				this.dispatchLoad(snapshot);
				closeContainingDialog(container);
			};
			reader.readAsText(file);
		});

		void showDialog({
			title: t("saveload.upload.title"),
			content: container,
			width: "420px",
			buttons: [{ label: t("saveload.close"), variant: "secondary" }],
		});
	}
}

/** Extra context the debug panel knows and the bug report should carry. */
export interface BugReportContext {
	/** The route currently shown, if any. */
	route?: string | null;
	/** The generated HTML of the current page, if any. */
	pageHtml?: string | null;
	/** The student's source code, if the engine exposes it. */
	sourceCode?: string | null;
}

/** Names and sizes of Drafter's own localStorage entries (no values —
 * saved states may contain personal data students didn't mean to share). */
function describeDrafterStorage(): Array<{ key: string; size: number }> {
	const entries: Array<{ key: string; size: number }> = [];
	try {
		for (let i = 0; i < window.localStorage.length; i++) {
			const key = window.localStorage.key(i);
			if (key && key.startsWith("drafter.")) {
				entries.push({
					key,
					size: (window.localStorage.getItem(key) ?? "").length,
				});
			}
		}
	} catch {
		// localStorage unavailable — report an empty list.
	}
	return entries.sort((a, b) => a.key.localeCompare(b.key));
}

/** Best-effort system status details for diagnosing bug reports. */
export function collectSystemStatus(): Record<string, unknown> {
	const runtimeWindow = window as {
		DRAFTER_ENGINE?: string;
		pyodide?: { version?: string; loadedPackages?: Record<string, string> };
	};
	const memory = (
		performance as { memory?: { usedJSHeapSize?: number; jsHeapSizeLimit?: number } }
	).memory;
	return {
		engine: runtimeWindow.DRAFTER_ENGINE ?? null,
		pyodideVersion: runtimeWindow.pyodide?.version ?? null,
		loadedPackages: runtimeWindow.pyodide?.loadedPackages ?? null,
		userAgent: navigator.userAgent,
		platform: navigator.platform ?? null,
		language: navigator.language ?? null,
		screen: {
			width: window.screen?.width ?? null,
			height: window.screen?.height ?? null,
			viewportWidth: window.innerWidth,
			viewportHeight: window.innerHeight,
			devicePixelRatio: window.devicePixelRatio ?? null,
		},
		memory: memory
			? {
					usedJSHeapSize: memory.usedJSHeapSize ?? null,
					jsHeapSizeLimit: memory.jsHeapSizeLimit ?? null,
				}
			: null,
		timezone:
			Intl.DateTimeFormat?.().resolvedOptions?.().timeZone ?? null,
		online: navigator.onLine ?? null,
		localStorageKeys: describeDrafterStorage(),
	};
}

/**
 * Download a bug-report bundle: the accumulated telemetry events plus
 * system status and page context, as a JSON file that can be attached to
 * an email or issue.
 */
export function downloadBugReport(
	events: unknown[],
	context: BugReportContext = {},
): void {
	const created = new Date().toISOString();
	const firstMeta = (
		events[0] as { metadata?: { version?: string } } | undefined
	)?.metadata;
	downloadJson(`drafter-bug-report-${created.replace(/[:.]/g, "-")}.json`, {
		kind: "drafter-bug-report",
		version: 1,
		created,
		url: window.location.href,
		drafterVersion: firstMeta?.version ?? null,
		system: collectSystemStatus(),
		currentRoute: context.route ?? null,
		pageHtml: context.pageHtml ?? null,
		sourceCode: context.sourceCode ?? null,
		configOverrides: safeGetItem(getConfigurationOverridesStorageKey()),
		eventCount: events.length,
		events,
	});
}
