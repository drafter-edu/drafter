A **Button** creates a clickable button on a webpage. When the user clicks the button, Drafter can either:

- Navigate to another page in your application.
- Run another route to update your application's state.

Buttons are commonly used for navigation, submitting forms, and responding to user actions.

## Syntax

```python
Button(text, url)
Button(text, url, arguments)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The text displayed on the button. |
| `url` | `str` or `function` | The destination of the button. This can be a URL or the name of a route function. |
| `arguments` | `list[Argument]` *(optional)* | Additional arguments to send when the button is clicked. Defaults to an empty list. |

---

## Example 1: Navigate to another page

```python drafter
from drafter import *


@route
def index():
	return Page([
		 "Take a look at the about page!",
		Button("Go to About", about)
	])

@route
def about():
	return Page([
		"Welcome to the About page!",
		Button("Go to Original Page", index)
	])

start_server()
```

This button navigates to the `about` route when clicked.

---

## Example 2: Editing State Via Button

```python drafter
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
	count: int


@route
def index(state: State):
	return Page(state, [
		("Count:" + str(state.count)),
		Button("Increase", increase)
	])


@route
def increase(state: State):
	state.count += 1
	return index(state)


start_server(State(0))
```

This button leads to a route that returns the index route again while editing the state count field, allowing the counter to be incremented.

---

## Example 3: Send an Argument Through a Button

```python drafter
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
	count: int


@route
def index(state: State):
	return Page(state, [
		"Current count: " + str(state.count),
		Button("Set to 5", set_count, [Argument("amount", 5)])
	])


@route
def set_count(state: State, amount: int):
	state.count = amount
	return index(state)


start_server(State(0))
```

This button sends a hidden argument named `amount` to the `set_count` route. The route uses that value to update the state.

---

## Example 4: Send Multiple Arguments Through a Button

```python drafter
from drafter import *
from dataclasses import dataclass


@dataclass
class State:
	count: int
	message: str


@route
def index(state: State):
	return Page(state, [
		"Current count: " + str(state.count),
		"Current message: " + state.message,
		Button(
			"Update Both Values",
			set_values, 
			[Argument("amount", 7),Argument("new_message", "Ready")]
		)
	])


@route
def set_values(state: State, amount: int, new_message: str):
	state.count = amount
	state.message = new_message
	return index(state)


start_server(State(0, "Waiting"))
```

This button sends two hidden arguments at once. The `set_values` route receives both values and uses them to update the state.

## Notes

- The `url` parameter can be either a route function or a URL string.
- The `arguments` parameter is optional.
- Any input fields on the page are submitted when the button is pressed.