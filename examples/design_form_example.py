"""
Example of a well-designed form demonstrating:
- Clear labels and structure
- Consistent spacing
- Visual grouping
- Good contrast and readability
"""
from drafter import *

@route
def index(state: str) -> Page:
    return Page(state, [
        # Clear title
        Div(
            Header("Create Your Account"),
            style="margin: 0 0 30px 0;"
        ),
        
        # Form with good spacing
        Div(
            bold("Username"),
            LineBreak(),
            TextBox("username", "Choose a username"),
            style="margin: 0 0 20px 0;"
        ),
        
        Div(
            bold("Email Address"),
            LineBreak(),
            TextBox("email", "your.email@example.com"),
            style="margin: 0 0 20px 0;"
        ),
        
        Div(
            bold("Password"),
            LineBreak(),
            TextBox("password", "Create a strong password"),
            style="margin: 0 0 20px 0;"
        ),
        
        # Terms with smaller text
        Div(
            small_font("By creating an account, you agree to our Terms of Service."),
            style="margin: 10px 0 20px 0;"
        ),
        
        # Action buttons - primary action is more prominent
        Button("Create Account", process_signup,
               style_background_color="#2ecc71", style_color="white",
               style_padding="12px 30px", style_margin_right="10px"),
        Button("Cancel", index,
               style_background_color="#95a5a6", style_color="white",
               style_padding="12px 30px")
    ])

@route
def process_signup(state: str, username: str, email: str, password: str) -> Page:
    return Page(state, [
        Header("Welcome!"),
        f"Thank you for signing up, {username}!",
        LineBreak(),
        f"We sent a confirmation email to {email}.",
        LineBreak(),
        LineBreak(),
        Button("Back to Form", index)
    ])

set_site_information(
    author="Design Example",
    description="Example demonstrating form design principles",
    sources="",
    planning="",
    links=""
)

start_server("")
