"""
Example: Using site_description to create an about page

This example demonstrates the new site_description function in Drafter,
which allows you to easily create an "about" page for your website without
needing to write a separate Markdown file.
"""

from drafter import *

# Simple usage - just provide title and description
site_description(
    title="My First Website",
    description="This is my first website built with Drafter. It's a simple example to learn web development."
)

# Advanced usage - include all metadata
site_description(
    title="My Portfolio Website", 
    description="A professional portfolio showcasing my projects and skills in computer science.",
    author="Alice Johnson",
    contact_email="alice.johnson@email.com",
    creation_date="October 2024",
    version="1.2.0",
    url="about",  # URL where the page will be accessible (defaults to "about")
    
    # Additional custom metadata - underscores become spaces and are capitalized
    project_type="Portfolio Website",
    programming_languages="Python, JavaScript, HTML, CSS",
    course="CS 150 - Introduction to Computer Science",
    semester="Fall 2024",
    university="State University"
)

# Create other pages for your site
@route("index")
def home():
    return Page([
        "<h1>Welcome to My Portfolio</h1>",
        "<p>Hello! I'm Alice, a computer science student passionate about web development.</p>",
        "<p>Check out my <a href='/projects'>projects</a> or learn more <a href='/about'>about me and this site</a>.</p>"
    ])

@route("projects")  
def projects():
    return Page([
        "<h1>My Projects</h1>",
        "<h2>Project 1: Calculator App</h2>",
        "<p>A simple calculator built with Python and Drafter.</p>",
        "<h2>Project 2: To-Do List</h2>", 
        "<p>A web-based to-do list application with add/remove functionality.</p>",
        "<p><a href='/'>← Back to Home</a></p>"
    ])

if __name__ == "__main__":
    start_server()