import os
import time
import pytest
from utils.log_verifier import verify_chiptool_log_flow
from utils.chip_tool_helper import send_toggle_command


def test_verify_toggle_flow_from_logs(pi_device, flashed_device, device_rtt, config):
    """Verify that the Pi log and RTT log contain evidence of command dispatch and device execution."""

    # Build config với đúng device đã flash/pair
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]

    # Send a command to generate log data so this test is completely independent
    send_toggle_command(pi_device, target_config, "Toggle for log verification")

    # Give the RTT logger a moment to flush to disk
    time.sleep(2)

    from config.loader import ConfigLoader
    loader = ConfigLoader.instance()

    rtt_log_path = device_rtt.log_dir
    pi_log_path = getattr(pi_device, 'log_dir', None)
    if pi_log_path is None:
        pi_log_path = os.path.join(pi_device.log_dir, "pi_connection.log")

    result = verify_chiptool_log_flow(
        project_root=loader.root_dir,
        explicit_rtt_path=rtt_log_path,
        explicit_pi_path=pi_log_path
    )

    # Single combined assertion: all three checks must pass.
    overall = (
        result["command_dispatched"]
        and result["device_received_command"]
        and result["device_executed_action"]
    )

    # Provide a single pass/fail via pytest assert with details on failure
    assert overall, result["details"]

    # Optional: print details on success for visibility
    print("Log verification result:", result["details"])
