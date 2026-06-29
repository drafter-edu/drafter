import { alertDialog } from "../dialogs";

export interface DrafterInitOptions {
	studentFilename?: string;
	code?: string;
	url?: string;
	presentErrors?: boolean;
	assetsUrl?: string;
	loadPackagesAutomatically?: boolean;
	explicitPackageList?: string[];
}

export interface SystemErrorOptions {
	title?: string;
	suggestion?: string;
	presentation?: "auto" | "dialog" | "root";
	symbolicId?: string;
}

export function clearDrafterSiteRoot() {
	const rootElement = document.getElementById(
		"drafter-root--",
	) as HTMLElement;
	if (rootElement) {
		rootElement.innerHTML = "";
	} else {
		throw new Error(`Element with ID drafter-root-- not found`);
	}
}

export function normalizeSystemError(error: unknown): Error {
	if (error instanceof Error) {
		return error;
	}

	return new Error(String(error));
}

function formatSystemErrorMessage(
	message: string,
	error: Error,
	suggestion: string,
): string {
	return `${message}\n\n${suggestion}\n\n${error.name}: ${error.message}`;
}

function renderSystemErrorInRoot(
	message: string,
	error: Error,
	suggestion: string,
): boolean {
	const rootElement = document.getElementById("drafter-root--");
	if (!rootElement) {
		return false;
	}

	rootElement.replaceChildren();

	const container = document.createElement("div");
	container.className = "drafter-system-error";

	const title = document.createElement("h1");
	title.textContent = "Drafter System Error";

	const lead = document.createElement("p");
	lead.textContent = message;

	const advice = document.createElement("p");
	advice.textContent = suggestion;

	const details = document.createElement("pre");
	details.textContent = `${error.name}: ${error.message}`;

	container.append(title, lead, advice, details);
	rootElement.appendChild(container);
	return true;
}

export function presentSystemError(
	message: string,
	error: unknown,
	{
		title = "System Error",
		suggestion = "Please show this to your instructor for more help.",
		presentation = "auto",
		symbolicId = "drafter-system-error",
	}: SystemErrorOptions = {},
): Error {
	const normalizedError = normalizeSystemError(error);

	if (
		(presentation === "root" || presentation === "auto") &&
		renderSystemErrorInRoot(message, normalizedError, suggestion)
	) {
		return normalizedError;
	}

	void alertDialog(
		formatSystemErrorMessage(message, normalizedError, suggestion),
		{
			title,
			modal: true,
			draggable: true,
			width: "560px",
			symbolicId,
		},
	).catch((dialogError) => {
		console.error(
			"[Drafter System Error] Failed to present system error dialog",
			dialogError,
		);
	});

	return normalizedError;
}

export function handleSystemError(
	message: string,
	error: unknown,
	suggestion: string = "Please show this to your instructor for more help.",
) {
	console.error("[Drafter System Error]", message, error);
	return presentSystemError(message, error, { suggestion });
}

export function handleSystemErrorWithOptions(
	message: string,
	error: unknown,
	options: SystemErrorOptions,
) {
	console.error("[Drafter System Error]", message, error);
	return presentSystemError(message, error, options);
}
