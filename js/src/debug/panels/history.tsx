import type {
    RequestEvent,
    RequestParseEvent,
    ResponseEvent,
} from "../telemetry/requests";

type HistoryEvent = RequestEvent | ResponseEvent;

/**
 * Converts HTTP status codes to human-readable status names
 */
function statusCodeToText(statusCode: number): string {
    if (statusCode === 200) return "Success";
    if (statusCode >= 200 && statusCode < 300) return `Success (${statusCode})`;
    if (statusCode >= 300 && statusCode < 400) return `Redirect (${statusCode})`;
    if (statusCode >= 400 && statusCode < 500) return `Client Error (${statusCode})`;
    if (statusCode >= 500) return `Server Error (${statusCode})`;
    return `${statusCode}`;
}

/**
 * Truncates a URL by showing start and end with "..." in the middle.
 * Returns a clickable element that can expand/collapse.
 */
function createTruncatableUrl(url: string, maxLength: number = 50): HTMLElement {
    if (url.length <= maxLength) {
        return <code class="drafter-history-request-url">{url}</code>;
    }
    
    const halfLength = Math.floor((maxLength - 3) / 2);
    const truncated = url.slice(0, halfLength) + "..." + url.slice(-halfLength);
    
    const code = (
        <code class="drafter-history-request-url truncatable-url truncated" data-full-value={url}>
            {truncated}
        </code>
    ) as HTMLElement;
    
    code.addEventListener("click", (e) => {
        const target = e.target as HTMLElement;
        const isTruncated = target.classList.contains("truncated");
        if (isTruncated) {
            target.textContent = target.dataset.fullValue || url;
            target.classList.remove("truncated");
        } else {
            target.textContent = truncated;
            target.classList.add("truncated");
        }
    });
    
    return code;
}

export class HistoryPanel {
    private contentElement: HTMLElement;
    private listElement: HTMLElement;

    private MAX_URL_LENGTH = 42;

    constructor() {
        const content = document.getElementById(
            "drafter-debug-page-history-content"
        );

        if (!content) {
            throw new Error("DebugPanel: History section not found.");
        }

        this.contentElement = content;

        const clearButton = (
            <button class="drafter-debug-clear-history-btn">
                Clear History
            </button>
        ) as HTMLButtonElement;
        
        clearButton.addEventListener("click", () => this.clearHistory());

        const initialContent = (
            <div>
                {clearButton}
                <div
                    id="drafter-debug-page-history-list"
                    class="drafter-debug-page-history-list"
                ></div>
            </div>
        );
        content?.appendChild(initialContent);
        this.listElement = document.getElementById(
            "drafter-debug-page-history-list"
        )!;
    }

    public clearHistory(): void {
        if (this.listElement) {
            this.listElement.innerHTML = "";
        }
    }

    public addRequest(request: RequestEvent): void {
        const now = new Date();
        const prettyTime = now.toLocaleTimeString();

        const urlElement = createTruncatableUrl(request.url);
        
        // Show parameters if available
        const paramsElement = request.kwargs && request.kwargs !== "{}" 
            ? (
                <div class="request-params">
                    <strong>Parameters: </strong>
                    <code class="drafter-history-request-params">{request.kwargs}</code>
                </div>
            )
            : null;
        
        // Create a link to recreate the request
        const recreateLink = (
            <a href={request.url} class="request-recreate-link" title="Click to recreate this request">
                🔄 Recreate
            </a>
        );
        
        const requestElement = (
            <div class="history-event" data-request-id={request.request_id}>
                <div class="request-event">
                    <strong>Request:</strong>{" "}
                    <span class="drafter-history-request-time">
                        {prettyTime}
                    </span>
                    {urlElement}{" "}
                    {recreateLink}{" "}
                    <span class="drafter-history-request-meta">
                        <span class="drafter-history-via">via</span> {request.action} (ID: {request.request_id})
                    </span>
                </div>
                {paramsElement}
            </div>
        );

        this.listElement.prepend(requestElement);
    }

