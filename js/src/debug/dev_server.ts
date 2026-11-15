/**
 * Talking to Drafter's local development server from the browser.
 *
 * A page served by the development server (src/drafter/app/app_server.py)
 * can ask that server to shut down, through the debug panel's "Stop Server"
 * menu item or the button on the `--stop-server` system route. Deployed
 * sites have no server to stop, so instances record whether their document
 * came from the development server and the controls stay hidden elsewhere.
 *
 * The same page can ask the server which files sit next to the student's
 * program (the debug panel's Host File System list). A deployed site has
 * no such server either, so that list is only shown on these documents.
 */

/** Mirror of INTERNAL_ROUTES["STOP_SERVER"] in src/drafter/config/urls.py. */
export const STOP_SERVER_PATH = "/__drafter_stop_server";

/** Mirror of INTERNAL_ROUTES["LIST_FILES"] in src/drafter/config/urls.py. */
export const LIST_FILES_PATH = "/__drafter_list_files";

/** One entry of a folder on the development server's side. */
export interface HostFileEntry {
	name: string;
	is_dir: boolean;
}

/**
 * Documents served by the development server. A page the development
 * server serves hosts exactly one instance, while embedded instances (the
 * documentation's demos, iframes) live in documents that never get marked.
 */
const devServerDocuments = new WeakSet<Document>();

/** Record that `doc` was served by the local development server. */
export function markDevServerDocument(doc: Document): void {
	devServerDocuments.add(doc);
}

/** Whether `doc` was served by the local development server. */
export function isDevServerDocument(doc: Document): boolean {
	return devServerDocuments.has(doc);
}

/** The document that owns a debug panel's root (a Document or ShadowRoot). */
export function ownerDocumentOf(root: ParentNode): Document {
	if (root instanceof Document) {
		return root;
	}
	return root.ownerDocument ?? document;
}

/**
 * Ask the development server which files and folders are in a folder of
 * the student's project (see list_user_files in
 * src/drafter/app/app_server.py).
 *
 * Resolves to the folder's entries, folders first and each group in
 * alphabetical order. Resolves to null when no listing could be had: the
 * server is gone, it does not share the project's files
 * (`serve_adjacent_files` off), the folder does not exist, or the answer
 * was not a listing. Never throws.
 *
 * @param path The folder to list, relative to the project folder; the
 *   empty string is the project folder itself.
 */
export async function requestHostFileListing(
	path: string = "",
): Promise<HostFileEntry[] | null> {
	if (typeof fetch !== "function") {
		return null;
	}
	try {
		const query = path ? `?path=${encodeURIComponent(path)}` : "";
		const response = await fetch(`${LIST_FILES_PATH}${query}`, {
			cache: "no-store",
		});
		if (!response.ok) {
			return null;
		}
		const payload = (await response.json()) as { entries?: unknown };
		if (!Array.isArray(payload?.entries)) {
			return null;
		}
		const entries: HostFileEntry[] = [];
		for (const entry of payload.entries as Array<Record<string, unknown>>) {
			if (entry && typeof entry.name === "string") {
				entries.push({ name: entry.name, is_dir: entry.is_dir === true });
			}
		}
		return entries.sort(
			(a, b) =>
				Number(b.is_dir) - Number(a.is_dir) ||
				a.name.localeCompare(b.name),
		);
	} catch {
		return null;
	}
}

/**
 * Ask the development server to shut down.
 *
 * Resolves to true when the server acknowledged the request. A missing
 * server, a rejected request, or a failed network call resolves to false
 * rather than throwing, so callers only have to show the right message.
 */
export async function requestDevServerStop(): Promise<boolean> {
	if (typeof fetch !== "function") {
		return false;
	}
	try {
		const response = await fetch(STOP_SERVER_PATH, {
			method: "POST",
			keepalive: true,
		});
		return response.ok;
	} catch {
		return false;
	}
}
