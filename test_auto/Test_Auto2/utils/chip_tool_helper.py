"""
DEPRECATED: Backward compatibility module.
All functions have been refactored to utils/chiptool.py
Please import from utils.chiptool instead.
"""

import warnings
from utils.chiptool import (
    resolve_chip_target,
    fetch_thread_data_set,
    validate_device_state,
    validate_pairing,
    run_pairing,
    send_on_command,
    send_off_command,
    send_toggle_command,
    execute_command,
)

# Re-export for backward compatibility
__all__ = [
    "resolve_chip_target",
    "fetch_thread_data_set",
    "validate_device_state",
    "validate_pairing",
    "run_pairing",
    "send_on_command",
    "send_off_command",
    "send_toggle_command",
    "execute_command",
]

warnings.warn(
    "chip_tool_helper is deprecated. Import from utils.chiptool instead.",
    DeprecationWarning,
    stacklevel=2
)