    public addRequestParse(parseEvent: RequestParseEvent): void {
        const requestEventElement = this.contentElement.querySelector(
            `.history-event[data-request-id="${parseEvent.request_id}"]`
        );

        if (requestEventElement) {
            const parseElement = (
                <div class="request-parse-event">
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
            `.history-event[data-request-id="${response.request_id}"]`
        );

        if (requestEventElement) {
            requestEventElement.classList.add("has-response");
        } else {
            throw new Error(
                `DebugPanel: Corresponding request ${response.request_id} not found for response ID ${response.response_id}.`
            );
        }
        // Choose a red marker, green marker, or yellow marker based on errors/warnings
        const marker = response.has_errors
            ? "🔴"
            : response.has_warnings
            ? "🟡"
            : "🟢";
        const statusText = statusCodeToText(response.status_code);
        
        // Detect content type and format accordingly
        const contentElement = this.formatResponseContent(response);
        
        const responseElement = (
            <div class="response-event">
                <strong>Response:</strong> {marker} {statusText} for
                Request ID: {response.request_id} (Response ID:{" "}
                {response.response_id})
                <details>
                    <summary>View Page Content</summary>
                    {contentElement}
                </details>
            </div>
        );

        requestEventElement?.appendChild(responseElement);
    }

    /**
     * Formats response content based on content type detection
     */
    private formatResponseContent(response: ResponseEvent): HTMLElement {
        const content = response.formatted_page_content || "No content available.";
        
        // Check for image content
        if (content.includes('<img ') || content.includes('data:image/')) {
            const div = <div class="response-media-content"></div> as HTMLElement;
            
            // Parse and display images
            const imgRegex = /<img[^>]+src="([^"]+)"[^>]*>/gi;
            let match;
            const images: HTMLElement[] = [];
            
            while ((match = imgRegex.exec(content)) !== null) {
                const imgSrc = match[1];
                images.push(
                    <div class="response-image-container">
                        <img src={imgSrc} alt="Response Image" class="response-image" />
                        <div class="response-image-info">📷 Image: {imgSrc.substring(0, 50)}...</div>
                    </div>
                );
            }
            
            if (images.length > 0) {
                div.append(...images);
                div.appendChild(<pre class="response-html-source">{content}</pre>);
            } else {
                div.appendChild(<pre>{content}</pre>);
            }
            
            return div;
        }
        
        // Check for file downloads
        if (content.includes('<a ') && (content.includes('download') || content.includes('href="data:'))) {
            const div = <div class="response-media-content"></div> as HTMLElement;
            
            const downloadRegex = /<a[^>]+href="([^"]+)"[^>]*download[^>]*>([^<]*)<\/a>/gi;
            let match;
            const downloads: HTMLElement[] = [];
            
            while ((match = downloadRegex.exec(content)) !== null) {
                const downloadHref = match[1];
                const downloadText = match[2] || 'Download File';
                downloads.push(
                    <div class="response-download-info">
                        📥 Download: <code>{downloadText}</code> ({downloadHref.substring(0, 40)}...)
                    </div>
                );
            }
            
            if (downloads.length > 0) {
                div.append(...downloads);
                div.appendChild(<pre class="response-html-source">{content}</pre>);
                return div;
            }
        }
        
        // Check for video/audio content
        if (content.includes('<video ') || content.includes('<audio ')) {
            const div = <div class="response-media-content"></div> as HTMLElement;
            
            if (content.includes('<video ')) {
                div.appendChild(<div class="response-media-info">🎥 Video content detected</div>);
            }
            if (content.includes('<audio ')) {
                div.appendChild(<div class="response-media-info">🎵 Audio content detected</div>);
            }
            
            div.appendChild(<pre class="response-html-source">{content}</pre>);
            return div;
        }
        
        // Default: plain text/HTML
        return <pre>{content}</pre> as HTMLElement;
    }
}
