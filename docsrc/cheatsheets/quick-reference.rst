.. _quick-reference:

========================
Quick Reference Card
========================

.. raw:: html

    <style>
    @media print {
        .quick-ref-card {
            width: 5in;
            height: 7in;
            border: 1px solid #ccc;
            padding: 0.2in;
            margin: 0;
            font-size: 9px;
            font-family: 'Courier New', monospace;
            page-break-after: always;
            column-count: 2;
            column-gap: 0.2in;
        }
        .quick-ref-card h1 {
            font-size: 12px;
            margin: 0 0 8px 0;
            text-align: center;
            column-span: all;
        }
        .quick-ref-card .section {
            margin-bottom: 8px;
            break-inside: avoid;
        }
        .quick-ref-card .section h2 {
            font-size: 10px;
            margin: 0 0 3px 0;
            font-weight: bold;
        }
        .quick-ref-card code {
            font-size: 8px;
            display: block;
            margin: 2px 0;
        }
    }
    @media screen {
        .quick-ref-card {
            width: 500px;
            min-height: 700px;
            border: 2px solid #333;
            padding: 20px;
            margin: 20px 0;
            font-size: 12px;
            font-family: 'Courier New', monospace;
            background: #f9f9f9;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .quick-ref-card h1 {
            font-size: 16px;
            margin: 0 0 15px 0;
            text-align: center;
            color: #333;
            grid-column: 1 / -1;
        }
        .quick-ref-card .section {
            margin-bottom: 15px;
        }
        .quick-ref-card .section h2 {
            font-size: 13px;
            margin: 0 0 5px 0;
            font-weight: bold;
            color: #666;
        }
    }
    </style>

    <div class="quick-ref-card">
        <h1>🚀 DRAFTER QUICK REFERENCE</h1>
        
        <div>
            <div class="section">
                <h2>Essential Setup</h2>
                <code>from drafter import *<br>
                from dataclasses import dataclass<br><br>
                @dataclass<br>
                class State:<br>
                &nbsp;&nbsp;message: str<br>
                &nbsp;&nbsp;count: int = 0<br><br>
                start_server(State("Hello World!"))</code>
            </div>
            
            <div class="section">
                <h2>Basic Route</h2>
                <code>@route<br>
                def index(state: State) -> Page:<br>
                &nbsp;&nbsp;return Page(state, [<br>
                &nbsp;&nbsp;&nbsp;&nbsp;"Welcome!",<br>
                &nbsp;&nbsp;&nbsp;&nbsp;f"Message: {state.message}",<br>
                &nbsp;&nbsp;&nbsp;&nbsp;Button("Next", other_page)<br>
                &nbsp;&nbsp;])</code>
            </div>
            
            <div class="section">
                <h2>Form Handling</h2>
                <code>@route<br>
                def form_page(state: State) -> Page:<br>
                &nbsp;&nbsp;return Page(state, [<br>
                &nbsp;&nbsp;&nbsp;&nbsp;TextBox("user_input", state.message),<br>
                &nbsp;&nbsp;&nbsp;&nbsp;Button("Submit", process_form)<br>
                &nbsp;&nbsp;])<br><br>
                @route<br>
                def process_form(state: State, user_input: str):<br>
                &nbsp;&nbsp;state.message = user_input<br>
                &nbsp;&nbsp;return index(state)</code>
            </div>
        </div>
        
        <div>
            <div class="section">
                <h2>Common Components</h2>
                <code># Text input<br>
                TextBox("field_name", default_value)<br><br>
                # Checkbox<br>
                CheckBox("is_checked", state.flag)<br><br>
                # Dropdown<br>
                SelectBox("choice", ["A", "B", "C"])<br><br>
                # Number input<br>
                NumberBox("amount", state.count)<br><br>
                # Image display<br>
                Image("https://example.com/pic.jpg")</code>
            </div>
            
            <div class="section">
                <h2>Common Mistakes</h2>
                <code># ❌ Forgot @route<br>
                def my_page(state): ...<br><br>
                # ✅ With @route<br>
                @route<br>
                def my_page(state): ...<br><br>
                # ❌ Wrong parameter name<br>
                TextBox("username", ...)<br>
                def process(state, name): ...<br><br>
                # ✅ Matching names<br>
                TextBox("name", ...)<br>
                def process(state, name): ...</code>
            </div>
            
            <div class="section">
                <h2>Debugging Tips</h2>
                <code># Check the debug panel at bottom<br>
                # Look for route registration<br>
                # Verify state changes<br>
                # Check browser console for errors<br><br>
                # Test routes individually:<br>
                result = my_route(test_state)<br>
                print(result)</code>
            </div>
        </div>
    </div>

This quick reference card covers the most common patterns and problems students encounter when learning Drafter.

Common Student Problems & Solutions
===================================

**"My page doesn't show up!"**
   * Check that you added ``@route`` decorator
   * Verify function name matches the URL you're trying to visit
   * Make sure you're returning a ``Page`` object

**"My form doesn't work!"**
   * Ensure TextBox/CheckBox names match function parameter names exactly
   * Check that your route function accepts the right parameter types
   * Verify you're updating state correctly

**"State isn't saving!"**
   * Make sure you're modifying the state object, not creating a new one
   * Check that you're passing the same state object to ``Page()``
   * Verify your dataclass has the right field types

**"I get weird errors!"**
   * Check for typos in component names and parameters
   * Make sure all imports are correct
   * Look at the debug panel at the bottom of your webpage

Form Parameter Types
===================

When using form components, the parameter types in your route functions matter:

* ``TextBox`` → ``str`` parameter
* ``CheckBox`` → ``bool`` parameter  
* ``NumberBox`` → ``int`` or ``float`` parameter
* ``SelectBox`` → ``str`` parameter (the selected option)

Navigation Patterns
==================

**Simple Navigation:**

.. code-block:: python

   Button("Go to Page 2", page2)

**Navigation with State Changes:**

.. code-block:: python

   @route
   def go_to_page2(state: State) -> Page:
       state.current_page = "page2"
       return page2(state)

**Conditional Navigation:**

.. code-block:: python

   return Page(state, [
       Button("Admin Panel", admin_page) if state.is_admin else "Access Denied"
   ])

This reference focuses on practical examples rather than exhaustive documentation!