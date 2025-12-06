#!/usr/bin/env python3
"""
Example demonstrating emoji support in SelectBox
This reproduces the issue from the bug report
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from drafter import *
from dataclasses import dataclass

@dataclass
class TodoState:
    task_name: str
    priority: str
    
@route
def index(state: TodoState) -> Page:
    return Page(state, [
        Header("Todo App with Star Ratings"),
        "Task name:",
        TextBox("task_name", state.task_name),
        "Priority (stars):",
        SelectBox("priority", ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], state.priority),
        Button("Save Changes", save_new)
    ])

@route
def save_new(state: TodoState, task_name: str, priority: str) -> Page:
    state.task_name = task_name
    state.priority = priority
    return Page(state, [
        Header("Task Saved!"),
        f"Task: {state.task_name}",
        LineBreak(),
        f"Priority: {state.priority}",
        LineBreak(), LineBreak(),
        Button("Edit Again", index)
    ])

if __name__ == "__main__":
    start_server(TodoState("Buy groceries", "⭐⭐⭐"))
