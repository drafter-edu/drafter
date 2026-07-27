import {
	afterAll,
	afterEach,
	describe,
	expect,
	jest,
	test,
} from "@jest/globals";

import {
	alertDialog,
	confirmDialog,
	promptDialog,
	showDialog,
} from "../dialogs";

// Note on jsdom modality: the dialog system is implemented with plain <div>
// elements (a backdrop div plus a dialog div), NOT the native <dialog>
// element, so no showModal()/close() polyfill is needed. "Modal" behavior is
// purely CSS (`is-modal` backdrop class) plus a backdrop click handler, both
// of which are directly testable in jsdom.

// Failed button callbacks are logged via console.error; keep output clean.
const consoleErrorSpy = jest
	.spyOn(console, "error")
	.mockImplementation(() => {});

function getDialogs(): HTMLDivElement[] {
	return Array.from(document.querySelectorAll(".drafter-dialog"));
}

function getBackdrops(): HTMLDivElement[] {
	return Array.from(document.querySelectorAll(".drafter-dialog-backdrop"));
}

function getButtonByLabel(label: string, scope: ParentNode = document) {
	const buttons = Array.from(
		scope.querySelectorAll<HTMLButtonElement>(".drafter-dialog-button"),
	);
	const match = buttons.find(
		(button) => button.textContent?.trim() === label,
	);
	if (!match) {
		throw new Error(`No dialog button labeled '${label}'`);
	}
	return match;
}

/** Let queued microtasks and the async button-click handler settle. */
function flush(): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, 0));
}

function pressEscape(): void {
	document.dispatchEvent(
		new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
	);
}

afterEach(async () => {
	// Close any dialogs a test left open so their symbolicId registrations and
	// document-level keydown listeners do not leak into the next test.
	document
		.querySelectorAll<HTMLButtonElement>(".drafter-dialog-close")
		.forEach((button) => button.click());
	pressEscape();
	await flush();
	document.body.innerHTML = "";
	consoleErrorSpy.mockClear();
});

afterAll(() => {
	consoleErrorSpy.mockRestore();
});

describe("showDialog DOM structure", () => {
	test("renders backdrop, title, string content, close button, and buttons", () => {
		void showDialog({ title: "My Title", content: "Hello world" });

		const dialog = getDialogs()[0];
		expect(dialog).toBeDefined();
		expect(dialog.getAttribute("role")).toBe("dialog");
		expect(dialog.getAttribute("aria-modal")).toBe("true");

		const title = dialog.querySelector(".drafter-dialog-title");
		expect(title?.textContent).toBe("My Title");

		const content = dialog.querySelector(".drafter-dialog-content");
		expect(content?.querySelector("p")?.textContent).toBe("Hello world");

		expect(dialog.querySelector(".drafter-dialog-close")).not.toBeNull();

		// Default button set is a single primary OK button.
		const buttons = dialog.querySelectorAll(".drafter-dialog-button");
		expect(buttons).toHaveLength(1);
		expect(buttons[0].textContent).toBe("OK");
		expect(buttons[0].classList.contains("is-primary")).toBe(true);

		const backdrop = getBackdrops()[0];
		expect(backdrop.classList.contains("is-modal")).toBe(true);
	});

	test("modeless dialog marks backdrop and aria-modal accordingly", () => {
		void showDialog({ modal: false });

		expect(getDialogs()[0].getAttribute("aria-modal")).toBe("false");
		expect(getBackdrops()[0].classList.contains("is-modeless")).toBe(true);
	});

	test("HTMLElement content is inserted as-is", () => {
		const custom = document.createElement("section");
		custom.id = "custom-content";
		void showDialog({ content: custom });

		expect(
			getDialogs()[0].querySelector(
				".drafter-dialog-content > section#custom-content",
			),
		).not.toBeNull();
	});

	test("showCloseButton: false omits the close button", () => {
		void showDialog({ showCloseButton: false, closeOnEscape: true });

		expect(getDialogs()[0].querySelector(".drafter-dialog-close")).toBeNull();
	});

	test("width and maxWidth are applied to the dialog element", () => {
		void showDialog({ width: "500px", maxWidth: "90vw" });

		const dialog = getDialogs()[0];
		expect(dialog.style.width).toBe("500px");
		expect(dialog.style.maxWidth).toBe("90vw");
	});
});

