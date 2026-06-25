"""
Unified Log Parser for pi_connection.log and rtt_log.txt
- Parse chip-tool commands from Pi log with timestamps
- Parse device responses from RTT log
- Match commands to responses
"""

import re
from typing import List, Dict, Optional


class PiLogParser:
    """Parse Raspberry Pi connection log."""
    
    @staticmethod
    def extract_commands(pi_log_content: str) -> List[Dict]:
        """
        Extract chip-tool onoff commands from Pi log.
        
        Returns:
            List of {timestamp, action, node_id, endpoint_id}
        """
        commands = []
        
        # Pattern: timestamp ... chip-tool onoff ACTION NODE_ID ENDPOINT_ID
        pattern = re.compile(
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?"
            r"chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)",
            re.IGNORECASE
        )
        
        for match in pattern.finditer(pi_log_content):
            ts, action, node_id, endpoint_id = match.groups()
            commands.append({
                "timestamp": ts,
                "action": action.lower(),
                "node_id": node_id,
                "endpoint_id": endpoint_id,
            })
        
        return commands
    
    @staticmethod
    def extract_pairing_result(pi_log_content: str) -> Optional[str]:
        """
        Check if pairing was successful or failed.
        
        Returns:
            "success", "failure", or None if pairing not found
        """
        # Look for pairing command success indicators
        if re.search(r"Commissioning complete", pi_log_content, re.IGNORECASE):
            return "success"
        
        if re.search(r"Commissioning failed|pairing failed|error", pi_log_content, re.IGNORECASE):
            return "failure"
        
        return None


class RTTLogParser:
    """Parse RTT device log."""
    
    # Patterns to detect device responses
    TURN_ON_PATTERNS = [
        r"Turning light On",
        r"Turning [Ll]ight [Oo]n",
        r"Turning On",
    ]
    
    TURN_OFF_PATTERNS = [
        r"Turning light Off",
        r"Turning [Ll]ight [Oo]ff",
        r"Turning Off",
    ]
    
    ALREADY_SET_PATTERNS = [
        r"Endpoint\s+\d+\s+On/off\s+already\s+set",
        r"already\s+set",
    ]
    
    @staticmethod
    def extract_device_responses(rtt_content: str) -> List[str]:
        """
        Extract device action responses from RTT log.
        
        Returns:
            List of "TURN_ON", "TURN_OFF", "ALREADY_SET"
        """
        results = []
        lines = rtt_content.splitlines()
        
        for line in lines:
            # Check TURN_ON patterns
            for pattern in RTTLogParser.TURN_ON_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    results.append("TURN_ON")
                    break
            else:
                # Check TURN_OFF patterns
                for pattern in RTTLogParser.TURN_OFF_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        results.append("TURN_OFF")
                        break
                else:
                    # Check ALREADY_SET patterns
                    for pattern in RTTLogParser.ALREADY_SET_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            results.append("ALREADY_SET")
                            break
        
        return results



class LogMatcher:
    """Match Pi commands to RTT responses."""
    
    @staticmethod
    def verify_all_commands(pi_commands: List[Dict], device_results: List[str]) -> bool:
        """
        Verify all commands matched expected results.
        
        Args:
            pi_commands: List of {action, node_id, endpoint_id}
            device_results: List of device response strings
            
        Returns:
            True if all commands matched, raises AssertionError otherwise
        """
        if len(device_results) < len(pi_commands):
            raise AssertionError(
                f"❌ Not enough device results ({len(device_results)}) "
                f"for commands ({len(pi_commands)})"
            )
        
        failures = []
        
        for i, cmd in enumerate(pi_commands):
            expected = cmd["action"]
            actual = device_results[i]
            
            success = False
            
            if expected == "toggle":
                success = actual in ["TURN_ON", "TURN_OFF"]
            elif expected == "on":
                success = actual in ["TURN_ON", "ALREADY_SET"]
            elif expected == "off":
                success = actual in ["TURN_OFF", "ALREADY_SET"]
            
            print(
                f"CMD #{i+1}: {expected:<6} -> {actual:<12} "
                f"=> {'✅ PASS' if success else '❌ FAIL'}"
            )
            
            if not success:
                failures.append((expected, actual))
        
        if failures:
            msg = "\n❌ FAILURES:\n"
            for exp, act in failures:
                msg += f" - expected={exp}, actual={act}\n"
            raise AssertionError(msg)
        
        return True
