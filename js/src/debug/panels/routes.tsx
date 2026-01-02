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

        // Create input field for testing routes with parameters
        const paramInput = (
            <input 
                type="text" 
                class="route-param-input" 
                placeholder="?param=value&other=123"
                title="Add query parameters to test this route"
            />
        ) as HTMLInputElement;

        // Create test button
        const testButton = (
            <button class="route-test-btn" title="Test route with parameters">
                🧪 Test
            </button>
        ) as HTMLButtonElement;

        testButton.addEventListener('click', () => {
            const params = paramInput.value.trim();
            const url = params.startsWith('?') ? `${route}${params}` : 
                        params ? `${route}?${params}` : route;
            window.location.href = url;
        });

        // Allow Enter key to trigger test
        paramInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                testButton.click();
            }
        });

        const testControls = (
            <div class="route-test-controls">
                {paramInput}
                {testButton}
            </div>
        );

        const newRouteItem = (
            <div class="route-signature">
                {routeLink}:<pre>{signature}</pre>
                {testControls}
            </div>
        );

        section.appendChild(newRouteItem);
    }
}
