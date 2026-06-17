import re
from pathlib import Path


def test_check_logs_merged():
    base_dir = Path(__file__).resolve().parent
    log_dir = base_dir.parent / "Log"

    pi_log_path = log_dir / "pi_connection.log"
    rtt_log_path = log_dir / "rtt_log.txt"

    assert pi_log_path.exists(), f"Pi log not found at {pi_log_path}"
    assert rtt_log_path.exists(), f"RTT log not found at {rtt_log_path}"

    pi_text = pi_log_path.read_text(encoding="utf-8", errors="ignore")
    rtt_text = rtt_log_path.read_text(encoding="utf-8", errors="ignore")

    # Extract pi 'onoff' commands
    pi_commands = []
    cmd_pattern = re.compile(r"chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)", re.IGNORECASE)
    for m in cmd_pattern.finditer(pi_text):
        action, node_id, endpoint_id = m.groups()
        pi_commands.append({
            "action": action.lower(),
            "node_id": node_id,
            "endpoint_id": endpoint_id,
        })

    # Fallback: also try to capture when command is inside an "EXECUTE COMMAND:" line with timestamp
    if not pi_commands:
        fallback = re.compile(r"(\d{4}-\d{2}-\d{2} .*?)EXECUTE COMMAND:.*?chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)", re.IGNORECASE)
        for m in fallback.finditer(pi_text):
            _, action, node_id, endpoint_id = m.groups()
            pi_commands.append({
                "action": action.lower(),
                "node_id": node_id,
                "endpoint_id": endpoint_id,
            })

    # Extract RTT events
    rtt_events = []
    rtt_pattern = re.compile(r"\[(\d{2}:\d{2}:\d{2}\.\d{3})\].*?Turning light\s+(On|Off)", re.IGNORECASE)
    for m in rtt_pattern.finditer(rtt_text):
        time_str, state = m.groups()
        rtt_events.append({"time": time_str, "state": state.lower()})

    # Receipt marker
    receipt_marker = "im:invokecommandrequest"
    receipt_found = receipt_marker in rtt_text.lower()

    # Basic assertions
    assert len(pi_commands) > 0, "No 'onoff' commands found in pi_connection.log"
    assert len(rtt_events) > 0, "No 'Turning light On/Off' messages found in rtt_log.txt"

    has_on = any(c["action"] == "on" for c in pi_commands)
    has_off = any(c["action"] == "off" for c in pi_commands)
    has_toggle = any(c["action"] == "toggle" for c in pi_commands)

    if has_on:
        assert any(e["state"] == "on" for e in rtt_events), "'onoff on' was sent but 'Turning light On' was not found in RTT log"
    if has_off:
        assert any(e["state"] == "off" for e in rtt_events), "'onoff off' was sent but 'Turning light Off' was not found in RTT log"
    if has_toggle:
        assert any(e["state"] in ("on", "off") for e in rtt_events), "'onoff toggle' was sent but no light transition state was found in RTT log"

    # Also ensure the RTT log shows receipt of command
    assert receipt_found, f"RTT log does not contain receipt marker '{receipt_marker}'"

    # If all checks pass, print a short summary for CI logs
    print(f"Found {len(pi_commands)} onoff command(s); {len(rtt_events)} RTT event(s); receipt={receipt_found}")
