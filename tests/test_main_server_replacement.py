"""
Test that MAIN_SERVER can be properly replaced via set_main_server
"""
from drafter import *
from drafter.server import Server, get_main_server, set_main_server, get_server_setting, start_server


def test_set_main_server_replaces_properly():
    """
    Test that set_main_server properly replaces the main server in all contexts.
    This includes functions with default parameters and functions that directly access the server.
    """
    # Store the original server
    original_server = get_main_server()
    
    # Create a new server with different configuration
    new_server = Server(_custom_name='TEST_REPLACEMENT_SERVER')
    new_server.configuration.title = "Test Replacement Title"
    new_server.configuration.debug = True
    new_server.configuration.framed = False
    new_server.configuration.style = "test-style"
    
    try:
        # Set the new server as main
        set_main_server(new_server)
        
        # Verify get_main_server returns the new server
        assert get_main_server() is new_server, "get_main_server should return the new server"
        
        # Test functions with default server parameters
        assert get_server_setting('title') == "Test Replacement Title", \
            "get_server_setting should use the new server by default"
        assert get_server_setting('debug') == True, \
            "get_server_setting should use the new server's debug setting"
        
        # Test deploy.py functions that should use the new server
        set_website_title("Modified Title")
        assert get_main_server().configuration.title == "Modified Title", \
            "set_website_title should modify the new server"
        
        show_debug_information()
        assert get_main_server().configuration.debug == True, \
            "show_debug_information should modify the new server"
        
        hide_debug_information()
        assert get_main_server().configuration.debug == False, \
            "hide_debug_information should modify the new server"
        
        set_website_framed(True)
        assert get_main_server().configuration.framed == True, \
            "set_website_framed should modify the new server"
        
        set_website_style("new-style")
        assert get_main_server().configuration.style == "new-style", \
            "set_website_style should modify the new server"
        
        add_website_header("<meta test>")
        assert "<meta test>" in get_main_server().configuration.additional_header_content, \
            "add_website_header should modify the new server"
        
        add_website_css(".test", "color: red;")
        assert any(".test" in css for css in get_main_server().configuration.additional_css_content), \
            "add_website_css should modify the new server"
        
        # Test deploy_site
        initial_debug_state = get_main_server().configuration.debug
        deploy_site('test-images')
        assert get_main_server().production == True, \
            "deploy_site should set production flag on new server"
        assert get_main_server().image_folder == 'test-images', \
            "deploy_site should set image_folder on new server"
        assert get_main_server().configuration.debug == False, \
            "deploy_site should disable debug on new server"
        
    finally:
        # Restore the original server
        set_main_server(original_server)


def test_explicit_server_parameter_still_works():
    """
    Test that explicitly passing a server parameter still works correctly.
    """
    # Store the original server
    original_server = get_main_server()
    
    # Create two different servers
    server_a = Server(_custom_name='SERVER_A')
    server_a.configuration.title = "Server A Title"
    
    server_b = Server(_custom_name='SERVER_B')
    server_b.configuration.title = "Server B Title"
    
    try:
        set_main_server(server_a)
        
        # get_server_setting with explicit server should use that server
        assert get_server_setting('title', server=server_b) == "Server B Title", \
            "Explicit server parameter should override the default"
        
        # Without explicit server, should use server_a
        assert get_server_setting('title') == "Server A Title", \
            "Default should use server_a"
        
    finally:
        # Restore the original server
        set_main_server(original_server)


if __name__ == '__main__':
    test_set_main_server_replaces_properly()
    test_explicit_server_parameter_still_works()
    print("All tests passed!")
