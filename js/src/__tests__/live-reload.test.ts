/**
 * The live-reload connection to the development server.
 *
 * A tab left open from an earlier run used to keep its dead socket forever:
 * it showed the old program, ignored every save, and said nothing. The
 * connection now retries with growing waits, reloads the tab when the
 * server answers again, and after a time limit stops and shows a notice
 * the student can close. Sockets are faked at the WebSocket boundary and
 * time is faked with Jest's timers, so nothing here waits or uses a network.
 */
import {
	afterEach,
	beforeEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	connectLiveReload,
	DEFAULT_LIVE_RELOAD_SCHEDULE,
	DISCONNECTED_DIALOG_ID,
	type LiveReloadSocket,
} from "../live_reload";
import { closeDialog } from "../dialogs";
import { createDrafterInstance } from "../pyodide.index";

/** A stand-in for the browser's WebSocket that tests drive by hand. */
class FakeSocket implements LiveReloadSocket {
	static created: FakeSocket[] = [];

	onopen: ((event: any) => void) | null = null;
	onmessage: ((event: any) => void) | null = null;
	onclose: ((event: any) => void) | null = null;
	closedByPage = false;

	constructor(public url: string) {
		FakeSocket.created.push(this);
	}

	/** The page closes the socket; like the real one, this fires `close`. */
	close(): void {
		this.closedByPage = true;
		this.onclose?.({});
	}

	/** The server accepted the connection. */
	serverAccepts(): void {
		this.onopen?.({});
	}

	/** The server went away, or never answered. */
	serverGoesAway(): void {
		this.onclose?.({});
	}

	serverSends(message: unknown): void {
		this.onmessage?.({ data: JSON.stringify(message) });
	}
}

const WS_URL = "ws://localhost:8080/__drafter_ws";

function latestSocket(): FakeSocket {
	const socket = FakeSocket.created.at(-1);
	if (!socket) {
		throw new Error("No socket has been opened");
	}
	return socket;
}

function connect(overrides: Partial<Parameters<typeof connectLiveReload>[0]> = {}) {
	const onMessage = jest.fn();
	const onReconnect = jest.fn();
	const connection = connectLiveReload({
		url: WS_URL,
		onMessage,
		onReconnect,
		createSocket: (url) => new FakeSocket(url),
		...overrides,
	});
	return { connection, onMessage, onReconnect };
}

function noticeDialog(): HTMLElement | null {
	return document.querySelector(".drafter-dialog");
}

beforeEach(() => {
	jest.useFakeTimers();
	FakeSocket.created = [];
	// A socket that fails to connect is reported once on the console.
	jest.spyOn(console, "warn").mockImplementation(() => {});
});

afterEach(() => {
	closeDialog(DISCONNECTED_DIALOG_ID);
	jest.useRealTimers();
	jest.restoreAllMocks();
	document.body.innerHTML = "";
});

describe("a healthy connection", () => {
	test("opens one socket and passes the server's messages on", () => {
		const { onMessage, onReconnect } = connect();

		expect(FakeSocket.created).toHaveLength(1);
		expect(latestSocket().url).toBe(WS_URL);
		latestSocket().serverAccepts();
		latestSocket().serverSends({ type: "restart_student_code", code: "x" });

		expect(onMessage).toHaveBeenCalledWith({
			type: "restart_student_code",
			code: "x",
		});
		// The first connection is not a reconnection: nothing reloads.
		expect(onReconnect).not.toHaveBeenCalled();
		expect(jest.getTimerCount()).toBe(0);
	});

	test("a message that is not JSON is ignored", () => {
		const { onMessage } = connect();
		latestSocket().serverAccepts();

		latestSocket().onmessage?.({ data: "not json" });

		expect(onMessage).not.toHaveBeenCalled();
	});
});