describe("close paths", () => {
	test("close button resolves undefined with reason 'close-button' and removes DOM", async () => {
		const onClose =
			jest.fn<(value: unknown, reason: string) => void>();
		const promise = showDialog({ onClose });

		(
			document.querySelector(".drafter-dialog-close") as HTMLButtonElement
		).click();

		await expect(promise).resolves.toBeUndefined();
		expect(onClose).toHaveBeenCalledWith(undefined, "close-button");
		expect(getDialogs()).toHaveLength(0);
		expect(getBackdrops()).toHaveLength(0);
	});

	test("Escape closes the dialog with reason 'escape'", async () => {
		const onClose =
			jest.fn<(value: unknown, reason: string) => void>();
		const promise = showDialog({ onClose });

		pressEscape();

		await expect(promise).resolves.toBeUndefined();
		expect(onClose).toHaveBeenCalledWith(undefined, "escape");
		expect(getDialogs()).toHaveLength(0);
	});

	test("closeOnEscape: false ignores Escape", async () => {
		void showDialog({ closeOnEscape: false });

		pressEscape();
		await flush();

		expect(getDialogs()).toHaveLength(1);
	});

	test("backdrop click closes with reason 'backdrop'", async () => {
		const onClose =
			jest.fn<(value: unknown, reason: string) => void>();
		const promise = showDialog({ onClose });

		getBackdrops()[0].dispatchEvent(
			new MouseEvent("click", { bubbles: true }),
		);

		await expect(promise).resolves.toBeUndefined();
		expect(onClose).toHaveBeenCalledWith(undefined, "backdrop");
	});

	test("closeOnBackdrop: false ignores backdrop clicks", async () => {
		void showDialog({ closeOnBackdrop: false });

		getBackdrops()[0].dispatchEvent(
			new MouseEvent("click", { bubbles: true }),
		);
		await flush();

		expect(getDialogs()).toHaveLength(1);
	});

	test("clicking inside the dialog does not close it", async () => {
		void showDialog({ content: "stay open" });

		getDialogs()[0].dispatchEvent(new MouseEvent("click", { bubbles: true }));
		await flush();

		expect(getDialogs()).toHaveLength(1);
	});
});

describe("button behavior", () => {
	test("button with a value resolves that value with reason 'button'", async () => {
		const onClose =
			jest.fn<(value: unknown, reason: string) => void>();
		const promise = showDialog<string>({
			buttons: [{ label: "Pick", value: "picked" }],
			onClose,
		});

		getButtonByLabel("Pick").click();

		await expect(promise).resolves.toBe("picked");
		expect(onClose).toHaveBeenCalledWith("picked", "button");
	});

	test("onClick returning { close: false } keeps the dialog open", async () => {
		void showDialog({
			buttons: [{ label: "Stay", onClick: () => ({ close: false }) }],
		});

		getButtonByLabel("Stay").click();
		await flush();

		expect(getDialogs()).toHaveLength(1);
	});

	test("onClick returning { value } overrides the button's static value", async () => {
		const promise = showDialog<string>({
			buttons: [
				{
					label: "Compute",
					value: "static",
					onClick: () => ({ value: "computed" }),
				},
			],
		});

		getButtonByLabel("Compute").click();

		await expect(promise).resolves.toBe("computed");
	});

	test("closesDialog: false keeps the dialog open after a plain click", async () => {
		const onClick = jest.fn<() => void>();
		void showDialog({
			buttons: [{ label: "NoClose", closesDialog: false, onClick }],
		});

		getButtonByLabel("NoClose").click();
		await flush();

		expect(onClick).toHaveBeenCalledTimes(1);
		expect(getDialogs()).toHaveLength(1);
	});

	test("onClick receives event, dialogElement, and a working close()", async () => {
		const promise = showDialog<string>({
			buttons: [
				{
					label: "Manual",
					closesDialog: false,
					onClick: ({ event, dialogElement, close }) => {
						expect(event).toBeInstanceOf(MouseEvent);
						expect(
							dialogElement.classList.contains("drafter-dialog"),
						).toBe(true);
						close("manual-value");
					},
				},
			],
		});

		getButtonByLabel("Manual").click();

		await expect(promise).resolves.toBe("manual-value");
	});

	test("a throwing onClick logs the error and leaves the dialog open", async () => {
		void showDialog({
			buttons: [
				{
					label: "Boom",
					onClick: () => {
						throw new Error("kapow");
					},
				},
			],
		});

		getButtonByLabel("Boom").click();
		await flush();

		expect(consoleErrorSpy).toHaveBeenCalledWith(
			"Dialog button callback failed:",
			"Error: kapow",
		);
		expect(getDialogs()).toHaveLength(1);
	});

	test("autoFocus button receives focus when the dialog opens", () => {
		void showDialog({
			buttons: [
				{ label: "Other" },
				{ label: "Focused", autoFocus: true },
			],
		});

		expect(document.activeElement?.textContent).toBe("Focused");
	});
});

