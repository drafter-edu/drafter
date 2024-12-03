from tests.helpers import *
from drafter import *
from dataclasses import dataclass

def test_button_arguments(browser, splinter_headless):
    drafter_server = TestServer(None)

    @route(server=drafter_server.server)
    def index(state) -> Page:
        return Page(state, [
            "Welcome to Ada's Fruit site!",
            TextBox("pears", "7"),
            TextBox("plums", "3"),
            Argument("apples", 5),
            Argument('words', 'ups and downs'),
            Argument("check", True),
            Button("Buy Ada's Fruits", "buy_page", [
                Argument("oranges", 7),
                Argument("fruits", "oranges and pears and more"),
                Argument("bonus", False)
            ]),
        ])

    @route(server=drafter_server.server)
    def buy_page(state, apples: int, oranges: int, pears: int, plums: str, fruits: str, words: str, check: bool,
                 bonus: bool) -> Page:
        return Page(state, [
            f"You bought {apples} apples, {oranges} oranges, {plums} plums, and {pears} pears. ({fruits}) ({words}) ({check}) ({bonus})"
        ])

    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present("Welcome to Ada's Fruit site!")

        browser.fill("pears", "100")
        browser.fill("plums", "200")
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()

        assert browser.is_text_present('You bought 5 apples, 7 oranges, 200 plums, and 100 pears. (oranges and pears and more) (ups and downs) (True) (False)')