"""
Tests for the site_description function
"""
import unittest
from unittest.mock import patch

import sys
import os

# Add the drafter directory to the path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from drafter.site_description import site_description
from drafter.server import get_main_server, Server
from drafter.page import Page
from datetime import datetime


class TestSiteDescription(unittest.TestCase):
    
    def setUp(self):
        """Set up a fresh server for each test"""
        # Create a new server instance for each test to avoid conflicts
        self.server = Server()
        # Mock get_main_server in the routes module which is used by site_description
        self.server_patcher = patch('drafter.routes.get_main_server')
        self.mock_get_server = self.server_patcher.start()
        self.mock_get_server.return_value = self.server
    
    def tearDown(self):
        """Clean up after each test"""
        self.server_patcher.stop()
    
    def test_basic_site_description(self):
        """Test basic functionality with only required fields"""
        site_description(
            title="Test Site",
            description="A basic test site"
        )
        
        # Check that the route was created
        self.assertIn("/about", self.server.routes)
        
        # Get the route function and call it
        about_func = self.server.routes["/about"]
        result = about_func()
        
        # Verify it returns a Page object
        self.assertIsInstance(result, Page)
        
        # Check the content
        content_str = " ".join(result.content)
        self.assertIn("Test Site", content_str)
        self.assertIn("A basic test site", content_str)
    
    def test_site_description_with_all_fields(self):
        """Test site_description with all fields filled"""
        test_date = datetime(2024, 9, 15)
        
        site_description(
            title="Complete Test Site",
            description="A comprehensive test website",
            author="Test Author",
            contact_email="test@example.com",
            creation_date=test_date,
            version="2.0.1",
            url="info",  # Custom URL
            project_type="Educational",
            framework="Drafter"
        )
        
        # Check that the custom route was created
        self.assertIn("/info", self.server.routes)
        
        # Get and call the route function
        info_func = self.server.routes["/info"]
        result = info_func()
        
        # Verify content includes all fields
        content_str = " ".join(result.content)
        self.assertIn("Complete Test Site", content_str)
        self.assertIn("A comprehensive test website", content_str)
        self.assertIn("Test Author", content_str)
        self.assertIn("test@example.com", content_str)
        self.assertIn("September 15, 2024", content_str)  # Formatted date
        self.assertIn("2.0.1", content_str)
        self.assertIn("Educational", content_str)
        self.assertIn("Drafter", content_str)
    
    def test_site_description_minimal(self):
        """Test that optional fields are not shown when not provided"""
        site_description(
            title="Minimal Site",
            description="Just the essentials"
        )
        
        about_func = self.server.routes["/about"]
        result = about_func()
        content_str = " ".join(result.content)
        
        # Required fields should be present
        self.assertIn("Minimal Site", content_str)
        self.assertIn("Just the essentials", content_str)
        
        # Optional fields should not be present
        self.assertNotIn("Author:", content_str)
        self.assertNotIn("Contact:", content_str)
        self.assertNotIn("Created:", content_str)
        self.assertNotIn("Version:", content_str)
        self.assertNotIn("Additional Information", content_str)
    
    def test_site_description_custom_url(self):
        """Test that custom URLs work correctly"""
        site_description(
            title="Custom URL Site",
            description="Testing custom URLs",
            url="custom-about"
        )
        
        # Should create route with custom URL
        self.assertIn("/custom-about", self.server.routes)
        self.assertNotIn("/about", self.server.routes)
    
    def test_site_description_string_date(self):
        """Test that string dates work correctly"""
        site_description(
            title="String Date Site",
            description="Testing string dates",
            creation_date="Fall 2024"
        )
        
        about_func = self.server.routes["/about"]
        result = about_func()
        content_str = " ".join(result.content)
        
        self.assertIn("Fall 2024", content_str)
    
    def test_site_description_additional_metadata(self):
        """Test additional metadata with underscores"""
        site_description(
            title="Metadata Test",
            description="Testing additional metadata",
            programming_language="Python",
            target_grade_level="College"
        )
        
        about_func = self.server.routes["/about"]
        result = about_func()
        content_str = " ".join(result.content)
        
        # Check that additional metadata section is present
        self.assertIn("Additional Information", content_str)
        # Check that underscores are converted to spaces and capitalized
        self.assertIn("Programming Language:", content_str)
        self.assertIn("Target Grade Level:", content_str)
        self.assertIn("Python", content_str)
        self.assertIn("College", content_str)


if __name__ == '__main__':
    unittest.main()