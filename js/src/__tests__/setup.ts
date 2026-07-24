// Jest setup file - runs before each test file
import "@testing-library/jest-dom";

globalThis.console = {
	...globalThis.console,
	log: (...args: any[]) => {
		// Uncomment the next line to see logs during tests
		// process.stdout.write("[LOG] " + args.join(" ") + "\n");
	},
};

const noop = () => {};
Object.defineProperty(window, "scrollTo", { value: noop, writable: true });
Object.defineProperty(window.URL, "createObjectURL", {
	value: noop,
	writable: true,
});

Object.defineProperty(window, "showDirectoryPicker", {
	value: noop,
	writable: true,
});

// jsdom has no ResizeObserver; the map component observes its container.
if (typeof globalThis.ResizeObserver === "undefined") {
	class StubResizeObserver {
		observe() {}
		unobserve() {}
		disconnect() {}
	}
	(globalThis as { ResizeObserver?: unknown }).ResizeObserver =
		StubResizeObserver;
}

// Mock DecompressionStream if needed

// globalThis.DecompressionStream = class {
//     constructor() {
//         // Todo
//     }
// };
