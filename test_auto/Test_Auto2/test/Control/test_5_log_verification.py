from pathlib import Path

from utils.log_verifier import verify_chiptool_log_flow


def test_verify_toggle_flow_from_logs():
    """Verify that the Pi log and RTT log contain evidence of command dispatch and device execution."""
    project_root = Path(__file__).resolve().parents[2]

    result = verify_chiptool_log_flow(project_root)

    assert result["command_dispatched"], result["details"]
    assert result["device_received_command"], result["details"]
    assert result["device_executed_action"], result["details"]

    print(result["details"])
