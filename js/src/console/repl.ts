/**
 * Interactive Python REPL session backed by Pyodide's own console machinery
 * (pyodide.console.PyodideConsole). Each pushed line is compiled with the
 * standard interactive rules, so multi-line constructs report "incomplete"
 * until finished, results are repr()'d like the CPython REPL, and top-level
 * await works.
 *
 * The session shares its globals with __main__, so students can inspect and
 * call anything their program defined.
 */

export type ConsoleStream =
	| "stdout"
	| "stderr"
	| "echo"
	| "result"
	| "error"
	| "info";

export type ReplStatus = "complete" | "incomplete" | "syntax-error" | "error";

export type ConsoleEmitter = (stream: ConsoleStream, text: string) => void;

const REPL_BOOTSTRAP = `
def _drafter_make_repl_session(stdout_callback, stderr_callback):
    from pyodide.console import PyodideConsole, repr_shorten
    import __main__

    class _DrafterReplSession:
        def __init__(self):
            self.console = PyodideConsole(
                globals=__main__.__dict__,
                stdout_callback=stdout_callback,
                stderr_callback=stderr_callback,
            )

        def push(self, line):
            return self.console.push(line)

        def format_result(self, value):
            return repr_shorten(value, limit=2000)

    return _DrafterReplSession()

_drafter_make_repl_session
`;

export class ReplSession {
	private sessionPromise: Promise<any> | null = null;

	constructor(private emit: ConsoleEmitter) {}

	private getPyodide(): any {
		return (window as any).pyodide;
	}

	public isAvailable(): boolean {
		return this.getPyodide() !== undefined;
	}

	private ensureSession(): Promise<any> {
		if (!this.sessionPromise) {
			const pyodide = this.getPyodide();
			this.sessionPromise = (async () => {
				const factory = await pyodide.runPythonAsync(REPL_BOOTSTRAP);
				try {
					return factory(
						(text: string) => this.emit("stdout", text),
						(text: string) => this.emit("stderr", text),
					);
				} finally {
					factory.destroy?.();
				}
			})();
			// A failed bootstrap (e.g. interrupted load) should not poison
			// every later command; let the next run() retry from scratch.
			this.sessionPromise.catch(() => {
				this.sessionPromise = null;
			});
		}
		return this.sessionPromise;
	}

	/**
	 * Run one line of console input. Emits any produced output through the
	 * emitter and returns how the line was consumed ("incomplete" means the
	 * console is waiting for more lines of a multi-line construct).
	 */
	public async run(line: string): Promise<ReplStatus> {
		if (!this.isAvailable()) {
			this.emit(
				"error",
				"Python is not running yet; wait for the page to finish loading.\n",
			);
			return "error";
		}

		let session: any;
		try {
			session = await this.ensureSession();
		} catch (bootError) {
			this.emit(
				"error",
				`Could not start the Python console: ${String(bootError)}\n`,
			);
			return "error";
		}

		const future = session.push(line);
		try {
			const syntaxCheck = future.syntax_check;
			if (syntaxCheck === "incomplete") {
				return "incomplete";
			}
			if (syntaxCheck === "syntax-error") {
				const message: string =
					future.formatted_error ?? "SyntaxError: invalid syntax";
				this.emit("error", `${message.trimEnd()}\n`);
				return "syntax-error";
			}

			try {
				const value = await future;
				if (value !== undefined) {
					let text: unknown;
					try {
						text = session.format_result(value);
					} finally {
						value?.destroy?.();
					}
					if (text !== undefined && text !== null) {
						this.emit("result", `${String(text)}\n`);
					}
				}
				return "complete";
			} catch (runError) {
				let formatted: unknown;
				try {
					formatted = future.formatted_error;
				} catch {
					formatted = undefined;
				}
				this.emit(
					"error",
					`${String(formatted ?? runError).trimEnd()}\n`,
				);
				return "error";
			}
		} finally {
			try {
				future.destroy?.();
			} catch {
				// Already destroyed (or a plain JS object in tests); ignore.
			}
		}
	}
}
