"""
This module is the main entry point for the drafter bridge.
It provides the ClientBridge class which is responsible for handling
communication between the Python application and the browser DOM,
managing page-specific content, navigation, and
processing responses from the server.
"""

from drafter.bridge.client_bridge import ClientBridge
from drafter.bridge.bridger import run_client_bridge
from drafter.bridge.log import console_log, debug_log