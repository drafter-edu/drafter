export function enhanceCodeSnippetsWithCopyButtons() {
    let snippets = document.getElementsByClassName("copyable");
    const buttonText = "📋";
    for (let i = 0; i < snippets.length; i++) {
        let snippet = snippets[i];
        let code = snippet.textContent;
        //snippets[i].classList.add('hljs'); // append copy button to pre tag
        snippet.innerHTML =
            '<button class="copy-button">' +
            buttonText +
            "</button>" +
            snippet.innerHTML; // append copy button
        const copyButtons = snippet.getElementsByClassName("copy-button");
        const button = copyButtons[0] as HTMLButtonElement;
        button.addEventListener("click", function () {
            this.innerText = "Copying..";
            navigator.clipboard.writeText(code);
            this.innerText = "Copied!";
            let button = this;
            setTimeout(function () {
                button.innerText = buttonText;
            }, 1000);
        });
    }
}

export function enhanceExpandables() {
    let expandables = document.getElementsByClassName("expandable");
    // Any span with the expandable class will be turned into "...", and can be clicked
    // to expand the rest of the content.
    for (let i = 0; i < expandables.length; i++) {
        let expandable = expandables[i] as HTMLElement;
        let content = expandable.textContent;
        if (content.length > 100) {
            expandable.textContent = content.slice(0, 100) + "...";
            expandable.style.cursor = "pointer";
            expandable.addEventListener("click", function () {
                if (expandable.textContent.endsWith("...")) {
                    expandable.textContent = content;
                } else {
                    expandable.textContent = content.slice(0, 100) + "...";
                }
            });
        }
    }
}
