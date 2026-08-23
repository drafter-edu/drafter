"""Demonstrates the add_website_* helpers for files next to the program.

Run with `drafter examples/website_files.py` (from the repository root) or
`python website_files.py` from inside examples/. Then try the mistakes at
the bottom to see the student-facing errors.

- add_website_css_file: a stylesheet from a file or a URL, on every page
- add_website_js_file: a script from a file or a URL, on every page
- add_website_js: inline JavaScript that runs when the site loads
- add_website_file: other files the site needs, checked now and copied
  into the built site when deployed (`drafter website_files.py --compile`)
"""

from dataclasses import dataclass

from drafter import *

set_website_title("Fortune Teller")

# A stylesheet saved next to this program (a subfolder is fine). Drafter
# checks that the file exists as soon as this line runs.
add_website_css_file("files/site_style.css")
# A stylesheet from the web: a Google Fonts URL, used by the rule below.
add_website_css_file("https://fonts.googleapis.com/css2?family=Lora&display=swap")
add_website_css(".fortune-card", "font-family: 'Lora', Georgia, serif;")

# A script file next to the program, plus a line of inline JavaScript.
add_website_js_file("files/site_script.js")
add_website_js("console.log('Inline JavaScript from add_website_js ran.');")

# A data file the routes open() at runtime. Declaring it means a typo is
# caught right here, and the file ships with the compiled site.
add_website_file("files/fortunes.txt")


@dataclass
class State:
    fortune: str
    count: int


def load_fortunes() -> list[str]:
    with open("files/fortunes.txt", encoding="utf-8") as fortunes_file:
        return [line.strip() for line in fortunes_file if line.strip()]


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            Header("Fortune Teller"),
            Div(state.fortune, classes="fortune-card"),
            Span(f"Fortunes told: {state.count}", classes="fortune-count"),
            LineBreak(),
            Button("Tell my fortune", next_fortune, classes="fortune-button"),
            LineBreak(),
            "Open the browser console to see the messages from the JavaScript.",
        ],
    )


@route
def next_fortune(state: State) -> Page:
    fortunes = load_fortunes()
    state.fortune = fortunes[state.count % len(fortunes)]
    state.count += 1
    return index(state)


# Uncomment any of these to see the helpful error each mistake produces:
# add_website_css_file("files/site_styles.css")   # typo -> suggests site_style.css
# add_website_css_file("site_style.css")          # wrong folder -> points at files/site_style.css
# add_website_css_file("files/fortunes.txt")      # not a .css file
# add_website_css("files/site_style.css")         # a file name given as CSS code
# add_website_file("files/fortune.txt")           # missing -> suggests fortunes.txt
# add_website_file("../secret.txt")               # outside the program folder

start_server(State("Press the button to learn your fate.", 0))
