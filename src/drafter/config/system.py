from dataclasses import dataclass

from drafter.config.bootstrap import BootstrapConfiguration
from drafter.config.app_builder import AppBuilderConfiguration
from drafter.config.app_server import AppServerConfiguration
from drafter.config.client_server import ClientServerConfiguration
from drafter.config.app_common import AppCommonConfiguration

@dataclass
class SystemConfiguration:
    """
    Centralized global object that holds all the configuration settings
    for each of the core components of the Drafter system.
    
    This should be instantiated as a singleton.
    """
    bootstrap: BootstrapConfiguration
    client_server: ClientServerConfiguration
    app_server: AppServerConfiguration
    app_builder: AppBuilderConfiguration
    app_common: AppCommonConfiguration
    
    def merge_in_args(self, args: dict):
        """
        Merge in arguments from a dictionary into the appropriate configuration objects.
        
        Args:
            args: A dictionary of arguments to merge into the configuration.
        """
        self.bootstrap.merge_in_args(args, raise_errors=False)
        self.client_server.merge_in_args(args, raise_errors=False)
        self.app_server.merge_in_args(args, raise_errors=False)
        self.app_builder.merge_in_args(args, raise_errors=False)
        self.app_common.merge_in_args(args, raise_errors=False)