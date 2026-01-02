/**
 * Truncates a URL by showing start and end with "..." in the middle.
 * Returns a clickable element that can expand/collapse.
 */
export function createTruncatableUrl(url: string, maxLength: number = 50) {
    if (url.length <= maxLength) {
        return <code class="drafter-history-request-url">{url}</code>;
    }

    const halfLength = Math.floor((maxLength - 3) / 2);
    const truncated = url.slice(0, halfLength) + "..." + url.slice(-halfLength);

    const code = (
        <code
            class="drafter-history-request-url truncatable-url truncated"
            data-full-value={url}
        >
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
