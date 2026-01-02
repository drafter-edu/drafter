import type {
    SpecificRepresentation,
    UpdatedStateEvent,
} from "../telemetry/state";

// TODO: Cycle background colors for instances of the same type for easier distinction
// Need to track unique types seen so far, so promote to class later if needed

/**
 * Helper function to extract type information from a representation.
 */
function getTypeFromRepresentation(rep: SpecificRepresentation): string {
    if ('type' in rep) {
        return rep.type as string;
    }
    switch (rep.kind) {
        case "primitive":
            return rep.type || "unknown";
        case "dataclass":
            return rep.type || "dataclass";
        case "empty_linear_collection":
        case "homogenous_linear_collection":
        case "linear_collection":
            return rep.type || "list";
        case "tuple":
        case "empty_tuple":
            return "tuple";
        case "dict":
        case "empty_dict":
            return "dict";
        case "homogenous_grid":
            return rep.type || "grid";
        case "cycle_reference":
            return "circular ref";
        case "max_depth_reached":
            return "...";
        case "unknown":
            return rep.type || "unknown";
        case "error":
        case "complete_failure":
            return "error";
        default:
            return "unknown";
    }
}

/**
 * Truncates a string value by showing start and end with "..." in the middle.
 * Makes the truncated text clickable to expand/collapse.
 */
function createTruncatableString(value: string, maxLength: number = 80): HTMLElement {
    if (value.length <= maxLength) {
        return <span>{value}</span>;
    }
    
    const halfLength = Math.floor((maxLength - 3) / 2);
    const truncated = value.slice(0, halfLength) + "..." + value.slice(-halfLength);
    
    const span = (
        <span class="truncatable-string truncated" data-full-value={value}>
            {truncated}
        </span>
    ) as HTMLElement;
    
    span.addEventListener("click", (e) => {
        const target = e.target as HTMLElement;
        const isTruncated = target.classList.contains("truncated");
        if (isTruncated) {
            target.textContent = target.dataset.fullValue || value;
            target.classList.remove("truncated");
        } else {
            target.textContent = truncated;
            target.classList.add("truncated");
        }
    });
    
    return span;
}

function renderRepresentation(rep: SpecificRepresentation) {
    switch (rep.kind) {
        case "primitive":
            const valueElement = rep.type === "str" 
                ? createTruncatableString(String(rep.value))
                : rep.value;
            return (
                <div class="drafter-debug-rep-primitive drafter-debug-rep-row">
                    <div class="drafter-debug-rep-primitive-value drafter-debug-rep-cell">
                        {valueElement}
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
                        {rep.type}[{rep.elementType}] <span class="drafter-debug-count">({rep.elements.length} items)</span>
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
                        {rep.type} <span class="drafter-debug-count">({rep.fields.length} fields)</span>
                    </div>
                    <table class="drafter-debug-rep-dataclass-table">
                        <thead>
                            <tr>
                                <th class="drafter-debug-rep-field-name-header">Field</th>
                                <th class="drafter-debug-rep-field-value-header">Value</th>
                                <th class="drafter-debug-rep-field-type-header">Type</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rep.fields.map((field) => (
                                <tr class="drafter-debug-rep-dataclass-field-row">
                                    <td class="drafter-debug-rep-dataclass-field-name">
                                        {field.name}
                                    </td>
                                    <td class="drafter-debug-rep-dataclass-field-value">
                                        {renderRepresentation(field.value)}
                                    </td>
                                    <td class="drafter-debug-rep-dataclass-field-type">
                                        {field.value.type || getTypeFromRepresentation(field.value)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            );
        case "homogenous_grid":
            return (
                <div class="drafter-debug-rep-homogenous-grid drafter-debug-rep-column">
                    <div class="drafter-debug-rep-hg-type drafter-debug-rep-cell">
                        {rep.type}[{rep.type}[{rep.elementType}]] <span class="drafter-debug-count">({rep.rows.length} rows)</span>
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
                        {rep.type} <span class="drafter-debug-count">({rep.elements.length} items)</span>
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
                        {rep.type} <span class="drafter-debug-count">({rep.elements.length} items)</span>
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
                        {rep.type} <span class="drafter-debug-count">({rep.entries.length} entries)</span>
                    </div>
                    <div class="drafter-debug-rep-dict-entries drafter-debug-rep-cell">
                        {rep.entries.map((entry, index) => (
                            <div class="drafter-debug-rep-dict-entry drafter-debug-rep-row">
                                <div class="drafter-debug-rep-dict-key drafter-debug-rep-cell">
                                    {renderRepresentation(entry.key)}:
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
                        {{}}
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

export class StatePanel {
    private currentState: SpecificRepresentation | null = null;
    private isEnabled: boolean = true;
    private toggleButton: HTMLButtonElement | null = null;

    constructor() {
        this.addToggleButton();
    }

    private addToggleButton(): void {
        const section = document.getElementById(
            "drafter-debug-current-state-content"
        );
        if (!section) {
            return;
        }

        // Add toggle button at the top of the state panel
        this.toggleButton = (
            <button 
                class="drafter-debug-state-toggle-btn"
                title="Toggle state representation (improves performance when disabled)"
            >
                🔄 State Enabled
            </button>
        ) as HTMLButtonElement;

        this.toggleButton.addEventListener("click", () => this.toggleState());
        section.parentElement?.insertBefore(this.toggleButton, section);
    }

    private toggleState(): void {
        this.isEnabled = !this.isEnabled;
        
        if (this.toggleButton) {
            this.toggleButton.textContent = this.isEnabled 
                ? "🔄 State Enabled" 
                : "⏸️ State Disabled";
            this.toggleButton.classList.toggle("disabled", !this.isEnabled);
        }

        // Re-render current state if available
        if (this.currentState) {
            this.renderState(this.currentState);
        }
    }

    public renderState(
        state: SpecificRepresentation | null,
        html?: string
    ): void {
        this.currentState = state ?? null;

        const section = document.getElementById(
            "drafter-debug-current-state-content"
        );
        if (!section) {
            throw new Error("DebugPanel: State section not found.");
        }

        console.log(state);

        // If state representation is disabled, show a simple message
        if (!this.isEnabled) {
            section.replaceChildren(
                <div class="drafter-debug-state-disabled">
                    State representation disabled for performance. Click the button above to enable.
                </div>
            );
            return;
        }

        const result = renderRepresentation(state!);

        section.replaceChildren(result);
    }
}
