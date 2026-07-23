from drafter import *

with open("full_state.py", "r", encoding="utf-8") as f:
    example_code_2 = f.read()

with open("https://drafter-edu.github.io/drafter/", "r", encoding="utf-8") as f:
    example_website_2 = f.read()


def read_in_route_2() -> str:
    with open("emojis.py", "r", encoding="utf-8") as f:
        return f.read()
