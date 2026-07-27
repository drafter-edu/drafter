import { Panel } from "./panel";
import { t } from "../../i18n";

/**
 * Environment tab: the Python packages loaded into the pyodide runtime
 * (from `pyodide.loadedPackages`), with a refresh button. Engines without
 * that API (Skulpt, jsdom tests) get a graceful "not available" message.
 */
export class PackagesPanel extends Panel {
	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-packages",
			"Installed Packages",
			root,
		);
	}

	protected get initialContent() {
		const refresh = (
			<button
				type="button"
				class="drafter-debug-button-- drafter-debug-packages-refresh"
			>
				{t("packages.refresh")}
			</button>
		) as HTMLButtonElement;
		refresh.addEventListener("click", () => this.renderPackages());
		return (
			<>
				{refresh}
				<div
					class={`drafter-debug-packages-list drafter-debug-packages-list-${this.instanceId}`}
				></div>
			</>
		);
	}

	public initialize(): void {
		this.renderPackages();
	}

	private getLoadedPackages(): Record<string, string> | null {
		const pyodide = (
			window as { pyodide?: { loadedPackages?: Record<string, string> } }
		).pyodide;
		if (!pyodide || !pyodide.loadedPackages) {
			return null;
		}
		return pyodide.loadedPackages;
	}

	public renderPackages(): void {
		const list = this.queryWithin(
			this.scopedSelector("drafter-debug-packages-list"),
			"DebugPanel: Packages list not found.",
		);
		const packages = this.getLoadedPackages();
		if (packages === null) {
			list.replaceChildren(
				(
					<p class="drafter-debug-packages-empty">
						{t("packages.unavailable")}
					</p>
				) as HTMLElement,
			);
			return;
		}
		const names = Object.keys(packages).sort();
		if (names.length === 0) {
			list.replaceChildren(
				(
					<p class="drafter-debug-packages-empty">
						{t("packages.none")}
					</p>
				) as HTMLElement,
			);
			return;
		}
		list.replaceChildren(
			(
				<table class="drafter-debug-packages-table">
					<thead>
						<tr>
							<th>{t("packages.name")}</th>
							<th>{t("packages.source")}</th>
						</tr>
					</thead>
					<tbody>
						{names.map((name) => (
							<tr>
								<td>
									<code>{name}</code>
								</td>
								<td>{String(packages[name])}</td>
							</tr>
						))}
					</tbody>
				</table>
			) as HTMLElement,
		);
	}
}
