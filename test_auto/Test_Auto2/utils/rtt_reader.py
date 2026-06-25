"""
Real-time RTT Reader for per-function RTT capture.
- Returns raw RTT output for pattern matching
"""

import os
import time
from typing import List


def read_rtt_log_file(rtt_log_file: str) -> str:
    """
    Read entire RTT log file.
    
    Args:
        rtt_log_file: Path to rtt_log.txt
        
    Returns:
        Full RTT log content
    """
    if not os.path.exists(rtt_log_file):
        return ""
    
    try:
        with open(rtt_log_file, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def get_rtt_delta(rtt_log_file: str, baseline_content: str) -> str:
    """
    Get new RTT content that appeared after baseline.
    
    Args:
        rtt_log_file: Path to rtt_log.txt
        baseline_content: Previously captured RTT content
        
    Returns:
        New lines that appeared in RTT log
    """
    current = read_rtt_log_file(rtt_log_file)
    
    if not baseline_content:
        return current
    
    # Find where baseline ends in current
    if baseline_content in current:
        return current[len(baseline_content):].strip()
    
    return current.strip()
