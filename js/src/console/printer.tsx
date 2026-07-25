/**
 * The "printer console": a console/REPL area that captures Python
 * print()/stderr output (routed here from pyodide.setStdout/setStderr) and
 * lets the user run new Python commands interactively.
 *
 * Where the output goes is controlled by the `console_mode` client-server
 * configuration value:
 *
 * - "auto" (default): a console panel in the site footer, revealed the first
 *   time something is printed. The deploy stylesheet hides the whole footer,
 *   so in production this panel is invisible and output only reaches the
 *   browser devtools console.
 * - "hover": a floating console pinned to the bottom of the viewport,
 *   revealed on first print. Visible in production too.
 * - "toast": each printed line appears briefly as a toast in the corner.
 * - "devtools": output is only mirrored to the browser devtools console.
 *
 * All modes always mirror output to the devtools console, so nothing is ever
 * lost. Output produced before the site frame exists (e.g. module-level
 * prints) is buffered and replayed when the console attaches.
 */

import { t } from "../i18n";
import { ReplSession } from "./repl";
import type { ConsoleStream } from "./repl";

export type { ConsoleStream } from "./repl";

export type ConsoleMode = "auto" | "hover" | "toast" | "devtools";

export interface ConsoleEntry {
	stream: ConsoleStream;
	text: string;
}

const CONSOLE_MODES: ConsoleMode[] = ["auto", "hover", "toast", "devtools"];
const MAX_HISTORY_ENTRIES = 1000;
const MAX_TOASTS = 5;
const TOAST_LIFETIME_MS = 6000;

/**
 * Read the effective console mode from the page configuration. Overrides
 * (window.DRAFTER_MODIFIED_CONFIGURATION, which already merges CLI/env values
 * and local debug-panel overrides) win over the embedded full configuration.
 */
export function getConsoleMode(): ConsoleMode {
	const readSection = (source: unknown): unknown => {
		if (typeof source !== "object" || source === null) {
			return undefined;
		}
		const section = (source as Record<string, any>).client_server;
		return section?.console_mode;
	};
	const candidates = [
		readSection((window as any).DRAFTER_MODIFIED_CONFIGURATION),
		readSection((window as any).DRAFTER_CONFIGURATION),
	];
	for (const candidate of candidates) {
		if (CONSOLE_MODES.includes(candidate as ConsoleMode)) {
			return candidate as ConsoleMode;
		}
	}
	return "auto";
}

type ConsoleVariant = "footer" | "hover";

class PrinterConsoleView {
	public readonly element: HTMLElement;
	private outputElement: HTMLElement;
	private inputElement: HTMLInputElement;
	private promptElement: HTMLElement;
	// Set when the user explicitly hid the console; new output then no
	// longer re-reveals it (only the footer toggle button brings it back).
	private userHidden = false;
	private historyIndex: number | null = null;
	private pendingInput = "";

	constructor(
		private variant: ConsoleVariant,
		private onCommand: (line: string) => Promise<void>,
		private getCommandHistory: () => string[],
	) {
		this.element = this.createStructure();
		this.outputElement = this.element.querySelector(
			".drafter-printer-console-output",
		) as HTMLElement;
		this.inputElement = this.element.querySelector(
			".drafter-printer-console-input",
		) as HTMLInputElement;
		this.promptElement = this.element.querySelector(
			".drafter-printer-console-prompt",
		) as HTMLElement;
		this.attachHandlers();
	}

	private createStructure(): HTMLElement {
		return (
			<div
				class={`drafter-printer-console drafter-printer-console-${this.variant}`}
				hidden
			>
				<div class="drafter-printer-console-header">
					<span class="drafter-printer-console-title">
						🖨️ {t("console.title")}
					</span>
					<button
						type="button"
						class="drafter-printer-console-clear"
						title={t("console.clear.tooltip")}
					>
						{t("console.clear")}
					</button>
					<button
						type="button"
						class="drafter-printer-console-hide"
						title={t("console.hide.tooltip")}
					>
						{t("console.hide")}
					</button>
				</div>
				<div class="drafter-printer-console-output"></div>
				<div class="drafter-printer-console-input-row">
					<span class="drafter-printer-console-prompt">&gt;&gt;&gt;</span>
					<input
						type="text"
						class="drafter-printer-console-input"
						placeholder={t("console.input.placeholder")}
						autoComplete="off"
						spellCheck={false}
					/>
				</div>
			</div>
		) as HTMLElement;
	}

