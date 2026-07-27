import { Panel } from "./panel";
import { t } from "../../i18n";

/**
 * Environment tab: basic facts about the runtime the site is executing in.
 * Engine/browser rows are real; deeper metrics (memory, timing) are STUB
 * placeholders until the runtime exposes them.
 */
export class RuntimeInfoPanel extends Panel {
	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-runtime",
			"Runtime Info",
			root,
		);
	}

	protected get initialContent() {
		return (
			<div
				class={`drafter-debug-runtime-list drafter-debug-runtime-list-${this.instanceId}`}
			></div>
		);
	}

	public initialize(): void {
		this.renderInfo();
	}

	private collectRows(): Array<[string, string]> {
		const engine =
			(window as { DRAFTER_ENGINE?: string }).DRAFTER_ENGINE ??
			t("runtime.unknown_engine");
		const pyodideVersion = (
			window as { pyodide?: { version?: string } }
		).pyodide?.version;
		const rows: Array<[string, string]> = [
			[t("runtime.engine"), engine],
			[t("runtime.browser"), navigator.userAgent],
			[t("runtime.language"), navigator.language ?? ""],
		];
		if (pyodideVersion) {
			rows.push([t("runtime.pyodide_version"), pyodideVersion]);
		}
		// STUB rows, present for spacing/visualization until the runtime
		// reports real numbers.
		rows.push(
			[t("runtime.memory"), t("runtime.sample_value")],
			[t("runtime.uptime"), t("runtime.sample_value")],
		);
		return rows;
	}

	public renderInfo(): void {
		const list = this.queryWithin(
			this.scopedSelector("drafter-debug-runtime-list"),
			"DebugPanel: Runtime info list not found.",
		);
		list.replaceChildren(
			(
				<table class="drafter-debug-runtime-table">
					<tbody>
						{this.collectRows().map(([label, value]) => (
							<tr>
								<th>{label}</th>
								<td>{value}</td>
							</tr>
						))}
					</tbody>
				</table>
			) as HTMLElement,
		);
	}
}
