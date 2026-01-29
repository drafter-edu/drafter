import { Panel } from "./panel";

export class RoutesPanel extends Panel {
    constructor(containerId: string, instanceId: number) {
        super(
            containerId,
            instanceId,
            "drafter-debug-routes",
            "Registered Routes",
        );
    }

    protected get initialContent() {
        return (
            <div>
                <div
                    class={`drafter-debug-routes-list drafter-debug-regular-routes-list-${this.instanceId}`}
                ></div>
                <details
                    class={`drafter-debug-routes-list drafter-debug-system-routes-list-${this.instanceId}`}
                >
                    <summary>System Routes</summary>
                </details>
            </div>
        );
    }

    public renderRoute(
        route: string,
        signature: string,
        isSystemRoute: boolean = false,
    ): void {
        const section = this.queryWithin(
            this.scopedSelector(
                isSystemRoute && route != "index"
                    ? "drafter-debug-system-routes-list"
                    : "drafter-debug-regular-routes-list",
            ),
            "DebugPanel: Routes section not found.",
        );

        const newRouteItem = (
            <div class="drafter-debug-route-signature">
                <strong>{route}</strong>:<pre>{signature}</pre>
            </div>
        );

        section.appendChild(newRouteItem);
    }
}
