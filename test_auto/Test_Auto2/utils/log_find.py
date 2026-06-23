"""
DEPRECATED: Use utils.log_parser and utils.common instead.
Kept for backward compatibility.
"""

import re
import warnings
from pathlib import Path
from utils.log_parser import PiLogParser, RTTLogParser
from utils.common import find_log_dir, read_log_file as read_log_file_util


# =========================
# File utils (legacy wrappers)
# =========================
def find_log_dir():
    """Find log directory (backward compatible)."""
    warnings.warn(
        "find_log_dir is deprecated. Use find_log_dir from utils.common",
        DeprecationWarning,
        stacklevel=2
    )
    from utils.common import find_log_dir as find_log_dir_new
    return find_log_dir_new()


def read_file(path: Path):
    """Read file contents (backward compatible)."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


# =========================
# PI log parser (backward compatibility)
# =========================
def extract_pi_commands(content: str):
    """Extract chip-tool commands from Pi log (backward compatible)."""
    warnings.warn(
        "extract_pi_commands is deprecated. Use PiLogParser.extract_commands from utils.log_parser",
        DeprecationWarning,
        stacklevel=2
    )
    return PiLogParser.extract_commands(content)


# =========================
# RTT parser (backward compatibility)
# =========================
def extract_device_results(rtt_content: str):
    """Extract device results from RTT log (backward compatible)."""
    warnings.warn(
        "extract_device_results is deprecated. Use RTTLogParser.extract_device_responses from utils.log_parser",
        DeprecationWarning,
        stacklevel=2
    )
    return RTTLogParser.extract_device_responses(rtt_content)


__all__ = [
    "find_log_dir",
    "read_file",
    "extract_pi_commands",
    "extract_device_results",
]

