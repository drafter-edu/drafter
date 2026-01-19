import { Panel } from "./panel";

export class ConfigPanel extends Panel {
    constructor(containerId: string, instanceId: number) {
        super(containerId, instanceId, "drafter-debug-config", "Configuration");
    }

    protected get initialContent() {
        return (
            <div
                class={`drafter-debug-config-list drafter-debug-config-list-${this.instanceId}`}
            ></div>
        );
    }

    public renderInitialConfig(config: Record<string, any>): void {
        const section = this.queryWithin(
            this.scopedSelector("drafter-debug-config-list"),
            "DebugPanel: Config section not found.",
        );

        Object.entries(config).forEach(([key, value]) => {
            const configItem = this.newItemElement(key, value);
            section.appendChild(configItem);
        });
    }

    private newItemContents(key: string, value: any) {
        return (
            <>
                <strong>
                    <code>{key}</code>
                </strong>
                : <code>{JSON.stringify(value)}</code>
            </>
        );
    }

    private newItemElement(key: string, value: any) {
        return (
            <div class="drafter-debug-config-item" data-key={key}>
                {this.newItemContents(key, value)}
            </div>
        );
    }

    public renderConfigUpdate(key: string, value: any): void {
        console.log("Rendering config update", { key, value });
        const section = this.queryWithin(
            this.scopedSelector("drafter-debug-config-list"),
            "DebugPanel: Config section not found.",
        );

        const existingItem = section.querySelector(
            `.drafter-debug-config-item[data-key="${key}"]`,
        );
        if (existingItem) {
            const newContents = this.newItemContents(key, value);
            existingItem.innerHTML = "";
            existingItem.appendChild(newContents);
            existingItem.classList.add("drafter-debug-config-item-updated");
        } else {
            const configItem = this.newItemElement(key, value);
            section.appendChild(configItem);
        }
    }
}
