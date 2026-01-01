export class RoutesPanel {
    public renderRoute(route: string, signature: string): void {
        const section = document.getElementById("drafter-routes-list");
        if (!section) {
            throw new Error("DebugPanel: Routes section not found.");
        }

        // Create a clickable link for the route
        const routeLink = (
            <a href={route} class="route-link">
                <strong>{route}</strong>
            </a>
        ) as HTMLAnchorElement;

        const newRouteItem = (
            <div class="route-signature">
                {routeLink}:<pre>{signature}</pre>
            </div>
        );

        section.appendChild(newRouteItem);
    }
}
