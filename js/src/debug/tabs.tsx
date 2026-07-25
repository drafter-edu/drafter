import type { ReactElement } from "jsx-dom";
import { t } from "../i18n";

export interface TabDefinition {
	/** Stable identifier, e.g. "current" or "environment". */
	id: string;
	/** i18n key for the tab button label. */
	labelKey: string;
	/** Panel structures (from Panel.createStructure()) shown in this tab. */
	content: (ReactElement | HTMLElement)[];
}

export type TabBadgeVariant = "error" | "warn" | "fail";

const ACTIVE_TAB_STORAGE_KEY = "drafter.debug.active-tab.v1";

/**
 * Accessible tab bar for the debug panel: a `role="tablist"` row of buttons
 * plus one `role="tabpanel"` container per tab. Only the active tab's panel
 * is visible; the others are `hidden` but stay in the DOM so the individual
 * debug panels keep receiving telemetry updates while not shown.
 *
 * The active tab persists to localStorage so a page reload (or a full
 * browser reload via the "--reload" route) returns the student to the tab
 * they were using.
 */
export class TabBar {
	private tabButtons = new Map<string, HTMLButtonElement>();
	private tabPanels = new Map<string, HTMLElement>();
	private badges = new Map<string, HTMLElement>();
	private activeId: string;

	constructor(
		private readonly instanceId: number,
		private readonly tabs: TabDefinition[],
		private readonly onActivate?: (id: string) => void,
	) {
		this.activeId = this.loadStoredTab() ?? tabs[0]?.id ?? "";
	}

	private loadStoredTab(): string | null {
		try {
			const stored = window.localStorage.getItem(ACTIVE_TAB_STORAGE_KEY);
			if (stored && this.tabs.some((tab) => tab.id === stored)) {
				return stored;
			}
		} catch {
			// localStorage unavailable (private mode, sandboxed iframe) —
			// fall back to the first tab.
		}
		return null;
	}

	private storeActiveTab(id: string): void {
		try {
			window.localStorage.setItem(ACTIVE_TAB_STORAGE_KEY, id);
		} catch {
			// Persistence is best-effort only.
		}
	}

	public getButtonDomId(id: string): string {
		return `drafter-debug-tab-btn-${id}-${this.instanceId}`;
	}

	public getPanelDomId(id: string): string {
		return `drafter-debug-tab-${id}-${this.instanceId}`;
	}

	public getActiveTab(): string {
		return this.activeId;
	}

	/** The tab button row; mount inside the debug panel header. */
	public createTabList(): HTMLElement {
		const tablist = (
			<div
				class="drafter-debug-tabbar"
				role="tablist"
				aria-label={t("debug.tabs.label")}
			></div>
		) as HTMLElement;
		this.tabs.forEach((tab) => {
			const badge = (
				<span class="drafter-debug-tab-badge" hidden></span>
			) as HTMLElement;
			const button = (
				<button
					type="button"
					role="tab"
					id={this.getButtonDomId(tab.id)}
					class="drafter-debug-tab-button"
					aria-controls={this.getPanelDomId(tab.id)}
					aria-selected={tab.id === this.activeId ? "true" : "false"}
					tabIndex={tab.id === this.activeId ? 0 : -1}
				>
					<span class="drafter-debug-tab-label">
						{t(tab.labelKey)}
					</span>
					{badge}
				</button>
			) as HTMLButtonElement;
			button.addEventListener("click", () => this.activate(tab.id));
			button.addEventListener("keydown", (event) =>
				this.handleTabKeydown(event, tab.id),
			);
			this.tabButtons.set(tab.id, button);
			this.badges.set(tab.id, badge);
			tablist.appendChild(button);
		});
		return tablist;
	}

	/** The tabpanel containers; mount inside the debug panel content area. */
	public createTabPanels(): HTMLElement[] {
		return this.tabs.map((tab) => {
			const panel = (
				<div
					role="tabpanel"
					id={this.getPanelDomId(tab.id)}
					class="drafter-debug-tabpanel"
					aria-labelledby={this.getButtonDomId(tab.id)}
					hidden={tab.id !== this.activeId}
				>
					{tab.content}
				</div>
			) as HTMLElement;
			this.tabPanels.set(tab.id, panel);
			return panel;
		});
	}

	private handleTabKeydown(event: KeyboardEvent, currentId: string): void {
		const index = this.tabs.findIndex((tab) => tab.id === currentId);
		if (index === -1) {
			return;
		}
		let nextIndex: number | null = null;
		if (event.key === "ArrowRight") {
			nextIndex = (index + 1) % this.tabs.length;
		} else if (event.key === "ArrowLeft") {
			nextIndex = (index - 1 + this.tabs.length) % this.tabs.length;
		} else if (event.key === "Home") {
			nextIndex = 0;
		} else if (event.key === "End") {
			nextIndex = this.tabs.length - 1;
		}
		if (nextIndex === null) {
			return;
		}
		event.preventDefault();
		const nextId = this.tabs[nextIndex].id;
		this.activate(nextId);
		this.tabButtons.get(nextId)?.focus();
	}

	public activate(id: string): void {
		if (!this.tabPanels.has(id)) {
			return;
		}
		this.activeId = id;
		this.tabs.forEach((tab) => {
			const selected = tab.id === id;
			const button = this.tabButtons.get(tab.id);
			if (button) {
				button.setAttribute(
					"aria-selected",
					selected ? "true" : "false",
				);
				button.tabIndex = selected ? 0 : -1;
			}
			const panel = this.tabPanels.get(tab.id);
			if (panel) {
				panel.hidden = !selected;
			}
		});
		this.storeActiveTab(id);
		this.onActivate?.(id);
	}

	/**
	 * Show a count badge on a tab button (e.g. errors on Current, failures
	 * on Tests). A count of zero hides the badge.
	 */
	public setBadge(id: string, count: number, variant: TabBadgeVariant): void {
		const badge = this.badges.get(id);
		if (!badge) {
			return;
		}
		badge.textContent = count > 99 ? "99+" : `${count}`;
		badge.hidden = count <= 0;
		badge.classList.remove("is-error", "is-warn", "is-fail");
		badge.classList.add(`is-${variant}`);
	}
}
