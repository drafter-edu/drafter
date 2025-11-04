from drafter.utils import is_skulpt, seek_file_by_line
from drafter.client_server.commands import get_main_server


def start_server(initial_state=None, main_user_path=None, **kwargs) -> None:
    """
    Starts the Drafter server with the given initial state.
    
    :param initial_state: The initial state to set for the server.
    :param main_user_path: The path to the main user file (optional).
    :param kwargs: Additional keyword arguments (for backward compatibility, currently ignored).
    """
    if is_skulpt():
        from drafter.bridge import ClientBridge

        client_bridge = ClientBridge()
        client_bridge.connect_to_event_bus()

        server = get_main_server()
        site_body, site_title = server.render_site()
        client_bridge.setup_site(site_body, site_title)
        server.register_monitor_listener(client_bridge.handle_telemetry_event)
        server.monitor.listen_for_events()

        server.start(initial_state=initial_state)
        initial_request = client_bridge.make_initial_request()

        def handle_visit(request):
            response = server.visit(request)
            client_bridge.handle_response(response, handle_visit)

        handle_visit(initial_request)
        client_bridge.setup_navigation(handle_visit)

    else:
        from drafter.app.app_server import serve_app_once

        if main_user_path is None:
            # TODO: Provide more ways to specify the main file
            main_user_path = seek_file_by_line("start_server", "main.py")
        print("Starting local Drafter server...")
        # TODO: Title should come from configuration
        serve_app_once(user_file=main_user_path, title="Local Drafter App")
