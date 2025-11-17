/**
 * Tests for complex interactions and state mutations
 */

import { describe, test, expect, beforeAll } from "@jest/globals";
import "../../../src/drafter/assets/js/skulpt.js";
import "../../../src/drafter/assets/js/skulpt-stdlib.js";
import "../../../src/drafter/assets/js/skulpt-drafter.js";
import "../../../src/drafter/assets/js/drafter.js";
import { runStudentCode } from "../index";
import { within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";

describe("Complex Interactions Tests", () => {
    beforeAll(() => {
        document.body.innerHTML = "<div id='drafter-root--'></div>";
    });

    test("handles shopping cart with multiple items", async () => {
        const code = `
from drafter import *

@dataclass
class Item:
    name: str
    price: float
    quantity: int

@dataclass
class State:
    cart: list[Item]
    total: float

@route
def index(state: State):
    state.total = sum(item.price * item.quantity for item in state.cart)
    cart_display = [f"{item.name}: ${item.price} x {item.quantity}" for item in state.cart]
    return Page(state, [
        Header("Shopping Cart"),
        NumberedList(cart_display) if cart_display else "Cart is empty",
        f"Total: ${state.total:.2f}",
        HorizontalRule(),
        "Add item:",
        TextBox("name"),
        TextBox("price"),
        TextBox("quantity"),
        Button("Add to Cart", add_item),
    ])

@route
def add_item(state: State, name: str, price: str, quantity: str):
    state.cart.append(Item(name, float(price), int(quantity)))
    return index(state)

start_server(State([], 0.0))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Cart is empty/);
        await app.findByText(/Total:\s*\$0\.00/);

        // Add first item
        const nameBox = app.getByRole("textbox", { name: /^name$/i });
        const priceBox = app.getByRole("textbox", { name: /price/i });
        const quantityBox = app.getByRole("textbox", { name: /quantity/i });

        await userEvent.type(nameBox, "Apple");
        await userEvent.type(priceBox, "1.50");
        await userEvent.type(quantityBox, "3");
        await userEvent.click(
            await app.findByRole("button", { name: /add to cart/i })
        );

        await app.findByText(/Apple:\s*\$1\.5 x 3/);
        await app.findByText(/Total:\s*\$4\.50/);

        // Add second item
        const nameBox2 = app.getByRole("textbox", { name: /^name$/i });
        const priceBox2 = app.getByRole("textbox", { name: /price/i });
        const quantityBox2 = app.getByRole("textbox", { name: /quantity/i });

        await userEvent.clear(nameBox2);
        await userEvent.type(nameBox2, "Banana");
        await userEvent.clear(priceBox2);
        await userEvent.type(priceBox2, "0.75");
        await userEvent.clear(quantityBox2);
        await userEvent.type(quantityBox2, "2");
        await userEvent.click(
            await app.findByRole("button", { name: /add to cart/i })
        );

        await app.findByText(/Banana:\s*\$0\.75 x 2/);
        await app.findByText(/Total:\s*\$6\.00/);
    });

    test("handles todo list with add and delete operations", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    todos: list[str]
    mode: str

@route
def index(state: State):
    state.mode = "list"
    return Page(state, [
        Header("Todo List"),
        NumberedList(state.todos) if state.todos else "No todos",
        Button("Add Todo", add_mode),
        Button("Delete Todo", delete_mode) if state.todos else "",
    ])

@route
def add_mode(state: State):
    state.mode = "add"
    return Page(state, [
        Header("Add New Todo"),
        TextBox("task"),
        Button("Save", save_todo),
        Button("Cancel", index),
    ])

@route
def save_todo(state: State, task: str):
    if task:
        state.todos.append(task)
    return index(state)

@route
def delete_mode(state: State):
    state.mode = "delete"
    return Page(state, [
        Header("Delete Todo"),
        NumberedList(state.todos),
        TextBox("index_to_delete"),
        Button("Delete", delete_todo),
        Button("Cancel", index),
    ])

@route
def delete_todo(state: State, index_to_delete: str):
    if index_to_delete.isdigit():
        idx = int(index_to_delete) - 1
        if 0 <= idx < len(state.todos):
            state.todos.pop(idx)
    return index(state)

start_server(State([], "list"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/No todos/);

        // Add first todo
        await userEvent.click(
            await app.findByRole("button", { name: /add todo/i })
        );
        await app.findByText(/Add New Todo/);

        const taskBox = app.getByRole("textbox", { name: /task/i });
        await userEvent.type(taskBox, "Buy milk");
        await userEvent.click(await app.findByRole("button", { name: /^save$/i }));

        await app.findByText(/Buy milk/);

        // Add second todo
        await userEvent.click(
            await app.findByRole("button", { name: /add todo/i })
        );
        const taskBox2 = app.getByRole("textbox", { name: /task/i });
        await userEvent.type(taskBox2, "Walk dog");
        await userEvent.click(await app.findByRole("button", { name: /^save$/i }));

        await app.findByText(/Walk dog/);

        // Delete first todo
        await userEvent.click(
            await app.findByRole("button", { name: /delete todo/i })
        );
        const deleteBox = app.getByRole("textbox", {
            name: /index_to_delete/i,
        });
        await userEvent.type(deleteBox, "1");
        await userEvent.click(
            await app.findByRole("button", { name: /^delete$/i })
        );

        // "Buy milk" should be gone, "Walk dog" should remain
        expect(
            drafterBody?.textContent?.includes("Buy milk")
        ).toBeFalsy();
        await app.findByText(/Walk dog/);
    });

    test("handles form with validation and error messages", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    username: str
    password: str
    error_message: str
    logged_in: bool

@route
def index(state: State):
    if state.logged_in:
        return Page(state, [
            f"Welcome, {state.username}!",
            Button("Logout", logout),
        ])
    else:
        return Page(state, [
            Header("Login"),
            state.error_message if state.error_message else "",
            TextBox("username"),
            TextBox("password", kind="password"),
            Button("Login", login),
        ])

@route
def login(state: State, username: str, password: str):
    if not username:
        state.error_message = "Username is required"
        return index(state)
    if len(password) < 3:
        state.error_message = "Password must be at least 3 characters"
        return index(state)
    state.username = username
    state.password = password
    state.logged_in = True
    state.error_message = ""
    return index(state)

@route
def logout(state: State):
    state.logged_in = False
    state.username = ""
    state.password = ""
    state.error_message = ""
    return index(state)

start_server(State("", "", "", False))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        // Try to login with empty username
        await userEvent.click(
            await app.findByRole("button", { name: /login/i })
        );
        await app.findByText(/Username is required/);

        // Try to login with short password
        const usernameBox = app.getByRole("textbox", { name: /username/i });
        await userEvent.type(usernameBox, "alice");
        const passwordBox = app.getByRole("textbox", { name: /password/i });
        await userEvent.type(passwordBox, "12");
        await userEvent.click(
            await app.findByRole("button", { name: /login/i })
        );
        await app.findByText(/Password must be at least 3 characters/);

        // Login successfully
        const usernameBox2 = app.getByRole("textbox", { name: /username/i });
        await userEvent.clear(usernameBox2);
        await userEvent.type(usernameBox2, "alice");
        const passwordBox2 = app.getByRole("textbox", { name: /password/i });
        await userEvent.clear(passwordBox2);
        await userEvent.type(passwordBox2, "password123");
        await userEvent.click(
            await app.findByRole("button", { name: /login/i })
        );

        await app.findByText(/Welcome, alice!/);

        // Logout
        await userEvent.click(
            await app.findByRole("button", { name: /logout/i })
        );
        await app.findByText(/Login/);
    });

    test("handles calculator with multiple operations", async () => {
        const code = `
from drafter import *

@dataclass
class State:
    result: float
    first_number: float
    operation: str
    display: str

@route
def index(state: State):
    return Page(state, [
        Header("Calculator"),
        f"Display: {state.display}",
        TextBox("number", state.display),
        Button("Add", set_operation, [Argument("op", "add")]),
        Button("Subtract", set_operation, [Argument("op", "subtract")]),
        Button("Multiply", set_operation, [Argument("op", "multiply")]),
        Button("Divide", set_operation, [Argument("op", "divide")]),
        Button("Equals", calculate),
        Button("Clear", clear),
    ])

@route
def set_operation(state: State, number: str, op: str):
    state.first_number = float(number) if number else 0.0
    state.operation = op
    state.display = "0"
    return index(state)

@route
def calculate(state: State, number: str):
    second_number = float(number) if number else 0.0
    if state.operation == "add":
        state.result = state.first_number + second_number
    elif state.operation == "subtract":
        state.result = state.first_number - second_number
    elif state.operation == "multiply":
        state.result = state.first_number * second_number
    elif state.operation == "divide":
        state.result = state.first_number / second_number if second_number != 0 else 0.0
    state.display = str(state.result)
    state.operation = ""
    return index(state)

@route
def clear(state: State):
    state.result = 0.0
    state.first_number = 0.0
    state.operation = ""
    state.display = "0"
    return index(state)

start_server(State(0.0, 0.0, "", "0"))
`;
        await runStudentCode({ code, presentErrors: false });

        const drafterBody = document.querySelector("#drafter-body--");
        const app = within(drafterBody as HTMLElement);

        await app.findByText(/Display:\s*0/);

        // Calculate 5 + 3
        const numberBox = app.getByRole("textbox", { name: /number/i });
        await userEvent.clear(numberBox);
        await userEvent.type(numberBox, "5");
        await userEvent.click(await app.findByRole("button", { name: /^add$/i }));

        const numberBox2 = app.getByRole("textbox", { name: /number/i });
        await userEvent.clear(numberBox2);
        await userEvent.type(numberBox2, "3");
        await userEvent.click(
            await app.findByRole("button", { name: /equals/i })
        );

        await app.findByText(/Display:\s*8\.0/);

        // Calculate 10 * 4
        await userEvent.click(await app.findByRole("button", { name: /clear/i }));
        const numberBox3 = app.getByRole("textbox", { name: /number/i });
        await userEvent.clear(numberBox3);
        await userEvent.type(numberBox3, "10");
        await userEvent.click(
            await app.findByRole("button", { name: /multiply/i })
        );

        const numberBox4 = app.getByRole("textbox", { name: /number/i });
        await userEvent.clear(numberBox4);
        await userEvent.type(numberBox4, "4");
        await userEvent.click(
            await app.findByRole("button", { name: /equals/i })
        );

        await app.findByText(/Display:\s*40\.0/);
    });
});
