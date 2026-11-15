/**
 * Names for what Drafter keeps in the browser's localStorage.
 *
 * localStorage is shared by every page of an origin, and every site the
 * development server runs lives at the same origin (http://localhost:8080
 * by default). Without a per-app part in the key, the save slots, the
 * chosen theme, and the open debug tab of one student program would show
 * up in the next program run on that port, and in every site published
 * under one github.io address.
 *
 * Every per-app value is therefore stored under
 * `drafter.app.<scope>.<name>`, where the scope is a short hash of two
 * things:
 *
 * - the page address (origin and path, without the query or fragment, so
 *   moving between routes with `?route=` does not change it), and
 * - the main file, as the `DRAFTER_MAIN_FILE_ID` the page template embeds
 *   (see `main_file_id` in src/drafter/scaffolding/templating.py). That id
 *   is itself a hash of the file's full path, made in Python, so neither
 *   the page nor localStorage carries the student's folder names.
 *
 * Hashing the pair keeps key names short and keeps the address out of
 * them. The keys still start with `drafter.`, so the debug panel's Browser
 * Storage section lists them and can delete them. Values stored before
 * keys were scoped (for example `drafter.debug.snapshot.v1.quick`) are
 * never read or moved: there is no telling which app they belonged to.
 * They stay in storage, where that section still lists them.
 *
 * This module is the one place that builds these keys.
 */

/** Start of every per-app key, before the scope. */
export const APP_STORAGE_PREFIX = "drafter.app.";

/**
 * Hash a string to a short, stable hexadecimal token (cyrb53, a
 * non-cryptographic 53-bit hash). Synchronous on purpose: keys are needed
 * while the bundle is still loading, before anything can be awaited.
 */
export function hashText(text: string): string {
	let high = 0xdeadbeef;
	let low = 0x41c6ce57;
	for (let index = 0; index < text.length; index++) {
		const code = text.charCodeAt(index);
		high = Math.imul(high ^ code, 2654435761);
		low = Math.imul(low ^ code, 1597334677);
	}
	high =
		Math.imul(high ^ (high >>> 16), 2246822507) ^
		Math.imul(low ^ (low >>> 13), 3266489909);
	low =
		Math.imul(low ^ (low >>> 16), 2246822507) ^
		Math.imul(high ^ (high >>> 13), 3266489909);
	const value = 4294967296 * (2097151 & low) + (high >>> 0);
	return value.toString(16).padStart(14, "0");
}

/**
 * The address of the page an app is served from: origin and path only.
 * A trailing `index.html` and trailing slashes are dropped, so the usual
 * spellings of one address (`/site/`, `/site`, `/site/index.html`) agree.
 */
export function pageAddress(win: Window = window): string {
	let origin = "";
	let path = "";
	try {
		origin = win.location.origin ?? "";
		path = win.location.pathname ?? "";
	} catch {
		// A window whose location cannot be read (a cross-origin frame)
		// falls back to the main file alone.
	}
	path = path.replace(/index\.html?$/i, "").replace(/\/+$/, "");
	return `${origin}${path}`;
}

/** The id of the app's main file that the page template embedded, or "". */
export function mainFileId(win: Window = window): string {
	try {
		const id = (win as unknown as { DRAFTER_MAIN_FILE_ID?: unknown })
			.DRAFTER_MAIN_FILE_ID;
		return typeof id === "string" ? id : "";
	} catch {
		return "";
	}
}

/**
 * The scope that tells one app's stored values from another's: a hash of
 * the page address and the main file.
 *
 * @param win The window the app renders into. An instance embedded in an
 *   iframe passes that iframe's window, whose address and main file are
 *   its own, not the hosting page's.
 */
export function appStorageScope(win: Window = window): string {
	return hashText(`${pageAddress(win)}\n${mainFileId(win)}`);
}

/**
 * The localStorage key for one of an app's stored values.
 *
 * @param name What is stored, with its format version, such as
 *   `debug.active-tab.v1`. A name ending in `.` is a prefix for a family
 *   of keys (the snapshot slots).
 * @param win The window the app renders into (see appStorageScope).
 */
export function appStorageKey(name: string, win: Window = window): string {
	return `${APP_STORAGE_PREFIX}${appStorageScope(win)}.${name}`;
}
