import type {
    SpecificRepresentation,
    UpdatedStateEvent,
} from "../telemetry/state";

// TODO: Cycle background colors for instances of the same type for easier distinction
// Need to track unique types seen so far, so promote to class later if needed

function renderRepresentation(rep: SpecificRepresentation) {
    switch (rep.kind) {
        case "primitive":
            return (
                <div class="drafter-debug-rep-primitive drafter-debug-rep-row">
                    <div class="drafter-debug-rep-primitive-value drafter-debug-rep-cell">
                        {rep.value}
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
