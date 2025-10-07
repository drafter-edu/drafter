.. _why_drafter:

==============================
Why Use Drafter (and Why Not)?
==============================

This page helps you understand when Drafter is the right tool for you, and when you might want to consider alternatives.

.. contents:: Table of Contents
    :depth: 2

--------------
Why Drafter?
--------------

Drafter is designed specifically for **educational purposes** and **beginners learning Python web development**. Here's when Drafter is the perfect choice:

For Students Learning Python
=============================

**Drafter excels when:**

- You're in an introductory or intermediate Python course
- You want to build real, interactive web applications while learning
- You need to focus on Python programming concepts, not web infrastructure
- You want immediate visual feedback on your code
- You're building your first full-stack project

**Key Educational Benefits:**

- **Minimal Boilerplate**: Start building with just two lines of code
- **Python-Centric**: No need to learn HTML, CSS, or JavaScript initially
- **Automatic State Management**: State is handled for you across pages
- **Built-in Components**: Pre-made UI elements (buttons, text boxes, etc.)
- **Instant Deployment**: Can run in the browser via Skulpt
- **Beginner-Friendly Errors**: Clear error messages designed for learners

For Rapid Prototyping
======================

**Drafter works well for:**

- Quick prototypes and demos
- Class projects with tight deadlines
- Visualizing data or algorithms interactively
- Building simple interactive tools
- Creating educational applications

-----------------
Why NOT Drafter?
-----------------

Drafter intentionally trades power and flexibility for simplicity. Here's when you should consider other tools:

You Need Production-Ready Applications
=======================================

**Drafter is NOT designed for:**

- Production web applications with real users
- Applications requiring high performance or scalability
- Sites that need complex database operations
- Applications with sophisticated authentication systems
- Projects requiring fine-grained control over HTTP requests/responses

You Want to Learn Professional Web Development
===============================================

If your goal is to become a professional web developer, you'll eventually need to transition to industry-standard tools. Drafter is a stepping stone, not the destination.

**Signs it's time to move on:**

- You've mastered basic Python and web concepts
- You need to work with REST APIs or complex backend logic
- You want to learn modern frontend frameworks (React, Vue, etc.)
- You're building a portfolio for job applications
- You need to collaborate on a larger team project

You Need Advanced Features
===========================

**Drafter doesn't support:**

- Custom middleware or request/response processing
- WebSocket connections for real-time features
- Complex URL routing with regex patterns
- File uploads beyond basic functionality
- Advanced database ORMs (SQLAlchemy, Django ORM)
- Background tasks and async processing
- Multi-page application state without explicit management

----------------------------------------
How Drafter Compares to Other Tools
----------------------------------------

Flask
=====

**Flask** is a lightweight, production-ready web framework.

**Choose Flask if you:**

- Need a professional-grade framework
- Want fine control over HTTP requests and responses
- Are comfortable learning about routes, templates, and request handling
- Need to build APIs or integrate with databases
- Want industry-relevant experience

**Choose Drafter if you:**

- Are new to web development
- Want to focus on Python logic, not web plumbing
- Need something simpler than Flask's template system
- Prefer built-in UI components over writing HTML

**Transition Path:** Drafter → Flask is a natural progression. Check out our :doc:`flask` guide.

Streamlit
=========

**Streamlit** is designed for data science and machine learning applications.

**Choose Streamlit if you:**

- Are building data dashboards or ML demos
- Work primarily with pandas, matplotlib, or scikit-learn
- Need to quickly visualize data analysis results
- Want automatic re-running on code changes

**Choose Drafter if you:**

- Need multi-page applications with complex navigation
- Want explicit control over state management
- Are building general-purpose web applications
- Need to teach web development concepts (routing, state, etc.)

**Key Differences:**

- Streamlit auto-runs your entire script on interaction; Drafter uses explicit routes
- Streamlit is optimized for data science; Drafter is optimized for learning
- Streamlit has a stronger data visualization ecosystem
- Drafter gives more explicit control over page flow and state

Pynecone/Reflex
===============

**Pynecone** (now called **Reflex**) is a full-stack Python framework for building web apps.

**Choose Reflex if you:**

- Want to build production web applications entirely in Python
- Need reactive, modern frontend experiences
- Are comfortable with more complex architectures
- Want both frontend and backend in Python without learning JavaScript

**Choose Drafter if you:**

