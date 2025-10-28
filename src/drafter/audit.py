from dataclasses import dataclass, field
import traceback
from typing import Optional
from drafter.data.errors import DrafterError, DrafterInfo, DrafterWarning
import sys


@dataclass
class AuditLogger:
    errors: list[DrafterError] = field(default_factory=list)
    warnings: list[DrafterWarning] = field(default_factory=list)
    info: list[DrafterInfo] = field(default_factory=list)

    def log_error(
        self,
        message: str,
        where: str,
        details: str,
        url: str,
        exception: Optional[Exception] = None,
    ) -> DrafterError:
        print("Logging error:", message, where, details, url, exception)
        return self.log_existing_error(
            DrafterError(
                message=message,
                where=where,
                details=details,
                url=url,
                # TODO: Skulpt does not let me do format_traceback yet
                traceback="\n".join(traceback.format_exception(exception))
                if exception
                else traceback.format_exc(),
            )
        )

    def log_existing_error(self, error: DrafterError) -> DrafterError:
        self.errors.append(error)
        return error

    def log_warning(
        self,
        message: str,
        where: str,
        details: str,
        url: str,
        exception: Optional[Exception] = None,
    ) -> DrafterWarning:
        return self.log_existing_warning(
            DrafterWarning(
                message=message,
                where=where,
                details=details,
                url=url,
                traceback="".join(traceback.format_exception(exception))
                if exception
                else traceback.format_exc(),
            )
        )

    def log_existing_warning(self, warning: DrafterWarning) -> DrafterWarning:
        self.warnings.append(warning)
        return warning

    def log_info(
        self, message: str, where: str, details: str, url: str = ""
    ) -> DrafterInfo:
        return self.log_existing_info(
            DrafterInfo(
                message=message,
                where=where,
                details=details,
                url=url,
            )
        )

    def log_existing_info(self, info: DrafterInfo) -> DrafterInfo:
        self.info.append(info)
        return info
