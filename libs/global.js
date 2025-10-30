let snippets = document.getElementsByClassName('copyable');
const buttonText = "📋";
console.log(snippets);
for (let i = 0; i < snippets.length; i++) {
    code = snippets[i].textContent;
    //snippets[i].classList.add('hljs'); // append copy button to pre tag
    snippets[i].innerHTML = '<button class="copy-button">'+buttonText+'</button>' + snippets[i].innerHTML; // append copy button
    snippets[i].getElementsByClassName("copy-button")[0].addEventListener("click", function () {
        this.innerText = 'Copying..';
        navigator.clipboard.writeText(code);
        this.innerText = 'Copied!';
        button = this;
        setTimeout(function () {
            button.innerText = buttonText;
        }, 1000)
    });
}

let expandables = document.getElementsByClassName('expandable');
// Any span with the expandable class will be turned into "...", and can be clicked
// to expand the rest of the content.
for (let i = 0; i < expandables.length; i++) {
    let expandable = expandables[i];
    let content = expandable.textContent;
    if (content.length > 100) {
        expandable.textContent = content.slice(0, 100) + '...';
        expandable.style.cursor = 'pointer';
        expandable.addEventListener('click', function () {
            if (expandable.textContent.endsWith('...')) {
                expandable.textContent = content;
            } else {
                expandable.textContent = content.slice(0, 100) + '...';
            }
        });
    }
}

function navigateToAbout() {
    // if Sk.bottle is available, we'll use that:
    if (window.Sk && window.Sk.bottle) {
        window.Sk.bottle.changeLocation('/--about');
    } else {
        window.location.href = '--about';
    }
}

window.stopInformationPageListener = function() {
    throw new Error("Information page listener not initialized yet.");
};
window.addEventListener("popstate", (e) => {
    if (window.Sk && window.Sk.bottle) {
        const state = e.state;
        if (state?.flag === "DRAFTER_LOAD_ROUTE" && state?.realLocation) {
            window.Sk.bottle.changeLocation(state?.realLocation);
        } else {
            // Fallback for entries we didn't create (direct loads, external links, etc.)
            window.Sk.bottle.changeLocation(location.pathname);
        }
    }
});
document.addEventListener('DOMContentLoaded', () => {
    let lastPressTime = 0;
    const doublePressDelay = 600; // milliseconds allowed between presses

    function doubleIHandler(event) {
        // Check for Ctrl+I (case-insensitive)
        if (event.ctrlKey && (event.key === 'i' || event.key === 'I')) {
            const now = Date.now();

            if (now - lastPressTime <= doublePressDelay) {
                // Detected a double press within the allowed time
                navigateToAbout();
            }

            // Update the last press time
            lastPressTime = now;

            // Prevent default browser behavior if needed (e.g., to stop opening dev tools)
            event.preventDefault();
        }
    }

    document.addEventListener('keydown', doubleIHandler);
    window.stopInformationPageListener = () => {
        document.removeEventListener('keydown', doubleIHandler);
    };

});