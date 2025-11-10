"""
New Themes Example
==================
This example demonstrates the two new themes: dark-mode and water.
"""
from drafter import *

# Try different themes by uncommenting one of these:
# set_website_style("dark-mode")
set_website_style("water")

# Optional: Add custom CSS that overrides theme defaults
add_website_css("""
/* Custom tweaks that work with any theme */
h1 {
    text-transform: uppercase;
}

.highlight-box {
    padding: 15px;
    margin: 20px 0;
    border-radius: 8px;
}
""")


@route
def index(state: str) -> Page:
    """Main page showcasing the new themes"""
    return Page(
        state,
        [
            Header("New Themes Demo", level=1),
            
            """<div class="highlight-box">
                <h3>Dark Mode Theme</h3>
                <p>A modern dark theme with excellent contrast and accessibility features. 
                Perfect for reducing eye strain and creating a professional look.</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>High contrast text on dark background</li>
                    <li>Carefully selected accent colors</li>
                    <li>Custom scrollbar styling</li>
                    <li>Form elements designed for dark mode</li>
                </ul>
            </div>""",
            
            """<div class="highlight-box">
                <h3>Water Theme</h3>
                <p>A clean, classless CSS theme inspired by water.css. Provides beautiful 
                default styling for all HTML elements without requiring any classes.</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>Classless design - works with plain HTML</li>
                    <li>Responsive and mobile-friendly</li>
                    <li>Clean, modern aesthetic</li>
                    <li>Optimized for readability</li>
                </ul>
            </div>""",
            
            Header("Interactive Elements", level=2),
            TextBox("name", "Enter your name"),
            TextBox("email", "Enter your email"),
            Button("Submit", index),
            
            LineBreak(),
            LineBreak(),
            
            italic("Change the theme at the top of this file to see the difference!"),
        ],
    )


start_server()