describe("drag handle", () => {
	test("mousedown on the header + mousemove repositions the dialog", async () => {
		void showDialog({ title: "Drag me", draggable: true });

		const dialog = getDialogs()[0];
		const title = dialog.querySelector(
			".drafter-dialog-title",
		) as HTMLElement;

		// jsdom's getBoundingClientRect returns all zeros, so the drag offset
		// equals the mousedown coordinates.
		title.dispatchEvent(
			new MouseEvent("mousedown", {
				bubbles: true,
				clientX: 50,
				clientY: 40,
			}),
		);
		document.dispatchEvent(
			new MouseEvent("mousemove", { clientX: 120, clientY: 90 }),
		);

		expect(dialog.style.transform).toBe("none");
		expect(dialog.style.left).toBe("70px");
		expect(dialog.style.top).toBe("50px");

		// After mouseup the listeners are removed; further moves are ignored.
		document.dispatchEvent(new MouseEvent("mouseup"));
		document.dispatchEvent(
			new MouseEvent("mousemove", { clientX: 500, clientY: 500 }),
		);
		expect(dialog.style.left).toBe("70px");
		expect(dialog.style.top).toBe("50px");
	});

	test("mousedown on the header close button does not start a drag", () => {
		void showDialog({ title: "No drag", draggable: true });

		const dialog = getDialogs()[0];
		const closeButton = dialog.querySelector(
			".drafter-dialog-close",
		) as HTMLElement;

		closeButton.dispatchEvent(
			new MouseEvent("mousedown", {
				bubbles: true,
				clientX: 10,
				clientY: 10,
			}),
		);
		document.dispatchEvent(
			new MouseEvent("mousemove", { clientX: 100, clientY: 100 }),
		);

		expect(dialog.style.left).toBe("");
		expect(dialog.style.top).toBe("");
	});

	test("draggable: false attaches no drag behavior", () => {
		void showDialog({ title: "Static", draggable: false });

		const dialog = getDialogs()[0];
		const header = dialog.querySelector(
			".drafter-dialog-header",
		) as HTMLElement;
		expect(header.classList.contains("is-draggable")).toBe(false);

		header.dispatchEvent(
			new MouseEvent("mousedown", {
				bubbles: true,
				clientX: 5,
				clientY: 5,
			}),
		);
		document.dispatchEvent(
			new MouseEvent("mousemove", { clientX: 100, clientY: 100 }),
		);

		expect(dialog.style.left).toBe("");
	});
});

describe("multiple dialogs and stacking", () => {
	test("two dialogs stack with increasing z-index and close independently", async () => {
		const first = showDialog<string>({
			title: "First",
			buttons: [{ label: "CloseFirst", value: "one" }],
		});
		void showDialog<string>({
			title: "Second",
			buttons: [{ label: "CloseSecond", value: "two" }],
		});

		const dialogs = getDialogs();
		expect(dialogs).toHaveLength(2);
		expect(Number(dialogs[1].style.zIndex)).toBeGreaterThan(
			Number(dialogs[0].style.zIndex),
		);

		getButtonByLabel("CloseFirst").click();
		await expect(first).resolves.toBe("one");
		expect(getDialogs()).toHaveLength(1);
		expect(
			getDialogs()[0].querySelector(".drafter-dialog-title")?.textContent,
		).toBe("Second");
	});

	test("Escape closes only the topmost open dialog", async () => {
		const first = showDialog({ title: "A" });
		const second = showDialog({ title: "B" });

		pressEscape();

		await expect(second).resolves.toBeUndefined();
		expect(getDialogs()).toHaveLength(1);
		expect(
			getDialogs()[0].querySelector(".drafter-dialog-title")?.textContent,
		).toBe("A");

		pressEscape();

		await expect(first).resolves.toBeUndefined();
		expect(getDialogs()).toHaveLength(0);
	});
});

