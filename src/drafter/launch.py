from drafter.helpers.utils import is_web, seek_file_by_line


def start_server(
    initial_state=None,
    main_user_path=None,
    server=None,
    **extra_configuration,
) -> None:
    """
    Starts the Drafter server with the given initial state.

    :param initial_state: The initial state to set for the server.
    :param main_user_path: The path to the main user file (optional).
    :param extra_configuration: Additional keyword arguments (for backward compatibility, currently ignored).
    """
    if is_web():
        # TODO: This logic should really be encoded in a function somewhere
        from drafter.bridge import ClientBridge
        from drafter.client_server.commands import get_main_server

        server = server or get_main_server()
        server.do_configuration(extra_configuration)
        configuration = server.get_current_configuration()

        client_bridge = ClientBridge(configuration)
        client_bridge.setup_site(server.do_render())

        server.do_listen_for_events(client_bridge.handle_telemetry_event)

        server.do_start(initial_state=initial_state)
        initial_request = client_bridge.make_initial_request()

        def handle_visit(request):
            response = server.do_visit(request)
            client_bridge.handle_response(response, handle_visit)
            return response

        def handle_toggle_frame():
            server.reconfigure_flip("framed")

        def handle_debug_mode():
            server.reconfigure_flip("in_debug_mode")

        client_bridge.setup_events(handle_visit, handle_toggle_frame, handle_debug_mode)
        handle_visit(initial_request)

    else:
        from drafter.app.app_server import serve_app_once

        if main_user_path is None:
            # TODO: Provide more ways to specify the main file
            main_user_path = seek_file_by_line("start_server", "main.py")
        print("Starting local Drafter server...")
        # TODO: Title should come from configuration
        serve_app_once(
            user_file=main_user_path, title="Local Drafter App", engine="skulpt"
        )
