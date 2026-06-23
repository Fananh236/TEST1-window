"""
Consolidated utility functions for pattern detection, log path resolution, and common operations.
This module consolidates duplicate functions from across the codebase into single implementations.

Functions:
  - detect_pattern(): Unified pattern detection for RTT log lines
  - resolve_log_directory(): Unified log path resolution
  - get_log_files(): Get list of log files from directory
  - read_log_file(): Read log file contents
  - get_device_ip(): Extract device IP from config
"""

import os
from pathlib import Path
from typing import List, Dict, Optional


# ============================================================================
# UNIFIED PATTERN DETECTION
# ============================================================================

def detect_pattern(line: str, pattern_type: str) -> bool:
    """
    Unified pattern detection for RTT log line matching.
    Replaces: detect_receipt, detect_on_start, detect_on_done, detect_off_start, detect_off_done
    
    Args:
        line: RTT log line to check
        pattern_type: Type of pattern to detect
            - "receipt": Look for command receipt marker
            - "on_start": Look for "Turning ... On" pattern
            - "on_done": Look for "On ... done" completion
            - "off_start": Look for "Turning ... Off" pattern
            - "off_done": Look for "Off ... done" completion
            - Custom keywords can be passed as "keyword1,keyword2" (AND logic)
    
    Returns:
        True if pattern matches the line
    """
    line_lower = line.lower()
    
    if pattern_type == "receipt":
        return "receipt" in line_lower or "invokecommandrequest" in line_lower
    
    elif pattern_type == "on_start":
        return ("turning" in line_lower or "turn on" in line_lower) and "on" in line_lower
    
    elif pattern_type == "on_done":
        return "on" in line_lower and ("done" in line_lower or "confirm" in line_lower)
    
    elif pattern_type == "off_start":
        return ("turning" in line_lower or "turn off" in line_lower) and "off" in line_lower
    
    elif pattern_type == "off_done":
        return "off" in line_lower and ("done" in line_lower or "confirm" in line_lower)
    
    # Support custom patterns: "keyword1,keyword2" means ALL keywords must match
    elif "," in pattern_type:
        keywords = [k.strip().lower() for k in pattern_type.split(",")]
        return all(k in line_lower for k in keywords)
    
    # Single keyword pattern
    else:
        return pattern_type.lower() in line_lower


# Legacy function names for backward compatibility
def detect_receipt(line: str) -> bool:
    """Detect receipt in RTT log (legacy, use detect_pattern instead)."""
    return detect_pattern(line, "receipt")


def detect_on_start(line: str) -> bool:
    """Detect turn on start (legacy, use detect_pattern instead)."""
    return detect_pattern(line, "on_start")


def detect_on_done(line: str) -> bool:
    """Detect turn on done (legacy, use detect_pattern instead)."""
    return detect_pattern(line, "on_done")


def detect_off_start(line: str) -> bool:
    """Detect turn off start (legacy, use detect_pattern instead)."""
    return detect_pattern(line, "off_start")


def detect_off_done(line: str) -> bool:
    """Detect turn off done (legacy, use detect_pattern instead)."""
    return detect_pattern(line, "off_done")


# ============================================================================
# UNIFIED LOG PATH RESOLUTION
# ============================================================================

def resolve_log_directory(log_path: Optional[str] = None, project_root: Optional[str] = None) -> str:
    """
    Unified log directory resolution.
    Replaces: _resolve_log_dir() in conftest.py, resolve_log_path() in setup_log_rtt.py
    
    Args:
        log_path: Path from config (can be absolute or relative)
        project_root: Project root directory (auto-detected if not provided)
    
    Returns:
        Absolute path to log directory
    """
    if not log_path:
        # Use default Log directory at project root
        if not project_root:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.abspath(os.path.join(project_root, "Log"))
    
    if os.path.isabs(log_path):
        return os.path.abspath(log_path)
    
    # Relative path: resolve from project root
    if not project_root:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    return os.path.abspath(os.path.join(project_root, log_path))


def find_log_dir() -> Optional[Path]:
    """
    Find log directory by searching common locations.
    Replaces: find_log_dir() in log_find.py
    
    Returns:
        Path to log directory if found, None otherwise
    """
    here = Path(__file__).resolve().parent.parent
    
    candidates = [
        here / "Log",
        here.parent / "Log",
        here.parents[1] / "Log",
        Path.cwd() / "Log",
    ]
    
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    return None


# ============================================================================
# LOG FILE OPERATIONS
# ============================================================================

def get_log_files(log_dir: str) -> List[str]:
    """
    Get list of log files from directory.
    Replaces: get_log_files() in setup_log_rtt.py
    
    Args:
        log_dir: Directory path to search
    
    Returns:
        List of .log and .txt file names in the directory
    """
    if not os.path.isdir(log_dir):
        return []
    
    try:
        return [
            f for f in os.listdir(log_dir)
            if f.endswith((".log", ".txt"))
        ]
    except Exception:
        return []


def read_log_file(file_path: str) -> str:
    """
    Read log file contents.
    Replaces: read_log_file() in setup_log_rtt.py
    
    Args:
        file_path: Full path to log file
    
    Returns:
        File contents as string, empty string if error
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


# ============================================================================
# CONFIGURATION UTILITIES
# ============================================================================

def get_device_ip(config: Dict) -> Optional[str]:
    """
    Extract device IP from configuration.
    Replaces: get_device_ip() in setup_log_rtt.py
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Device IP address or None
    """
    if not config:
        return None
    
    serial_config = config.get("serial_config", {})
    
    # Check top-level IP first
    ip = serial_config.get("ip")
    if ip:
        return ip
    
    # Check devices list
    devices = serial_config.get("devices", [])
    if devices and isinstance(devices, list):
        for device in devices:
            if isinstance(device, dict) and device.get("ip"):
                return device["ip"]
    
    return None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # New consolidated functions
    "detect_pattern",
    "resolve_log_directory",
    "find_log_dir",
    "get_log_files",
    "read_log_file",
    "get_device_ip",
    # Legacy functions (for backward compatibility)
    "detect_receipt",
    "detect_on_start",
    "detect_on_done",
    "detect_off_start",
    "detect_off_done",
]
