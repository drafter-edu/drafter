from drafter import *
from threading import Thread, Event
from bottle import ServerAdapter, Bottle
import time
import requests
import socket


class MyWSGIRefServer(ServerAdapter):
    server = None

    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        self.server = make_server(self.host, self.port, handler, **self.options)
        self.server.serve_forever()

    def stop(self):
        self.server.server_close()
        self.server.shutdown()

class TestServer:
    __test__ = False

    def __init__(self, initial_state=None, setup_kwargs=None,
                 run_kwargs=None, custom_name="TEST_SERVER"):
        if setup_kwargs is None:
            setup_kwargs = {}
        if '_custom_name' not in setup_kwargs:
            setup_kwargs['_custom_name'] = custom_name
        if run_kwargs is None:
            run_kwargs = {}
        run_kwargs.setdefault('host', 'localhost')
        run_kwargs.setdefault('port', 8080)
        self.initial_state = initial_state
        self.setup_kwargs = setup_kwargs
        self.run_kwargs = run_kwargs
        self.custom_name = custom_name
        self.server = Server(**setup_kwargs)
        self.server_ready = Event()

    def __enter__(self):
        if not self.server.routes:
            route("index", self.server)(default_index)

        self.wsgi = MyWSGIRefServer(
            host=self.run_kwargs.get('host'),
            port=int(self.run_kwargs.get('port')))
        self.server.setup(self.initial_state)
        self.thread = Thread(target=self.run_server, daemon=True)
        self.thread.start()
        
        # Start a separate thread to check for server readiness
        readiness_thread = Thread(target=self.wait_for_server_ready, daemon=True)
        readiness_thread.start()
        
        # Wait for server to be ready
        if not self.server_ready.wait(timeout=10):  # 10 second timeout
            raise RuntimeError("Server failed to start within 10 seconds")
            
        return self.thread

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wsgi.stop()
        self.thread.join()

    def run_server(self):
        self.server.run(server=self.wsgi, **self.run_kwargs)

    def wait_for_server_ready(self):
        """Wait for server to be actually responding to requests"""
        host = self.run_kwargs.get('host', 'localhost')
        port = self.run_kwargs.get('port', 8080)
        url = f"http://{host}:{port}/"
        
        max_attempts = 50  # 5 seconds total with 0.1s intervals
        for attempt in range(max_attempts):
            try:
                # Try to connect to the server
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    self.server_ready.set()
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.1)
        
        # If we can't connect via HTTP, try just checking if port is open
        for attempt in range(max_attempts):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    self.server_ready.set()
                    return True
            except:
                pass
            time.sleep(0.1)
        
        return False