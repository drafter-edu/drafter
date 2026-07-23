A **Table** displays data in rows and columns. It is useful when you want to organize information in a structured way.

Tables are commonly used for:

- Simple datasets.
- Comparison charts.
- Lists of values with multiple fields.

## Syntax

```python
Table(data)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `list[list[str]]` or `list[object]` or `object` | The table data to display. |

---

## Example: Show a small table

```python drafter
from drafter import *


@route
def index():
	return Page([
		Table([
			["Name", "Score", "Age",],
			["Ava", "10", "16",],
			["Noah", "8", "17",]
		])
	])


start_server()
```

This creates a simple table with three columns.

---

## Example 2: Build a Table From Inputs

```python drafter
from drafter import *
from dataclasses import dataclass, field


@dataclass
class State:
	name: str
	score: str
	rows: list[list[str]] = field(default_factory=lambda: [["Name", "Score"]])


@route
def index(state: State):
	return Page(state, [
		TextBox("name", state.name),
		TextBox("score", state.score),
		Button("Add Row", add_row),
		Table(state.rows)
	])


@route
def add_row(state: State, name: str, score: str):
	state.name = name
	state.score = score
	state.rows.append([name, score])
	return index(state)


start_server(State("Ava", "10"))
```

This example lets the user type a name and score, then adds that row to the table and saves it in state.

## Notes

- Use a list of lists for manual table data.
- Tables are useful when you want information to be easy to scan.
