"""
Real-time RTT Reader for per-function RTT capture.
- Captures RTT logs immediately after command execution
- Returns raw RTT output for pattern matching
"""

import os
import time
from typing import List


def capture_rtt_logs(rtt_log_file: str, start_time: float, timeout: float = 5.0) -> str:
    """
    Capture RTT logs from a specific timestamp onwards.
    
    Args:
        rtt_log_file: Path to rtt_log.txt
        start_time: Timestamp when command started (time.time())
        timeout: How long to wait for RTT output (seconds)
        
    Returns:
        Raw RTT log content captured after start_time
    """
    if not os.path.exists(rtt_log_file):
        return ""
    
    end_time = time.time() + timeout
    captured_logs = []
    
    # Keep reading until timeout or we get meaningful output
    while time.time() < end_time:
        try:
            with open(rtt_log_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if content.strip():
                    captured_logs.append(content)
                    time.sleep(0.1)  # Brief pause to allow more data
        except Exception:
            pass
        
        time.sleep(0.05)
    
    return "\n".join(captured_logs) if captured_logs else ""


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
