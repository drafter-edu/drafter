from typing import TYPE_CHECKING
from drafter.config.system import SystemConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.bridge.client_bridge import ClientBridge
from drafter.client_server.client_server import ClientServer

def run_client_bridge(
    system: SystemConfiguration,
    server: ClientServer,
    initial_state,
):
    # Configuration Phase
    # TODO: We need to revisit this
    possible_error_data = server.do_configuration()
    # Rendering Phase
    if possible_error_data:
        # TODO: Need to handle the case where configuration failed and is None
        rendered_site = possible_error_data
        configuration = ClientServerConfiguration()
    else:
        configuration = server.get_current_configuration()
        rendered_site = server.do_render()
    client_bridge = ClientBridge(configuration)
    client_bridge.setup_site(rendered_site)
    
    if rendered_site.error:
        return

    server.do_listen_for_events(client_bridge.handle_telemetry_event)
    
    def handle_visit(request):
        # Visiting Phase
        response = server.do_visit(request)
        # Committing Phase
        client_bridge.handle_response(response, handle_visit)
        # Idle Phase
        server.do_finish_visit()
        return response

    def handle_toggle_frame():
        server.reconfigure_flip("framed")

    def handle_debug_mode():
        server.reconfigure_flip("in_debug_mode")

    client_bridge.setup_events(handle_visit, handle_toggle_frame, handle_debug_mode)
    # Starting Phase
    server.do_start(initial_state=initial_state)
    # Started Phase
    initial_request = client_bridge.make_initial_request()
    handle_visit(initial_request)