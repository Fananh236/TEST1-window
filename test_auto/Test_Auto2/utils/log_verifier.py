import re
import time
from pathlib import Path
from typing import Optional, Union



def verify_chiptool_log_flow(
    project_root: Optional[Union[str, Path]] = None,
    rtt_log_name: str = "rtt_log.txt",
    pi_log_name: str = "pi_connection.log",
    explicit_rtt_path: Optional[Union[str, Path]] = None,
    explicit_pi_path: Optional[Union[str, Path]] = None,
):
    """Verify that the Pi log and RTT log show chip-tool dispatch and end-device execution.
    Specially checks that when 'onoff on' or 'onoff off' are executed, the RTT log displays 'Turning light On' or 'Turning light Off'.
    """
    from config.loader import ConfigLoader
    loader = ConfigLoader.instance()
    log_dir = Path(loader.get_log_path())
    root = Path(project_root or loader.root_dir).resolve()

    rtt_log_path = Path(explicit_rtt_path) if explicit_rtt_path else None
    # If an explicit path is a directory, assume the log file resides inside it
    if rtt_log_path and rtt_log_path.is_dir():
        rtt_log_path = rtt_log_path / rtt_log_name
    if not rtt_log_path:
        for path in [
            log_dir / rtt_log_name,
            root / rtt_log_name,
            root / "-RTTTelnetPort",
            log_dir / "-RTTTelnetPort",
        ]:
            if path.exists():
                rtt_log_path = path
                break
        if not rtt_log_path:
            rtt_log_path = log_dir / rtt_log_name

    pi_log_path = Path(explicit_pi_path) if explicit_pi_path else None
    # If an explicit path is a directory, assume the log file resides inside it
    if pi_log_path and pi_log_path.is_dir():
        pi_log_path = pi_log_path / pi_log_name
    if not pi_log_path:
        for path in [
            log_dir / pi_log_name,
            root / "Log" / pi_log_name,
            root / pi_log_name,
        ]:
            if path.exists():
                pi_log_path = path
                break
        if not pi_log_path:
            pi_log_path = log_dir / pi_log_name

    details = []

    command_dispatched = False
    device_received_command = False
    device_executed_action = False

    if not pi_log_path.exists():
        details.append(f"Pi log not found: {pi_log_path}")
        pi_text = ""
    else:
        pi_text = pi_log_path.read_text(encoding="utf-8", errors="ignore")
        command_patterns = [
            r"chip-tool\s+onoff\s+(?:on|off|toggle)",
            r"chip-tool\s+pairing",
            r"EXECUTE COMMAND:.*chip-tool",
        ]
        if any(re.search(pattern, pi_text, re.IGNORECASE) for pattern in command_patterns):
            command_dispatched = True
            details.append("Pi log contains chip-tool command dispatch")
        else:
            details.append("Pi log does not contain chip-tool command dispatch")

    if not rtt_log_path.exists():
        details.append(f"RTT log not found: {rtt_log_path}")
        rtt_text = ""
    else:
        rtt_text = rtt_log_path.read_text(encoding="utf-8", errors="ignore")
        rtt_text_lower = rtt_text.lower()

        if "im:invokecommandrequest" in rtt_text_lower:
            device_received_command = True
            details.append("RTT log contains command receipt from the end device")
        else:
            details.append("RTT log does not contain command receipt markers")

        if re.search(r"turning light (on|off)|light (on|off)", rtt_text_lower):
            device_executed_action = True
            details.append("RTT log contains end-device action output")
        else:
            details.append("RTT log does not contain end-device action output")

    # Specific check for 'onoff on' -> 'Turning light On' and 'onoff off' -> 'Turning light Off'
    if pi_text and rtt_text:
        # Check all onoff commands in Pi log
        on_commands = re.findall(r"chip-tool\s+onoff\s+on\s+(\d+)\s+(\d+)", pi_text, re.IGNORECASE)
        off_commands = re.findall(r"chip-tool\s+onoff\s+off\s+(\d+)\s+(\d+)", pi_text, re.IGNORECASE)
        
        if on_commands:
            # Check for "Turning light On" in RTT log
            if re.search(r"turning light\s+on", rtt_text, re.IGNORECASE):
                details.append("Verified: 'onoff on' command matches 'Turning light On' in RTT log")
            else:
                details.append("Failed: 'onoff on' found in Pi log but 'Turning light On' NOT found in RTT log")
                device_executed_action = False
                
        if off_commands:
            # Check for "Turning light Off" in RTT log
            if re.search(r"turning light\s+off", rtt_text, re.IGNORECASE):
                details.append("Verified: 'onoff off' command matches 'Turning light Off' in RTT log")
            else:
                details.append("Failed: 'onoff off' found in Pi log but 'Turning light Off' NOT found in RTT log")
                device_executed_action = False

    return {
        "command_dispatched": command_dispatched,
        "device_received_command": device_received_command,
        "device_executed_action": device_executed_action,
        "details": " | ".join(details),
    }


