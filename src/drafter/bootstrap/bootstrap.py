import sys
import os
from drafter.config.bootstrap import BootstrapConfiguration
from drafter.helpers.args import get_argparser


def get_bootstrap_configuration() -> BootstrapConfiguration:
    """Get the bootstrap configuration for the current launch, whatever it is.

    This function processes environment variables, command line arguments, and config files
    to determine the bootstrap configuration. The bootstrap configuration is used to determine
    how to proceed with the rest of the launch process, including whether we are in `start_server`
    mode or `compile_site` mode.

    Returns:
        BootstrapConfiguration: The determined bootstrap configuration.
    """
    
    config = BootstrapConfiguration()
    
    # Check if we're being launched from the CLI with specific arguments
    # Check for the special Environment Variable that indicates we're in `compile_site` mode
    if "DRAFTER_MODE" in os.environ and os.environ["DRAFTER_MODE"] == "compile_site":
        config.mode = "compile_site"
    
    return config


# Singleton
BOOTSTRAP_CONFIGURATION = get_bootstrap_configuration()