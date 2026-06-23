
"""
DEPRECATED: Use utils.log_parser.LogMatcher and utils.common.detect_pattern instead.
Kept for backward compatibility.
"""

import warnings
from utils.log_parser import LogMatcher
from utils.common import detect_pattern


def verify_command_vs_device(pi_commands, device_results):
    """Verify command vs device result (backward compatible)."""
    warnings.warn(
        "verify_command_vs_device is deprecated. Use LogMatcher.verify_all_commands from utils.log_parser",
        DeprecationWarning,
        stacklevel=2
    )
    
    print("\n=== STEP 3: MATCH COMMAND ↔ DEVICE RESULT ===\n")
    LogMatcher.verify_all_commands(pi_commands, device_results)


# Legacy pattern detection functions for backward compatibility
# All now use detect_pattern from utils.common (consolidated implementation)

def detect_receipt(line: str) -> bool:
    """
    Detect receipt in RTT log.
    
    DEPRECATED: Use detect_pattern(line, "receipt") from utils.common instead.
    """
    warnings.warn(
        "detect_receipt is deprecated. Use detect_pattern(line, 'receipt') from utils.common",
        DeprecationWarning,
        stacklevel=2
    )
    return detect_pattern(line, "receipt")


def detect_on_start(line: str) -> bool:
    """
    Detect turn on start.
    
    DEPRECATED: Use detect_pattern(line, "on_start") from utils.common instead.
    """
    warnings.warn(
        "detect_on_start is deprecated. Use detect_pattern(line, 'on_start') from utils.common",
        DeprecationWarning,
        stacklevel=2
    )
    return detect_pattern(line, "on_start")


def detect_on_done(line: str) -> bool:
    """
    Detect turn on done.
    
    DEPRECATED: Use detect_pattern(line, "on_done") from utils.common instead.
    """
    warnings.warn(
        "detect_on_done is deprecated. Use detect_pattern(line, 'on_done') from utils.common",
        DeprecationWarning,
        stacklevel=2
    )
    return detect_pattern(line, "on_done")


def detect_off_start(line: str) -> bool:
    """
    Detect turn off start.
    
    DEPRECATED: Use detect_pattern(line, "off_start") from utils.common instead.
    """
    warnings.warn(
        "detect_off_start is deprecated. Use detect_pattern(line, 'off_start') from utils.common",
        DeprecationWarning,
        stacklevel=2
    )
    return detect_pattern(line, "off_start")


def detect_off_done(line: str) -> bool:
    """
    Detect turn off done.
    
    DEPRECATED: Use detect_pattern(line, "off_done") from utils.common instead.
    """
    warnings.warn(
        "detect_off_done is deprecated. Use detect_pattern(line, 'off_done') from utils.common",
        DeprecationWarning,
        stacklevel=2
    )
    return detect_pattern(line, "off_done")

