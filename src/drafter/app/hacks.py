"""Logging tweaks that rebrand uvicorn's startup messages for Drafter."""

import logging
from copy import deepcopy

from click import style
from uvicorn.config import LOGGING_CONFIG


class ReplaceUvicornStartupMessage(logging.Filter):
    """Logging filter that rewrites or drops uvicorn startup log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Suppress or rewrite uvicorn.error startup messages.

        Drops the "Started server process" record entirely and rewrites the
        "Uvicorn running on" record into a "Drafter ready at" message,
        preserving the protocol/host/port when available.

        Args:
            record: Log record being filtered.

        Returns:
            False to drop the record, True to emit it (possibly rewritten).
        """
        if record.name == "uvicorn.error":
            if record.getMessage().startswith("Started server process"):
                return False
            if record.getMessage().startswith("Uvicorn running on"):
                if isinstance(record.args, tuple) and len(record.args) == 3:
                    protocol, host, port = record.args
                    # Match Uvicorn's handling of IPv6 addresses.
                    addr_format = (
                        f"{protocol}://[{host}]:{port}"
                        if ":" in str(host)
                        else f"{protocol}://{host}:{port}"
                    )

                    record.msg = f"Drafter ready at {addr_format}"
                    record.color_message = "Drafter ready at " + style(
                        addr_format, bold=True
                    )
                else:
                    record.msg = "Drafter server is ready"
                    record.color_message = "Drafter server is ready"
                record.args = ()

        return True


DRAFTER_LOG_CONFIG_FOR_UVICORN = deepcopy(LOGGING_CONFIG)
"""Uvicorn logging config with the startup-message replacement filter attached."""

DRAFTER_LOG_CONFIG_FOR_UVICORN.setdefault("filters", {})["replace_startup"] = {
    "()": ReplaceUvicornStartupMessage,
}
DRAFTER_LOG_CONFIG_FOR_UVICORN["handlers"]["default"].setdefault("filters", []).append(
    "replace_startup"
)
