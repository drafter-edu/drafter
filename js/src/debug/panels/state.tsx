export class StatePanel {
    private currentState: any = null;
    public renderState(newState: any): void {
        this.currentState = newState;
        const section = document.getElementById(
            "drafter-debug-current-state-content"
        );
        if (!section) {
            throw new Error("DebugPanel: State section not found.");
        }

        const stateContent = (
            <div class="state-content">
                <div dangerouslySetInnerHTML={{ __html: newState }}></div>
            </div>
        );

        section.replaceChildren(stateContent);
    }
}
