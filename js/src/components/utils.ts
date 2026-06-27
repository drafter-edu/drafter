/** Attribute name used to store event handler routes as a JSON map. */
export const DRAFTER_EVENT_HANDLER = "data--drafter-handlers";

/**
 * Retrieve the event-handler route map stored on a Drafter custom element.
 *
 * The Python Component base class serialises event callbacks as a JSON object
 * on the `data--drafter-handlers` attribute, e.g.:
 *   `{"finish": "/beep", "tick": "/tick_route"}`
 *
 * Returns an empty object when the attribute is absent.
 */
export function getHandlers(element: HTMLElement): Record<string, string> {
	const raw = element.getAttribute(DRAFTER_EVENT_HANDLER);
	return raw ? JSON.parse(raw) : {};
}
