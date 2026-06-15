from utils.log_verifier import verify_chiptool_log_flow
from utils.chip_tool_helper import send_toggle_command
import time


def test_verify_toggle_flow_from_logs(pi_device, device_rtt, config):
    """Verify that the Pi log and RTT log contain evidence of command dispatch and device execution."""
    
    # Send a command to generate log data so this test is completely independent
    send_toggle_command(pi_device, config, "Toggle for log verification")
    
    # Give the RTT logger a moment to flush to disk
    time.sleep(2)
    
    from config.loader import ConfigLoader
    loader = ConfigLoader.instance()

    rtt_log_path = device_rtt.log_file
    pi_log_path = getattr(pi_device, 'log_file', None)
    if pi_log_path is None:
        import os
        pi_log_path = os.path.join(pi_device.log_dir, "pi_connection.log")

    result = verify_chiptool_log_flow(
        project_root=loader.root_dir,
        explicit_rtt_path=rtt_log_path,
        explicit_pi_path=pi_log_path
    )

    assert result["command_dispatched"], result["details"]
    assert result["device_received_command"], result["details"]
    assert result["device_executed_action"], result["details"]

    print(result["details"])
