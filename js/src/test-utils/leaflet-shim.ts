/**
 * Minimal Leaflet stand-in for jest (mapped via moduleNameMapper, like the
 * pyodide shim). Records enough state for tests to drive map/marker events
 * and assert what <drafter-map> asked Leaflet to do, without real layout.
 */

type Handler = (event?: unknown) => void;

export class FakeMap {
	handlers: Record<string, Handler[]> = {};
	center: [number, number];
	zoom: number;
	removed = false;
	invalidateCount = 0;

	constructor(
		public container: HTMLElement,
		options: { center: [number, number]; zoom: number },
	) {
		this.center = options.center;
		this.zoom = options.zoom;
	}

	on(events: string, handler: Handler): this {
		for (const name of events.split(" ")) {
			(this.handlers[name] ??= []).push(handler);
		}
		return this;
	}

	fire(name: string, event?: unknown): void {
		for (const handler of this.handlers[name] ?? []) {
			handler(event);
		}
	}

	getCenter() {
		return { lat: this.center[0], lng: this.center[1] };
	}

	getZoom(): number {
		return this.zoom;
	}

	setView(center: [number, number], zoom: number): this {
		this.center = center;
		this.zoom = zoom;
		return this;
	}

	setZoom(zoom: number): this {
		this.zoom = zoom;
		return this;
	}

	invalidateSize(): this {
		this.invalidateCount += 1;
		return this;
	}

	remove(): this {
		this.removed = true;
		return this;
	}

	addLayer(): this {
		return this;
	}
}

export class FakeLayerGroup {
	layers: FakeMarker[] = [];
	map: FakeMap | null = null;

	addTo(map: FakeMap): this {
		this.map = map;
		return this;
	}

	clearLayers(): this {
		this.layers = [];
		return this;
	}
}

export class FakeMarker {
	tooltip = "";
	handlers: Record<string, Handler[]> = {};

	constructor(
		public latlng: [number, number],
		public options: unknown,
	) {}

	bindTooltip(text: string): this {
		this.tooltip = text;
		return this;
	}

	on(events: string, handler: Handler): this {
		for (const name of events.split(" ")) {
			(this.handlers[name] ??= []).push(handler);
		}
		return this;
	}

	fire(name: string, event?: unknown): void {
		for (const handler of this.handlers[name] ?? []) {
			handler(event);
		}
	}

	addTo(group: FakeLayerGroup): this {
		group.layers.push(this);
		return this;
	}
}

export const created: { maps: FakeMap[]; layerGroups: FakeLayerGroup[] } = {
	maps: [],
	layerGroups: [],
};

export function __reset(): void {
	created.maps.length = 0;
	created.layerGroups.length = 0;
}

export function map(
	container: HTMLElement,
	options: { center: [number, number]; zoom: number },
): FakeMap {
	const instance = new FakeMap(container, options);
	created.maps.push(instance);
	return instance;
}

export function tileLayer(_url: string, _options: unknown) {
	return {
		addTo(_map: FakeMap) {
			return this;
		},
	};
}

export function layerGroup(): FakeLayerGroup {
	const group = new FakeLayerGroup();
	created.layerGroups.push(group);
	return group;
}

export function circleMarker(
	latlng: [number, number],
	options: unknown,
): FakeMarker {
	return new FakeMarker(latlng, options);
}

export const DomEvent = {
	stopPropagation(): void {},
};
