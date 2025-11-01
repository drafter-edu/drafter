from drafter.files import seek_file_by_line
from drafter.utils import is_skulpt
from drafter.client_server.commands import get_main_server


def start_server(initial_state=None, main_user_path=None) -> None:
    if is_skulpt():
        from drafter.bridge import ClientBridge

        client_bridge = ClientBridge()
        client_bridge.connect_to_event_bus()

        server = get_main_server()
        client_bridge.setup_site(server.render_site())
        server.register_monitor_listener(client_bridge.handle_telemetry_event)
        server.monitor.listen_for_events()

        server.start(initial_state=initial_state)
        initial_request = client_bridge.make_initial_request()

        def handle_visit(request):
            response = server.visit(request)
            client_bridge.handle_response(response, handle_visit)

        handle_visit(initial_request)

    else:
        from drafter.app.app_server import serve_app_once

        if main_user_path is None:
            # TODO: Provide more ways to specify the main file
            main_user_path = seek_file_by_line("start_server", "main.py")
        print("Starting local Drafter server...")
        # TODO: Title should come from configuration
        serve_app_once(user_file=main_user_path, title="Local Drafter App")
