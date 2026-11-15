/**
 * The page's connection to the development server's live-reload socket.
 *
 * The development server (src/drafter/app/watcher.py) tells the page over a
 * WebSocket when the student saves a file. That socket closes whenever the
 * program stops, including when the student simply runs the file again: the
 * new run takes over the port, and a tab left from the earlier run would
 * otherwise keep showing the old program and ignore every save without
 * saying anything.
 *
 * So a lost connection is retried, waiting a little longer each time. When
 * the server answers again the tab reloads, which is what makes it show
 * the program that is running now. If the server stays away past a time
 * limit, the retries stop and a notice the student can close says so.
 *
 * The reload and the notice are only for a connection that worked and was
 * then lost. A socket that never connects at all (a proxy or a hosted
 * editor that does not pass WebSockets through) is retried the same way,
 * but there was nothing to lose: when it finally connects nothing reloads,
 * and when it never does the page keeps working with a line on the console.
 */

import { closeDialog, showDialog } from "./dialogs";
import { t } from "./i18n";

/** When to retry a lost connection, and when to stop. */
export interface LiveReloadSchedule {
	/** How long to wait before the first retry, in milliseconds. */
	initialDelayMs: number;
	/** Each wait is the one before it multiplied by this. */
	backoffFactor: number;
	/** The longest wait between two retries, in milliseconds. */
	maxDelayMs: number;
	/** How long after the connection was lost to stop retrying. */
	giveUpAfterMs: number;
}

/**
 * Retries after 0.5, 1, 2 and 4 seconds, then every 5 seconds, for two
 * minutes. Stopping a program and running it again takes a few seconds, so
 * the early retries are close together; two minutes covers a student who
 * edits for a moment before running again.
 */
export const DEFAULT_LIVE_RELOAD_SCHEDULE: LiveReloadSchedule = {
	initialDelayMs: 500,
	backoffFactor: 2,
	maxDelayMs: 5000,
	giveUpAfterMs: 120000,
};

/** The `symbolicId` of the notice shown when the retries stop. */
export const DISCONNECTED_DIALOG_ID = "dev_server.disconnected";

/** The parts of a WebSocket this module uses. */
export interface LiveReloadSocket {
	onopen: ((event: any) => void) | null;
	onmessage: ((event: any) => void) | null;
	onclose: ((event: any) => void) | null;
	close(): void;
}

export interface LiveReloadOptions {
	/** The development server's live-reload WebSocket URL. */
	url: string;
	/** Called with each message from the server, parsed from JSON. */
	onMessage: (message: { type?: unknown; [key: string]: unknown }) => void;
	/** Overrides for parts of `DEFAULT_LIVE_RELOAD_SCHEDULE`. */
	schedule?: Partial<LiveReloadSchedule>;
	/** Called when a lost connection is re-established. Default: reload the page. */
	onReconnect?: () => void;
	/** Called when the retries stop. Default: show the disconnected notice. */
	onGiveUp?: () => void;
	/** Opens a socket. Default: the browser's WebSocket. */
	createSocket?: (url: string) => LiveReloadSocket;
}

/** A live-reload connection that can be shut down. */
export interface LiveReloadConnection {
	/**
	 * Close the connection on purpose (the instance is being torn down).
	 * Nothing is retried and no notice is shown; a pending retry is
	 * cancelled and a notice that is already showing is closed.
	 */
	close(): void;
}

/**
 * Tell the student that the page has stopped trying to reach their program.
 * The notice can be dismissed with its button, its close button, the Escape
 * key, or a click outside it. Dismissing it only closes it: the retries
 * have already ended and nothing starts them again.
 */
export function showDisconnectedNotice(): void {
	void showDialog<void>({
		title: t("live_reload.disconnected.title"),
		content: t("live_reload.disconnected.message"),
		symbolicId: DISCONNECTED_DIALOG_ID,
		width: "480px",
		buttons: [
			{
				label: t("live_reload.disconnected.close"),
				variant: "primary",
				autoFocus: true,
			},
		],
	});
}

