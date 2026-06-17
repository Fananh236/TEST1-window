import re
from pathlib import Path
import pytest


def test_check_logs():
    # Search for Log dir in several likely locations
    here = Path(__file__).resolve().parent
    candidates = [
        here / "Log",
        here.parent / "Log",
        here.parents[1] / "Log",
        here.parents[2] / "Log",
        Path.cwd() / "Log",
    ]

    log_dir = "../test_auto/Test_Auto2/Log"
    if log_dir is None:
        pytest.skip(f"Log directory not found in candidates: {candidates}")

    pi_log = log_dir / "pi_connection.log"
    rtt_log = log_dir / "rtt_log.txt"

    if not pi_log.exists():
        pytest.skip(f"Pi log not found at {pi_log}")
    if not rtt_log.exists():
        pytest.skip(f"RTT log not found at {rtt_log}")

    pi_content = pi_log.read_text(encoding="utf-8", errors="ignore")
    rtt_content = rtt_log.read_text(encoding="utf-8", errors="ignore")

    # Extract commands
    pi_commands = []
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?EXECUTE COMMAND:.*?chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)", re.IGNORECASE)
    for m in pattern.finditer(pi_content):
        timestamp, action, node_id, endpoint_id = m.groups()
        pi_commands.append({"timestamp": timestamp, "action": action.lower(), "node_id": node_id, "endpoint_id": endpoint_id})

    if not pi_commands:
        fallback = re.compile(r"chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)", re.IGNORECASE)
        for m in fallback.finditer(pi_content):
            action, node_id, endpoint_id = m.groups()
            pi_commands.append({"action": action.lower(), "node_id": node_id, "endpoint_id": endpoint_id})

    assert pi_commands, "No 'onoff' commands found in pi_connection.log"

    # Extract RTT events
    rtt_events = []
    rtt_pattern = re.compile(r"\[(\d{2}:\d{2}:\d{2}\.\d{3})\].*?Turning light\s+(On|Off)", re.IGNORECASE)
    for m in rtt_pattern.finditer(rtt_content):
        time_str, state = m.groups()
        rtt_events.append({"time": time_str, "state": state.lower()})

    assert rtt_events, "No 'Turning light On/Off' messages found in rtt_log.txt"

    has_on = any(c["action"] == "on" for c in pi_commands)
    has_off = any(c["action"] == "off" for c in pi_commands)
    has_toggle = any(c["action"] == "toggle" for c in pi_commands)

    if has_on:
        assert any(e["state"] == "on" for e in rtt_events), "'onoff on' was sent but 'Turning light On' was not found in RTT log"
    if has_off:
        assert any(e["state"] == "off" for e in rtt_events), "'onoff off' was sent but 'Turning light Off' was not found in RTT log"
    if has_toggle:
        assert any(e["state"] in ("on", "off") for e in rtt_events), "'onoff toggle' was sent but no light transition state was found in RTT log"

    assert "im:invokecommandrequest" in rtt_content.lower(), "RTT log does not contain receipt marker 'im:invokecommandrequest'"

    print(f"Found {len(pi_commands)} onoff command(s); {len(rtt_events)} RTT event(s)")
