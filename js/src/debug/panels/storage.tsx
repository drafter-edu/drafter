import { Panel } from "./panel";
import { t } from "../../i18n";

const PREVIEW_LENGTH = 80;

/**
 * Environment tab: a localStorage inspector. Lists every key with its size
 * and a truncated value preview; Drafter's own keys (`drafter.*`) can be
 * deleted individually so students can clear saved slots, config
 * overrides, or the remembered tab without opening devtools.
 */
export class StoragePanel extends Panel {
	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-storage",
			"Browser Storage",
			root,
		);
	}

	protected get initialContent() {
		const refresh = (
			<button
				type="button"
				class="drafter-debug-button-- drafter-debug-storage-refresh"
			>
				{t("storage.refresh")}
			</button>
		) as HTMLButtonElement;
		refresh.addEventListener("click", () => this.renderStorage());
		return (
			<>
				{refresh}
				<div
					class={`drafter-debug-storage-list drafter-debug-storage-list-${this.instanceId}`}
				></div>
			</>
		);
	}

	public initialize(): void {
		this.renderStorage();
	}

	private readKeys(): Array<{ key: string; value: string }> {
		const entries: Array<{ key: string; value: string }> = [];
		try {
			for (let i = 0; i < window.localStorage.length; i++) {
				const key = window.localStorage.key(i);
				if (key === null) {
					continue;
				}
				entries.push({
					key,
					value: window.localStorage.getItem(key) ?? "",
				});
			}
		} catch {
			// localStorage unavailable — render the empty message instead.
		}
		return entries.sort((a, b) => a.key.localeCompare(b.key));
	}

	private createRow(entry: { key: string; value: string }): HTMLElement {
		const preview =
			entry.value.length > PREVIEW_LENGTH
				? `${entry.value.slice(0, PREVIEW_LENGTH)}…`
				: entry.value;
		const row = (
			<tr>
				<td>
					<code>{entry.key}</code>
				</td>
				<td class="drafter-debug-storage-size">
					{entry.value.length}
				</td>
				<td class="drafter-debug-storage-preview">{preview}</td>
				<td class="drafter-debug-storage-actions"></td>
			</tr>
		) as HTMLElement;
		// Only Drafter's own keys are deletable from here; other keys may
		// belong to the hosting page.
		if (entry.key.startsWith("drafter.")) {
			const remove = (
				<button
					type="button"
					class="drafter-debug-button-- drafter-debug-storage-delete"
					title={t("storage.delete.tooltip")}
				>
					🗑️
				</button>
			) as HTMLButtonElement;
			remove.addEventListener("click", () => {
				try {
					window.localStorage.removeItem(entry.key);
				} catch {
					// Ignore, re-render shows the truth either way.
				}
				this.renderStorage();
			});
			row.querySelector(".drafter-debug-storage-actions")?.appendChild(
				remove,
			);
		}
		return row;
	}

	public renderStorage(): void {
		const list = this.queryWithin(
			this.scopedSelector("drafter-debug-storage-list"),
			"DebugPanel: Storage list not found.",
		);
		const entries = this.readKeys();
		if (entries.length === 0) {
			list.replaceChildren(
				(
					<p class="drafter-debug-storage-empty">
						{t("storage.empty")}
					</p>
				) as HTMLElement,
			);
			return;
		}
		list.replaceChildren(
			(
				<table class="drafter-debug-storage-table">
					<thead>
						<tr>
							<th>{t("storage.key")}</th>
							<th>{t("storage.size")}</th>
							<th>{t("storage.value")}</th>
							<th></th>
						</tr>
					</thead>
					<tbody>
						{entries.map((entry) => this.createRow(entry))}
					</tbody>
				</table>
			) as HTMLElement,
		);
	}
}
