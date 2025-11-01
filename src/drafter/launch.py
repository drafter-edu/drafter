from drafter.files import seek_file_by_line
from drafter.utils import is_skulpt
from drafter.client_server import get_main_server


def start_server(initial_state=None, main_user_path=None) -> None:
    if is_skulpt():
        from drafter.bridge import ClientBridge

        client_bridge = ClientBridge()

        server = get_main_server()
        server.start(initial_state=initial_state)
        initial_request = client_bridge.make_initial_request()

        def handle_visit(request):
            response = server.visit(request)
            outcome = client_bridge.handle_response(response, handle_visit)
            server.report_outcome(outcome)

        client_bridge.setup_site(server.render_site())

        handle_visit(initial_request)

        server.register_monitor_listener(client_bridge.handle_telemetry_event)
    else:
        from drafter.app.app_server import serve_app_once

        if main_user_path is None:
            # TODO: Provide more ways to specify the main file
            main_user_path = seek_file_by_line("start_server", "main.py")
        print("Starting local Drafter server...")
        # TODO: Title should come from configuration
        serve_app_once(user_file=main_user_path, title="Local Drafter App")
