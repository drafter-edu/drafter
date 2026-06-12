import type { ReactElement } from "jsx-dom";

/**
 * A simple dialog system for Drafter, implemented in plain TypeScript and DOM APIs without any external dependencies.
 * Provides a `showDialog` function that can be used to display custom dialogs with arbitrary content and buttons, as
 * well as convenience functions for common dialog types like alerts, confirms, and prompts.
 *
 * Initial version was AI-generated.
 */
type DialogCloseReason =
	| "button"
	| "backdrop"
	| "escape"
	| "close-button"
	| "programmatic";

type DialogButtonAction<T> = void | {
	close?: boolean;
	value?: T;
};

export interface DialogButtonContext {
	event: MouseEvent;
	dialogElement: HTMLDivElement;
	close: (value?: unknown, reason?: DialogCloseReason) => void;
}

export interface DialogButtonOptions<T> {
	label: string;
	variant?: "primary" | "secondary" | "danger";
	autoFocus?: boolean;
	closesDialog?: boolean;
	value?: T;
	onClick?: (
		context: DialogButtonContext,
	) => DialogButtonAction<T> | Promise<DialogButtonAction<T>>;
}

export interface DialogOptions<T = unknown> {
	title?: string;
	content?: string | HTMLElement | ReactElement;
	modal?: boolean;
	draggable?: boolean;
	closeOnBackdrop?: boolean;
	closeOnEscape?: boolean;
	showCloseButton?: boolean;
	width?: string;
	maxWidth?: string;
	buttons?: DialogButtonOptions<T>[];
	onClose?: (value: T | undefined, reason: DialogCloseReason) => void;
	symbolicId?: string;
}

let dialogStack = 0;

/** Internal record kept for every open dialog that has a symbolicId. */
interface TrackedDialog {
	updateContent: (content: string | HTMLElement | ReactElement) => void;
	promise: Promise<unknown>;
}

const openDialogs = new Map<string, TrackedDialog>();

function coerceError(error: unknown): string {
	if (error instanceof Error) {
		return `${error.name}: ${error.message}`;
	}
	return String(error);
}

function setupDragging(dialog: HTMLDivElement, header: HTMLDivElement): void {
	let isDragging = false;
	let offsetX = 0;
	let offsetY = 0;

	const onMouseMove = (event: MouseEvent) => {
		if (!isDragging) {
			return;
		}
		dialog.style.transform = "none";
		dialog.style.left = `${event.clientX - offsetX}px`;
		dialog.style.top = `${event.clientY - offsetY}px`;
	};

	const onMouseUp = () => {
		isDragging = false;
		document.removeEventListener("mousemove", onMouseMove);
		document.removeEventListener("mouseup", onMouseUp);
	};

	header.addEventListener("mousedown", (event: MouseEvent) => {
		const target = event.target as HTMLElement;
		if (target.closest("button")) {
			return;
		}
		isDragging = true;
		const rect = dialog.getBoundingClientRect();
		offsetX = event.clientX - rect.left;
		offsetY = event.clientY - rect.top;
		document.addEventListener("mousemove", onMouseMove);
		document.addEventListener("mouseup", onMouseUp);
	});
}

