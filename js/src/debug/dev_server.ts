/**
 * Talking to Drafter's local development server from the browser.
 *
 * A page served by the development server (src/drafter/app/app_server.py)
 * can ask that server to shut down, through the debug panel's "Stop Server"
 * menu item or the button on the `--stop-server` system route. Deployed
 * sites have no server to stop, so instances record whether their document
 * came from the development server and the controls stay hidden elsewhere.
 */

/** Mirror of INTERNAL_ROUTES["STOP_SERVER"] in src/drafter/config/urls.py. */
export const STOP_SERVER_PATH = "/__drafter_stop_server";

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
