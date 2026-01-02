export class RoutesPanel {
    public renderRoute(route: string, signature: string): void {
        const section = document.getElementById("drafter-debug-routes-list");
        if (!section) {
            throw new Error("DebugPanel: Routes section not found.");
        }

        const newRouteItem = (
            <div class="drafter-debug-route-signature">
                <strong>{route}</strong>:<pre>{signature}</pre>
            </div>
        );

        section.appendChild(newRouteItem);
    }
}
