"""
Theme Showcase Example
======================
This example demonstrates all available themes and how students can easily
override styles with simple CSS selectors.
"""
from drafter import *

# Try different themes by uncommenting one of these:
# set_website_style("default")
# set_website_style("none")
# set_website_style("mvp")
# set_website_style("sakura")
set_website_style("tacit")
# set_website_style("skeleton")
# set_website_style("7")
# set_website_style("98")
# set_website_style("XP")

# Student CSS that easily overrides theme defaults
add_website_css("""
/* Simple tag selectors that work! */
body {
    font-family: 'Comic Sans MS', cursive;
}

h1 {
    color: darkblue;
    border-bottom: 3px solid blue;
    padding-bottom: 10px;
}

button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 15px 32px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #45a049;
}

input {
    padding: 10px;
    border: 2px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
}

.custom-box {
    background-color: #f0f8ff;
    border-left: 4px solid #2196F3;
    padding: 15px;
    margin: 20px 0;
}
""")


@route
def index(state: str) -> Page:
    """Main page showcasing the theme and CSS overrides"""
    return Page(
        state,
        [
            Header("Welcome to the Theme Showcase!", level=1),
            
            """<div class="custom-box">
                <p><strong>Note:</strong> This page demonstrates how students can easily 
                override theme styles using simple CSS selectors like <code>body</code>, 
                <code>h1</code>, <code>button</code>, etc.</p>
            </div>""",
            
            Header("Styling Features", level=2),
            BulletedList([
                "Theme CSS uses low-specificity class selectors (.drafter-body)",
                "Student CSS can override with simple tag selectors (body, h1, button)",
                "No need for !important or complex selectors",
                "Works with all available themes"
            ]),
            
            Header("Try It Out", level=2),
            TextBox("name", "Enter your name"),
            TextBox("color", "Enter a color", value="blue"),
            Button("Submit", index),
            
            LineBreak(),
            italic("Change the theme at the top of this file and see how the styles adapt!"),
        ],
    )


start_server()
