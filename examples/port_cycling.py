# Open a Python server on port 8080 in a separate process

import os
import sys
import time
import subprocess

def load_separate_server():
    # Open a Python server on port 8080 in a separate process
    server_process = subprocess.Popen([sys.executable, "-m", "http.server", "8080"])
    time.sleep(1)
    return server_process

server_process = load_separate_server()

# Now open a new Drafter server on default port (8080)

from drafter import start_server

start_server()
