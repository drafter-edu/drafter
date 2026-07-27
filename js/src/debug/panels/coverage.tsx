import { Panel } from "./panel";
import { t } from "../../i18n";

/**
 * STUB: Tests tab's coverage summary (routes, state fields, code lines).
 * The bars below are hardcoded sample content for spacing and
 * visualization; real numbers will come from tracking which routes the
 * tests visited, which state fields they touched, and which lines ran.
 */
export class CoveragePanel extends Panel {
	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-coverage",
			"Coverage",
			root,
		);
	}

	private sampleBar(labelKey: string, percent: number): HTMLElement {
		return (
			<div class="drafter-debug-coverage-row">
				<span class="drafter-debug-coverage-label">
					{t(labelKey)}
				</span>
				<span class="drafter-debug-coverage-bar">
					<span
						class="drafter-debug-coverage-fill"
						style={`width: ${percent}%`}
					></span>
				</span>
				<span class="drafter-debug-coverage-percent">
					{percent}%
				</span>
			</div>
		) as HTMLElement;
	}

	protected get initialContent() {
		return (
			<div class="drafter-debug-coverage-stub">
				<p class="drafter-debug-stub-notice">
					{t("coverage.coming_soon")}
				</p>
				{this.sampleBar("coverage.routes", 75)}
				{this.sampleBar("coverage.state", 50)}
				{this.sampleBar("coverage.code", 62)}
			</div>
		);
	}
}
