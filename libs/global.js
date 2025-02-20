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