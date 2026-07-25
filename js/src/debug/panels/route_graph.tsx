import { Panel } from "./panel";
import { t } from "../../i18n";

/**
 * STUB: Overview tab's route graph. Renders a hardcoded sample graph (SVG
 * boxes and arrows) purely for spacing and visualization; a real graph of
 * the registered routes and the links/redirects between them will replace
 * it.
 */
export class RouteGraphPanel extends Panel {
	constructor(
		containerId: string,
		instanceId: number,
		root: ParentNode = document,
	) {
		super(
			containerId,
			instanceId,
			"drafter-debug-route-graph",
			"Route Graph",
			root,
		);
	}

	protected get initialContent() {
		return (
			<div class="drafter-debug-route-graph-stub">
				<p class="drafter-debug-stub-notice">
					{t("route_graph.coming_soon")}
				</p>
				<svg
					viewBox="0 0 420 160"
					width="420"
					height="160"
					role="img"
					aria-label="Sample route graph"
					class="drafter-debug-route-graph-sample"
				>
					<defs>
						<marker
							id={`drafter-route-arrow-${this.instanceId}`}
							markerWidth="8"
							markerHeight="8"
							refX="7"
							refY="4"
							orient="auto"
						>
							<path d="M0,0 L8,4 L0,8 z" fill="#3a7db8" />
						</marker>
					</defs>
					<rect
						x="10"
						y="60"
						width="90"
						height="36"
						rx="6"
						fill="#e3eefa"
						stroke="#3a7db8"
					/>
					<text x="55" y="83" text-anchor="middle">
						index
					</text>
					<rect
						x="170"
						y="15"
						width="110"
						height="36"
						rx="6"
						fill="#e3eefa"
						stroke="#3a7db8"
					/>
					<text x="225" y="38" text-anchor="middle">
						guess
					</text>
					<rect
						x="170"
						y="105"
						width="110"
						height="36"
						rx="6"
						fill="#e3eefa"
						stroke="#3a7db8"
					/>
					<text x="225" y="128" text-anchor="middle">
						give_up
					</text>
					<rect
						x="330"
						y="60"
						width="80"
						height="36"
						rx="6"
						fill="#e3eefa"
						stroke="#3a7db8"
					/>
					<text x="370" y="83" text-anchor="middle">
						result
					</text>
					<line
						x1="100"
						y1="70"
						x2="168"
						y2="40"
						stroke="#3a7db8"
						marker-end={`url(#drafter-route-arrow-${this.instanceId})`}
					/>
					<line
						x1="100"
						y1="88"
						x2="168"
						y2="118"
						stroke="#3a7db8"
						marker-end={`url(#drafter-route-arrow-${this.instanceId})`}
					/>
					<line
						x1="280"
						y1="40"
						x2="328"
						y2="70"
						stroke="#3a7db8"
						marker-end={`url(#drafter-route-arrow-${this.instanceId})`}
					/>
					<line
						x1="280"
						y1="118"
						x2="328"
						y2="88"
						stroke="#3a7db8"
						marker-end={`url(#drafter-route-arrow-${this.instanceId})`}
					/>
				</svg>
			</div>
		);
	}
}
