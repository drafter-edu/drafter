import { Panel } from "./panel";
import { t } from "../../i18n";

/**
 * STUB: Tests tab's guided test-creation tool. Shows the intended
 * three-step flow with sample content for spacing and visualization; the
 * real wizard will record a route invocation, capture the resulting
 * state/page, and emit an assert_equal call students can paste into their
 * code.
 */
export class TestWizardPanel extends Panel {
	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-test-wizard",
			"Create a Test",
			root,
		);
	}

	protected get initialContent() {
		return (
			<div class="drafter-debug-test-wizard-stub">
				<p class="drafter-debug-stub-notice">
					{t("test_wizard.coming_soon")}
				</p>
				<ol class="drafter-debug-test-wizard-steps">
					<li>{t("test_wizard.step_pick")}</li>
					<li>{t("test_wizard.step_run")}</li>
					<li>{t("test_wizard.step_copy")}</li>
				</ol>
				<pre class="drafter-debug-test-wizard-sample">
					{
						'assert_equal(\n    guess(GameState(score=0), answer=4),\n    Page(GameState(score=1), ["Correct!"])\n)'
					}
				</pre>
			</div>
		);
	}
}
