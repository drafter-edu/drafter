from drafter import *
from threading import Thread
from bottle import ServerAdapter, Bottle


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

class TestServer:
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

    def __enter__(self):
        if not self.server.routes:
            route("index", self.server)(default_index)

        self.wsgi = MyWSGIRefServer(
            host=self.run_kwargs.get('host'),
            port=int(self.run_kwargs.get('port')))
        self.server.setup(self.initial_state)
        self.thread = Thread(target=self.run_server, daemon=True)
        self.thread.start()
        return self.thread

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wsgi.stop()
        self.thread.join()

    def run_server(self):
        self.server.run(server=self.wsgi, **self.run_kwargs)