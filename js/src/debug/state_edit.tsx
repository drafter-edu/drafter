import { showDialog } from "../dialogs";
import { t } from "../i18n";

/**
 * STUB: "Edit > Edit State" dialog. For now it previews the current state
 * (as plain text from the state panel) alongside a notice that editing is
 * not implemented yet. The dialog exists so the menu structure, spacing,
 * and flow can be evaluated; a real editor will replace the preview.
 */
export function openStateEditor(getStatePreview: () => string): void {
	const preview = getStatePreview().trim();
	const content = (
		<div class="drafter-state-editor-container">
			<p class="drafter-state-editor-notice">
				{t("state_edit.coming_soon")}
			</p>
			<pre class="drafter-state-editor-preview">
				{preview || t("state_edit.no_state")}
			</pre>
		</div>
	) as HTMLDivElement;

	showDialog({
		title: t("state_edit.title"),
		content,
		modal: true,
		draggable: true,
		width: "520px",
		maxWidth: "95vw",
		buttons: [
			{
				label: t("state_edit.close"),
				variant: "primary",
				closesDialog: true,
			},
		],
	});
}
