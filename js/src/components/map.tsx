/**
 * <drafter-map> — the client side of the Python Map component
 * (src/drafter/components/map.py; the CONTRACT there defines the event
 * payloads this element must emit).
 *
 * - The element attaches its OWN shadow root holding the Leaflet container
 *   and Leaflet's CSS (imported as text), so the map is fully encapsulated
 *   regardless of whether the Drafter instance itself uses a shadow root.
 * - A hidden <input data-transform="json-decode"> stays in the light DOM so
 *   it participates in form collection, exactly like drafter-current-location.
 * - Interactions dispatch CustomEvents on the host element ("pin" for map
 *   clicks, "marker" for marker clicks, "view" for move/zoom), which the
 *   bridge's data--drafter-handlers wiring turns into route calls.
 */
import * as L from "leaflet";
import leafletCss from "leaflet/dist/leaflet.css";
import { DrafterHTMLElement } from "./drafterHTMLElement";

type MarkerSpec = {
	latitude: number;
	longitude: number;
	label?: string;
};

const HOST_CSS = `
:host {
	display: block;
	width: 100%;
}
.drafter-map-container {
	width: 100%;
	height: 100%;
	min-height: 120px;
}
`;

const DEFAULT_CENTER: [number, number] = [0, 0];
// Python's Map omits zoom=13 (its default) from the rendered attributes, so
// the element must assume 13 whenever a center is given; without a center it
// falls back to a whole-world view.
const DEFAULT_ZOOM_WITH_CENTER = 13;
const DEFAULT_ZOOM_WORLD = 2;
const DEFAULT_HEIGHT = 300;

const OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const OSM_ATTRIBUTION =
	'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

/** Returns the parsed center, or null when the attribute is missing or malformed. */
function parseCenter(raw: string | null): [number, number] | null {
	if (!raw) {
		return null;
	}
	const parts = raw.split(",").map((part) => Number(part.trim()));
	if (parts.length !== 2 || parts.some((n) => !Number.isFinite(n))) {
		return null;
	}
	return [parts[0], parts[1]];
}

function parseMarkers(raw: string | null): MarkerSpec[] {
	if (!raw) {
		return [];
	}
	try {
		const parsed = JSON.parse(raw);
		if (!Array.isArray(parsed)) {
			return [];
		}
		return parsed.filter(
			(entry) =>
				entry &&
				Number.isFinite(entry.latitude) &&
				Number.isFinite(entry.longitude),
		);
	} catch {
		return [];
	}
}

class DrafterMap extends DrafterHTMLElement {
	static get observedAttributes() {
		return ["name", "center", "zoom", "markers", "height"];
	}

	private map: L.Map | null = null;
	private markerLayer: L.LayerGroup | null = null;
	private input: HTMLInputElement | null = null;
	private container: HTMLDivElement | null = null;
	private resizeObserver: ResizeObserver | null = null;

	private getName(): string {
		return this.getAttribute("name") ?? "";
	}

	private emit(eventType: string, detail: Record<string, unknown>): void {
		if (this.input !== null) {
			this.input.value = JSON.stringify(detail);
		}
		this.dispatchEvent(new CustomEvent(eventType, { detail }));
	}

	private renderStructure(): void {
		// The hidden input lives in the LIGHT DOM: form association walks the
		// light tree, so this is what makes the map's last interaction show up
		// in the route's form payload.
		const input = document.createElement("input");
		input.type = "hidden";
		input.name = this.getName();
		input.setAttribute("data-transform", "json-decode");
		this.replaceChildren(input);
		this.input = input;

		const shadow = this.shadowRoot ?? this.attachShadow({ mode: "open" });
		const style = document.createElement("style");
		style.textContent = leafletCss + HOST_CSS;
		const container = document.createElement("div");
		container.className = "drafter-map-container";
		shadow.replaceChildren(style, container);
		this.container = container;

		this.style.height = `${this.getNumberAttribute("height", DEFAULT_HEIGHT)}px`;
	}

	private buildMap(): void {
		if (this.container === null) {
			return;
		}
		// A missing OR malformed center both fall back to the whole-world view.
		const center = parseCenter(this.getAttribute("center"));
		const defaultZoom =
			center === null ? DEFAULT_ZOOM_WORLD : DEFAULT_ZOOM_WITH_CENTER;
		const map = L.map(this.container, {
			center: center ?? DEFAULT_CENTER,
			zoom: this.getNumberAttribute("zoom", defaultZoom),
		});
		L.tileLayer(OSM_TILE_URL, { attribution: OSM_ATTRIBUTION }).addTo(map);

		map.on("click", (event: L.LeafletMouseEvent) => {
			this.emit("pin", {
				latitude: event.latlng.lat,
				longitude: event.latlng.lng,
			});
		});
		map.on("moveend zoomend", () => {
			const center = map.getCenter();
			this.dispatchEvent(
				new CustomEvent("view", {
					detail: {
						latitude: center.lat,
						longitude: center.lng,
						zoom: map.getZoom(),
					},
				}),
			);
		});

		this.markerLayer = L.layerGroup().addTo(map);
		this.map = map;
		this.syncMarkers();

		// The element may not have been laid out yet when Leaflet measured it.
		requestAnimationFrame(() => map.invalidateSize());
		this.resizeObserver = new ResizeObserver(() => map.invalidateSize());
		this.resizeObserver.observe(this.container);
	}

	private syncMarkers(): void {
		if (this.map === null || this.markerLayer === null) {
			return;
		}
		this.markerLayer.clearLayers();
		for (const spec of parseMarkers(this.getAttribute("markers"))) {
			// circleMarker avoids Leaflet's default icon images, which don't
			// resolve when the CSS is inlined into a shadow root.
			const marker = L.circleMarker([spec.latitude, spec.longitude], {
				radius: 8,
			});
			if (spec.label) {
				marker.bindTooltip(spec.label);
			}
			marker.on("click", (event: L.LeafletMouseEvent) => {
				L.DomEvent.stopPropagation(event);
				this.emit("marker", {
					latitude: spec.latitude,
					longitude: spec.longitude,
					label: spec.label ?? "",
				});
			});
			marker.addTo(this.markerLayer);
		}
	}

	connectedCallback() {
		if (this.isMovingBetweenParents() || this.map !== null) {
			this.map?.invalidateSize();
			return;
		}
		this.renderStructure();
		this.buildMap();
	}

	connectedMoveCallback(): void {
		this.map?.invalidateSize();
	}

	attributeChangedCallback(
		name: string,
		oldValue: string | null,
		newValue: string | null,
	) {
		if (oldValue === newValue || this.map === null) {
			return;
		}
		if (name === "name" && this.input !== null) {
			this.input.name = newValue ?? "";
		} else if (name === "center") {
			this.map.setView(
				parseCenter(newValue) ?? DEFAULT_CENTER,
				this.getNumberAttribute("zoom", this.map.getZoom()),
			);
		} else if (name === "zoom") {
			this.map.setZoom(
				this.getNumberAttribute("zoom", DEFAULT_ZOOM_WITH_CENTER),
			);
		} else if (name === "markers") {
			this.syncMarkers();
		} else if (name === "height") {
			this.style.height = `${this.getNumberAttribute("height", DEFAULT_HEIGHT)}px`;
			this.map.invalidateSize();
		}
	}

	disconnectedCallback() {
		if (this.isMovingBetweenParents()) {
			return;
		}
		this.resizeObserver?.disconnect();
		this.resizeObserver = null;
		this.map?.remove();
		this.map = null;
		this.markerLayer = null;
		this.input = null;
		this.container = null;
	}
}

customElements.define("drafter-map", DrafterMap);
