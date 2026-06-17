import re
from pathlib import Path


def test_check_logs():
    base_dir = Path(__file__).resolve().parent
    log_dir = base_dir.parent / "Log"

    pi_log_path = log_dir / "pi_connection.log"
    rtt_log_path = log_dir / "rtt_log.txt"

    assert pi_log_path.exists(), f"Pi log not found at {pi_log_path}"
    assert rtt_log_path.exists(), f"RTT log not found at {rtt_log_path}"

    pi_text = pi_log_path.read_text(encoding="utf-8", errors="ignore")
    rtt_text = rtt_log_path.read_text(encoding="utf-8", errors="ignore")
    def test_check_logs():
        # Try to locate the Log directory in a few sensible places:
        # 1) next to this test file (test/Verify/Log)
        # 2) sibling test folder (test/Log)
        # 3) project root Log directory (../../Log from this file)
        here = Path(__file__).resolve().parent
        candidates = [
            here / "Log",
            here.parent / "Log",
            here.parents[2] / "Log",
        ]

        log_dir = None
        for c in candidates:
            if c.exists() and c.is_dir():
                log_dir = c
                break

        assert log_dir is not None, f"Could not find Log directory in candidates: {candidates}"

        pi_log = log_dir / "pi_connection.log"
        rtt_log = log_dir / "rtt_log.txt"

        assert pi_log.exists(), f"Pi log not found at {pi_log}"
        assert rtt_log.exists(), f"RTT log not found at {rtt_log}"

        pi_content = pi_log.read_text(encoding="utf-8", errors="ignore")
        rtt_content = rtt_log.read_text(encoding="utf-8", errors="ignore")

        # Extract onoff commands
        pi_commands = []
        pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?EXECUTE COMMAND:.*?chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)", re.IGNORECASE)
        for m in pattern.finditer(pi_content):
            timestamp, action, node_id, endpoint_id = m.groups()
            pi_commands.append({
                "timestamp": timestamp,
                "action": action.lower(),
                "node_id": node_id,
                "endpoint_id": endpoint_id,
            })

        # Fallback to simpler pattern if none found
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

        # Also check for receipt marker
        assert "im:invokecommandrequest" in rtt_content.lower(), "RTT log does not contain receipt marker 'im:invokecommandrequest'"

        print(f"Found {len(pi_commands)} onoff command(s); {len(rtt_events)} RTT event(s)")
