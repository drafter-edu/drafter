from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "Download Examples:",
        Header("Text File Download"),
        Download("Download Sample Text", "sample.txt", "Hello, this is a sample text file!\nIt contains multiple lines."),
        
        Header("CSV File Download"),
        Download("Download CSV Data", "data.csv", "Name,Age,City\nAlice,25,New York\nBob,30,San Francisco\nCharlie,35,Chicago"),
        
        Header("JSON File Download"),
        Download("Download JSON Data", "data.json", '{"users": [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]}')
    ])

start_server("")