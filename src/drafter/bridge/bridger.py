from drafter.config.system import SystemConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.bridge.client_bridge import ClientBridge
from drafter.bridge.context import DomContext
from drafter.client_server.client_server import ClientServer
from drafter.client_server.commands import (
    consume_pending_instance_context,
    register_server,
    set_main_server,
)


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
    # The embedding host may have handed this instance its own window (an
    # iframe's contentWindow) and a unique registry key via configure_instance.
    pending_context = consume_pending_instance_context() or {}
    context = DomContext.for_window(pending_context.get("window"))
    instance_key = pending_context.get("instance_id") or configuration.root_element_id
    # Adopt the instance's filesystem folder before registration so
    # register_server's set_main_server() syncs the current instance-root.
    server.instance_root = pending_context.get("instance_root")
    # Register this server under its instance key so multiple concurrent
    # instances can coexist and be looked up / reset independently.
    register_server(instance_key, server)
    client_bridge = ClientBridge(configuration, context=context)
    client_bridge.setup_site(rendered_site)

    if rendered_site.error:
        return

    server.do_listen_for_events(client_bridge.handle_server_event)

    def handle_visit(request):
        # Make this instance's server "current" for the duration of the visit so
        # runtime get_main_server() calls (e.g. the default reset route) resolve
        # to this instance rather than whichever instance loaded last.
        set_main_server(server)
        # Visiting Phase
        response = server.do_visit(request)
        # Committing Phase
        client_bridge.handle_response(response, handle_visit)
        # Idle Phase
        server.do_finish_visit()
        return response

    def handle_toggle_frame():
        # Like handle_visit: make this instance current so the resulting
        # UpdatedConfigurationEvent publishes on THIS instance's event bus
        # (log_record routes through the global current-server pointer).
        set_main_server(server)
        server.reconfigure_flip("framed")

    def handle_debug_mode():
        set_main_server(server)
        server.reconfigure_flip("in_debug_mode")

    client_bridge.setup_events(handle_visit, handle_toggle_frame, handle_debug_mode)
    # Starting Phase
    server.do_start(initial_state=initial_state)
    # Started Phase
    client_bridge.start()
