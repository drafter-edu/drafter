import * as Diff2Html from "diff2html";
import { createTwoFilesPatch } from "diff";
import { Panel } from "./panel";
import { t } from "../../i18n";
import { errorFingerprint } from "../utils/errors";
import type { ErrorDetailsJson } from "../telemetry/errors";

/**
 * The Current tab's lead panel: the route being shown, the page content the
 * server produced for it, the errors/warnings raised while producing it
 * (reset on every navigation), and a diff of the current state against the
 * previous one (rendered with diff2html, like test-failure diffs).
 */
export class CurrentPanel extends Panel {
	// Problems not tied to any single request (startup/setup warnings and
	// errors). They are re-rendered after every navigation instead of being
	// wiped with the per-page problems.
	private persistentProblems: ErrorDetailsJson[] = [];
	/** Rendered problems on the current slate, by fingerprint, with their
	 * repeat counters, so a repeat raises a count instead of a new line. */
	private shownProblems = new Map<
		string,
		{ element: HTMLElement; count: number }
	>();

	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
		// Supplier of the state texts to diff (backed by the StatePanel).
		private readonly getDiffTexts: () => {
			previous: string | null;
			current: string | null;
		} = () => ({ previous: null, current: null }),
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-current",
			"Current Page",
			root,
		);
	}

	protected get initialContent() {
		const diffButton = (
			<button
				type="button"
				class="drafter-debug-button-- drafter-debug-current-diff-button"
				title={t("current.diff.tooltip")}
			>
				{t("current.diff.button")}
			</button>
		) as HTMLButtonElement;
		diffButton.addEventListener("click", () => this.renderStateDiff());
		return (
			<>
				<div class="drafter-debug-current-route-row">
					<strong>{t("current.route")}</strong>{" "}
					<code
						class={`drafter-debug-current-route drafter-debug-current-route-${this.instanceId}`}
					></code>
				</div>
				<details class="drafter-debug-current-page">
					<summary>{t("current.page_content")}</summary>
					<pre
						class={`drafter-debug-current-page-content drafter-debug-current-page-content-${this.instanceId}`}
					></pre>
				</details>
				<div class="drafter-debug-current-problems-area">
					<strong>{t("current.problems")}</strong>
					<div
						class={`drafter-debug-current-problems drafter-debug-current-problems-${this.instanceId}`}
					>
						<p class="drafter-debug-current-no-problems">
							{t("current.no_problems")}
						</p>
					</div>
				</div>
				<div class="drafter-debug-current-diff-area">
					{diffButton}
					<div
						class={`drafter-debug-current-diff drafter-debug-current-diff-${this.instanceId}`}
					></div>
				</div>
			</>
		);
	}

	private getRouteElement(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-current-route"),
			"DebugPanel: Current route display not found.",
		);
	}

	private getProblemsElement(): HTMLElement {
		return this.queryWithin(
			this.scopedSelector("drafter-debug-current-problems"),
			"DebugPanel: Current problems list not found.",
		);
	}

	/**
	 * A new navigation began: clear the per-page problems list, keeping the
	 * persistent (page-independent) problems visible.
	 */
	public startNavigation(route: string): void {
		this.getRouteElement().textContent = route;
		const problems = this.getProblemsElement();
		problems.replaceChildren();
		this.shownProblems.clear();
		for (const envelope of this.persistentProblems) {
			this.shownProblems.set(errorFingerprint(envelope), {
				element: this.renderProblem(problems, envelope),
				count: 1,
			});
		}
		if (this.persistentProblems.length === 0) {
			problems.appendChild(
				(
					<p class="drafter-debug-current-no-problems">
						{t("current.no_problems")}
					</p>
				) as HTMLElement,
			);
		}
	}

	public setRoute(route: string): void {
		this.getRouteElement().textContent = route;
	}

	public setPageContent(formatted: string): void {
		this.queryWithin(
			this.scopedSelector("drafter-debug-current-page-content"),
			"DebugPanel: Current page content area not found.",
		).textContent = formatted;
	}

	/**
	 * Append an error/warning envelope to this page's problems list. When
	 * `persistent` is true, the problem is not tied to the current page and
	 * stays visible across navigations (e.g. warnings raised at startup).
	 */
	public addProblem(
		envelope: ErrorDetailsJson,
		persistent: boolean = false,
	): boolean {
		const fingerprint = errorFingerprint(envelope);
		const shown = this.shownProblems.get(fingerprint);
		if (shown) {
			shown.count += 1;
			this.renderRepeatCount(shown.element, shown.count);
			return false;
		}
		if (persistent) {
			this.persistentProblems.push(envelope);
		}
		const problems = this.getProblemsElement();
		problems
			.querySelector(".drafter-debug-current-no-problems")
			?.remove();
		const element = this.renderProblem(problems, envelope);
		this.shownProblems.set(fingerprint, { element, count: 1 });
		return true;
	}

	/** Show (or update) the "×N" badge on a problem that has repeated. */
	private renderRepeatCount(element: HTMLElement, count: number): void {
		let badge = element.querySelector(
			".drafter-debug-problem-count",
		) as HTMLElement | null;
		if (!badge) {
			badge = (
				<span
					class="drafter-debug-problem-count"
					title={t("current.problem_repeats", { n: count })}
				></span>
			) as HTMLElement;
			element
				.querySelector(".drafter-debug-current-problem-message")
				?.after(badge);
		}
		badge.textContent = `×${count}`;
		badge.title = t("current.problem_repeats", { n: count });
	}

	private renderProblem(
		problems: HTMLElement,
		envelope: ErrorDetailsJson,
	): HTMLElement {
		const isError =
			envelope.severity === "error" || envelope.severity === "critical";
		// Lead with the student-friendly explanation when the envelope
		// carries one; the technical message then joins the collapsible
		// details so it stays one click away (and is never shown twice).
		const friendly = envelope.friendly_message ?? "";
		const primary = friendly || envelope.message;
		// Bridged envelopes may hold a proxy here, so even key inspection
		// stays inside the try.
		let structured = "";
		try {
			if (envelope.data && Object.keys(envelope.data).length > 0) {
				structured = JSON.stringify(envelope.data, null, 2);
			}
		} catch {
			structured = "";
		}
		const technicalParts = friendly
			? [envelope.message, envelope.details, structured]
			: [envelope.details, structured];
		const technical = technicalParts
			.filter((part) => part && part !== primary)
			.join("\n");
		const element = (
				<div
					class={`drafter-debug-current-problem ${
						isError ? "is-error" : "is-warning"
					}`}
				>
					<span class="drafter-debug-current-problem-icon">
						{isError ? "❌" : "⚠"}
					</span>
					<span class="drafter-debug-current-problem-message">
						{primary}
					</span>
					{technical ? (
						<details class="drafter-debug-current-problem-details">
							<summary>{t("current.problem_details")}</summary>
							<pre>{technical}</pre>
						</details>
					) : null}
				</div>
			) as HTMLElement;
		problems.appendChild(element);
		return element;
	}

	/** Render the previous-vs-current state diff below the button. */
	public renderStateDiff(): void {
		const target = this.queryWithin(
			this.scopedSelector("drafter-debug-current-diff"),
			"DebugPanel: Current state diff area not found.",
		);
		const { previous, current } = this.getDiffTexts();
		if (current === null) {
			target.replaceChildren(
				(
					<p class="drafter-debug-current-diff-empty">
						{t("current.diff.no_state")}
					</p>
				) as HTMLElement,
			);
			return;
		}
		if (previous === null) {
			target.replaceChildren(
				(
					<p class="drafter-debug-current-diff-empty">
						{t("current.diff.no_previous")}
					</p>
				) as HTMLElement,
			);
			return;
		}
		if (previous === current) {
			target.replaceChildren(
				(
					<p class="drafter-debug-current-diff-empty">
						{t("current.diff.identical")}
					</p>
				) as HTMLElement,
			);
			return;
		}
		const patch = createTwoFilesPatch(
			t("current.diff.previous_label"),
			t("current.diff.current_label"),
			`${previous}\n`,
			`${current}\n`,
		);
		target.innerHTML = Diff2Html.html(patch, {
			drawFileList: false,
			matching: "words",
			diffStyle: "char",
			outputFormat: "side-by-side",
		});
	}
}
