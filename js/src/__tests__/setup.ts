// Jest setup file - runs before each test file
import "@testing-library/jest-dom";

globalThis.console = {
    ...globalThis.console,
    log: (...args: any[]) => {
        // Uncomment the next line to see logs during tests
        // process.stdout.write('[LOG] ' + args.join(' ') + '\n');
    },
};

const noop = () => {};
Object.defineProperty(window, "scrollTo", { value: noop, writable: true });

// globalThis.DecompressionStream = class {
//     constructor() {
//         // Todo
//     }
// };
