import { t } from "../i18n";

export interface MenuItemDefinition {
	/** i18n key for the item label. */
	labelKey: string;
	/** Optional i18n key resolving to an emoji/icon prefix. */
	iconKey?: string;
	/** i18n key for the tooltip; defaults to none. */
	tooltipKey?: string;
	/** Click behavior. Omitted or `disabled` items render greyed out. */
	action?: () => void;
	disabled?: boolean;
	/** Render a separator line after this item. */
	separatorAfter?: boolean;
	/** Extra class for tests/styling, e.g. "drafter-menu-item-home". */
	className?: string;
	/**
	 * Live state supplier, re-evaluated every time the menu opens: an
	 * optional parenthetical suffix after the label (e.g. how long ago the
	 * last save happened) and whether the item is currently disabled.
	 */
	dynamic?: () => { suffix?: string; disabled?: boolean };
}

export interface MenuDefinition {
	/** Stable identifier used in DOM classes, e.g. "navigate". */
	id: string;
	/** i18n key for the top-level menu button. */
	labelKey: string;
	items: MenuItemDefinition[];
}

/**
 * Accessible dropdown menu bar for the application-frame header (the
 * Navigate / View / Edit / Save-Load / Help menus). Click-to-open with
 * hover-switching while a menu is open, Escape/arrow-key support, and
 * outside-click dismissal that works under shadow DOM (via composedPath).
 */
export class HeaderMenuBar {
	public readonly element: HTMLElement;
	private menuButtons: HTMLButtonElement[] = [];
	private menuPopups: HTMLElement[] = [];
	private dynamicItems: Array<{
		element: HTMLButtonElement;
		suffixElement: HTMLElement;
		dynamic: () => { suffix?: string; disabled?: boolean };
	}> = [];
	private openIndex: number = -1;
	private readonly onOutsidePointerDown = (event: Event) => {
		const path = event.composedPath?.() ?? [];
		if (!path.includes(this.element)) {
			this.closeAll();
		}
	};

	constructor(private readonly menus: MenuDefinition[]) {
		this.element = (
			<div class="drafter-header-menubar" role="menubar"></div>
		) as HTMLElement;
		menus.forEach((menu, index) => {
			this.element.appendChild(this.createMenu(menu, index));
		});
	}

	private createMenu(menu: MenuDefinition, index: number): HTMLElement {
		const popup = (
			<div
				class={`drafter-menu-popup drafter-menu-popup-${menu.id}`}
				role="menu"
				aria-label={t(menu.labelKey)}
				hidden
			></div>
		) as HTMLElement;
		menu.items.forEach((item) => {
			popup.appendChild(this.createMenuItem(item));
			if (item.separatorAfter) {
				popup.appendChild(
					(
						<div
							class="drafter-menu-separator"
							role="separator"
						></div>
					) as HTMLElement,
				);
			}
		});

		const button = (
			<button
				type="button"
				class={`drafter-menu-button drafter-menu-button-${menu.id}`}
				role="menuitem"
				aria-haspopup="menu"
				aria-expanded="false"
			>
				<span class="drafter-menu-button-label">
					{t(menu.labelKey)}
				</span>
				<span class="drafter-menu-caret" aria-hidden="true">
					▾
				</span>
			</button>
		) as HTMLButtonElement;
		button.addEventListener("click", (event) => {
			event.stopPropagation();
			this.toggleMenu(index);
		});
		button.addEventListener("mouseenter", () => {
			// Classic menubar affordance: once any menu is open, sliding the
			// pointer across the bar switches menus without extra clicks.
			if (this.openIndex !== -1 && this.openIndex !== index) {
				this.openMenu(index);
			}
		});
		button.addEventListener("keydown", (event) => {
			if (event.key === "ArrowDown" || event.key === "Enter") {
				event.preventDefault();
				this.openMenu(index);
				this.focusItem(index, 0);
			} else if (event.key === "ArrowRight") {
				event.preventDefault();
				this.focusButton((index + 1) % this.menus.length);
			} else if (event.key === "ArrowLeft") {
				event.preventDefault();
				this.focusButton(
					(index - 1 + this.menus.length) % this.menus.length,
				);
			} else if (event.key === "Escape") {
				this.closeAll();
			}
		});

		popup.addEventListener("keydown", (event) => {
			this.handlePopupKeydown(event, index);
		});

		this.menuButtons.push(button);
		this.menuPopups.push(popup);
		return (
			<div class="drafter-menu">
				{button}
				{popup}
			</div>
		) as HTMLElement;
	}

