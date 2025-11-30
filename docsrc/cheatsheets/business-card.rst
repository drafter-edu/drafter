.. _business-card:

===============================
Business Card Cheat Sheet
===============================

.. raw:: html

    <style>
    @media print {
        .business-card {
            width: 3.5in;
            height: 2in;
            border: 1px solid #ccc;
            padding: 0.1in;
            margin: 0;
            font-size: 8px;
            font-family: 'Courier New', monospace;
            page-break-after: always;
        }
        .business-card h1 {
            font-size: 10px;
            margin: 0 0 2px 0;
            text-align: center;
        }
        .business-card .section {
            margin-bottom: 3px;
        }
        .business-card .section h2 {
            font-size: 8px;
            margin: 0;
            font-weight: bold;
        }
        .business-card code {
            font-size: 7px;
        }
    }
    @media screen {
        .business-card {
            width: 350px;
            height: 200px;
            border: 2px solid #333;
            padding: 10px;
            margin: 20px 0;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            background: #f9f9f9;
        }
        .business-card h1 {
            font-size: 14px;
            margin: 0 0 8px 0;
            text-align: center;
            color: #333;
        }
        .business-card .section {
            margin-bottom: 8px;
        }
        .business-card .section h2 {
            font-size: 11px;
            margin: 0 0 2px 0;
            font-weight: bold;
            color: #666;
        }
    }
    </style>

    <div class="business-card">
        <h1>🐍 DRAFTER ESSENTIALS</h1>
        
        <div class="section">
            <h2>Basic Setup</h2>
            <code>from drafter import *<br>
            start_server(State("hello"))</code>
        </div>
        
        <div class="section">
            <h2>State & Routes</h2>
            <code>@dataclass<br>
            class State:<br>
            &nbsp;&nbsp;name: str<br><br>
            @route<br>
            def index(state: State) -> Page:</code>
        </div>
        
        <div class="section">
            <h2>Page & Components</h2>
            <code>return Page(state, [<br>
            &nbsp;&nbsp;"Hello", state.name,<br>
            &nbsp;&nbsp;Button("Click", next_page),<br>
            &nbsp;&nbsp;TextBox("name", state.name)<br>
            ])</code>
        </div>
        
        <div class="section">
            <h2>Quick Fixes</h2>
            <code>• Missing @route? Add it!<br>
            • Wrong URL? Check function name<br>
            • Form not working? Match parameter names</code>
        </div>
    </div>

Essential Drafter patterns that fit on a business card. Perfect for keeping handy while coding!

**Core Pattern:** Every Drafter app needs:

1. Import statement: ``from drafter import *``
2. State dataclass with ``@dataclass``  
3. Route functions with ``@route``
4. Return ``Page(state, [...])`` from routes
5. Start server: ``start_server(initial_state)``

**Common Components:**

* ``Button("text", function)`` - Links to other pages
* ``TextBox("name", default)`` - Text input  
* ``CheckBox("name", checked)`` - Boolean input
* ``Image("url")`` - Display images

**Quick Troubleshooting:**

* Missing ``@route`` decorator? Functions won't be accessible via URL
* Wrong URL? Check that function name matches the URL path  
* Form not submitting? Ensure TextBox names match function parameters
* State not updating? Make sure you're modifying the state object

This card contains the absolute essentials - just enough to get started and fix the most common issues!