import { Panel } from "./panel";
import type { SpecificRepresentation } from "../telemetry/state";

// TODO: Cycle background colors for instances of the same type for easier distinction
// Need to track unique types seen so far, so promote to class later if needed

function renderRepresentation(rep: SpecificRepresentation) {
	switch (rep.kind) {
		case "primitive":
			return (
				<div class="drafter-debug-rep-primitive drafter-debug-rep-row">
					<div class="drafter-debug-rep-primitive-value drafter-debug-rep-cell">
						{"" + rep.value}
					</div>
					<div class="drafter-debug-rep-primitive-type drafter-debug-rep-cell">
						{rep.type}
					</div>
				</div>
			);
		case "empty_linear_collection":
			return (
				<div class="drafter-debug-rep-empty-linear-collection drafter-debug-rep-row">
					<div class="drafter-debug-rep-elc-value drafter-debug-rep-cell">
						[]
					</div>
					<div class="drafter-debug-rep-elc-type drafter-debug-rep-cell">
						Empty {rep.type}
					</div>
				</div>
			);
		case "homogenous_linear_collection":
			return (
				<div class="drafter-debug-rep-homogenous-linear-collection drafter-debug-rep-column">
					<div class="drafter-debug-rep-hlc-type drafter-debug-rep-cell">
						{rep.type}[{rep.elementType}]
					</div>
					<div class="drafter-debug-rep-hlc-elements drafter-debug-rep-cell drafter-debug-rep-row">
						{rep.elements.map((el, index) => (
							<div class="drafter-debug-rep-hlc-element drafter-debug-rep-row">
								<div class="drafter-debug-rep-hlc-element-value drafter-debug-rep-cell">
									{renderRepresentation(el)}
								</div>
							</div>
						))}
					</div>
				</div>
			);
		case "dataclass":
			return (
				<div class="drafter-debug-rep-dataclass drafter-debug-rep-col">
					<div class="drafter-debug-rep-dataclass-type drafter-debug-rep-cell">
						{rep.type}
					</div>
					<div class="drafter-debug-rep-dataclass-fields drafter-debug-rep-cell">
						{rep.fields.map((field) => (
							<>
								<div class="drafter-debug-rep-dataclass-field-name  drafter-debug-rep-cell">
									{field.name}:
								</div>
								<div class="drafter-debug-rep-dataclass-field-value  drafter-debug-rep-cell">
									{renderRepresentation(field.value)}
								</div>
							</>
						))}
					</div>
				</div>
			);
		case "homogenous_grid":
			return (
				<div class="drafter-debug-rep-homogenous-grid drafter-debug-rep-column">
					<div class="drafter-debug-rep-hg-type drafter-debug-rep-cell">
						{rep.type}[{rep.type}[{rep.elementType}]]
					</div>
					<div class="drafter-debug-rep-hg-rows">
						{rep.rows.map((row) => (
							<div class="drafter-debug-rep-hg-row">
								{row.elements.map((el) => (
									<div class="drafter-debug-rep-hg-element">
										{renderRepresentation(el)}
									</div>
								))}
							</div>
						))}
					</div>
				</div>
			);
		case "linear_collection":
			return (
				<div class="drafter-debug-rep-linear-collection drafter-debug-rep-column">
					<div class="drafter-debug-rep-lc-type drafter-debug-rep-cell">
						{rep.type}{" "}
						<span class="drafter-debug-count">
							({rep.elements.length} items)
						</span>
					</div>
					<div class="drafter-debug-rep-lc-elements drafter-debug-rep-cell drafter-debug-rep-row">
						{rep.elements.map((el, index) => (
							<div class="drafter-debug-rep-lc-element drafter-debug-rep-row">
								<div class="drafter-debug-rep-lc-element-value drafter-debug-rep-cell">
									{renderRepresentation(el)}
								</div>
							</div>
						))}
					</div>
				</div>
			);
		case "tuple":
			return (
				<div class="drafter-debug-rep-tuple drafter-debug-rep-column">
					<div class="drafter-debug-rep-tuple-type drafter-debug-rep-cell">
						{rep.type}{" "}
						<span class="drafter-debug-count">
							({rep.elements.length} items)
						</span>
					</div>
					<div class="drafter-debug-rep-tuple-elements drafter-debug-rep-cell drafter-debug-rep-row">
						{rep.elements.map((el, index) => (
							<div class="drafter-debug-rep-tuple-element drafter-debug-rep-row">
								<div class="drafter-debug-rep-tuple-element-value drafter-debug-rep-cell">
									{renderRepresentation(el)}
								</div>
							</div>
						))}
					</div>
				</div>
			);
		case "dict":
			return (
				<div class="drafter-debug-rep-dict drafter-debug-rep-column">
					<div class="drafter-debug-rep-dict-type drafter-debug-rep-cell">
						{rep.type}{" "}
						<span class="drafter-debug-count">
							({rep.entries.length} entries)
						</span>
					</div>
					<div class="drafter-debug-rep-dict-entries drafter-debug-rep-cell">
						{rep.entries.map((entry, index) => (
							<div class="drafter-debug-rep-dict-entry drafter-debug-rep-row">
								<div class="drafter-debug-rep-dict-key drafter-debug-rep-cell">
									{renderRepresentation(entry.key)}
								</div>
								<div class="drafter-debug-rep-dict-value drafter-debug-rep-cell">
									{renderRepresentation(entry.value)}
								</div>
							</div>
						))}
					</div>
				</div>
			);
		case "empty_tuple":
			return (
				<div class="drafter-debug-rep-empty-tuple drafter-debug-rep-row">
					<div class="drafter-debug-rep-et-value drafter-debug-rep-cell">
						()
					</div>
					<div class="drafter-debug-rep-et-type drafter-debug-rep-cell">
						Empty tuple
					</div>
				</div>
			);
		case "empty_dict":
			return (
				<div class="drafter-debug-rep-empty-dict drafter-debug-rep-row">
					<div class="drafter-debug-rep-ed-value drafter-debug-rep-cell">
						{"{}"}
					</div>
					<div class="drafter-debug-rep-ed-type drafter-debug-rep-cell">
						Empty dict
					</div>
				</div>
			);
		case "cycle_reference":
			return (
				<div class="drafter-debug-rep-cycle drafter-debug-rep-row">
					<div class="drafter-debug-rep-cycle-message drafter-debug-rep-cell">
						↻ Circular reference to {rep.type} (ID: {rep.targetId})
					</div>
				</div>
			);
		case "max_depth_reached":
			return (
				<div class="drafter-debug-rep-max-depth drafter-debug-rep-row">
					<div class="drafter-debug-rep-max-depth-message drafter-debug-rep-cell">
						... (max depth reached for {rep.type})
					</div>
				</div>
			);
		case "unknown":
			return (
				<div class="drafter-debug-rep-unknown drafter-debug-rep-row">
					<div class="drafter-debug-rep-unknown-type drafter-debug-rep-cell">
						{rep.type}
					</div>
					<div class="drafter-debug-rep-unknown-value drafter-debug-rep-cell">
						{rep.value}
					</div>
				</div>
			);
		case "error":
			return (
				<div class="drafter-debug-rep-error drafter-debug-rep-column">
					<div class="drafter-debug-rep-error-message drafter-debug-rep-cell">
						⚠️ Error: {rep.error_message}
					</div>
					<div class="drafter-debug-rep-error-details drafter-debug-rep-cell">
						Type: {rep.type}, Value: {rep.value}
					</div>
				</div>
			);
		case "complete_failure":
			return (
				<div class="drafter-debug-rep-failure drafter-debug-rep-column">
					<div class="drafter-debug-rep-failure-message drafter-debug-rep-cell">
						❌ Complete Failure
					</div>
					<div class="drafter-debug-rep-failure-details drafter-debug-rep-cell">
						Original error: {rep.error_message}
						<br />
						Recovery error: {rep.new_error_message}
					</div>
				</div>
			);
		case "image": {
			const dimensions =
				rep.width != null && rep.height != null
					? `${rep.width}×${rep.height}`
					: "";
			const format = rep.mime
				? rep.mime.replace("image/", "").toUpperCase()
				: "";
			const caption = [rep.filename, dimensions, format]
				.filter(Boolean)
				.join(" — ");
			return (
				<div class="drafter-debug-rep-image drafter-debug-rep-row">
					<div class="drafter-debug-rep-image-preview drafter-debug-rep-cell">
						{rep.value ? (
							<img
								src={rep.value}
								alt={rep.filename ?? rep.type}
								class="drafter-debug-rep-image-value"
							/>
						) : (
							<span>Image not available</span>
						)}
						{caption ? (
							<div class="drafter-debug-rep-image-caption">
								{caption}
							</div>
						) : null}
					</div>
					<div class="drafter-debug-rep-image-type drafter-debug-rep-cell">
						{rep.type}
					</div>
				</div>
			);
		}
		case "bytes":
			return (
				<div class="drafter-debug-rep-bytes drafter-debug-rep-row">
					<div class="drafter-debug-rep-bytes-value drafter-debug-rep-cell">
						{rep.thumbnail ? (
							<img
								src={rep.thumbnail}
								alt={rep.type}
								class="drafter-debug-rep-image-value"
							/>
						) : null}
						<code class="drafter-debug-rep-bytes-preview">
							{rep.preview}
							{rep.length > 16 ? " …" : ""}
						</code>
					</div>
					<div class="drafter-debug-rep-bytes-type drafter-debug-rep-cell">
						{rep.type} ({rep.length}{" "}
						{rep.length === 1 ? "byte" : "bytes"})
					</div>
				</div>
			);
		default:
			return (
				<div class="drafter-debug-rep-default drafter-debug-rep-row">
					<div class="drafter-debug-rep-default-kind drafter-debug-rep-cell">
						{rep.kind}
					</div>
					<div class="drafter-debug-rep-default-type drafter-debug-rep-cell">
						{rep.type}
					</div>
				</div>
			);
	}
}