- Are learning web development basics
- Want simpler, more educational code
- Don't need reactive UI patterns yet
- Prefer minimal setup and configuration

**Key Differences:**

- Reflex is more powerful but has a steeper learning curve
- Reflex requires understanding of components and state management patterns
- Drafter is designed for education; Reflex is designed for production
- Reflex compiles to JavaScript; Drafter can run purely in Python

FastHTML
========

**FastHTML** is a modern Python framework for building HTML applications.

**Choose FastHTML if you:**

- Want to write HTML-like structures in Python
- Need modern web application features
- Are comfortable with more advanced Python concepts
- Want something between Drafter's simplicity and Flask's power

**Choose Drafter if you:**

- Are newer to Python and web development
- Want pre-built UI components
- Prefer declarative component syntax
- Need educational scaffolding and documentation

**Key Differences:**

- FastHTML uses Python to generate HTML more directly
- FastHTML is newer and more modern, but less educational
- Drafter has more extensive beginner documentation
- FastHTML offers more flexibility at the cost of complexity

Anvil
=====

**Anvil** is a full-stack Python web framework with a drag-and-drop designer.

**Choose Anvil if you:**

- Want a visual designer for building interfaces
- Need cloud hosting integrated into the platform
- Are building business applications
- Want both frontend and backend in Python

**Choose Drafter if you:**

- Prefer code-first approaches
- Want to run applications locally and understand how they work
- Need free, open-source tools
- Are in an educational setting where you can't use commercial platforms

**Key Differences:**

- Anvil is a commercial platform; Drafter is free and open-source
- Anvil has a visual designer; Drafter is code-only
- Anvil includes hosting; Drafter runs locally or deploys separately
- Drafter is more appropriate for educational environments

------------------------------------
When to Transition from Drafter
------------------------------------

Drafter is designed as a **stepping stone**, not a permanent solution. Here are signs it's time to graduate:

You've Mastered the Basics
===========================

Once you're comfortable with:

- Python functions and data structures
- Routing and navigation between pages
- State management across requests
- Building interactive UIs

...you're ready to learn professional tools like Flask or Django.

Your Project Outgrows Drafter
==============================

If you find yourself fighting against Drafter's limitations:

- Needing features that Drafter doesn't provide
- Writing workarounds for simple tasks
- Wanting more control over HTML/CSS
- Requiring performance improvements

...it's time to move to a more flexible framework.

You Want to Build Your Portfolio
=================================

For job applications and professional portfolios:

- Use Flask, Django, or FastAPI for backend projects
- Learn a JavaScript framework (React, Vue) for frontend projects
- Build full-stack applications with industry-standard tools

Drafter is great for learning, but employers want to see experience with professional tools.

------------------------
Recommended Next Steps
------------------------

After Drafter
=============

**Immediate Next Steps:**

1. **Learn Flask**: Check out our :doc:`flask` transition guide
2. **Study HTML/CSS**: Understand what Drafter was abstracting away
3. **Explore Databases**: Learn SQL and SQLAlchemy
4. **Practice Git**: Version control for collaborative development

**Advanced Learning:**

- **Django** for full-featured web applications
- **FastAPI** for modern API development
- **JavaScript/TypeScript** for frontend development
- **React or Vue** for interactive user interfaces

Embrace Drafter's Niche
========================

If you're teaching or learning:

- Drafter is perfect for educational settings
- Use it to focus on programming concepts, not web infrastructure
- Appreciate its simplicity as a teaching tool
- Recognize it's designed for this specific use case

-----
Summary
-----

**Use Drafter when:**

- You're learning Python in an educational context
- You need to build simple web applications quickly
- You want to focus on logic, not infrastructure
- You're in an introductory programming course

**Don't use Drafter when:**

- You need production-ready applications
- You want to learn professional web development
- You require advanced features or performance
- You're building a portfolio for job applications

**Remember:** Drafter is a teaching tool that excels at its specific purpose. It's meant to be outgrown, and that's okay! Use it to learn fundamentals, then graduate to professional tools when you're ready.

-----------
Learn More
-----------

- :doc:`installation` - Get started with Drafter
- :doc:`docs` - Full documentation for Drafter features
- :doc:`flask` - Transition from Drafter to Flask
- :doc:`deployment` - Deploy your Drafter applications
- :doc:`help` - Get help with common issues
