"""
Example of a clean landing page demonstrating design principles:
- Visual hierarchy (large title, smaller subtitle, clear call-to-action)
- Good use of white space (margins and padding)
- Consistent color scheme
- Readable typography
"""
from drafter import *

# Style constants for consistency
PRIMARY_COLOR = "#2c3e50"
ACCENT_COLOR = "#3498db"

@route
def index(state: str) -> Page:
    return Page(state, [
        # Main title - largest and centered for impact
        Div(
            Header("Welcome to TaskMaster"),
            style=f"text-align: center; color: {PRIMARY_COLOR}; font-size: 48px; margin-top: 40px;"
        ),
        
        # Subtitle - smaller, centered, with margin
        Div(
            "Organize your life, one task at a time.",
            style="text-align: center; color: #7f8c8d; margin: 10px 0 40px 0; font-size: 20px;"
        ),
        
        # Call to action - centered with good padding
        Div(
            Button("Get Started", signup, style_padding="15px 40px",
                   style_background_color=ACCENT_COLOR, style_color="white",
                   style_font_size="20px"),
            style="text-align: center; margin: 20px 0;"
        ),
        
        # Features section with space
        Div(
            Header("Features", 2),
            style="margin: 60px 0 20px 0;"
        ),
        
        BulletedList([
            "Simple and intuitive task management",
            "Set reminders and due dates",
            "Track your progress over time",
            "Works on all your devices"
        ])
    ])

@route
def signup(state: str) -> Page:
    return Page(state, [
        Header("Sign Up"),
        "This would be the signup page!",
        LineBreak(),
        Button("Back", index)
    ])

set_site_information(
    author="Design Example",
    description="Example demonstrating design principles",
    sources="",
    planning="",
    links=""
)

start_server("")
