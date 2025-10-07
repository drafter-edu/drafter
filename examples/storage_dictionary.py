"""
Example demonstrating dictionary-based storage API.

This approach uses a Storage object that works like a dictionary,
making it familiar for students who have learned about dictionaries.
"""

from drafter import *
from dataclasses import dataclass

set_website_style('none')

# Create a storage instance
storage = Storage(prefix="todo_app_")


@dataclass
class TodoItem:
    """A single todo item."""
    text: str
    completed: bool


@dataclass
class State:
    """Application state containing todo items."""
    todos: list[TodoItem]
    new_item_text: str


@route
def index(state: State) -> Page:
    """Main page showing the todo list."""
    # Count completed items
    completed_count = sum(1 for todo in state.todos if todo.completed)
    total_count = len(state.todos)
    
    return Page(state, [
        Header("Dictionary-based Storage Demo"),
        SubHeader("Todo List Application"),
        Div(
            f"Progress: {completed_count} / {total_count} completed",
            style_padding="10px",
            style_background_color="#e0f0ff",
            style_border_radius="5px"
        ),
        HorizontalRule(),
        Div([
            Div([
                CheckBox(f"todo_{i}", todo.completed),
                " ",
                todo.text if not todo.completed else Strikethrough(todo.text),
                " ",
                Button("Delete", delete_item, Argument("index", i))
            ], style_margin_bottom="5px")
            for i, todo in enumerate(state.todos)
        ] if state.todos else ["No todos yet!"]),
        HorizontalRule(),
        "Add new todo:",
        TextBox("new_item_text", state.new_item_text),
        Button("Add Item", add_item),
        HorizontalRule(),
        Div(
            Button("Save Todos", save_todos),
            Button("Load Todos", load_todos),
            Button("Clear Storage", clear_storage),
            style_padding="10px",
            style_background_color="#fff0e0"
        ),
        Div(
            "Note: Storage uses a dictionary-like interface.",
            "You can save with storage['key'] = value.",
            style_font_size="0.9em",
            style_color="#666",
            style_margin_top="20px"
        )
    ])


@route
def add_item(state: State, new_item_text: str) -> Page:
    """Add a new todo item."""
    if new_item_text.strip():
        state.todos.append(TodoItem(new_item_text, False))
        state.new_item_text = ""
    return index(state)


@route
def delete_item(state: State, index: int, **kwargs) -> Page:
    """Delete a todo item by index."""
    if 0 <= index < len(state.todos):
        state.todos.pop(index)
    
    # Update checkbox states for remaining items
    for i in range(len(state.todos)):
        key = f"todo_{i}"
        if key in kwargs:
            state.todos[i].completed = kwargs[key]
    
    return index(state)


@route
def save_todos(state: State, **kwargs) -> Page:
    """Save the current todos to storage using dictionary syntax."""
    # Update todo completion status from checkboxes
    for i in range(len(state.todos)):
        key = f"todo_{i}"
        if key in kwargs:
            state.todos[i].completed = kwargs[key]
    
    # Save using dictionary-style assignment
    storage["todos"] = state.todos
    
    return Page(state, [
        Header("Todos Saved!"),
        f"Saved {len(state.todos)} todo items to storage.",
        HorizontalRule(),
        Div([
            Div(
                "✓ " if todo.completed else "○ ",
                todo.text if not todo.completed else Strikethrough(todo.text),
                style_padding="5px"
            )
            for todo in state.todos
        ] if state.todos else ["No todos to save."]),
        HorizontalRule(),
        Button("Back to Todos", index)
    ])


@route
def load_todos(state: State) -> Page:
    """Load todos from storage using dictionary syntax."""
    # Load using dictionary-style get method
    default_todos = []
    loaded_todos = storage.get("todos", list, default_todos)
    
    state.todos = loaded_todos
    
    return Page(state, [
        Header("Todos Loaded!"),
        f"Loaded {len(state.todos)} todo items from storage.",
        Button("Back to Todos", index)
    ])


@route
def clear_storage(state: State) -> Page:
    """Clear all saved data."""
    if "todos" in storage:
        storage.delete("todos")
    
    return Page(state, [
        Header("Storage Cleared!"),
        "All saved data has been removed.",
        Button("Back to Todos", index)
    ])


# Start with some example todos
initial_state = State(
    todos=[
        TodoItem("Learn about Drafter", False),
        TodoItem("Try the storage API", False),
        TodoItem("Build something cool", False)
    ],
    new_item_text=""
)

start_server(initial_state)
