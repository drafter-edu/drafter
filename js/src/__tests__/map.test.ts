import { afterEach, beforeEach, describe, expect, test } from "@jest/globals";

// "leaflet" resolves to the recording shim via jest moduleNameMapper.
import * as L from "leaflet";
import "../components/map";

const shim = L as unknown as typeof import("../test-utils/leaflet-shim");

class StubResizeObserver {
	observe(): void {}
	unobserve(): void {}
	disconnect(): void {}
}

describe("drafter-map", () => {
	beforeEach(() => {
		document.body.innerHTML = "";
		shim.__reset();
		(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
			StubResizeObserver;
	});

	afterEach(() => {
		document.body.innerHTML = "";
	});

	function createComponent(
		attributes: Record<string, string> = { name: "spot" },
	): HTMLElement {
		const element = document.createElement("drafter-map");
		for (const [name, value] of Object.entries(attributes)) {
			element.setAttribute(name, value);
		}
		document.body.appendChild(element);
		return element;
	}

	function lastMap() {
		const map = shim.created.maps.at(-1);
		if (!map) {
			throw new Error("No Leaflet map was created");
		}
		return map;
	}

	function getHiddenInput(element: HTMLElement): HTMLInputElement {
		const input = element.querySelector('input[type="hidden"]');
		if (!(input instanceof HTMLInputElement)) {
			throw new Error("Hidden input was not rendered");
		}
		return input;
	}

	test("renders a hidden JSON form field and a shadow-rooted map", () => {
		const element = createComponent({ name: "spot" });
		const input = getHiddenInput(element);
		expect(input.name).toBe("spot");
		expect(input.getAttribute("data-transform")).toBe("json-decode");
		expect(element.shadowRoot).not.toBeNull();
		expect(
			element.shadowRoot!.querySelector(".drafter-map-container"),
		).not.toBeNull();
		expect(shim.created.maps).toHaveLength(1);
	});

	test("parses center and defaults zoom to 13 when centered", () => {
		createComponent({ name: "spot", center: "39.68,-75.75" });
		expect(lastMap().center).toEqual([39.68, -75.75]);
		expect(lastMap().zoom).toBe(13);
	});

	test("defaults to a world view without a center", () => {
		createComponent({ name: "spot" });
		expect(lastMap().center).toEqual([0, 0]);
		expect(lastMap().zoom).toBe(2);
	});

	test("renders markers from the markers attribute", () => {
		createComponent({
			name: "spot",
			markers: JSON.stringify([
				{ latitude: 1, longitude: 2, label: "Home" },
				{ latitude: 3, longitude: 4 },
			]),
		});
		const group = shim.created.layerGroups.at(-1)!;
		expect(group.layers).toHaveLength(2);
		expect(group.layers[0].latlng).toEqual([1, 2]);
		expect(group.layers[0].tooltip).toBe("Home");
		expect(group.layers[1].tooltip).toBe("");
	});

	test("map click dispatches pin event and fills the form field", () => {
		const element = createComponent({ name: "spot" });
		const details: unknown[] = [];
		element.addEventListener("pin", (event) => {
			details.push((event as CustomEvent).detail);
		});
		lastMap().fire("click", { latlng: { lat: 39.5, lng: -75.5 } });
		expect(details).toEqual([{ latitude: 39.5, longitude: -75.5 }]);
		expect(JSON.parse(getHiddenInput(element).value)).toEqual({
			latitude: 39.5,
			longitude: -75.5,
		});
	});

	test("marker click dispatches marker event with its label", () => {
		const element = createComponent({
			name: "spot",
			markers: JSON.stringify([{ latitude: 1, longitude: 2, label: "A" }]),
		});
		const details: unknown[] = [];
		element.addEventListener("marker", (event) => {
			details.push((event as CustomEvent).detail);
		});
		shim.created.layerGroups.at(-1)!.layers[0].fire("click", {});
		expect(details).toEqual([{ latitude: 1, longitude: 2, label: "A" }]);
	});

	test("pan/zoom dispatches view event with the new center and zoom", () => {
		const element = createComponent({ name: "spot", center: "10,20" });
		const details: unknown[] = [];
		element.addEventListener("view", (event) => {
			details.push((event as CustomEvent).detail);
		});
		lastMap().setView([11, 21], 8);
		lastMap().fire("moveend");
		expect(details).toEqual([{ latitude: 11, longitude: 21, zoom: 8 }]);
	});

	test("updating the markers attribute replaces markers without a rebuild", () => {
		const element = createComponent({
			name: "spot",
			markers: JSON.stringify([{ latitude: 1, longitude: 2 }]),
		});
		element.setAttribute(
			"markers",
			JSON.stringify([
				{ latitude: 3, longitude: 4, label: "B" },
				{ latitude: 5, longitude: 6 },
			]),
		);
		expect(shim.created.maps).toHaveLength(1);
		const group = shim.created.layerGroups.at(-1)!;
		expect(group.layers).toHaveLength(2);
		expect(group.layers[0].tooltip).toBe("B");
	});

	test("removal tears the map down", () => {
		const element = createComponent({ name: "spot" });
		const map = lastMap();
		element.remove();
		expect(map.removed).toBe(true);
	});

	test("persistence move keeps the running map alive", () => {
		const element = createComponent({ name: "spot" }) as HTMLElement & {
			_drafterBeginMove(): void;
			_drafterEndMove(): void;
		};
		const map = lastMap();
		element._drafterBeginMove();
		element.remove();
		document.body.appendChild(element);
		element._drafterEndMove();
		expect(map.removed).toBe(false);
		expect(shim.created.maps).toHaveLength(1);
	});
});

describe("drafter-map (extended)", () => {
	beforeEach(() => {
		document.body.innerHTML = "";
		shim.__reset();
		(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
			StubResizeObserver;
	});

	afterEach(() => {
		document.body.innerHTML = "";
	});

	function createComponent(
		attributes: Record<string, string> = { name: "spot" },
	): HTMLElement {
		const element = document.createElement("drafter-map");
		for (const [name, value] of Object.entries(attributes)) {
			element.setAttribute(name, value);
		}
		document.body.appendChild(element);
		return element;
	}

	function lastMap() {
		const map = shim.created.maps.at(-1);
		if (!map) {
			throw new Error("No Leaflet map was created");
		}
		return map;
	}

	function getHiddenInput(element: HTMLElement): HTMLInputElement {
		const input = element.querySelector('input[type="hidden"]');
		if (!(input instanceof HTMLInputElement)) {
			throw new Error("Hidden input was not rendered");
		}
		return input;
	}

	test("center update recenters in place, keeping the current zoom", () => {
		const element = createComponent({ name: "spot", center: "10,20" });
		expect(lastMap().zoom).toBe(13);

		element.setAttribute("center", "30,40");
		expect(shim.created.maps).toHaveLength(1);
		expect(lastMap().center).toEqual([30, 40]);
		expect(lastMap().zoom).toBe(13);
	});

	test("center update uses the zoom attribute when one is present", () => {
		const element = createComponent({
			name: "spot",
			center: "10,20",
			zoom: "5",
		});
		element.setAttribute("center", "30,40");
		expect(lastMap().center).toEqual([30, 40]);
		expect(lastMap().zoom).toBe(5);
	});

	test("zoom update calls setZoom without rebuilding the map", () => {
		const element = createComponent({ name: "spot", center: "10,20" });
		element.setAttribute("zoom", "7");
		expect(shim.created.maps).toHaveLength(1);
		expect(lastMap().zoom).toBe(7);
	});

	test("height update resizes the host and invalidates the map size", () => {
		const element = createComponent({ name: "spot" });
		expect(element.style.height).toBe("300px");
		const before = lastMap().invalidateCount;

		element.setAttribute("height", "450");
		expect(element.style.height).toBe("450px");
		expect(lastMap().invalidateCount).toBe(before + 1);

		// A non-numeric height falls back to the 300px default.
		element.setAttribute("height", "banana");
		expect(element.style.height).toBe("300px");
	});

	test("a malformed center falls back to the default world view", () => {
		// A center that fails to parse is treated the same as a missing one:
		// the map falls back entirely to the whole-world default view.
		createComponent({ name: "spot", center: "1,banana" });
		expect(lastMap().center).toEqual([0, 0]);
		expect(lastMap().zoom).toBe(2);

		shim.__reset();
		createComponent({ name: "spot", center: "1,2,3" });
		expect(lastMap().center).toEqual([0, 0]);
		expect(lastMap().zoom).toBe(2);
	});

	test("bad marker JSON is tolerated and clears previously-drawn markers", () => {
		const element = createComponent({
			name: "spot",
			markers: JSON.stringify([{ latitude: 1, longitude: 2 }]),
		});
		const group = shim.created.layerGroups.at(-1)!;
		expect(group.layers).toHaveLength(1);

		// Malformed JSON parses to no markers, which wipes the layer group.
		element.setAttribute("markers", "{oops");
		expect(group.layers).toHaveLength(0);

		// Entries without finite coordinates are filtered out; valid ones stay.
		element.setAttribute(
			"markers",
			JSON.stringify([
				{ latitude: 5, longitude: 6 },
				{ latitude: "x", longitude: 6 },
				{ label: "no coords" },
				null,
			]),
		);
		expect(group.layers).toHaveLength(1);
		expect(group.layers[0].latlng).toEqual([5, 6]);
	});

	test("marker updates reuse the same map and layer group (diff, not rebuild)", () => {
		const element = createComponent({
			name: "spot",
			markers: JSON.stringify([{ latitude: 1, longitude: 2 }]),
		});
		element.setAttribute(
			"markers",
			JSON.stringify([{ latitude: 3, longitude: 4 }]),
		);
		expect(shim.created.maps).toHaveLength(1);
		expect(shim.created.layerGroups).toHaveLength(1);
	});

	test("name update renames the hidden form field in place", () => {
		const element = createComponent({ name: "spot" });
		element.setAttribute("name", "location");
		expect(getHiddenInput(element).name).toBe("location");

		element.removeAttribute("name");
		expect(getHiddenInput(element).name).toBe("");
	});

	test("marker clicks fill the hidden form field with the marker payload", () => {
		const element = createComponent({
			name: "spot",
			markers: JSON.stringify([{ latitude: 1, longitude: 2, label: "A" }]),
		});
		shim.created.layerGroups.at(-1)!.layers[0].fire("click", {});
		expect(JSON.parse(getHiddenInput(element).value)).toEqual({
			latitude: 1,
			longitude: 2,
			label: "A",
		});
	});

	test("detach disconnects the resize observer; reattach builds a fresh map", () => {
		const observers: Array<{ disconnects: number }> = [];
		class RecordingResizeObserver {
			disconnects = 0;
			constructor() {
				observers.push(this);
			}
			observe(): void {}
			unobserve(): void {}
			disconnect(): void {
				this.disconnects += 1;
			}
		}
		(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
			RecordingResizeObserver;

		const element = createComponent({ name: "spot" });
		const firstMap = lastMap();
		expect(observers).toHaveLength(1);

		element.remove();
		expect(firstMap.removed).toBe(true);
		expect(observers[0].disconnects).toBe(1);

		// Reattaching is a full rebuild: a second Leaflet map and observer.
		document.body.appendChild(element);
		expect(shim.created.maps).toHaveLength(2);
		expect(lastMap()).not.toBe(firstMap);
		expect(lastMap().removed).toBe(false);
		expect(observers).toHaveLength(2);
		expect(getHiddenInput(element).name).toBe("spot");
	});
});
