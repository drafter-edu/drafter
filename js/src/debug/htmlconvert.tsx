import { showDialog } from "../dialogs";
import { t } from "../i18n";
import { loadLazyBundle } from "../lazy";
import { buildPythonEditorView } from "./editor";

/** A function that turns HTML into Drafter Python code. */
export type HtmlConverter = (html: string) => string;

/** How long the "Copied!" note stays visible. */
const COPIED_NOTE_MS = 2000;

/**
 * Fetch the converter bundle the first time it is needed. It is not part
 * of the main bundle because of its size (see transpiler.index.ts).
 */
export async function loadHtmlConverter(): Promise<HtmlConverter> {
	const bundle = await loadLazyBundle<{
		convertHtmlToDrafter: HtmlConverter;
	}>("drafter.transpiler", "DrafterTranspiler");
	return bundle.convertHtmlToDrafter;
}

async function copyText(text: string): Promise<boolean> {
	try {
		await navigator.clipboard.writeText(text);
		return true;
	} catch {
		// Clipboard API unavailable (e.g. insecure context): fall back to
		// a transient textarea + execCommand copy.
		const scratch = document.createElement("textarea");
		scratch.value = text;
		document.body.appendChild(scratch);
		scratch.select();
		let copied = false;
		try {
			copied = document.execCommand("copy");
		} catch {
			copied = false;
		}
		scratch.remove();
		return copied;
	}
}

/**
 * Opens the "Convert HTML to Drafter" dialog: paste HTML or choose an HTML
 * file, press Convert, and copy the generated Python. The converter itself
 * is loaded on first use.
 *
 * @param load Supplies the converter; replaceable so tests need no bundle.
 */
export function openHtmlConverter(
	load: () => Promise<HtmlConverter> = loadHtmlConverter,
): void {
	const input = (
		<textarea
			class="drafter-html-converter-input"
			rows={8}
			spellcheck={false}
			aria-label={t("htmlconvert.input_label")}
			placeholder={"<h1>Hello</h1>\n<p>Paste your HTML here.</p>"}
		></textarea>
	) as HTMLTextAreaElement;
	const upload = (
		<input
			class="drafter-html-converter-upload"
			type="file"
			accept=".html,.htm,text/html"
		/>
	) as HTMLInputElement;
	const convertButton = (
		<button
			type="button"
			class="drafter-debug-button-- drafter-html-converter-convert"
		>
			{t("htmlconvert.convert")}
		</button>
	) as HTMLButtonElement;
	const copyButton = (
		<button
			type="button"
			class="drafter-debug-button-- drafter-html-converter-copy"
			disabled
		>
			{t("htmlconvert.copy")}
		</button>
	) as HTMLButtonElement;
	const status = (
		<span class="drafter-html-converter-status" role="status"></span>
	) as HTMLSpanElement;
	const outputContainer = (
		<div
			class="drafter-code-editor-container drafter-code-viewer-container drafter-html-converter-output"
			aria-label={t("htmlconvert.output_label")}
		></div>
	) as HTMLDivElement;

	const content = (
		<div class="drafter-html-converter">
			<p class="drafter-html-converter-intro">{t("htmlconvert.intro")}</p>
			{input}
			<label class="drafter-html-converter-upload-label">
				{t("htmlconvert.upload_label")} {upload}
			</label>
			<div class="drafter-html-converter-actions">
				{convertButton}
				{copyButton}
				{status}
			</div>
			{outputContainer}
		</div>
	) as HTMLDivElement;

	const view = buildPythonEditorView(
		outputContainer,
		`# ${t("htmlconvert.output_placeholder")}`,
		true,
		"python",
	);
	let converted = "";
	let copiedTimer: ReturnType<typeof setTimeout> | null = null;

	const showOutput = (code: string) => {
		view.dispatch({
			changes: { from: 0, to: view.state.doc.length, insert: code },
		});
	};

	const convert = async () => {
		const html = input.value;
		if (!html.trim()) {
			status.textContent = t("htmlconvert.empty");
			return;
		}
		convertButton.disabled = true;
		status.textContent = t("htmlconvert.loading");
		let converter: HtmlConverter;
		try {
			converter = await load();
		} catch {
			status.textContent = t("htmlconvert.load_failed");
			convertButton.disabled = false;
			return;
		}
		try {
			converted = converter(html);
			showOutput(converted);
			copyButton.disabled = false;
			status.textContent = t("htmlconvert.done");
		} catch (error) {
			converted = "";
			copyButton.disabled = true;
			status.textContent = t("htmlconvert.failed", {
				message: error instanceof Error ? error.message : String(error),
			});
		} finally {
			convertButton.disabled = false;
		}
	};

	convertButton.addEventListener("click", () => void convert());
	upload.addEventListener("change", () => {
		const file = upload.files?.[0];
		if (!file) {
			return;
		}
		void file.text().then((text) => {
			input.value = text;
			return convert();
		});
	});
	copyButton.addEventListener("click", () => {
		void copyText(converted).then((copied) => {
			status.textContent = copied
				? t("htmlconvert.copied")
				: t("htmlconvert.copy_failed");
			if (copiedTimer) {
				clearTimeout(copiedTimer);
			}
			copiedTimer = setTimeout(() => {
				status.textContent = "";
			}, COPIED_NOTE_MS);
		});
	});

	showDialog({
		title: t("htmlconvert.title"),
		content,
		modal: true,
		draggable: true,
		width: "760px",
		maxWidth: "95vw",
		buttons: [
			{
				label: t("htmlconvert.close"),
				variant: "primary",
				closesDialog: true,
			},
		],
		onClose: () => {
			if (copiedTimer) {
				clearTimeout(copiedTimer);
			}
			try {
				view.destroy();
			} catch {
				// Already destroyed — ignore
			}
		},
	});
}
