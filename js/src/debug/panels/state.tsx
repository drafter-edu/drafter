import type {
    SpecificRepresentation,
    UpdatedStateEvent,
} from "../telemetry/state";

// TODO: Cycle background colors for instances of the same type for easier distinction
// Need to track unique types seen so far, so promote to class later if needed

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

        const result = renderRepresentation(state!);

        section.replaceChildren(result);
    }
}
