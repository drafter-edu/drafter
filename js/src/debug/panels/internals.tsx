import { Panel } from "./panel";
import { t } from "../../i18n";

/**
 * STUB: the "Advanced" section at the bottom of the Environment tab,
 * describing Drafter's internals (client server, bridge, navigation)
 * for the curious. Collapsed by default; the rows are sample content for
 * spacing and visualization until the internals report live details.
 */
export class InternalsPanel extends Panel {
	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-internals",
			"Advanced",
			root,
		);
	}

	protected get initialContent() {
		return (
			<details class="drafter-debug-internals">
				<summary>{t("internals.summary")}</summary>
				<p class="drafter-debug-stub-notice">
					{t("internals.coming_soon")}
				</p>
				<table class="drafter-debug-internals-table">
					<tbody>
						<tr>
							<th>ClientServer</th>
							<td>{t("internals.sample_server")}</td>
						</tr>
						<tr>
							<th>ClientBridge</th>
							<td>{t("internals.sample_bridge")}</td>
						</tr>
						<tr>
							<th>NavigationController</th>
							<td>{t("internals.sample_navigation")}</td>
						</tr>
						<tr>
							<th>EventBus</th>
							<td>{t("internals.sample_bus")}</td>
						</tr>
					</tbody>
				</table>
			</details>
		);
	}
}
