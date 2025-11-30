"""
Tests for file upload functionality, especially empty file uploads.
"""
from tests.helpers import *
from drafter import *
from dataclasses import dataclass
from typing import Optional
from PIL import Image as PILImage
import time


def test_empty_file_upload_str(browser, splinter_headless):
    """Test that empty file upload with str type works"""
    
    @dataclass
    class State:
        result: str = "initial"

    drafter_server = TestServer(State())

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            "Upload a text file:",
            FileUpload("text_file"),
            Button("Submit", "process"),
            f"Result: {state.result}"
        ])

    @route(server=drafter_server.server)
    def process(state: State, text_file: str) -> Page:
        state.result = "No file" if text_file is None else f"File: {text_file[:10]}"
        return index(state)

    with drafter_server:
        time.sleep(1)
        browser.visit('http://localhost:8080')
        assert browser.is_text_present("Upload a text file:")
        assert browser.is_text_present("Result: initial")

        # Submit without uploading a file
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        time.sleep(0.5)
        
        # Should handle empty file gracefully
        assert browser.is_text_present("Result: No file")


def test_empty_file_upload_bytes(browser, splinter_headless):
    """Test that empty file upload with bytes type works"""
    
    @dataclass
    class State:
        result: str = "initial"

    drafter_server = TestServer(State())

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            "Upload a binary file:",
            FileUpload("binary_file"),
            Button("Submit", "process"),
            f"Result: {state.result}"
        ])

    @route(server=drafter_server.server)
    def process(state: State, binary_file: bytes) -> Page:
        state.result = "No file" if binary_file is None else f"File: {len(binary_file)} bytes"
        return index(state)

    with drafter_server:
        time.sleep(1)
        browser.visit('http://localhost:8080')
        assert browser.is_text_present("Upload a binary file:")
        
        # Submit without uploading a file
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        time.sleep(0.5)
        
        # Should handle empty file gracefully
        assert browser.is_text_present("Result: No file")


def test_empty_file_upload_image(browser, splinter_headless):
    """Test that empty file upload with PIL.Image type works"""
    
    @dataclass
    class State:
        result: str = "initial"

    drafter_server = TestServer(State())

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            "Upload an image file:",
            FileUpload("image_file", accept="image/*"),
            Button("Submit", "process"),
            f"Result: {state.result}"
        ])

    @route(server=drafter_server.server)
    def process(state: State, image_file: PILImage.Image) -> Page:
        state.result = "No file" if image_file is None else f"Image: {image_file.size}"
        return index(state)

    with drafter_server:
        time.sleep(1)
        browser.visit('http://localhost:8080')
        assert browser.is_text_present("Upload an image file:")
        
        # Submit without uploading a file
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        time.sleep(0.5)
        
        # Should handle empty file gracefully
        assert browser.is_text_present("Result: No file")


def test_optional_file_upload(browser, splinter_headless):
    """Test that Optional file upload types work"""
    
    @dataclass
    class State:
        result: str = "initial"

    drafter_server = TestServer(State())

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            "Upload a text file (optional):",
            FileUpload("text_file"),
            Button("Submit", "process"),
            f"Result: {state.result}"
        ])

    @route(server=drafter_server.server)
    def process(state: State, text_file: Optional[str]) -> Page:
        state.result = "No file" if text_file is None else f"File: {text_file[:10]}"
        return index(state)

    with drafter_server:
        time.sleep(1)
        browser.visit('http://localhost:8080')
        assert browser.is_text_present("Upload a text file (optional):")
        
        # Submit without uploading a file
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        time.sleep(0.5)
        
        # Should handle empty file gracefully
        assert browser.is_text_present("Result: No file")


def test_multiple_file_uploads_mixed(browser, splinter_headless):
    """Test that multiple file upload fields work when some are empty"""
    
    @dataclass
    class State:
        text_result: str = "initial"
        bytes_result: str = "initial"

    drafter_server = TestServer(State())

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            "Upload files:",
            "Text file:", FileUpload("text_file"),
            "Binary file:", FileUpload("binary_file"),
            Button("Submit", "process"),
            f"Text: {state.text_result}",
            f"Bytes: {state.bytes_result}"
        ])

    @route(server=drafter_server.server)
    def process(state: State, text_file: str, binary_file: bytes) -> Page:
        state.text_result = "No file" if text_file is None else f"Text: {text_file[:10]}"
        state.bytes_result = "No file" if binary_file is None else f"{len(binary_file)} bytes"
        return index(state)

    with drafter_server:
        time.sleep(1)
        browser.visit('http://localhost:8080')
        assert browser.is_text_present("Upload files:")
        
        # Submit without uploading any files
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        time.sleep(0.5)
        
        # Both should handle empty files gracefully
        assert browser.is_text_present("Text: No file")
        assert browser.is_text_present("Bytes: No file")
