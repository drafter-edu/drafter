"""Base class and shared machinery for Drafter configuration sections.

Defines `BaseConfiguration`, the dataclass all configuration sections inherit
from. It provides the generic pipeline for building a configuration from
dataclass defaults, environment variables, and parsed command line arguments,
plus helpers for merging, copying, and JSON (de)serialization.
"""

import json
from dataclasses import dataclass, fields
from typing import Any, Optional, Literal


FalseType = Literal[False]
"""Type alias for the literal value `False`, used in `Union[FalseType, str]`
annotations where a field is either disabled (`False`) or holds a string."""


@dataclass
class BaseConfiguration:
    """Base dataclass for a section of the Drafter system configuration.

    Subclasses declare their settings as dataclass fields (whose defaults form
    the lowest-precedence layer) and override the hook methods `get_key`,
    `parse_env_variables`, `extend_parser`, and `parse_args`. The
    `map_from_raw` classmethod then assembles an instance by layering values
    with the precedence: dataclass defaults < environment variables < parsed
    command line arguments.
    """

    @staticmethod
    def get_key() -> str:
        """Return the key identifying this configuration section.

        The key names the section in serialized `SystemConfiguration`
        dictionaries (e.g., "bootstrap", "app_server").

        Returns:
            The unique string key for this configuration section.

        Raises:
            NotImplementedError: Always, in this base implementation;
                subclasses must override this method.
        """
        raise NotImplementedError(
            "Subclasses must implement get_key method to return their configuration key."
        )

    @classmethod
    def map_from_raw(
        cls,
        parsed_args: dict[str, Any],
        env_vars: Optional[dict[str, Any]] = None,
        existing_config=None,
    ):
        """Build a configuration instance by layering raw sources in precedence order.

        This is the central precedence-defining pipeline for all configuration
        sections. The starting point is either a fresh instance (dataclass
        defaults) or a copy of `existing_config`. Environment variables, if
        given, are filtered through `parse_env_variables` and merged on top of
        that base. Finally, command line arguments are filtered through
        `parse_args` and merged last, so they win. The resulting precedence is:
        defaults (or existing config) < environment variables < command line
        arguments. Both merges ignore unknown keys and `None` values, and
        `existing_config` itself is never mutated.

        Args:
            parsed_args: Dictionary of parsed command line arguments (e.g.,
                `vars()` of an argparse namespace).
            env_vars: Optional dictionary of environment variables; when
                omitted or empty, the environment layer is skipped.
            existing_config: Optional configuration instance to use (copied)
                as the base instead of a default-constructed one.

        Returns:
            A new configuration instance with all sources merged in.
        """
        if existing_config is None:
            config = cls()
        else:
            config = existing_config.copy()

        if env_vars:
            filtered_env = cls.parse_env_variables(env_vars)
            config.merge_in_args(filtered_env, raise_errors=False)

        filtered_args = cls.parse_args(parsed_args)
        config.merge_in_args(filtered_args, raise_errors=False)

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

    def load_from_file(self, file_path: str) -> dict:
        """Load configuration values from a JSON file.

        The file's contents are parsed and returned as-is; nothing is merged
        into this configuration instance.

        Args:
            file_path: Path to the JSON configuration file.

        Returns:
            The parsed contents of the JSON file as a dictionary.
        """
        # if not os.path.isfile(file_path):
        #    raise FileNotFoundError(f"Configuration file not found: {file_path}")
        with open(file_path, "r") as f:
            return json.load(f)

    def merge_in_args(self, new_args: dict, raise_errors=True) -> None:
        """Merge new arguments into configuration.

        Args:
            new_args: Dict of argument names and values. None values are ignored.
            raise_errors: Whether to raise on unknown attribute names; when
                False, unknown names are silently skipped.

        Raises:
            AttributeError: If an unknown configuration attribute is provided
                and `raise_errors` is True.
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

    def to_json(self) -> dict:
        """Serialize this configuration to a dictionary.

        Returns:
            A dictionary mapping each dataclass field name to its current value.
        """
        return {field.name: getattr(self, field.name) for field in fields(self)}

    @classmethod
    def from_json(cls, data: dict):
        """Construct a configuration instance from a dictionary.

        Args:
            data: Dictionary of field names to values, as produced by `to_json`.

        Returns:
            A new instance of this configuration class.
        """
        return cls(**data)

    def copy(self):
        """
        Creates a copy of the current configuration instance.

        Returns:
            Self: A new instance of the same class with the same values.
        """
        return self.__class__(
            **{field.name: getattr(self, field.name) for field in fields(self)}
        )