	private attachHandlers(): void {
		const clearButton = this.element.querySelector(
			".drafter-printer-console-clear",
		) as HTMLButtonElement;
		clearButton.addEventListener("click", (event) => {
			event.stopPropagation();
			this.clear();
		});
		const hideButton = this.element.querySelector(
			".drafter-printer-console-hide",
		) as HTMLButtonElement;
		hideButton.addEventListener("click", (event) => {
			event.stopPropagation();
			this.userHidden = true;
			this.element.hidden = true;
		});
		// The footer console lives inside the site <form>, so Enter must not
		// bubble into a form submission (which would navigate the app).
		this.inputElement.addEventListener("keydown", (event) => {
			if (event.key === "Enter") {
				event.preventDefault();
				event.stopPropagation();
				this.submit();
			} else if (event.key === "ArrowUp") {
				event.preventDefault();
				this.navigateHistory(-1);
			} else if (event.key === "ArrowDown") {
				event.preventDefault();
				this.navigateHistory(1);
			}
		});
	}

	private navigateHistory(direction: number): void {
		const history = this.getCommandHistory();
		if (history.length === 0) {
			return;
		}
		if (this.historyIndex === null) {
			if (direction > 0) {
				return;
			}
			this.pendingInput = this.inputElement.value;
			this.historyIndex = history.length - 1;
		} else {
			const next = this.historyIndex + direction;
			if (next >= history.length) {
				this.historyIndex = null;
				this.inputElement.value = this.pendingInput;
				return;
			}
			this.historyIndex = Math.max(0, next);
		}
		this.inputElement.value = history[this.historyIndex];
	}

	private submit(): void {
		const line = this.inputElement.value;
		this.inputElement.value = "";
		this.historyIndex = null;
		this.pendingInput = "";
		this.inputElement.disabled = true;
		void this.onCommand(line).finally(() => {
			this.inputElement.disabled = false;
			this.inputElement.focus();
		});
	}

	public append(entry: ConsoleEntry): void {
		const node = (
			<span
				class={`drafter-printer-console-entry drafter-printer-console-${entry.stream}`}
			>
				{entry.text}
			</span>
		) as HTMLElement;
		this.outputElement.appendChild(node);
		while (this.outputElement.childElementCount > MAX_HISTORY_ENTRIES) {
			this.outputElement.firstElementChild?.remove();
		}
		this.outputElement.scrollTop = this.outputElement.scrollHeight;
	}

	/** New output arrived: reveal unless the user explicitly hid us. */
	public notifyOutput(): void {
		if (!this.userHidden) {
			this.element.hidden = false;
		}
	}

	public toggle(): void {
		if (this.element.hidden) {
			this.userHidden = false;
			this.element.hidden = false;
			this.inputElement.focus();
		} else {
			this.userHidden = true;
			this.element.hidden = true;
		}
	}

	public clear(): void {
		this.outputElement.replaceChildren();
	}

	public setContinuation(continuing: boolean): void {
		this.promptElement.textContent = continuing ? "..." : ">>>";
	}
}

export class PrinterConsoleManager {
	private history: ConsoleEntry[] = [];
	private commandHistory: string[] = [];
	private views = new Map<ParentNode, PrinterConsoleView>();
	private toastHosts = new Map<ParentNode, HTMLElement>();
	private continuation = false;
	private repl: ReplSession;

	constructor() {
		this.repl = new ReplSession((stream, text) =>
			this.recordOutput(stream, text),
		);
	}

	/**
	 * Record one chunk of console output. Called for every captured Python
	 * stdout/stderr line and for the REPL's own echo/result/error output.
	 */
	public recordOutput(stream: ConsoleStream, text: string): void {
		this.mirrorToDevtools(stream, text);
		const mode = getConsoleMode();
		if (mode === "devtools") {
			return;
		}
		this.history.push({ stream, text });
		if (this.history.length > MAX_HISTORY_ENTRIES) {
			this.history.splice(0, this.history.length - MAX_HISTORY_ENTRIES);
		}
		if (mode === "toast") {
			this.spawnToasts(stream, text);
			return;
		}
		this.forEachLiveView((view) => {
			view.append({ stream, text });
			view.notifyOutput();
		});
	}

	private mirrorToDevtools(stream: ConsoleStream, text: string): void {
		const trimmed = text.replace(/\n$/, "");
		if (stream === "stderr" || stream === "error") {
			console.error(trimmed);
		} else if (stream !== "echo") {
			console.log(trimmed);
		}
	}

	private forEachLiveView(action: (view: PrinterConsoleView) => void): void {
		for (const [root, view] of this.views) {
			if (!view.element.isConnected) {
				this.views.delete(root);
				continue;
			}
			action(view);
		}
	}

