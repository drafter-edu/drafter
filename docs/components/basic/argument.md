A **Argument** creates a hidden value that can be passed to the server. This is useful when a button should send extra information without showing it on the page. Many different components across drafter can utilize arguments. 

Arguments are commonly used for:

- Passing extra data to a route.
- Reusing buttons with different hidden values.
- Sending information without adding another visible input.

## Syntax

```python
Argument(name, value)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name of the argument that will be sent to the route. |
| `value` | `str` or `int` or `float` or `bool` | The value to send to the server. |

---

## Example 1: Send hidden data with a button

```python drafter
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
	message: str


@route
def index(state: State):
	return Page(state, [
		"Current message: " + state.message,
		Button("Set to Hello", set_message, [Argument("new_message", "Hello")])
	])


@route
def set_message(state: State, new_message: str):
	state.message = new_message
	return index(state)


start_server(State("Hi"))
```

---

## Example 2: Send multiple pieces of data with a button

```python drafter
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    message_one: str
    message_two: str


@route
def index(state: State):
    return Page(state, [
        "Current message one: " + state.message_one,
        LineBreak(),
        "Current message two: " + state.message_two,
        Button(
            "Set to Hello",
            set_message,
            [
                Argument("new_message_one", "Hello"),
                Argument("new_message_two", "Hello Hello")
            ]
        )
    ])


@route
def set_message(state: State, new_message_one: str, new_message_two: str):
    state.message_one = new_message_one
    state.message_two = new_message_two
    return index(state)


start_server(State("Hi", "Bye"))
```

This button sends `new_message_one` and `new_message_two` value to the `set_message` route.

## Notes

- Use `Argument` when you want a button to send extra information.
- Arguments are hidden from the user.
- Multiple buttons can use the same label if they send different arguments.
