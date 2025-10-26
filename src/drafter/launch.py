from drafter.files import seek_file_by_line
from drafter.utils import is_skulpt
from drafter.client_server import get_main_server


def start_server(initial_state=None, main_user_path=None) -> None:
    if is_skulpt():
        print("Starting local Drafter server in Skulpt...")
        from drafter.bridge import update_root

        server = get_main_server()
        response = server.visit("index")
        update_root("app", response.page.content)
    else:
        from drafter.app.local_server import serve_app_once

        if main_user_path is None:
            main_user_path = seek_file_by_line("start_server", "main.py")
        print("Starting local Drafter server...")
        serve_app_once(user_file=main_user_path, title="Local Drafter App")
