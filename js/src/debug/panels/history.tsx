import type {
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
} from "../telemetry/requests";

type HistoryEvent = RequestEvent | ResponseEvent;

export class HistoryPanel {
    private contentElement: HTMLElement;
    private listElement: HTMLElement;

    constructor() {
        const content = document.getElementById(
            "drafter-debug-page-history-content"
        );

        if (!content) {
            throw new Error("DebugPanel: History section not found.");
        }

        this.contentElement = content;

        const initialContent = <div id="drafter-debug-page-history-list"></div>;
        content?.appendChild(initialContent);
        this.listElement = document.getElementById(
            "drafter-debug-page-history-list"
        )!;
    }

    public addRequest(request: RequestEvent): void {
        const requestElement = (
            <div
                class="history-event request-event"
                data-request-id={request.request_id}
            >
                <strong>Request:</strong> {request.url} (ID:{" "}
                {request.request_id}) via {request.action}
            </div>
        );

        this.listElement.appendChild(requestElement);
    }

    public addRequestParse(parseEvent: RequestParseEvent): void {
        const requestEventElement = this.contentElement.querySelector(
            `.history-event.request-event[data-request-id="${parseEvent.request_id}"]`
        );

        if (requestEventElement) {
            const parseElement = (
                <div class="history-event request-parse-event">
                    <strong>Called: </strong>
                    <code>{parseEvent.representation}</code>
                </div>
            );

            requestEventElement.appendChild(parseElement);
        } else {
            throw new Error(
                `DebugPanel: Corresponding request ${parseEvent.request_id} not found for parse event.`
            );
        }
    }

    public addResponse(response: ResponseEvent): void {
        const requestEventElement = this.contentElement.querySelector(
            `.history-event.request-event[data-request-id="${response.request_id}"]`
        );

        if (requestEventElement) {
            requestEventElement.classList.add("has-response");
        } else {
            throw new Error(
                `DebugPanel: Corresponding request ${response.request_id} not found for response ID ${response.response_id}.`
            );
        }
        const responseElement = (
            <div class="history-event response-event">
                <strong>Response:</strong> {response.status_code} for Request
                ID: {response.request_id} (Response ID: {response.response_id})
            </div>
        );

        requestEventElement?.appendChild(responseElement);
    }
}
