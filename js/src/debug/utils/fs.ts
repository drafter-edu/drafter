export function getAllClientFiles() {
	if (window.DRAFTER_ENGINE === "skulpt") {
		return Object.keys(Sk.builtinFiles["files"]);
	} else if (window.DRAFTER_ENGINE === "pyodide") {
		return pyodide.FS.readdir("/").filter((name: string) => name !== ".");
	} else {
		console.error("Unknown DRAFTER_ENGINE:", window.DRAFTER_ENGINE);
		return [];
	}
}

export function getFileContents(path: string): string | null {
	if (window.DRAFTER_ENGINE === "skulpt") {
		const fileContent = Sk.builtinFiles["files"][path];
		if (fileContent === undefined) {
			console.warn(
				`File not found in Skulpt virtual filesystem: ${path}`,
			);
			return null;
		}
		return fileContent;
	} else if (window.DRAFTER_ENGINE === "pyodide") {
		try {
			return pyodide.FS.readFile("/" + path, { encoding: "utf8" });
		} catch (error) {
			console.warn(
				`File not found in Pyodide virtual filesystem: ${path}`,
			);
			return null;
		}
	} else {
		console.error("Unknown DRAFTER_ENGINE:", window.DRAFTER_ENGINE);
		return null;
	}
}
