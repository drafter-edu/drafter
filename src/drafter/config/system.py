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
        
    def to_json(self) -> dict:
        """
        Serialize the system configuration to a JSON-serializable dictionary.
        
        Returns:
            A dictionary representation of the system configuration.
        """
        return {
            self.bootstrap.get_key(): self.bootstrap.to_json(),
            self.client_server.get_key(): self.client_server.to_json(),
            self.app_server.get_key(): self.app_server.to_json(),
            self.app_builder.get_key(): self.app_builder.to_json(),
            self.app_common.get_key(): self.app_common.to_json(),
        }
    
    @staticmethod
    def from_json(json_dict: dict) -> 'SystemConfiguration':
        """
        Deserialize a SystemConfiguration from a JSON dictionary.
        
        Args:
            json_dict: A dictionary containing the configuration data.
        Returns:
            An instance of SystemConfiguration populated with the data from the dictionary.
        """
        return SystemConfiguration(
            bootstrap=BootstrapConfiguration.from_json(json_dict.get(BootstrapConfiguration.get_key(), {})),
            client_server=ClientServerConfiguration.from_json(json_dict.get(ClientServerConfiguration.get_key(), {})),
            app_server=AppServerConfiguration.from_json(json_dict.get(AppServerConfiguration.get_key(), {})),
            app_builder=AppBuilderConfiguration.from_json(json_dict.get(AppBuilderConfiguration.get_key(), {})),
            app_common=AppCommonConfiguration.from_json(json_dict.get(AppCommonConfiguration.get_key(), {})),
        )