describe("symbolicId registration", () => {
	test("reopening with the same symbolicId reuses the dialog and promise", async () => {
		const first = showDialog<string>({
			symbolicId: "sym-1",
			content: "original",
			buttons: [{ label: "Done", value: "done" }],
		});
		const second = showDialog<string>({
			symbolicId: "sym-1",
			content: "updated",
		});

		expect(second).toBe(first);
		expect(getDialogs()).toHaveLength(1);
		expect(
			getDialogs()[0].querySelector(".drafter-dialog-content")
				?.textContent,
		).toBe("updated");

		getButtonByLabel("Done").click();
		await expect(first).resolves.toBe("done");
	});

	test("closing frees the symbolicId so a fresh dialog can open", async () => {
		const first = showDialog({ symbolicId: "sym-2", content: "first" });
		(
			document.querySelector(".drafter-dialog-close") as HTMLButtonElement
		).click();
		await first;

		const second = showDialog({ symbolicId: "sym-2", content: "fresh" });
		expect(second).not.toBe(first);
		expect(getDialogs()).toHaveLength(1);
		expect(
			getDialogs()[0].querySelector(".drafter-dialog-content")
				?.textContent,
		).toBe("fresh");
	});

	test("different symbolicIds open separate dialogs", () => {
		void showDialog({ symbolicId: "sym-a" });
		void showDialog({ symbolicId: "sym-b" });

		expect(getDialogs()).toHaveLength(2);
	});
});

describe("alertDialog", () => {
	test("shows message and resolves after OK", async () => {
		const promise = alertDialog("Heads up!", { title: "Warning" });

		const dialog = getDialogs()[0];
		expect(
			dialog.querySelector(".drafter-dialog-title")?.textContent,
		).toBe("Warning");
		expect(
			dialog.querySelector(".drafter-dialog-content")?.textContent,
		).toBe("Heads up!");

		getButtonByLabel("OK").click();
		await expect(promise).resolves.toBeUndefined();
		expect(getDialogs()).toHaveLength(0);
	});

	test("uses a custom okLabel", async () => {
		const promise = alertDialog("Bye", { okLabel: "Got it" });

		getButtonByLabel("Got it").click();
		await expect(promise).resolves.toBeUndefined();
	});
});

describe("confirmDialog", () => {
	test("confirm button resolves true", async () => {
		const promise = confirmDialog("Proceed?");

		getButtonByLabel("Confirm").click();
		await expect(promise).resolves.toBe(true);
	});

	test("cancel button resolves false", async () => {
		const promise = confirmDialog("Proceed?");

		getButtonByLabel("Cancel").click();
		await expect(promise).resolves.toBe(false);
	});

	test("dismissing via Escape resolves false", async () => {
		const promise = confirmDialog("Proceed?");

		pressEscape();
		await expect(promise).resolves.toBe(false);
	});

	test("dismissing via close button resolves false", async () => {
		const promise = confirmDialog("Proceed?");

		(
			document.querySelector(".drafter-dialog-close") as HTMLButtonElement
		).click();
		await expect(promise).resolves.toBe(false);
	});

	test("custom labels and danger variant are applied", async () => {
		const promise = confirmDialog("Delete it?", {
			confirmLabel: "Delete",
			cancelLabel: "Keep",
			confirmVariant: "danger",
		});

		const confirmButton = getButtonByLabel("Delete");
		expect(confirmButton.classList.contains("is-danger")).toBe(true);

		getButtonByLabel("Keep").click();
		await expect(promise).resolves.toBe(false);
	});
});

describe("promptDialog", () => {
	function getPromptInput(): HTMLInputElement {
		return document.querySelector(
			".drafter-dialog-prompt-input",
		) as HTMLInputElement;
	}

	test("resolves the typed value on OK", async () => {
		const promise = promptDialog("Name?", { defaultValue: "start" });

		const input = getPromptInput();
		expect(input.value).toBe("start");
		input.value = "Ada";

		getButtonByLabel("OK").click();
		await expect(promise).resolves.toBe("Ada");
	});

	test("resolves null on cancel", async () => {
		const promise = promptDialog("Name?");

		getButtonByLabel("Cancel").click();
		await expect(promise).resolves.toBeNull();
	});

	test("failed validation keeps the dialog open and shows the message", async () => {
		const promise = promptDialog("Name?", {
			validate: (value) => (value === "" ? "Required!" : null),
		});

		getButtonByLabel("OK").click();
		await flush();

		expect(getDialogs()).toHaveLength(1);
		expect(getDialogs()[0].textContent).toContain("Required!");

		getPromptInput().value = "ok now";
		getButtonByLabel("OK").click();
		await expect(promise).resolves.toBe("ok now");
	});
});
