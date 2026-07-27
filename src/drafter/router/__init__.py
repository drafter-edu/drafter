"""
URL routing for Drafter applications.

This package maps URLs to student-written route functions and prepares their
arguments from incoming requests. It contains the student-facing `route`
decorator (`drafter.router.commands`), the `Router` that stores and looks up
handlers (`drafter.router.routes`), the parameter pipeline that collects,
merges, binds, and converts request values (`drafter.router.parameters`),
and the built-in default routes (`drafter.router.defaults`).
"""
