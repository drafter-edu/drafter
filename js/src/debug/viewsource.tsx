import { showDialog } from "../dialogs";
import { t } from "../i18n";
import { buildPythonEditorView } from "./editor";

/**
 * Lightweight HTML indenter for the page-source viewer: breaks between
 * tags and indents by nesting depth. Purely cosmetic — the browser's
 * innerHTML comes back as one long line.
 */
export function formatHtml(rawHtml: string): string {
	const tokens = rawHtml
		.replace(/>\s+</g, "><")
		.split(/(?=<)|(?<=>)/g)
		.map((token) => token.trim())
		.filter((token) => token.length > 0);
	const lines: string[] = [];
	let depth = 0;
	tokens.forEach((token) => {
		const isClosing = /^<\//.test(token);
		const isSelfContained =
			/^<[^>]*\/>$/.test(token) ||
			/^<(area|base|br|col|embed|hr|img|input|link|meta|source|track|wbr)\b/i.test(
				token,
			) ||
			/^<!/.test(token);
		const isOpening =
			/^</.test(token) && !isClosing && !isSelfContained;
		if (isClosing) {
			depth = Math.max(0, depth - 1);
		}
		lines.push("  ".repeat(depth) + token);
		if (isOpening) {
			depth += 1;
		}
	});
	return lines.join("\n");
}

/**
 * Opens a read-only CodeMirror dialog showing the generated HTML of the
 * current page — what Drafter actually rendered into the site body — so
 * students can inspect the output of their components. (The Python source
 * itself is edited via Edit > Edit Source.)
 */
export function openSourceViewer(getPageHtml: () => string | null): void {
	const rawHtml = getPageHtml();
	const doc = rawHtml
		? formatHtml(rawHtml)
		: `<!-- ${t("viewsource.empty")} -->`;

	const viewerContainer = (
		<div class="drafter-code-editor-container drafter-code-viewer-container"></div>
	) as HTMLDivElement;

	const view = buildPythonEditorView(viewerContainer, doc, true, "html");

	showDialog({
		title: t("viewsource.title"),
		content: viewerContainer,
		modal: true,
		draggable: true,
		width: "760px",
		maxWidth: "95vw",
		buttons: [
			{
				label: t("viewsource.close"),
				variant: "primary",
				closesDialog: true,
			},
		],
		onClose: () => {
			try {
				view.destroy();
			} catch {
				// Already destroyed — ignore
			}
		},
	});
}
