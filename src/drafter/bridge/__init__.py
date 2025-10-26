import document


def update_root(target: str, content: str) -> None:
    element = document.getElementById(target)
    element.innerHTML = content
    return element


def add_script(src: str) -> None:
    script = document.createElement("script")
    script.src = src
    head = document.getElementsByTagName("head")[0]
    head.appendChild(script)
    return script
