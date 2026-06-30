import { EditorView, keymap, lineNumbers } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import {
	defaultKeymap,
	indentWithTab,
	history,
	historyKeymap,
} from "@codemirror/commands";
import { python } from "@codemirror/lang-python";
import {
	syntaxHighlighting,
	defaultHighlightStyle,
	bracketMatching,
	indentOnInput,
} from "@codemirror/language";
import { showDialog } from "../dialogs";
import { t } from "../i18n";

/**
 * Opens a CodeMirror-based dialog allowing the user to edit the current
 * site's source code and reload it.
 *
 * On pyodide, a `drafter-restart-student-code` CustomEvent is dispatched
 * with `{ code: string }` in its `detail`, which `startPyodideAppServerSession`
 * listens for. On other engines a simple `location.reload()` is used as a
 * fallback after the new code is stored in sessionStorage.
 */
export function openCodeEditor(): void {
	const initialCode: string =
		(window as any).__drafterCurrentCode ?? "# Source code not available";

	// Container that will host the CodeMirror view
	const editorContainer = (
		<div class="drafter-code-editor-container"></div>
	) as HTMLDivElement;

	const extensions = [
		lineNumbers(),
		history(),
		indentOnInput(),
		bracketMatching(),
		syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
		python(),
		keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
		EditorView.theme({
			"&": {
				height: "100%",
				fontSize: "0.9rem",
				fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
			},
			".cm-scroller": { overflow: "auto" },
		}),
	];

	const state = EditorState.create({
		doc: initialCode,
		extensions,
	});

	const view = new EditorView({
		state,
		parent: editorContainer,
	});

	showDialog({
		title: t("editor.title"),
		content: editorContainer,
		modal: true,
		draggable: true,
		width: "760px",
		maxWidth: "95vw",
		closeOnBackdrop: false,
		buttons: [
			{
				label: t("editor.cancel"),
				variant: "secondary",
				closesDialog: true,
				onClick: () => {
					view.destroy();
				},
			},
			{
				label: t("editor.run"),
				variant: "primary",
				closesDialog: true,
				onClick: () => {
					const newCode = view.state.doc.toString();
					// Keep the global snapshot in sync so the editor shows the
					// latest code if reopened before the restart completes.
					(window as any).__drafterCurrentCode = newCode;
					view.destroy();
					window.dispatchEvent(
						new CustomEvent("drafter-restart-student-code", {
							detail: {
								code: newCode,
								_token: (window as any).__drafterRestartToken,
							},
						}),
					);
				},
			},
		],
		onClose: () => {
			// Ensure the view is always cleaned up if the dialog is dismissed
			// via backdrop, escape, or the close button.
			try {
				view.destroy();
			} catch {
				// Already destroyed — ignore
			}
		},
	});
}