export function showDialog<T = unknown>(
	options: DialogOptions<T>,
): Promise<T | undefined> {
	const {
		title = "Dialog",
		content = "",
		modal = true,
		draggable = true,
		closeOnBackdrop = true,
		closeOnEscape = true,
		showCloseButton = true,
		width,
		maxWidth,
		buttons = [{ label: "OK", variant: "primary" }],
		onClose,
		symbolicId,
	} = options;

	// If a dialog with this symbolicId is already open, update its content in
	// place and return the same promise so the caller awaits the same user action.
	if (symbolicId !== undefined && openDialogs.has(symbolicId)) {
		const tracked = openDialogs.get(symbolicId)!;
		tracked.updateContent(content);
		return tracked.promise as Promise<T | undefined>;
	}

	// Captured outside the constructor so we can register it in openDialogs
	// after the promise object is created (Promise constructor runs synchronously).
	let setContentRef: (
		c: string | HTMLElement | ReactElement,
	) => void = () => {};

	const promise = new Promise<T | undefined>((resolve) => {
		dialogStack += 1;
		const zIndex = 12000 + dialogStack;

		const backdrop = (
			<div
				class={`drafter-dialog-backdrop ${modal ? "is-modal" : "is-modeless"}`}
			></div>
		) as HTMLDivElement;
		backdrop.style.zIndex = `${zIndex}`;

		const dialog = (
			<div
				class="drafter-dialog"
				role="dialog"
				aria-modal={modal ? "true" : "false"}
			></div>
		) as HTMLDivElement;
		dialog.style.zIndex = `${zIndex + 1}`;
		if (width) {
			dialog.style.width = width;
		}
		if (maxWidth) {
			dialog.style.maxWidth = maxWidth;
		}

		const header = (
			<div
				class={`drafter-dialog-header ${draggable ? "is-draggable" : ""}`}
			>
				<div class="drafter-dialog-title">{title}</div>
				{showCloseButton ? (
					<button
						class="drafter-dialog-close"
						title="Close"
						aria-label="Close dialog"
					>
						×
					</button>
				) : null}
			</div>
		) as HTMLDivElement;

		const contentContainer = (
			<div class="drafter-dialog-content"></div>
		) as HTMLDivElement;

		function setContent(newContent: string | HTMLElement | ReactElement) {
			contentContainer.replaceChildren(
				typeof newContent === "string"
					? ((<p>{newContent}</p>) as HTMLParagraphElement)
					: newContent,
			);
		}
		setContentRef = setContent;

		setContent(content);

		const actions = (
			<div class="drafter-dialog-actions"></div>
		) as HTMLDivElement;

		let finished = false;
		const close = (
			value?: T,
			reason: DialogCloseReason = "programmatic",
		) => {
			if (finished) {
				return;
			}
			finished = true;
			if (symbolicId !== undefined) {
				openDialogs.delete(symbolicId);
			}
			document.removeEventListener("keydown", onKeyDown);
			backdrop.remove();
			dialog.remove();
			onClose?.(value, reason);
			resolve(value);
		};

		const onKeyDown = (event: KeyboardEvent) => {
			if (event.key === "Escape" && closeOnEscape) {
				event.preventDefault();
				close(undefined, "escape");
			}
		};

		if (modal && closeOnBackdrop) {
			backdrop.addEventListener("click", (event) => {
				if (event.target === backdrop) {
					close(undefined, "backdrop");
				}
			});
		}

		const closeButton = header.querySelector(".drafter-dialog-close");
		if (closeButton) {
			closeButton.addEventListener("click", () => {
				close(undefined, "close-button");
			});
		}

		buttons.forEach((buttonConfig) => {
			const variant = buttonConfig.variant ?? "secondary";
			const button = (
				<button class={`drafter-dialog-button is-${variant}`}>
					{buttonConfig.label}
				</button>
			) as HTMLButtonElement;

			if (buttonConfig.autoFocus) {
				button.autofocus = true;
			}

			button.addEventListener("click", async (event) => {
				try {
					const action = await buttonConfig.onClick?.({
						event,
						dialogElement: dialog,
						close: close as (
							value?: unknown,
							reason?: DialogCloseReason,
						) => void,
					});

					let shouldClose = buttonConfig.closesDialog ?? true;
					let value = buttonConfig.value;

					if (action && typeof action === "object") {
						if (
							Object.prototype.hasOwnProperty.call(
								action,
								"close",
							)
						) {
							shouldClose = action.close !== false;
						}
						if (
							Object.prototype.hasOwnProperty.call(
								action,
								"value",
							)
						) {
							value = action.value;
						}
					}

					if (shouldClose) {
						close(value, "button");
					}
				} catch (error) {
					console.error(
						"Dialog button callback failed:",
						coerceError(error),
					);
				}
			});

			actions.appendChild(button);
		});

		dialog.appendChild(header);
		dialog.appendChild(contentContainer);
		dialog.appendChild(actions);

		if (draggable) {
			setupDragging(dialog, header);
		}

		document.body.appendChild(backdrop);
		document.body.appendChild(dialog);
		document.addEventListener("keydown", onKeyDown);

		const autoFocusElement = dialog.querySelector(
			"[autofocus]",
		) as HTMLElement | null;
		if (autoFocusElement) {
			autoFocusElement.focus();
		}
	});

	if (symbolicId !== undefined) {
		openDialogs.set(symbolicId, {
			updateContent: setContentRef,
			promise,
		});
	}

	return promise;
}