	private createMenuItem(item: MenuItemDefinition): HTMLElement {
		const icon = item.iconKey ? `${t(item.iconKey)} ` : "";
		const disabled = item.disabled || !item.action;
		const suffixElement = (
			<span class="drafter-menu-item-suffix"></span>
		) as HTMLElement;
		const element = (
			<button
				type="button"
				class={`drafter-menu-item ${item.className ?? ""}`}
				role="menuitem"
				title={item.tooltipKey ? t(item.tooltipKey) : undefined}
				disabled={disabled}
			>
				{icon}
				{t(item.labelKey)}
				{suffixElement}
			</button>
		) as HTMLButtonElement;
		if (item.dynamic) {
			this.dynamicItems.push({
				element,
				suffixElement,
				dynamic: item.dynamic,
			});
			this.refreshDynamicItem(element, suffixElement, item.dynamic);
		}
		element.addEventListener("click", (event) => {
			event.stopPropagation();
			// Re-check the live attribute: setItemEnabled() may have
			// enabled/disabled this item after construction.
			if (element.disabled) {
				return;
			}
			this.closeAll();
			item.action?.();
		});
		return element;
	}

	private enabledItemsOf(index: number): HTMLButtonElement[] {
		return Array.from(
			this.menuPopups[index].querySelectorAll(
				".drafter-menu-item:not([disabled])",
			),
		) as HTMLButtonElement[];
	}

	private handlePopupKeydown(event: KeyboardEvent, index: number): void {
		const items = this.enabledItemsOf(index);
		const current = items.indexOf(
			event.target as HTMLButtonElement,
		);
		if (event.key === "Escape") {
			event.preventDefault();
			this.closeAll();
			this.focusButton(index);
		} else if (event.key === "ArrowDown") {
			event.preventDefault();
			this.focusElement(items[(current + 1) % items.length]);
		} else if (event.key === "ArrowUp") {
			event.preventDefault();
			this.focusElement(
				items[(current - 1 + items.length) % items.length],
			);
		} else if (event.key === "ArrowRight") {
			event.preventDefault();
			const next = (index + 1) % this.menus.length;
			this.openMenu(next);
			this.focusItem(next, 0);
		} else if (event.key === "ArrowLeft") {
			event.preventDefault();
			const previous = (index - 1 + this.menus.length) % this.menus.length;
			this.openMenu(previous);
			this.focusItem(previous, 0);
		} else if (event.key === "Tab") {
			this.closeAll();
		}
	}

	private focusElement(element: HTMLElement | undefined): void {
		element?.focus();
	}

	private focusButton(index: number): void {
		this.menuButtons[index]?.focus();
	}

	private focusItem(menuIndex: number, itemIndex: number): void {
		this.focusElement(this.enabledItemsOf(menuIndex)[itemIndex]);
	}

	private toggleMenu(index: number): void {
		if (this.openIndex === index) {
			this.closeAll();
		} else {
			this.openMenu(index);
		}
	}

	private refreshDynamicItem(
		element: HTMLButtonElement,
		suffixElement: HTMLElement,
		dynamic: () => { suffix?: string; disabled?: boolean },
	): void {
		const state = dynamic();
		suffixElement.textContent = state.suffix ?? "";
		if (state.disabled !== undefined) {
			element.disabled = state.disabled;
		}
	}

	/** Re-evaluate every dynamic item (called when a menu opens). */
	public refreshDynamicItems(): void {
		this.dynamicItems.forEach(({ element, suffixElement, dynamic }) =>
			this.refreshDynamicItem(element, suffixElement, dynamic),
		);
	}

	private openMenu(index: number): void {
		if (this.openIndex === -1) {
			document.addEventListener(
				"mousedown",
				this.onOutsidePointerDown,
				true,
			);
		}
		this.refreshDynamicItems();
		this.openIndex = index;
		this.menuPopups.forEach((popup, popupIndex) => {
			popup.hidden = popupIndex !== index;
		});
		this.menuButtons.forEach((button, buttonIndex) => {
			button.setAttribute(
				"aria-expanded",
				buttonIndex === index ? "true" : "false",
			);
		});
	}

	public closeAll(): void {
		if (this.openIndex === -1) {
			return;
		}
		this.openIndex = -1;
		this.menuPopups.forEach((popup) => {
			popup.hidden = true;
		});
		this.menuButtons.forEach((button) => {
			button.setAttribute("aria-expanded", "false");
		});
		document.removeEventListener(
			"mousedown",
			this.onOutsidePointerDown,
			true,
		);
	}

	/** Enable/disable a rendered item (e.g. Save/Load once wired). */
	public setItemEnabled(className: string, enabled: boolean): void {
		const items = this.element.querySelectorAll(`.${className}`);
		items.forEach((item) => {
			(item as HTMLButtonElement).disabled = !enabled;
		});
	}
}
