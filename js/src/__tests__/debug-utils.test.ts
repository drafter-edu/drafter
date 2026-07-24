/**
 * Table-driven unit tests for the pure helpers in js/src/debug/utils/:
 * text.ts (wordWrap), lists.ts (intersperse), errors.ts (DebugPanelError),
 * and fs.ts (virtual filesystem accessors for both engines).
 */
import {
	afterAll,
	afterEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import { wordWrap } from "../debug/utils/text";
import { intersperse } from "../debug/utils/lists";
import { DebugPanelError } from "../debug/utils/errors";
import { getAllClientFiles, getFileContents } from "../debug/utils/fs";

describe("wordWrap", () => {
	test.each([
		["short string is unchanged", "hello", 20, "hello"],
		["wraps at the width boundary", "aaaa bbbb", 4, "aaaa\nbbbb"],
		[
			"packs words while they fit",
			"one two three four",
			10,
			"one two\nthree four",
		],
		[
			// Current behavior quirk: a first word longer than the width
			// pushes the (empty) current line first, yielding a leading
			// blank line.
			"single overlong first word produces a leading blank line",
			"supercalifragilistic",
			5,
			"\nsupercalifragilistic",
		],
		[
			"overlong word forces a break before it",
			"hi supercalifragilistic",
			5,
			"hi\nsupercalifragilistic",
		],
		["empty string stays empty", "", 10, ""],
		["exact-width word is kept on one line", "abcd", 4, "abcd"],
	])("%s", (_label, input, width, expected) => {
		expect(wordWrap(input, width)).toBe(expected);
	});

	test("wrapped output never re-joins words with extra spaces", () => {
		const wrapped = wordWrap("alpha beta gamma delta", 11);
		for (const line of wrapped.split("\n")) {
			expect(line).toBe(line.trim());
		}
	});
});

describe("intersperse", () => {
	test.each([
		["empty list", [], 0, []],
		["single element has no separator", [1], 0, [1]],
		["two elements get one separator", [1, 2], 0, [1, 0, 2]],
		["three elements get two separators", [1, 2, 3], 0, [1, 0, 2, 0, 3]],
	])("%s", (_label, input, separator, expected) => {
		expect(intersperse(input as number[], separator as number)).toEqual(
			expected,
		);
	});

	test("works with string separators", () => {
		expect(intersperse(["a", "b", "c"], "|")).toEqual([
			"a",
			"|",
			"b",
			"|",
			"c",
		]);
	});

	test("returns a new array and does not mutate the input", () => {
		const input = [1, 2];
		const result = intersperse(input, 9);
		expect(result).not.toBe(input);
		expect(input).toEqual([1, 2]);

		const single = [5];
		expect(intersperse(single, 9)).not.toBe(single);
	});
});

describe("DebugPanelError", () => {
	test("is an Error with its own name and the given message", () => {
		const error = new DebugPanelError("panel exploded");
		expect(error).toBeInstanceOf(Error);
		expect(error).toBeInstanceOf(DebugPanelError);
		expect(error.name).toBe("DebugPanelError");
		expect(error.message).toBe("panel exploded");
	});
});

describe("fs helpers", () => {
	const globalAny = globalThis as Record<string, unknown>;
	const windowAny = window as unknown as Record<string, unknown>;

	const consoleErrorSpy = jest
		.spyOn(console, "error")
		.mockImplementation(() => {});
	const consoleWarnSpy = jest
		.spyOn(console, "warn")
		.mockImplementation(() => {});

	afterEach(() => {
		delete globalAny.Sk;
		delete globalAny.pyodide;
		delete windowAny.DRAFTER_ENGINE;
		consoleErrorSpy.mockClear();
		consoleWarnSpy.mockClear();
	});

	afterAll(() => {
		consoleErrorSpy.mockRestore();
		consoleWarnSpy.mockRestore();
	});

	function useSkulpt(files: Record<string, string>) {
		windowAny.DRAFTER_ENGINE = "skulpt";
		globalAny.Sk = { builtinFiles: { files } };
	}

	function usePyodide(files: Record<string, string>) {
		windowAny.DRAFTER_ENGINE = "pyodide";
		globalAny.pyodide = {
			FS: {
				readdir: () => [".", "..", ...Object.keys(files)],
				readFile: (path: string, _options: { encoding: string }) => {
					// fs.ts always prefixes the path with "/".
					const name = path.replace(/^\//, "");
					if (!(name in files)) {
						throw new Error(`No such file: ${path}`);
					}
					return files[name];
				},
			},
		};
	}

	describe("getAllClientFiles", () => {
		test("skulpt: returns the builtinFiles keys", () => {
			useSkulpt({ "src/lib/drafter.py": "...", "main.py": "..." });
			expect(getAllClientFiles()).toEqual([
				"src/lib/drafter.py",
				"main.py",
			]);
		});

		test("pyodide: filters '.' from readdir results", () => {
			usePyodide({ "main.py": "print('hi')" });
			// Note current behavior: only "." is filtered out, ".." is kept.
			expect(getAllClientFiles()).toEqual(["..", "main.py"]);
		});

		test("unknown engine: logs an error and returns []", () => {
			windowAny.DRAFTER_ENGINE = "quantum";
			expect(getAllClientFiles()).toEqual([]);
			expect(consoleErrorSpy).toHaveBeenCalledWith(
				"Unknown DRAFTER_ENGINE:",
				"quantum",
			);
		});
	});

	describe("getFileContents", () => {
		test("skulpt: returns the file's contents", () => {
			useSkulpt({ "main.py": "print('skulpt')" });
			expect(getFileContents("main.py")).toBe("print('skulpt')");
		});

		test("skulpt: warns and returns null for a missing file", () => {
			useSkulpt({});
			expect(getFileContents("missing.py")).toBeNull();
			expect(consoleWarnSpy).toHaveBeenCalledWith(
				"File not found in Skulpt virtual filesystem: missing.py",
			);
		});

		test("pyodide: reads the file with a leading slash", () => {
			usePyodide({ "main.py": "print('pyodide')" });
			expect(getFileContents("main.py")).toBe("print('pyodide')");
		});

		test("pyodide: warns and returns null when readFile throws", () => {
			usePyodide({});
			expect(getFileContents("missing.py")).toBeNull();
			expect(consoleWarnSpy).toHaveBeenCalledWith(
				"File not found in Pyodide virtual filesystem: missing.py",
			);
		});

		test("unknown engine: logs an error and returns null", () => {
			windowAny.DRAFTER_ENGINE = "quantum";
			expect(getFileContents("main.py")).toBeNull();
			expect(consoleErrorSpy).toHaveBeenCalledWith(
				"Unknown DRAFTER_ENGINE:",
				"quantum",
			);
		});
	});
});