/**
 * Open the live-reload connection and keep it alive as described at the
 * top of this file.
 */
export function connectLiveReload(
	options: LiveReloadOptions,
): LiveReloadConnection {
	const schedule = { ...DEFAULT_LIVE_RELOAD_SCHEDULE, ...options.schedule };
	const createSocket =
		options.createSocket ??
		((url: string): LiveReloadSocket => new WebSocket(url));
	const onReconnect = options.onReconnect ?? (() => window.location.reload());
	const onGiveUp = options.onGiveUp ?? showDisconnectedNotice;

	let socket: LiveReloadSocket | null = null;
	let retryTimer: ReturnType<typeof setTimeout> | null = null;
	// Whether any socket has opened: only then is there a connection to lose.
	let everConnected = false;
	// When the connection was lost (or first failed); null while it is fine.
	let lostAt: number | null = null;
	let nextDelayMs = schedule.initialDelayMs;
	// Set once nothing more should happen: closed on purpose, reconnected
	// (the page is reloading), or given up.
	let finished = false;

	/** Stop listening to a socket and close it. */
	const release = (target: LiveReloadSocket) => {
		target.onopen = null;
		target.onmessage = null;
		target.onclose = null;
		try {
			target.close();
		} catch {
			// A socket that never opened may refuse to close; it is gone
			// either way.
		}
	};

	const handleLoss = () => {
		if (finished) {
			return;
		}
		socket = null;
		const now = Date.now();
		if (lostAt === null) {
			lostAt = now;
			nextDelayMs = schedule.initialDelayMs;
		}
		const remainingMs = lostAt + schedule.giveUpAfterMs - now;
		if (remainingMs <= 0) {
			finished = true;
			if (everConnected) {
				onGiveUp();
			} else {
				console.warn(
					"[Drafter] The live-reload connection never opened, so this page will not update when you save. Reload the page to see a change.",
				);
			}
			return;
		}
		// The last retry lands on the time limit rather than after it.
		const waitMs = Math.min(nextDelayMs, remainingMs);
		nextDelayMs = Math.min(
			nextDelayMs * schedule.backoffFactor,
			schedule.maxDelayMs,
		);
		retryTimer = setTimeout(() => {
			retryTimer = null;
			connect();
		}, waitMs);
	};

	const connect = () => {
		if (finished) {
			return;
		}
		let opened: LiveReloadSocket;
		try {
			opened = createSocket(options.url);
		} catch (error) {
			console.warn(
				"[Drafter] Could not open the live-reload connection:",
				error,
			);
			handleLoss();
			return;
		}
		socket = opened;
		opened.onopen = () => {
			if (finished || socket !== opened) {
				return;
			}
			if (!everConnected) {
				// The first connection, even if it took a few tries.
				everConnected = true;
				lostAt = null;
				return;
			}
			// The server is back, most likely as a new run of the program:
			// reload so this tab shows what is running now.
			finished = true;
			onReconnect();
		};
		opened.onmessage = (event: { data?: unknown }) => {
			if (finished || socket !== opened) {
				return;
			}
			let message: unknown;
			try {
				message = JSON.parse(String(event.data));
			} catch (error) {
				console.warn(
					"[Drafter] Ignoring a live-reload message that is not JSON:",
					error,
				);
				return;
			}
			if (message !== null && typeof message === "object") {
				options.onMessage(message as { type?: unknown });
			}
		};
		// A failed connection attempt also ends in a close event, so this
		// one handler covers both a dropped connection and a refused one.
		opened.onclose = () => {
			if (socket !== opened) {
				return;
			}
			handleLoss();
		};
	};

	connect();

	return {
		close: () => {
			const wasFinished = finished;
			finished = true;
			if (retryTimer !== null) {
				clearTimeout(retryTimer);
				retryTimer = null;
			}
			if (socket) {
				release(socket);
				socket = null;
			}
			if (wasFinished) {
				closeDialog(DISCONNECTED_DIALOG_ID);
			}
		},
	};
}
