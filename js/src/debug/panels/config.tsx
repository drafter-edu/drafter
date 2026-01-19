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

    private newItemElement(key: string, value: any) {
        return (
            <div class="drafter-debug-config-item" data-key={key}>
                <strong>{key}</strong>:<pre>{JSON.stringify(value)}</pre>
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
            existingItem.innerHTML = `<strong>${key}</strong>:<pre>${JSON.stringify(value)}</pre>`;
        } else {
            const configItem = this.newItemElement(key, value);
            section.appendChild(configItem);
        }
    }
}