/**
 * Stable plain-text rendering of a state representation, for diffing two
 * states. The per-value `id` and `complexity` bookkeeping fields are
 * stripped so they never show up as spurious differences.
 */
export function representationToText(
	rep: SpecificRepresentation | null,
): string {
	if (rep === null) {
		return "";
	}
	const strip = (value: unknown): unknown => {
		if (Array.isArray(value)) {
			return value.map(strip);
		}
		if (value && typeof value === "object") {
			const cleaned: Record<string, unknown> = {};
			for (const [key, entry] of Object.entries(value)) {
				if (key === "id" || key === "complexity") {
					continue;
				}
				cleaned[key] = strip(entry);
			}
			return cleaned;
		}
		return value;
	};
	return JSON.stringify(strip(rep), null, 2);
}

export class StatePanel extends Panel {
	private currentState: SpecificRepresentation | null = null;
	private previousState: SpecificRepresentation | null = null;

	constructor(containerId: string, instanceId: number, root: ParentNode = document) {
		super(
			containerId,
			instanceId,
			"drafter-debug-current-state",
			"Current State",
			root,
		);
	}

	protected get initialContent() {
		return <div></div>;
	}

	public renderState(state: SpecificRepresentation): void {
		this.previousState = this.currentState;
		this.currentState = state;
		const result = renderRepresentation(state!);
		this.getContentElement().replaceChildren(result);
	}

	/**
	 * Plain-text rendering of the current state, for previews outside the
	 * panel (e.g. the Edit State dialog).
	 */
	public getPlainText(): string {
		return this.getContentElement().textContent ?? "";
	}

	/**
	 * Text renderings of the previous and current states for the Current
	 * tab's state diff; each is null when that state does not exist yet.
	 */
	public getDiffTexts(): {
		previous: string | null;
		current: string | null;
	} {
		return {
			previous: this.previousState
				? representationToText(this.previousState)
				: null,
			current: this.currentState
				? representationToText(this.currentState)
				: null,
		};
	}
}
