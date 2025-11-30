from drafter import *

@route
def index(state: str) -> Page:
    # Sample data for the table
    student_data = [
        ["Name", "Grade", "Subject"],
        ["Alice", "A", "Math"],
        ["Bob", "B+", "Science"],
        ["Charlie", "A-", "History"],
        ["Diana", "B", "English"]
    ]
    
    return Page(state, [
        "Table Example:",
        Header("Student Grades"),
        Table(student_data),
        HorizontalRule(),
        Header("Simple Number Table"),
        Table([
            ["X", "X²", "X³"],
            [1, 1, 1],
            [2, 4, 8],
            [3, 9, 27],
            [4, 16, 64]
        ])
    ])

start_server("")