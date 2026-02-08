import os
from dataclasses import dataclass, field, fields
from typing import Union, Optional, Literal

from drafter.helpers.utils import seek_filename_by_line
from drafter.config.engines import EngineType

FalseType = Literal[False]

@dataclass
class AppBackendConfig:
    engine: EngineType = "skulpt"

    user_directory: Union[FalseType, str] = False
    main_filename: Union[FalseType, str] = False
    asset_directory: Union[FalseType, str] = False
    show_filename_as: Union[FalseType, str] = False
    
    mount_drafter_locally: bool = False

    override_asset_url: Union[bool, str] = False

    site_title: str = "Drafter App Server"
    
    def merge_in_args(self, new_args: dict) -> None:
        """Merge new arguments into configuration.

        Args:
            new_args: Dict of argument names and values.

        Raises:
            AttributeError: If unknown configuration attribute provided.
        """
        for key, value in new_args.items():
            if hasattr(self, key):
                if value is not None:
                    setattr(self, key, value)
            else:
                raise AttributeError(f"Unknown configuration attribute: {key}")

    def extract_from_args(self, potential_args: dict):
        """Extract configuration values from argument dict.

        Args:
            potential_args: Dict potentially containing configuration values.
        """
        for field in fields(self):
            if field.name in potential_args:
                value = potential_args[field.name]
                if value is not None:
                    setattr(self, field.name, value)
                    
    def leverage_filesystem(self):
        # TODO: Move this logic into AppServerConfiguration?
        if self.user_directory is False:
            found_path = seek_filename_by_line("start_server", self.main_filename)
            self.user_directory = (
                os.path.dirname(found_path) if found_path else os.getcwd()
            )
            self.main_filename = (
                os.path.basename(found_path)
                if found_path
                else (self.main_filename or "main.py")
            )

        elif not os.path.isdir(self.user_directory):
            if os.path.isfile(self.user_directory):
                self.main_filename = os.path.basename(self.user_directory)
                self.user_directory = os.path.dirname(self.user_directory)

        else:
            # TODO: Logic seems redundant, maybe only do it in app_server?
            self.main_filename = (
                self.main_filename if self.main_filename is not False else "main.py"
            )

        if self.show_filename_as is False:
            self.show_filename_as = self.main_filename