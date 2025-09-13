from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        "FileUpload Example:",
        Header("Upload a File"),
        FileUpload("uploaded_file"),
        Button("Process File", process_file)
    ])

@route 
def process_file(state: str, uploaded_file) -> Page:
    if uploaded_file:
        file_info = f"File uploaded: {uploaded_file.filename} ({len(uploaded_file.content)} bytes)"
    else:
        file_info = "No file was uploaded"
    
    return Page(state, [
        file_info,
        LineBreak(),
        Link("Upload another file", index)
    ])

start_server("")