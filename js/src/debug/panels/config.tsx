import { Panel } from "./panel";
import type { JsonObject, JsonValue } from "../../config_overrides";
import {
	clearStoredConfigurationOverrides,
	getStoredConfigurationOverrides,
	setStoredConfigurationOverrides,
	syncWindowConfigurationOverrides,
} from "../../config_overrides";

export class ConfigPanel extends Panel {
	private baseConfig: JsonObject = {};
	private overrides: JsonObject = {};
	private editingKeys = new Set<string>();

	constructor(containerId: string, instanceId: number) {
		super(containerId, instanceId, "drafter-debug-config", "Configuration");
		this.overrides = getStoredConfigurationOverrides();
	}

	protected get initialContent() {
		return (
			<>
				<div
					class={`drafter-debug-config-actions drafter-debug-config-actions-${this.instanceId}`}
				>
					<button
						class={`drafter-debug-config-reload drafter-debug-config-reload-${this.instanceId}`}
						title="Reload page and re-run with current configuration values"
					>
						Reload page
					</button>
					<button
						class={`drafter-debug-config-clear-all drafter-debug-config-clear-all-${this.instanceId}`}
						title="Clear all local overrides and return to embedded values"
					>
						Clear all overrides
					</button>
					<span
						class={`drafter-debug-config-note drafter-debug-config-note-${this.instanceId}`}
					>
						Local overrides are saved and re-applied on reload.
					</span>
				</div>
				<div
					class={`drafter-debug-config-list drafter-debug-config-list-${this.instanceId}`}
				></div>
			</>
		);
	}

	public override initialize(): void {
		const reloadButton = this.queryWithin(
			this.scopedSelector("drafter-debug-config-reload"),
			"DebugPanel: Config reload button not found.",
		);
		reloadButton.addEventListener("click", () => {
			window.location.reload();
		});

		const clearAllButton = this.queryWithin(
			this.scopedSelector("drafter-debug-config-clear-all"),
			"DebugPanel: Config clear-all button not found.",
		);
		clearAllButton.addEventListener("click", () => {
			this.clearAllOverrides();
		});
	}

	public renderInitialConfig(config: Record<string, any>): void {
		this.baseConfig = { ...(config as JsonObject) };
		this.overrides = getStoredConfigurationOverrides();
		this.renderAllItems();
	}