describe("a lost connection", () => {
	test("is retried, waiting longer each time up to the longest wait", () => {
		connect({
			schedule: {
				initialDelayMs: 100,
				backoffFactor: 2,
				maxDelayMs: 500,
				giveUpAfterMs: 60000,
			},
		});
		latestSocket().serverAccepts();
		latestSocket().serverGoesAway();

		// Waits of 100, 200, 400, then 500 (the cap) and 500 again.
		for (const wait of [100, 200, 400, 500, 500]) {
			const before = FakeSocket.created.length;
			jest.advanceTimersByTime(wait - 1);
			expect(FakeSocket.created).toHaveLength(before);
			jest.advanceTimersByTime(1);
			expect(FakeSocket.created).toHaveLength(before + 1);
			latestSocket().serverGoesAway();
		}
	});

	test("reloads the page once the server answers again", () => {
		const { onReconnect } = connect();
		latestSocket().serverAccepts();
		latestSocket().serverGoesAway();
		jest.advanceTimersByTime(DEFAULT_LIVE_RELOAD_SCHEDULE.initialDelayMs);
		latestSocket().serverGoesAway();
		expect(onReconnect).not.toHaveBeenCalled();

		jest.advanceTimersByTime(60000);
		latestSocket().serverAccepts();

		expect(onReconnect).toHaveBeenCalledTimes(1);
		// Nothing is left running while the page reloads.
		expect(jest.getTimerCount()).toBe(0);
		expect(noticeDialog()).toBeNull();
	});

});

describe("a connection that has never worked", () => {
	// For example behind a proxy that does not pass WebSockets through:
	// the page itself is fine, so nothing may reload it or interrupt it.

	test("is retried, and connecting late does not reload the page", () => {
		const { onMessage, onReconnect } = connect();
		// The socket closes without ever opening.
		latestSocket().serverGoesAway();

		jest.advanceTimersByTime(DEFAULT_LIVE_RELOAD_SCHEDULE.initialDelayMs);
		expect(FakeSocket.created).toHaveLength(2);
		latestSocket().serverAccepts();
		latestSocket().serverSends({ type: "reload" });

		expect(onReconnect).not.toHaveBeenCalled();
		expect(onMessage).toHaveBeenCalledWith({ type: "reload" });
	});

	test("once it has worked, losing it and getting it back reloads the page", () => {
		const { onReconnect } = connect();
		latestSocket().serverGoesAway();
		jest.advanceTimersByTime(DEFAULT_LIVE_RELOAD_SCHEDULE.initialDelayMs);
		latestSocket().serverAccepts();

		latestSocket().serverGoesAway();
		jest.advanceTimersByTime(DEFAULT_LIVE_RELOAD_SCHEDULE.initialDelayMs);
		latestSocket().serverAccepts();

		expect(onReconnect).toHaveBeenCalledTimes(1);
	});

	test("a socket that cannot even be created is retried", () => {
		let refuse = true;
		const { onMessage } = connect({
			createSocket: (url) => {
				if (refuse) {
					throw new Error("SecurityError");
				}
				return new FakeSocket(url);
			},
		});
		expect(FakeSocket.created).toHaveLength(0);

		refuse = false;
		jest.advanceTimersByTime(DEFAULT_LIVE_RELOAD_SCHEDULE.initialDelayMs);
		latestSocket().serverAccepts();
		latestSocket().serverSends({ type: "reload" });

		expect(onMessage).toHaveBeenCalledWith({ type: "reload" });
	});

	test("stops at the time limit without a notice", () => {
		connect({
			schedule: {
				initialDelayMs: 100,
				backoffFactor: 2,
				maxDelayMs: 400,
				giveUpAfterMs: 1000,
			},
		});
		latestSocket().serverGoesAway();

		while (jest.getTimerCount() > 0) {
			jest.runOnlyPendingTimers();
			latestSocket().serverGoesAway();
		}

		expect(noticeDialog()).toBeNull();
		expect(console.warn).toHaveBeenCalledWith(
			expect.stringContaining("live-reload connection never opened"),
		);
	});
});

