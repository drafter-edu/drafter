import { clearDrafterSiteRoot, setupPyodide } from "../../pyodide.index";

type WindowWithPyodideState = Window & {
	pyodide?: any;
	__drafterPyodideMounted?: boolean;
};

function ensureRootElement() {
	if (!document.getElementById("drafter-root--")) {
		document.body.innerHTML = "<div id='drafter-root--'></div>";
	}
}

export async function setupPyodideWithLocalDrafter() {
	ensureRootElement();

	const pyodide = await setupPyodide({
		pyodideUrl: "",
		systemPackages: [],
	});

	const stateWindow = window as WindowWithPyodideState;
	if (!stateWindow.__drafterPyodideMounted) {
		const drafterSrcDir = (globalThis as Record<string, unknown>)
			.__drafterSrcDir as string;
		const mountPoint = "/drafter_pkg/drafter";
		pyodide.FS.mkdirTree(mountPoint);
		pyodide.FS.mount(
			pyodide.FS.filesystems.NODEFS,
			{ root: drafterSrcDir },
			mountPoint,
		);

		stateWindow.__drafterPyodideMounted = true;
	}

	await micropip.install("bakery");
	await micropip.install("pillow");

	// Drafter expects this config file to exist when DRAFTER_CONFIG_FILE is set.
	pyodide.FS.writeFile("/_drafter_config.json", "{}");

	await pyodide.runPythonAsync(
		[
			"import sys",
			"sys.dont_write_bytecode = True",
			'if "/drafter_pkg" not in sys.path:',
			'    sys.path.insert(0, "/drafter_pkg")',
		].join("\n"),
	);

	return pyodide;
}

export async function resetPyodideDrafterRuntime() {
	const pyodide = (window as WindowWithPyodideState).pyodide;
	if (!pyodide) {
		return;
	}

	// Heap forensics: a leaked bridge listener compounds renders quadratically
	// and only blows up on slow machines (CI), so always log the trend.
	const gc = (globalThis as { gc?: () => void }).gc;
	if (gc) {
		gc();
	}
	process.stderr.write(
		`[harness] heapUsed before reset: ${Math.round(
			process.memoryUsage().heapUsed / 1024 / 1024,
		)}MB\n`,
	);

	// Tear down the previous run's server AND its bridge (event listeners,
	// debug panel, navigation handlers). set_main_server(None) alone leaves
	// the old bridge listening, so every past run re-renders on each event —
	// across dozens of examples that compounds into an OOM.
	await pyodide.runPythonAsync(
		[
			"from drafter.client_server.commands import reset_server_for_root, set_main_server",
			'reset_server_for_root("drafter-root--")',
			"set_main_server(None)",
		].join("\n"),
	);

	clearDrafterSiteRoot();
}
