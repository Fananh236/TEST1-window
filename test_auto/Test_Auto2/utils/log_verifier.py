import re
from pathlib import Path
from typing import Optional, Union


def verify_chiptool_log_flow(
    project_root: Optional[Union[str, Path]] = None,
    rtt_log_name: str = "-RTTTelnetPort",
    pi_log_name: str = "Log/pi_connection.log",
):
    """Verify that the Pi log and RTT log show chip-tool dispatch and end-device execution."""
    root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
    rtt_log_path = root / rtt_log_name
    pi_log_path = root / pi_log_name

    details = []

    command_dispatched = False
    device_received_command = False
    device_executed_action = False

    if not pi_log_path.exists():
        details.append(f"Pi log not found: {pi_log_path}")
    else:
        pi_text = pi_log_path.read_text(encoding="utf-8", errors="ignore")
        command_patterns = [
            r"chip-tool\s+onoff\s+toggle",
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
    else:
        rtt_text = rtt_log_path.read_text(encoding="utf-8", errors="ignore").lower()

        if "im:invokecommandrequest" in rtt_text:
            device_received_command = True
            details.append("RTT log contains command receipt from the end device")
        else:
            details.append("RTT log does not contain command receipt markers")

        if re.search(r"turning light (on|off)|light (on|off)", rtt_text):
            device_executed_action = True
            details.append("RTT log contains end-device action output")
        else:
            details.append("RTT log does not contain end-device action output")

    return {
        "command_dispatched": command_dispatched,
        "device_received_command": device_received_command,
        "device_executed_action": device_executed_action,
        "details": " | ".join(details),
    }
