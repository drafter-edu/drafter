import os
import json
from dataclasses import dataclass, field, fields
from typing import Any, Union, Optional, Literal, Self

from drafter.helpers.utils import seek_filename_by_line
from drafter.config.engines import EngineType

FalseType = Literal[False]

@dataclass
class BaseConfiguration:
    
    @classmethod
    def map_from_raw(cls, parsed_args: dict[str, Any],
                     env_vars: Optional[dict[str, Any]] = None,
                     existing_config: "Optional[Self]" = None) -> "Self":
        if existing_config is None:
            config = cls()
        else:
            config = existing_config.copy()
        
        if env_vars:
            filtered_env = cls.parse_env_variables(env_vars)
            config.merge_in_args(filtered_env, raise_errors=False)
        
        filtered_args = cls.parse_args(parsed_args)
        config.merge_in_args(filtered_args, raise_errors=False)
        
        config.leverage_filesystem()
        
        return config
    
    @staticmethod
    def extend_parser(parser):
        """Extend argument parser with configuration-specific arguments.

        Args:
            parser: An argparse.ArgumentParser instance to extend.
        """
        return parser
    
    @staticmethod
    def parse_env_variables(env_vars: dict) -> dict:
        """Parse environment variables relevant to this configuration.

        Args:
            env_vars: A dictionary of environment variables.

        Returns:
            A dictionary of configuration values extracted from environment variables.
        """
        return {}
    
    @staticmethod
    def parse_args(parsed_args: dict) -> dict:
        """Parse command line arguments relevant to this configuration.

        Args:
            parsed_args: A dictionary of parsed command line arguments.

        Returns:
            A dictionary of configuration values extracted from command line arguments.
        """
        return {}
    
    def merge_in_file(self, file_path: str, raise_errors: bool = True) -> None:
        """Merge configuration values from a JSON file.

        Args:
            file_path: Path to the JSON configuration file.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, "r") as f:
            data = json.load(f)
        
        self.merge_in_args(data, raise_errors=raise_errors)
    
    def merge_in_args(self, new_args: dict, raise_errors=True) -> None:
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
                if raise_errors:
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
        pass
    
    def to_json(self) -> dict:
        return {field.name: getattr(self, field.name) for field in fields(self)}
    
    @classmethod
    def from_json(cls, data: dict) -> "Self":
        return cls(
            **data
        )
        
    def copy(self) -> "Self":
        """
        Creates a copy of the current configuration instance.

        Returns:
            Self: A new instance of the same class with the same values.
        """
        return self.__class__(**{field.name: getattr(self, field.name) for field in fields(self)})