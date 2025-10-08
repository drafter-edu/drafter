.. _full-reference:

=======================
Full Page Reference
=======================

.. raw:: html

    <style>
    @media print {
        .full-reference {
            font-size: 10px;
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 0.3in;
        }
        .full-reference h1 {
            font-size: 14px;
            text-align: center;
            margin: 0 0 10px 0;
        }
        .full-reference h2 {
            font-size: 12px;
            margin: 8px 0 4px 0;
            border-bottom: 1px solid #ccc;
        }
        .full-reference .two-column {
            column-count: 2;
            column-gap: 0.3in;
        }
        .full-reference .example-box {
            border: 1px solid #ddd;
            padding: 4px;
            margin: 4px 0;
            break-inside: avoid;
        }
        .full-reference code {
            font-size: 9px;
        }
    }
    @media screen {
        .full-reference {
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            font-family: 'Courier New', monospace;
            background: #f9f9f9;
            border: 2px solid #333;
        }
        .full-reference h1 {
            font-size: 18px;
            text-align: center;
            margin: 0 0 20px 0;
            color: #333;
        }
        .full-reference h2 {
            font-size: 15px;
            margin: 15px 0 8px 0;
            color: #666;
            border-bottom: 2px solid #ddd;
            padding-bottom: 3px;
        }
        .full-reference .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .full-reference .example-box {
            border: 1px solid #ddd;
            padding: 10px;
            margin: 10px 0;
            background: white;
            border-radius: 4px;
        }
    }
    </style>

    <div class="full-reference">
        <h1>🎓 DRAFTER COMPLETE REFERENCE</h1>
        
        <h2>Complete Application Template</h2>
        <div class="example-box">
            <code>from drafter import *<br>
            from dataclasses import dataclass<br><br>
            @dataclass<br>
            class State:<br>
            &nbsp;&nbsp;username: str<br>
            &nbsp;&nbsp;score: int = 0<br>
            &nbsp;&nbsp;is_logged_in: bool = False<br><br>
            @route<br>
            def index(state: State) -> Page:<br>
            &nbsp;&nbsp;if state.is_logged_in:<br>
            &nbsp;&nbsp;&nbsp;&nbsp;return dashboard(state)<br>
            &nbsp;&nbsp;return Page(state, [<br>
            &nbsp;&nbsp;&nbsp;&nbsp;"Welcome to My App!",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;TextBox("username", state.username),<br>
            &nbsp;&nbsp;&nbsp;&nbsp;Button("Login", login)<br>
            &nbsp;&nbsp;])<br><br>
            @route<br>
            def login(state: State, username: str) -> Page:<br>
            &nbsp;&nbsp;state.username = username<br>
            &nbsp;&nbsp;state.is_logged_in = True<br>
            &nbsp;&nbsp;return dashboard(state)<br><br>
            @route<br>
            def dashboard(state: State) -> Page:<br>
            &nbsp;&nbsp;return Page(state, [<br>
            &nbsp;&nbsp;&nbsp;&nbsp;f"Hello, {state.username}!",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;f"Your score: {state.score}",<br>
            &nbsp;&nbsp;&nbsp;&nbsp;Button("Increase Score", add_score),<br>
            &nbsp;&nbsp;&nbsp;&nbsp;Button("Logout", logout)<br>
            &nbsp;&nbsp;])<br><br>
            @route<br>
            def add_score(state: State) -> Page:<br>
            &nbsp;&nbsp;state.score += 10<br>
            &nbsp;&nbsp;return dashboard(state)<br><br>
            @route<br>
            def logout(state: State) -> Page:<br>
            &nbsp;&nbsp;state.is_logged_in = False<br>
            &nbsp;&nbsp;state.username = ""<br>
            &nbsp;&nbsp;return index(state)<br><br>
            start_server(State(""))</code>
        </div>
        
        <div class="two-column">
            <div>
                <h2>All Components</h2>
                <div class="example-box">
                    <code># Text Components<br>
                    "Plain text"<br>
                    LineBreak()<br>
                    Header("Big Title")<br><br>
                    # Input Components<br>
                    TextBox("name", "default")<br>
                    NumberBox("age", 25)<br>
                    CheckBox("agree", True)<br>
                    SelectBox("color", ["Red", "Blue"])<br><br>
                    # Interactive Components<br>
                    Button("Click Me", my_function)<br>
                    Link("Visit", "https://example.com")<br>
                    Image("https://example.com/pic.jpg")<br><br>
                    # Lists<br>
                    BulletedList(["Item 1", "Item 2"])<br>
                    NumberedList(["Step 1", "Step 2"])</code>
                </div>
                
                <h2>Form Validation</h2>
                <div class="example-box">
                    <code>@route<br>
                    def process_age(state: State, age_input: str):<br>
                    &nbsp;&nbsp;if not age_input.isnumeric():<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;return Page(state, [<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Error: Please enter a number",<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TextBox("age_input", age_input),<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Button("Try Again", process_age)<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;])<br>
                    &nbsp;&nbsp;state.age = int(age_input)<br>
                    &nbsp;&nbsp;return success_page(state)</code>
                </div>
                
                <h2>Error Patterns</h2>
                <div class="example-box">
                    <code># ❌ Common Mistake: Missing @route<br>
                    def my_page(state): pass<br><br>
                    # ✅ Correct: With @route<br>
                    @route<br>
                    def my_page(state): pass<br><br>
                    # ❌ Wrong: Parameter name mismatch<br>
                    TextBox("user_name", "")<br>
                    def process(state, username): pass<br><br>
                    # ✅ Correct: Names match<br>
                    TextBox("username", "")<br>
                    def process(state, username): pass</code>
                </div>
            </div>
            
            <div>
                <h2>State Management</h2>
                <div class="example-box">
                    <code># Complex State Example<br>
                    @dataclass<br>
                    class State:<br>
                    &nbsp;&nbsp;user: str<br>
                    &nbsp;&nbsp;items: list[str]<br>
                    &nbsp;&nbsp;settings: dict[str, bool]<br>
                    &nbsp;&nbsp;current_page: str = "home"<br><br>
                    # Adding to lists<br>
                    @route<br>
                    def add_item(state: State, new_item: str):<br>
                    &nbsp;&nbsp;state.items.append(new_item)<br>
                    &nbsp;&nbsp;return show_items(state)<br><br>
                    # Updating dictionaries<br>
                    @route<br>
                    def toggle_setting(state: State, setting: str):<br>
                    &nbsp;&nbsp;state.settings[setting] = not state.settings.get(setting, False)<br>
                    &nbsp;&nbsp;return settings_page(state)</code>
                </div>
                
                <h2>Conditional Rendering</h2>
                <div class="example-box">
                    <code>@route<br>
                    def dynamic_page(state: State) -> Page:<br>
                    &nbsp;&nbsp;content = ["Welcome!"]<br>
                    &nbsp;&nbsp;<br>
                    &nbsp;&nbsp;if state.is_admin:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;content.extend([<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Admin Panel",<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Button("Delete All", dangerous_action)<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;])<br>
                    &nbsp;&nbsp;<br>
                    &nbsp;&nbsp;if state.items:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;content.append(BulletedList(state.items))<br>
                    &nbsp;&nbsp;else:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;content.append("No items yet!")<br>
                    &nbsp;&nbsp;<br>
                    &nbsp;&nbsp;return Page(state, content)</code>
                </div>
                
                <h2>Testing Routes</h2>
                <div class="example-box">
                    <code>from drafter import assert_equal<br><br>
                    # Test a simple route<br>
                    test_state = State("John", 0, True)<br>
                    result = dashboard(test_state)<br>
                    <br>
                    expected = Page(test_state, [<br>
                    &nbsp;&nbsp;"Hello, John!",<br>
                    &nbsp;&nbsp;"Your score: 0",<br>
                    &nbsp;&nbsp;Button("Increase Score", add_score),<br>
                    &nbsp;&nbsp;Button("Logout", logout)<br>
                    ])<br><br>
                    assert_equal(result, expected)</code>
                </div>
            </div>
        </div>
        
        <h2>Troubleshooting Guide</h2>
        <div class="example-box">
            <code><strong>Problem:</strong> "NameError: name 'route' is not defined"<br>
            <strong>Solution:</strong> Add `from drafter import *` at the top<br><br>
            
            <strong>Problem:</strong> "TypeError: Page() missing required argument"<br>
            <strong>Solution:</strong> Make sure you're passing both state and content list: `Page(state, [...])`<br><br>
            
            <strong>Problem:</strong> "Page not found" when clicking button<br>
            <strong>Solution:</strong> Check that the target function has @route decorator<br><br>
            
            <strong>Problem:</strong> Form data not being passed to function<br>
            <strong>Solution:</strong> Ensure TextBox/CheckBox names match function parameter names exactly<br><br>
            
            <strong>Problem:</strong> State changes not persisting<br>
            <strong>Solution:</strong> Make sure you're modifying the same state object passed to the function<br><br>
            
            <strong>Problem:</strong> "Cannot convert string to int"<br>
            <strong>Solution:</strong> Validate user input with .isnumeric() before converting to int</code>
        </div>
    </div>

Complete Drafter Reference for Student Study
===========================================

This comprehensive reference includes everything students need to build complete Drafter applications. 

Key Learning Progression
-----------------------

1. **Start Simple:** Begin with basic routes and static content
2. **Add State:** Introduce dataclasses to store information
3. **Handle Forms:** Use TextBox and Button components for user input
4. **Add Logic:** Implement conditional rendering and validation
5. **Test Everything:** Use assert_equal to verify your routes work

Best Practices for Students
--------------------------

* **Name Things Clearly:** Use descriptive names for routes, state fields, and form components
* **Test Early:** Write simple tests for each route as you build them
* **Start Small:** Build one page at a time before connecting everything
* **Use the Debug Panel:** The information at the bottom of your webpage shows route history and state changes
* **Keep State Simple:** Start with basic types (str, int, bool) before moving to lists and dictionaries

Common Student Projects
----------------------

* **Personal Portfolio:** Static pages with navigation
* **Simple Calculator:** Number inputs with mathematical operations  
* **Todo List:** Adding/removing items from a list
* **Quiz Application:** Multiple choice questions with scoring
* **Simple Game:** Turn-based games with state tracking
* **Survey Form:** Collecting and displaying user responses

This reference emphasizes practical patterns over exhaustive API documentation!