describe("a server that never returns", () => {
	const schedule = {
		initialDelayMs: 100,
		backoffFactor: 2,
		maxDelayMs: 400,
		giveUpAfterMs: 1000,
	};

	/** Lose the connection and refuse every retry until the retries stop. */
	function runOutTheClock(): number {
		latestSocket().serverAccepts();
		latestSocket().serverGoesAway();
		let attempts = 0;
		while (jest.getTimerCount() > 0) {
			jest.runOnlyPendingTimers();
			attempts += 1;
			latestSocket().serverGoesAway();
		}
		return attempts;
	}

	test("stops retrying at the time limit and says so", () => {
		const start = Date.now();
		const { onReconnect } = connect({ schedule });

		// Retries at 100, 300, 700 and, cut short by the limit, at 1000.
		const attempts = runOutTheClock();

		expect(attempts).toBe(4);
		expect(Date.now() - start).toBe(schedule.giveUpAfterMs);
		expect(onReconnect).not.toHaveBeenCalled();
		const dialog = noticeDialog();
		expect(dialog).not.toBeNull();
		expect(dialog?.textContent).toContain("Disconnected");
		expect(dialog?.textContent).toContain("Run your program again");
	});

	test("the notice is not shown before the time limit", () => {
		connect({ schedule });
		latestSocket().serverAccepts();
		latestSocket().serverGoesAway();

		jest.advanceTimersByTime(schedule.giveUpAfterMs - 1);

		expect(noticeDialog()).toBeNull();
	});

	test.each([
		[
			"its Close button",
			() =>
				(
					document.querySelector(
						".drafter-dialog-button",
					) as HTMLButtonElement
				).click(),
		],
		[
			"the × in its corner",
			() =>
				(
					document.querySelector(
						".drafter-dialog-close",
					) as HTMLButtonElement
				).click(),
		],
		[
			"the Escape key",
			() =>
				document.dispatchEvent(
					new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
				),
		],
		[
			"a click outside it",
			() =>
				(
					document.querySelector(
						".drafter-dialog-backdrop",
					) as HTMLElement
				).click(),
		],
	])("the notice can be dismissed with %s", async (_label, dismiss) => {
		connect({ schedule });
		runOutTheClock();
		const socketsBefore = FakeSocket.created.length;
		expect(noticeDialog()).not.toBeNull();

		dismiss();
		// The button's click handler finishes on a later microtask.
		await jest.advanceTimersByTimeAsync(0);

		expect(noticeDialog()).toBeNull();
		expect(document.querySelector(".drafter-dialog-backdrop")).toBeNull();
		// Dismissing only closes the notice: no timer is left and no retry
		// starts, however long the student keeps reading the page.
		expect(jest.getTimerCount()).toBe(0);
		await jest.advanceTimersByTimeAsync(10 * schedule.giveUpAfterMs);
		expect(FakeSocket.created).toHaveLength(socketsBefore);
		expect(noticeDialog()).toBeNull();
	});

	test("a server that returns after the notice does not reload the page", () => {
		const { onReconnect } = connect({ schedule });
		runOutTheClock();
		const abandoned = latestSocket();

		// Nothing is listening any more, so a late answer changes nothing.
		abandoned.serverAccepts();

		expect(onReconnect).not.toHaveBeenCalled();
	});
});

