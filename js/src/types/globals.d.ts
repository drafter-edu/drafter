declare global {
	type pyBool = import("./skulpt").pyBool;
	type pyInt = import("./skulpt").pyInt;
	type pyObject = import("./skulpt").pyObject;
	type pyStr = import("./skulpt").pyStr;
	type pyList = import("./skulpt").pyList;
	type pyTuple = import("./skulpt").pyTuple;
	type pyDict = import("./skulpt").pyDict;
	type pyFunc = import("./skulpt").pyFunc;
	type pyNone = import("./skulpt").pyNone;

	var DRAFTER_SITE_ROOT_ELEMENT_ID: string;
	var stopHotkeyListener: () => void;
	var hotkeyListenerReady: boolean;
	var DebugPanel: typeof import("../debug").DebugPanel;

	var DRAFTER_ENGINE: "skulpt" | "pyodide";
	/**
	 * A short hash of the main file's full path, embedded by the index
	 * template; part of the per-app localStorage keys (storage_keys.ts).
	 */
	var DRAFTER_MAIN_FILE_ID: string | undefined;
	var DRAFTER_CONFIGURATION: Record<string, unknown> | undefined;
	var DRAFTER_MODIFIED_CONFIGURATION: Record<string, unknown> | undefined;
	var DRAFTER_EMBEDDED_MODIFIED_CONFIGURATION:
		| Record<string, unknown>
		| undefined;
	var DRAFTER_PERSISTED_CONFIGURATION_OVERRIDES:
		| Record<string, unknown>
		| undefined;

	// Pyodide globals:
	var pyodide: any;
	var micropip: any;
}

export {};
