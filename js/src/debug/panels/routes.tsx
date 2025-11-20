export class RoutesPanel {
    public renderRoute(route: string, signature: string): void {
        const section = document.getElementById("drafter-routes-list");
        if (!section) {
            throw new Error("DebugPanel: Routes section not found.");
        }

        const newRouteItem = (
            <div class="route-signature">
                <strong>{route}</strong>:<pre>{signature}</pre>
            </div>
        );

        section.appendChild(newRouteItem);
    }
}