	/**
	 * Mount the console into a site frame. Called whenever a Drafter instance
	 * (re)builds its debug UI; a stale view from a torn-down frame is replaced
	 * and the buffered output is replayed into the new one.
	 */
	public attach(root: ParentNode): void {
		const mode = getConsoleMode();
		if (mode === "devtools") {
			return;
		}
		if (mode === "toast") {
			this.ensureToastHost(root);
			return;
		}

		const existing = this.views.get(root);
		if (existing?.element.isConnected) {
			return;
		}
		this.views.delete(root);

		const variant: ConsoleVariant = mode === "hover" ? "hover" : "footer";
		const host = this.findHost(root, variant);
		if (!host) {
			return;
		}

		const view = new PrinterConsoleView(
			variant,
			(line) => this.submitCommand(line),
			() => this.commandHistory,
		);
		host.appendChild(view.element);
		this.views.set(root, view);
		view.setContinuation(this.continuation);

		for (const entry of this.history) {
			view.append(entry);
		}
		if (this.history.length > 0) {
			view.notifyOutput();
		}

		if (variant === "footer") {
			this.addFooterToggleButton(root, view);
		}
	}

	private findHost(
		root: ParentNode,
		variant: ConsoleVariant,
	): HTMLElement | null {
		if (variant === "footer") {
			return root.querySelector(".drafter-footer--") as HTMLElement | null;
		}
		// The hover console floats over the page, but must still live inside
		// the instance's scope so the (possibly shadow-rooted) stylesheets
		// apply to it.
		return (
			(root.querySelector(".drafter-site--") as HTMLElement | null) ??
			(root as Document).body ??
			null
		);
	}

	private addFooterToggleButton(
		root: ParentNode,
		view: PrinterConsoleView,
	): void {
		const footerBar = root.querySelector(
			".drafter-footer-bar",
		) as HTMLElement | null;
		if (!footerBar || footerBar.querySelector(".drafter-footer-console-button")) {
			return;
		}
		const button = (
			<button
				type="button"
				class="drafter-footer-console-button"
				title={t("console.toggle.tooltip")}
			>
				🖨️ {t("console.title")}
			</button>
		) as HTMLButtonElement;
		button.addEventListener("click", (event) => {
			event.stopPropagation();
			view.toggle();
		});
		footerBar.appendChild(button);
	}

	private ensureToastHost(root: ParentNode): void {
		const existing = this.toastHosts.get(root);
		if (existing?.isConnected) {
			return;
		}
		this.toastHosts.delete(root);
		const host =
			(root.querySelector(".drafter-site--") as HTMLElement | null) ??
			(root as Document).body ??
			null;
		if (!host) {
			return;
		}
		const container = (
			<div class="drafter-printer-toasts" aria-live="polite"></div>
		) as HTMLElement;
		host.appendChild(container);
		this.toastHosts.set(root, container);
	}

	private spawnToasts(stream: ConsoleStream, text: string): void {
		const message = text.replace(/\n$/, "");
		if (message === "") {
			return;
		}
		for (const [root, container] of this.toastHosts) {
			if (!container.isConnected) {
				this.toastHosts.delete(root);
				continue;
			}
			const toast = (
				<div
					class={`drafter-printer-toast drafter-printer-console-${stream}`}
				>
					{message}
				</div>
			) as HTMLElement;
			container.appendChild(toast);
			while (container.childElementCount > MAX_TOASTS) {
				container.firstElementChild?.remove();
			}
			setTimeout(() => toast.remove(), TOAST_LIFETIME_MS);
		}
	}

	/** Run one REPL line: echo it, execute it, track continuation state. */
	public async submitCommand(line: string): Promise<void> {
		const prompt = this.continuation ? "... " : ">>> ";
		this.recordOutput("echo", `${prompt}${line}\n`);
		if (line.trim() !== "") {
			if (this.commandHistory[this.commandHistory.length - 1] !== line) {
				this.commandHistory.push(line);
			}
			if (this.commandHistory.length > MAX_HISTORY_ENTRIES) {
				this.commandHistory.shift();
			}
		}
		const status = await this.repl.run(line);
		this.continuation = status === "incomplete";
		this.forEachLiveView((view) => view.setContinuation(this.continuation));
	}
}

let sharedManager: PrinterConsoleManager | null = null;

/** The page-wide printer console (one per page, like the Pyodide runtime). */
export function getPrinterConsole(): PrinterConsoleManager {
	if (!sharedManager) {
		sharedManager = new PrinterConsoleManager();
	}
	return sharedManager;
}

/**
 * Mount the page's printer console into an instance's site frame. Safe to
 * call in any environment: failures only affect the console, never the site.
 */
export function attachPrinterConsole(root: ParentNode): void {
	try {
		getPrinterConsole().attach(root);
	} catch (error) {
		console.warn("[Drafter Console] Failed to attach printer console:", error);
	}
}
