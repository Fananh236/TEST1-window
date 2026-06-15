import re
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