def watch_logs_realtime(
    project_root: Optional[Union[str, Path]] = None,
    rtt_log_name: str = "rtt_log.txt",
    pi_log_name: str = "pi_connection.log",
    explicit_rtt_path: Optional[Union[str, Path]] = None,
    explicit_pi_path: Optional[Union[str, Path]] = None,
    duration_seconds: int = 60,
    poll_interval: float = 0.5,
):
    """Monitors Pi log and RTT log in real-time.
    Whenever a command is dispatched on Pi, it verifies the reaction in RTT log.
    """
    from config.loader import ConfigLoader
    loader = ConfigLoader.instance()
    log_dir = Path(loader.get_log_path())
    root = Path(project_root or loader.root_dir).resolve()

    rtt_path = Path(explicit_rtt_path) if explicit_rtt_path else None
    # If an explicit path is a directory, assume the RTT log file resides inside it
    if rtt_path and rtt_path.is_dir():
        rtt_path = rtt_path / rtt_log_name
    if not rtt_path:
        for path in [
            log_dir / rtt_log_name,
            root / rtt_log_name,
            root / "-RTTTelnetPort",
            log_dir / "-RTTTelnetPort",
        ]:
            if path.exists():
                rtt_path = path
                break
        if not rtt_path:
            rtt_path = log_dir / rtt_log_name

    pi_path = Path(explicit_pi_path) if explicit_pi_path else None
    # If an explicit path is a directory, assume the Pi log file resides inside it
    if pi_path and pi_path.is_dir():
        pi_path = pi_path / pi_log_name
    if not pi_path:
        for path in [
            log_dir / pi_log_name,
            root / "Log" / pi_log_name,
            root / pi_log_name,
        ]:
            if path.exists():
                pi_path = path
                break
        if not pi_path:
            pi_path = log_dir / pi_log_name

    print(f"[*] Starting Real-time Log Monitor...")
    print(f"[*] Pi Log: {pi_path}")
    print(f"[*] RTT Log: {rtt_path}")
    print(f"[*] Duration: {duration_seconds}s, Polling: {poll_interval}s")

    pi_offset = pi_path.stat().st_size if pi_path.exists() else 0
    rtt_offset = rtt_path.stat().st_size if rtt_path.exists() else 0

    def get_new_data(filepath, last_offset):
        if not filepath.exists():
            return "", last_offset
        current_size = filepath.stat().st_size
        if current_size < last_offset:
            last_offset = 0
        if current_size == last_offset:
            return "", last_offset
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(last_offset)
            data = f.read()
            return data, f.tell()

    start_time = time.time()
    try:
        while time.time() - start_time < duration_seconds:
            # Check for new command in Pi log
            new_pi, pi_offset = get_new_data(pi_path, pi_offset)
            if new_pi:
                # Find commands like chip-tool onoff ...
                pattern = r"chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)"
                for match in re.finditer(pattern, new_pi, re.IGNORECASE):
                    action, node_id, endpoint_id = match.groups()
                    print(f"\n[+] Detected Pi Command: onoff {action} {node_id} {endpoint_id}")
                    
                    # Wait up to 3 seconds for RTT reaction
                    reaction_found = False
                    reaction_start = time.time()
                    while time.time() - reaction_start < 3.0:
                        new_rtt, rtt_offset = get_new_data(rtt_path, rtt_offset)
                        if new_rtt:
                            # Search for Turning light On/Off
                            rtt_match = re.search(r"turning light\s+(on|off)", new_rtt, re.IGNORECASE)
                            if rtt_match:
                                rtt_action = rtt_match.group(1).lower()
                                print(f"  [=>] RTT Event Captured: Turning light {rtt_action.upper()}")
                                
                                # Verification assertion logic
                                if action.lower() == "on":
                                    assert rtt_action == "on", f"Expected light ON, got {rtt_action.upper()}"
                                elif action.lower() == "off":
                                    assert rtt_action == "off", f"Expected light OFF, got {rtt_action.upper()}"
                                print("  [Assert] PASS")
                                reaction_found = True
                                break
                        time.sleep(0.1)
                    
                    if not reaction_found:
                        print("  [Assert] WARNING: No corresponding RTT 'Turning light' output detected within 3s.")

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n[*] Monitor stopped by user.")
    except AssertionError as e:
        print(f"\n[!] ASSERTION FAILURE: {e}")
        raise
    
    print("\n[*] Monitor finished.")


