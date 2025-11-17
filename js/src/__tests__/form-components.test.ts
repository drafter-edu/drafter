/**
 * Tests for different form components
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Form Components Tests", () => {
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("handles TextBox with different default values", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    text1: str
    text2: str
    text3: str

@route
def index(state: State):
    return Page(state, [
        "Enter values:",
        TextBox("text1", state.text1),
        TextBox("text2", state.text2),
        TextBox("text3", state.text3),
        Button("Submit", submit),
    ])

@route
def submit(state: State, text1: str, text2: str, text3: str):
    state.text1 = text1
    state.text2 = text2
    state.text3 = text3
    return result(state)

@route
def result(state: State):
    return Page(state, [
        f"Text1: {state.text1}",
        f"Text2: {state.text2}",
        f"Text3: {state.text3}",
        Button("Back", index),
    ])

start_server(State("", "default text", "123"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const text1 = app.getByRole("textbox", { name: /text1/i });
        const text2 = app.getByRole("textbox", { name: /text2/i });
        const text3 = app.getByRole("textbox", { name: /text3/i });

        expect(text1).toHaveValue("");
        expect(text2).toHaveValue("default text");
        expect(text3).toHaveValue("123");

        await userEvent.type(text1, "Hello");
        await userEvent.clear(text2);
        await userEvent.type(text2, "World");
        await userEvent.clear(text3);
        await userEvent.type(text3, "456");

        await userEvent.click(
            await app.findByRole("button", { name: /submit/i })
        );

        await app.findByText(/Text1:\s*Hello/);
        await app.findByText(/Text2:\s*World/);
        await app.findByText(/Text3:\s*456/);
    });

    test("handles CheckBox component", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    option1: bool
    option2: bool
    option3: bool

@route
def index(state: State):
    return Page(state, [
        "Select options:",
        CheckBox("option1", state.option1),
        CheckBox("option2", state.option2),
        CheckBox("option3", state.option3),
        Button("Submit", submit),
    ])

@route
def submit(state: State, option1: bool, option2: bool, option3: bool):
    state.option1 = option1
    state.option2 = option2
    state.option3 = option3
    return result(state)

@route
def result(state: State):
    return Page(state, [
        f"Option1: {state.option1}",
        f"Option2: {state.option2}",
        f"Option3: {state.option3}",
        Button("Back", index),
    ])

start_server(State(True, False, True))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const option1 = app.getByRole("checkbox", { name: /option1/i });
        const option2 = app.getByRole("checkbox", { name: /option2/i });
        const option3 = app.getByRole("checkbox", { name: /option3/i });

        expect(option1).toBeChecked();
        expect(option2).not.toBeChecked();
        expect(option3).toBeChecked();

        await userEvent.click(option1); // uncheck
        await userEvent.click(option2); // check
        await userEvent.click(
            await app.findByRole("button", { name: /submit/i })
        );

        await app.findByText(/Option1:\s*False/);
        await app.findByText(/Option2:\s*True/);
        await app.findByText(/Option3:\s*True/);
    });

    test("handles SelectBox component", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    selected: str

@route
def index(state: State):
    return Page(state, [
        "Choose an option:",
        SelectBox("choice", ["apple", "banana", "cherry"], state.selected),
        Button("Submit", submit),
    ])

@route
def submit(state: State, choice: str):
    state.selected = choice
    return result(state)

@route
def result(state: State):
    return Page(state, [
        f"You selected: {state.selected}",
        Button("Back", index),
    ])

start_server(State("banana"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const selectBox = app.getByRole("combobox", { name: /choice/i });
        expect(selectBox).toHaveValue("banana");

        await userEvent.selectOptions(selectBox, "cherry");
        await userEvent.click(
            await app.findByRole("button", { name: /submit/i })
        );

        await app.findByText(/You selected:\s*cherry/);
    });

    test("handles RadioButton component", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    choice: str

@route
def index(state: State):
    return Page(state, [
        "Choose one:",
        RadioButton("choice", ["red", "green", "blue"], state.choice),
        Button("Submit", submit),
    ])

@route
def submit(state: State, choice: str):
    state.choice = choice
    return result(state)

@route
def result(state: State):
    return Page(state, [
        f"You chose: {state.choice}",
        Button("Back", index),
    ])

start_server(State("green"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const redRadio = app.getByRole("radio", { name: /red/i });
        const greenRadio = app.getByRole("radio", { name: /green/i });
        const blueRadio = app.getByRole("radio", { name: /blue/i });

        expect(greenRadio).toBeChecked();
        expect(redRadio).not.toBeChecked();

        await userEvent.click(blueRadio);
        await userEvent.click(
            await app.findByRole("button", { name: /submit/i })
        );

        await app.findByText(/You chose:\s*blue/);
    });

    test("handles TextArea component", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    content: str

@route
def index(state: State):
    return Page(state, [
        "Enter long text:",
        TextArea("content", state.content),
        Button("Submit", submit),
    ])

@route
def submit(state: State, content: str):
    state.content = content
    return result(state)

@route
def result(state: State):
    return Page(state, [
        "Your text:",
        state.content,
        Button("Back", index),
    ])

start_server(State("Initial content\\nSecond line"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const textarea = app.getByRole("textbox", { name: /content/i });
        expect(textarea.tagName).toBe("TEXTAREA");

        await userEvent.clear(textarea);
        await userEvent.type(textarea, "New content{Enter}New line");
        await userEvent.click(
            await app.findByRole("button", { name: /submit/i })
        );

        await app.findByText(/New content/);
    });

    test("handles mixed form components", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    name: str
    age: int
    subscribe: bool
    color: str

@route
def index(state: State):
    return Page(state, [
        "Registration Form",
        TextBox("name", state.name),
        TextBox("age", str(state.age)),
        CheckBox("subscribe", state.subscribe),
        SelectBox("color", ["red", "blue", "green"], state.color),
        Button("Register", register),
    ])

@route
def register(state: State, name: str, age: str, subscribe: bool, color: str):
    state.name = name
    state.age = int(age)
    state.subscribe = subscribe
    state.color = color
    return result(state)

@route
def result(state: State):
    return Page(state, [
        f"Name: {state.name}",
        f"Age: {state.age}",
        f"Subscribe: {state.subscribe}",
        f"Color: {state.color}",
    ])

start_server(State("", 0, False, "red"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        const nameBox = app.getByRole("textbox", { name: /name/i });
        const ageBox = app.getByRole("textbox", { name: /age/i });
        const subscribeBox = app.getByRole("checkbox", { name: /subscribe/i });
        const colorBox = app.getByRole("combobox", { name: /color/i });

        await userEvent.type(nameBox, "Alice");
        await userEvent.type(ageBox, "25");
        await userEvent.click(subscribeBox);
        await userEvent.selectOptions(colorBox, "blue");

        await userEvent.click(
            await app.findByRole("button", { name: /register/i })
        );

        await app.findByText(/Name:\s*Alice/);
        await app.findByText(/Age:\s*25/);
        await app.findByText(/Subscribe:\s*True/);
        await app.findByText(/Color:\s*blue/);
    });
});
