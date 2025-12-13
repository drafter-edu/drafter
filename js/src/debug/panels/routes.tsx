export class RoutesPanel {
    private routes: Map<string, string> = new Map();
    private currentView: "list" | "graph" = "list";

    constructor() {
        const section = document.getElementById("drafter-routes-list");
        if (section) {
            this.setupViewToggle(section);
        }
    }

    private setupViewToggle(section: HTMLElement): void {
        const toggleContainer = document.createElement("div");
        toggleContainer.className = "routes-view-toggle";
        
        const listButton = (
            <button class="view-toggle-btn active" data-view="list">
                📋 List View
            </button>
        );
        const graphButton = (
            <button class="view-toggle-btn" data-view="graph">
                🗺️ Graph View
            </button>
        );
        
        toggleContainer.appendChild(listButton);
        toggleContainer.appendChild(graphButton);
        
        section.parentElement?.insertBefore(toggleContainer, section);
        
        listButton.addEventListener("click", () => {
            this.switchView("list");
            listButton.classList.add("active");
            graphButton.classList.remove("active");
        });
        
        graphButton.addEventListener("click", () => {
            this.switchView("graph");
            graphButton.classList.add("active");
            listButton.classList.remove("active");
        });
    }

    private switchView(view: "list" | "graph"): void {
        this.currentView = view;
        this.renderAllRoutes();
    }

    public renderRoute(route: string, signature: string): void {
        this.routes.set(route, signature);
        this.renderAllRoutes();
    }

    private renderAllRoutes(): void {
        const section = document.getElementById("drafter-routes-list");
        if (!section) {
            throw new Error("DebugPanel: Routes section not found.");
        }

        section.replaceChildren();

        if (this.currentView === "list") {
            this.renderListView(section);
        } else {
            this.renderGraphView(section);
        }
    }

    private renderListView(section: HTMLElement): void {
        const sortedRoutes = Array.from(this.routes.entries()).sort((a, b) => 
            a[0].localeCompare(b[0])
        );

        for (const [route, signature] of sortedRoutes) {
            const routeItem = (
                <div class="route-signature">
                    <strong>{route}</strong>:<pre>{signature}</pre>
                </div>
            );
            section.appendChild(routeItem);
        }

        if (this.routes.size === 0) {
            section.appendChild(<div class="routes-empty">No routes registered yet.</div>);
        }
    }

    private renderGraphView(section: HTMLElement): void {
        const sortedRoutes = Array.from(this.routes.entries()).sort((a, b) => 
            a[0].localeCompare(b[0])
        );

        const graphContainer = <div class="routes-graph"></div>;
        
        if (this.routes.size === 0) {
            graphContainer.appendChild(
                <div class="routes-empty">No routes registered yet.</div>
            );
        } else {
            // Create a simple hierarchical graph
            const routeNodes: Record<string, string[]> = {};
            
            for (const [route] of sortedRoutes) {
                const parts = route.split('_');
                const category = parts[0] || 'main';
                
                if (!routeNodes[category]) {
                    routeNodes[category] = [];
                }
                routeNodes[category].push(route);
            }

            for (const [category, routes] of Object.entries(routeNodes)) {
                const categoryNode = (
                    <div class="route-category">
                        <div class="category-header">{category}</div>
                        <div class="category-routes">
                            {routes.map(route => (
                                <div class="route-node" title={this.routes.get(route)}>
                                    <span class="route-name">{route}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                );
                graphContainer.appendChild(categoryNode);
            }
        }

        section.appendChild(graphContainer);
    }
}