	private getConfigSection(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-config-list"),
			"DebugPanel: Config section not found.",
		);
	}

	private updateWindowConfiguration(): void {
		setStoredConfigurationOverrides(this.overrides);
		syncWindowConfigurationOverrides(this.overrides);
	}

	private clearAllOverrides(): void {
		this.overrides = {};
		this.editingKeys.clear();
		clearStoredConfigurationOverrides();
		syncWindowConfigurationOverrides(this.overrides);
		this.renderAllItems();
	}

	private isEditing(key: string): boolean {
		return this.editingKeys.has(key);
	}

	private getCurrentValue(key: string): JsonValue | undefined {
		if (Object.prototype.hasOwnProperty.call(this.overrides, key)) {
			return this.overrides[key];
		}
		return this.baseConfig[key];
	}

	private getAllKeys(): string[] {
		return Array.from(
			new Set([
				...Object.keys(this.baseConfig),
				...Object.keys(this.overrides),
			]),
		).sort((a, b) => a.localeCompare(b));
	}

	private renderAllItems(): void {
		const section = this.getConfigSection();
		section.innerHTML = "";
		this.getAllKeys().forEach((key) => {
			section.appendChild(this.newItemElement(key));
		});
	}

	private renderItem(key: string): void {
		const section = this.getConfigSection();
		const existingItem = section.querySelector(
			`.drafter-debug-config-item[data-key="${key}"]`,
		);
		const newItem = this.newItemElement(key);
		if (existingItem) {
			existingItem.replaceWith(newItem);
			return;
		}
		section.appendChild(newItem);
	}

	private parseOverrideValue(
		rawValue: string,
	): { ok: true; value: JsonValue } | { ok: false; error: string } {
		try {
			const parsed = JSON.parse(rawValue) as JsonValue;
			return { ok: true, value: parsed };
		} catch (error) {
			return {
				ok: false,
				error:
					error instanceof Error
						? error.message
						: "Invalid JSON value",
			};
		}
	}

	private setInlineError(item: HTMLElement, message: string | null): void {
		const errorTag = item.querySelector(
			".drafter-debug-config-error",
		) as HTMLElement | null;
		if (!errorTag) {
			return;
		}
		errorTag.textContent = message ?? "";
		errorTag.classList.toggle("visible", Boolean(message));
	}

	private newItemContents(key: string) {
		const isOverridden = Object.prototype.hasOwnProperty.call(
			this.overrides,
			key,
		);
		const isEditing = this.isEditing(key);
		const baseValue = this.baseConfig[key];
		const currentValue = this.getCurrentValue(key);

		const prettyCurrent = JSON.stringify(currentValue, null, 2);
		const compactCurrent = JSON.stringify(currentValue);
		const prettyBase = JSON.stringify(baseValue);

		return (
			<>
				<div class="drafter-debug-config-item-header">
					{!isEditing ? (
						<div class="drafter-debug-config-inline-main">
							<strong>
								<code>{key}</code>
							</strong>
							<span class="drafter-debug-config-inline-separator">
								:
							</span>
							<code
								class="drafter-debug-config-inline-value"
								title={compactCurrent}
							>
								{compactCurrent}
							</code>
						</div>
					) : (
						<strong>
							<code>{key}</code>
						</strong>
					)}
					<div class="drafter-debug-config-inline-right">
						<span
							class={`drafter-debug-config-source ${
								isOverridden
									? "drafter-debug-config-source-override"
									: "drafter-debug-config-source-base"
							}`}
						>
							{isOverridden ? "Override" : "Embedded"}
						</span>

						{!isEditing ? (
							<div class="drafter-debug-config-buttons">
								<button class="drafter-debug-config-edit">
									Edit
								</button>
								<button
									class="drafter-debug-config-clear"
									disabled={!isOverridden}
									title={
										isOverridden
											? "Clear override for this key"
											: "No override to clear"
									}
								>
									Clear
								</button>
							</div>
						) : null}
					</div>
				</div>
				{isOverridden ? (
					<div class="drafter-debug-config-base-value">
						embedded: <code>{prettyBase}</code>
					</div>
				) : null}

				{!isEditing ? null : (
					<>
						<textarea class="drafter-debug-config-editor">
							{prettyCurrent}
						</textarea>
						<div class="drafter-debug-config-buttons">
							<button class="drafter-debug-config-save">
								Save override
							</button>
							<button class="drafter-debug-config-cancel">
								Cancel
							</button>
							<button
								class="drafter-debug-config-clear"
								disabled={!isOverridden}
								title={
									isOverridden
										? "Clear override for this key"
										: "No override to clear"
								}
							>
								Clear
							</button>
						</div>
						<div
							class="drafter-debug-config-error"
							aria-live="polite"
						></div>
					</>
				)}
			</>
		);
	}

	private attachItemHandlers(item: HTMLElement, key: string): void {
		const editButton = item.querySelector(
			".drafter-debug-config-edit",
		) as HTMLButtonElement | null;
		const editor = item.querySelector(
			".drafter-debug-config-editor",
		) as HTMLTextAreaElement | null;
		const saveButton = item.querySelector(
			".drafter-debug-config-save",
		) as HTMLButtonElement | null;
		const cancelButton = item.querySelector(
			".drafter-debug-config-cancel",
		) as HTMLButtonElement | null;
		const clearButton = item.querySelector(
			".drafter-debug-config-clear",
		) as HTMLButtonElement | null;

		editButton?.addEventListener("click", () => {
			this.editingKeys.add(key);
			this.renderItem(key);
		});

		saveButton?.addEventListener("click", () => {
			if (!editor) {
				return;
			}
			const parsedValue = this.parseOverrideValue(editor.value);
			if (!parsedValue.ok) {
				this.setInlineError(item, parsedValue.error);
				return;
			}

			this.overrides[key] = parsedValue.value;
			this.editingKeys.delete(key);
			this.updateWindowConfiguration();
			this.renderItem(key);
		});

		cancelButton?.addEventListener("click", () => {
			this.editingKeys.delete(key);
			this.setInlineError(item, null);
			this.renderItem(key);
		});

		clearButton?.addEventListener("click", () => {
			if (Object.prototype.hasOwnProperty.call(this.overrides, key)) {
				delete this.overrides[key];
				this.updateWindowConfiguration();
			}
			this.editingKeys.delete(key);
			this.setInlineError(item, null);
			this.renderItem(key);
		});
	}

	private newItemElement(key: string) {
		const isOverridden = Object.prototype.hasOwnProperty.call(
			this.overrides,
			key,
		);

		const configItem = (
			<div class="drafter-debug-config-item" data-key={key}>
				{this.newItemContents(key)}
			</div>
		);
		if (isOverridden) {
			configItem.classList.add("drafter-debug-config-item-overridden");
		}
		this.attachItemHandlers(configItem, key);
		return configItem;
	}

	public renderConfigUpdate(key: string, value: any): void {
		this.baseConfig[key] = value as JsonValue;
		this.renderItem(key);

		const updatedItem = this.getConfigSection().querySelector(
			`.drafter-debug-config-item[data-key="${key}"]`,
		) as HTMLElement | null;
		if (updatedItem) {
			updatedItem.classList.add("drafter-debug-config-item-updated");
		}
	}
}