describe("closing the connection on purpose", () => {
	test("closes the socket without retrying or showing a notice", () => {
		const { connection, onReconnect } = connect();
		const socket = latestSocket();
		socket.serverAccepts();

		connection.close();

		expect(socket.closedByPage).toBe(true);
		expect(jest.getTimerCount()).toBe(0);
		jest.advanceTimersByTime(10 * DEFAULT_LIVE_RELOAD_SCHEDULE.giveUpAfterMs);
		expect(FakeSocket.created).toHaveLength(1);
		expect(onReconnect).not.toHaveBeenCalled();
		expect(noticeDialog()).toBeNull();
	});

	test("cancels a retry that was waiting", () => {
		const { connection } = connect();
		latestSocket().serverAccepts();
		latestSocket().serverGoesAway();
		expect(jest.getTimerCount()).toBe(1);

		connection.close();

		expect(jest.getTimerCount()).toBe(0);
		jest.advanceTimersByTime(10 * DEFAULT_LIVE_RELOAD_SCHEDULE.giveUpAfterMs);
		expect(FakeSocket.created).toHaveLength(1);
		expect(noticeDialog()).toBeNull();
	});

	test("closes a notice that is already showing", () => {
		const { connection } = connect({
			schedule: { giveUpAfterMs: 0 },
		});
		latestSocket().serverAccepts();
		latestSocket().serverGoesAway();
		expect(noticeDialog()).not.toBeNull();

		connection.close();

		expect(noticeDialog()).toBeNull();
	});
});

// ---------------------------------------------------------------------------
// The instance's use of the connection (createDrafterInstance)
// ---------------------------------------------------------------------------

type AnyGlobal = Record<string, any>;

describe("a Drafter instance on the development server", () => {
	let runs: string[];
	let originalWebSocket: unknown;

	beforeEach(() => {
		runs = [];
		document.body.innerHTML = '<div id="drafter-root--"></div>';
		originalWebSocket = (globalThis as AnyGlobal).WebSocket;
		(globalThis as AnyGlobal).WebSocket = FakeSocket;
		// Just enough interpreter for a run: the syntax check answers "ok"
		// and the student's code is recorded instead of executed.
		(window as AnyGlobal).pyodide = {
			toPy: (value: unknown) => ({ value, destroy: () => {} }),
			FS: { writeFile: () => {}, mkdirTree: () => {} },
			runPythonAsync: jest.fn(async (code: string) => {
				if (code.includes("_drafter_check_syntax")) {
					return JSON.stringify({ ok: true });
				}
				if (code.startsWith("# student")) {
					runs.push(code);
				}
				return undefined;
			}),
		};
	});

	afterEach(() => {
		(globalThis as AnyGlobal).WebSocket = originalWebSocket;
		delete (window as AnyGlobal).pyodide;
	});

	async function startInstance() {
		const handle = await createDrafterInstance({
			verbose: false,
			inlineCode: "# student v1",
			devWsUrl: WS_URL,
			liveReloadSchedule: {
				initialDelayMs: 100,
				backoffFactor: 2,
				maxDelayMs: 400,
				giveUpAfterMs: 1000,
			},
		});
		latestSocket().serverAccepts();
		return handle;
	}

	test("still restarts the program when the server sends new code", async () => {
		const handle = await startInstance();
		expect(runs).toEqual(["# student v1"]);

		latestSocket().serverSends({
			type: "restart_student_code",
			code: "# student v2",
		});
		await jest.advanceTimersByTimeAsync(0);

		expect(runs).toEqual(["# student v1", "# student v2"]);
		handle.stop();
	});

	test("retries when the server goes away, on the schedule it was given", async () => {
		const handle = await startInstance();

		latestSocket().serverGoesAway();
		jest.advanceTimersByTime(100);

		expect(FakeSocket.created).toHaveLength(2);
		handle.stop();
	});

	test("stopping the instance is not treated as a disconnection", async () => {
		const handle = await startInstance();
		const socket = latestSocket();

		handle.stop();

		expect(socket.closedByPage).toBe(true);
		expect(jest.getTimerCount()).toBe(0);
		jest.advanceTimersByTime(60000);
		expect(FakeSocket.created).toHaveLength(1);
		expect(noticeDialog()).toBeNull();
	});

	test("stopping the instance while it is retrying leaves nothing behind", async () => {
		const handle = await startInstance();
		latestSocket().serverGoesAway();
		expect(jest.getTimerCount()).toBe(1);

		handle.stop();

		expect(jest.getTimerCount()).toBe(0);
		jest.advanceTimersByTime(60000);
		expect(FakeSocket.created).toHaveLength(1);
		expect(noticeDialog()).toBeNull();
	});
});
