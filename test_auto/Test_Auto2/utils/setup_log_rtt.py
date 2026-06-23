"""
Log directory and file utilities.
These functions are now consolidated in utils.common module.
This module is kept for backward compatibility.
"""

import warnings
from utils.common import (
    resolve_log_directory,
    get_log_files,
    read_log_file,
    get_device_ip,
)


def resolve_log_path(config):
    """Legacy wrapper for resolve_log_directory (backward compatible)."""
    warnings.warn(
        "resolve_log_path is deprecated. Use resolve_log_directory from utils.common",
        DeprecationWarning,
        stacklevel=2
    )
    log_path = config.get("log_path")
    return resolve_log_directory(log_path)


__all__ = [
    "resolve_log_path",
    "get_log_files",
    "read_log_file",
    "get_device_ip",
    # Re-export from common
    "resolve_log_directory",
]

