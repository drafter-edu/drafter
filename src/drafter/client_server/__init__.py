"""
The client-side "server" at the heart of a running Drafter application.

This package contains the `ClientServer` class that receives requests from
the browser bridge, dispatches them through the router, and produces
responses (`drafter.client_server.client_server`); the module-level commands
that track the current server instance and configure multi-instance
execution (`drafter.client_server.commands`); and the request/response scope
tracking helpers (`drafter.client_server.context`).
"""
