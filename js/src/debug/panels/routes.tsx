import { Panel } from "./panel";

export class RoutesPanel extends Panel {
    constructor(containerId: string, instanceId: number) {
        super(
            containerId,
            instanceId,
            "drafter-debug-routes",
            "Registered Routes"
        );
    }

    protected get initialContent() {
        return (
            <div
                class={`drafter-debug-routes-list drafter-debug-routes-list-${this.instanceId}`}
            ></div>
        );
    }

    public renderRoute(route: string, signature: string): void {
        const section = this.queryWithin(
            this.scopedSelector("drafter-debug-routes-list"),
            "DebugPanel: Routes section not found."
        );

        const newRouteItem = (
            <div class="drafter-debug-route-signature">
                <strong>{route}</strong>:<pre>{signature}</pre>
            </div>
        );

        section.appendChild(newRouteItem);
    }
}