export interface AlertDialogOptions {
	/** The visible title for the alert dialog. */
	title?: string;
	/** The label for the OK button. Defaults to "OK". */
	okLabel?: string;
	/**
	 * Whether the dialog should be modal (blocking interaction with the rest of the page) or modeless. Defaults to true (modal).
	 */
	modal?: boolean;
	/**
	 * Whether the dialog can be dragged around the screen by its header. Defaults to true.
	 */
	draggable?: boolean;
	/** Optional fixed width for the dialog (e.g. "400px"). If not set, the dialog will size based on its content. */
	width?: string;
	/** If provided, existing dialogs with this symbolic id will be reused. */
	symbolicId?: string;
}

export async function alertDialog(
	message: string | HTMLElement | ReactElement,
	options: AlertDialogOptions = {},
): Promise<void> {
	const {
		title = "Notice",
		okLabel = "OK",
		modal = true,
		draggable = true,
		width,
		symbolicId,
	} = options;

	await showDialog<void>({
		title,
		content: message,
		modal,
		draggable,
		width,
		symbolicId,
		buttons: [{ label: okLabel, variant: "primary", autoFocus: true }],
	});
}

export interface ConfirmDialogOptions {
	title?: string;
	confirmLabel?: string;
	cancelLabel?: string;
	modal?: boolean;
	draggable?: boolean;
	width?: string;
	confirmVariant?: "primary" | "danger";
	symbolicId?: string;
}

export async function confirmDialog(
	message: string,
	options: ConfirmDialogOptions = {},
): Promise<boolean> {
	const {
		title = "Confirm",
		confirmLabel = "Confirm",
		cancelLabel = "Cancel",
		modal = true,
		draggable = true,
		width,
		confirmVariant = "primary",
		symbolicId,
	} = options;

	const value = await showDialog<boolean>({
		title,
		content: message,
		modal,
		draggable,
		width,
		symbolicId,
		buttons: [
			{ label: cancelLabel, variant: "secondary", value: false },
			{
				label: confirmLabel,
				variant: confirmVariant,
				autoFocus: true,
				value: true,
			},
		],
	});

	return value === true;
}

export interface PromptDialogOptions {
	title?: string;
	okLabel?: string;
	cancelLabel?: string;
	defaultValue?: string;
	placeholder?: string;
	modal?: boolean;
	draggable?: boolean;
	width?: string;
	validate?: (value: string) => string | null;
	symbolicId?: string;
}

export async function promptDialog(
	message: string,
	options: PromptDialogOptions = {},
): Promise<string | null> {
	const {
		title = "Input Required",
		okLabel = "OK",
		cancelLabel = "Cancel",
		defaultValue = "",
		placeholder = "",
		modal = true,
		draggable = true,
		width,
		validate,
		symbolicId,
	} = options;

	const container = (<div></div>) as HTMLDivElement;
	const messageElement = (<p>{message}</p>) as HTMLParagraphElement;
	const input = (
		<input
			class="drafter-dialog-prompt-input"
			value={defaultValue}
			placeholder={placeholder}
			autoFocus
		/>
	) as HTMLInputElement;
	const validationMessage = (
		<p style="color: #9f2424; margin-top: 0.45rem;"></p>
	) as HTMLParagraphElement;

	container.appendChild(messageElement);
	container.appendChild(input);
	container.appendChild(validationMessage);

	const result = await showDialog<string | null>({
		title,
		content: container,
		modal,
		draggable,
		width,
		symbolicId,
		buttons: [
			{ label: cancelLabel, variant: "secondary", value: null },
			{
				label: okLabel,
				variant: "primary",
				autoFocus: true,
				onClick: () => {
					const value = input.value;
					const validationError = validate?.(value) ?? null;
					if (validationError) {
						validationMessage.textContent = validationError;
						input.focus();
						return { close: false };
					}
					validationMessage.textContent = "";
					return { value };
				},
			},
		],
	});

	return result ?? null;
}
