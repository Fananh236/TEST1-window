import re
from pathlib import Path
import pytest


# =========================
# Utils
# =========================
def _find_log_dir():
    here = Path(__file__).resolve().parent

    candidates = [
        here / "Log",
        here.parent / "Log",
        here.parents[1] / "Log",
        here.parents[2] / "Log",
        Path.cwd() / "Log",
    ]

    for c in candidates:
        if c.exists() and c.is_dir():
            return c

    return None


def _read_file(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore")


# =========================
# Extractors
# =========================
def _extract_pi_commands(content: str):
    commands = []

    pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?"
        r"EXECUTE COMMAND:.*?chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)",
        re.IGNORECASE,
    )

    for m in pattern.finditer(content):
        timestamp, action, node_id, endpoint_id = m.groups()
        commands.append({
            "timestamp": timestamp,
            "action": action.lower(),
            "node_id": node_id,
            "endpoint_id": endpoint_id,
        })

    # fallback
    if not commands:
        fallback = re.compile(
            r"chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)",
            re.IGNORECASE,
        )

        for m in fallback.finditer(content):
            action, node_id, endpoint_id = m.groups()
            commands.append({
                "action": action.lower(),
                "node_id": node_id,
                "endpoint_id": endpoint_id,
            })

    return commands


# =========================
# Main Check Logic
# =========================
def check_logs():
    log_dir = _find_log_dir()

    if log_dir is None:
        raise RuntimeError("Log directory not found")

    pi_log = log_dir / "pi_connection.log"
    rtt_log = log_dir / "rtt_log.txt"

    if not pi_log.exists():
        raise RuntimeError(f"Missing {pi_log}")

    if not rtt_log.exists():
        raise RuntimeError(f"Missing {rtt_log}")

    pi_content = _read_file(pi_log)
    rtt_content = _read_file(rtt_log)

    print("=== Analyzing Logs ===")

    # =========================
    # Extract PI commands
    # =========================
    pi_commands = _extract_pi_commands(pi_content)

    print(f"Found {len(pi_commands)} 'onoff' commands:")
    for cmd in pi_commands[:15]:
        ts = cmd.get("timestamp", "N/A")
        print(f"  - [{ts}] onoff {cmd['action']} {cmd['node_id']} {cmd['endpoint_id']}")

    if len(pi_commands) > 15:
        print(f"  ... and {len(pi_commands) - 15} more")

    if not pi_commands:
        raise AssertionError("No 'onoff' commands found in pi log")

    # =========================
    # RTT analysis
    # =========================
    jlink_lower = rtt_content.lower()

    receipt_marker = "im:invokecommandrequest"
    action_on_re = re.compile(r"turning light\s+on", re.IGNORECASE)
    action_off_re = re.compile(r"turning light\s+off", re.IGNORECASE)

    print(f"\nRTT log size: {len(rtt_content)} bytes")
    print("\n=== Verifying each command ===")

    failures = []

    for idx, cmd in enumerate(pi_commands, start=1):
        expected_action = cmd["action"]

        receipt_found = receipt_marker in jlink_lower

        if expected_action == "on":
            action_found = bool(action_on_re.search(rtt_content))
        elif expected_action == "off":
            action_found = bool(action_off_re.search(rtt_content))
        else:
            # toggle
            action_found = bool(
                action_on_re.search(rtt_content)
                or action_off_re.search(rtt_content)
            )

        print(
            f"Command #{idx}: onoff {expected_action} -> "
            f"receipt={receipt_found}, action={action_found}"
        )

        if not receipt_found or not action_found:
            failures.append({
                "command": cmd,
                "receipt_found": receipt_found,
                "action_found": action_found,
            })

    # =========================
    # Final assert
    # =========================
    if failures:
        lines = [f"FAIL: {len(failures)} command(s) failed:"]
        for f in failures:
            c = f["command"]
            lines.append(
                f" - {c['action']} {c['node_id']}:{c['endpoint_id']} "
                f"-> receipt={f['receipt_found']} action={f['action_found']}"
            )

        raise AssertionError("\n".join(lines))

    print("\n✅ SUCCESS: All commands verified with RTT log")


# =========================
# Pytest entry
# =========================
def test_check_logs():
    try:
        check_logs()
    except RuntimeError as e:
        pytest.skip(str(e))


# =========================
# Standalone run
# =========================
if __name__ == "__main__":
    check_logs()