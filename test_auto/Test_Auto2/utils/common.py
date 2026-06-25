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
from typing import List, Dict, Optional



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
    "resolve_log_directory",
    "get_log_files",
    "read_log_file",
    "get_device_ip",
]
