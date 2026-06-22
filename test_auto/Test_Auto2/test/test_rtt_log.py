import os
from pathlib import Path
import pytest

from utils.pi_log_parser import parse_pi_commands


def _find_pi_log():
    here = Path(__file__).resolve().parent
    candidates = [
        here / "py_connections.txt",
        here.parent / "py_connections.txt",
        here.parents[1] / "py_connections.txt",
        Path.cwd() / "py_connections.txt",
        Path.cwd() / "test_auto" / "py_connections.txt",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return str(c)
    return None


@pytest.mark.usefixtures("device_rtt")
def test_on_off_commands(device_rtt, request):
    """Parse Pi commands and verify RTT realtime events for each command."""
    pi_log = _find_pi_log()
    if not pi_log:
        pytest.skip("py_connections.txt not found")

    commands = parse_pi_commands(pi_log)
    if not commands:
        pytest.skip("No chip-tool onoff commands found in py_connections.txt")

    # optional: get pi_device fixture if provided to actually send commands
    pi_device = None
    try:
        pi_device = request.getfixturevalue("pi_device")
    except Exception:
        pi_device = None

    for cmd in commands:
        action = cmd["action"]
        node = cmd["node_id"]
        endpoint = cmd["endpoint_id"]

        # If we have pi_device, send the command live; otherwise assume external actor sent it.
        if pi_device:
            pi_device.execute_command(f"chip-tool onoff {action} {node} {endpoint}")

        ok = device_rtt.wait_for_command(action, timeout=5)
        assert ok, f"RTT did not confirm '{action}' for node {node} endpoint {endpoint}"
