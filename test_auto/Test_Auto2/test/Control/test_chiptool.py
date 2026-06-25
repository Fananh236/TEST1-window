"""
Chip-tool control tests with full log verification per command.

Each command follows the complete E2E workflow:
  1. Open RTT log    → Ensure RTT is active, record baseline
  2. Send command    → Execute chip-tool command via SSH
  3. Close Pi        → Disconnect SSH
  4. Check Pi log    → Verify command in pi_connection.log delta
  5. Close RTT       → Stop JLinkRTTLogger
  6. Check RTT log   → Verify device response in rtt_log.txt delta
  7. Compare         → Match sent command ↔ device response, print result
  8. Reconnect       → Re-open SSH + RTT for next command

Test order: Device check → Pairing → Toggle → On → Off
"""

import pytest

from utils.chiptool import resolve_chip_target, validate_device_state, run_pairing, run_and_verify


# =====================================================================
# TEST FUNCTIONS
# =====================================================================

def test_0_device_state_check(pi_device, flashed_device, config):
    """Validate device is reachable before testing."""
    print(f"\n[STEP 0] Checking device state: {flashed_device['name']} (IP: {flashed_device['ip']})")

    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]

    assert validate_device_state(pi_device), "❌ Device state validation failed"
    print(f"✅ Device state valid: {flashed_device['name']}")


def test_1_pairing_device(pi_device, flashed_device, config, log_paths):
    """Perform chip-tool pairing."""
    print(f"\n[STEP 1] Pairing: {flashed_device['name']} (node_id: {flashed_device['node_id']})")

    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]

    success, node_id = run_pairing(
        pi_device, target_config, pi_log_file=log_paths["pi_log"],
    )
    assert success, f"❌ Pairing failed for node {node_id}"
    print(f"✅ Pairing successful: node_id={node_id}")


def test_2_toggle(pi_device, flashed_device, config, device_rtt, log_paths):
    """Toggle command with full log verification."""
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    chip = resolve_chip_target(target_config)

    chip_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff toggle {chip['node_id']} {chip['endpoint_id']}"
    )

    run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, "Toggle")


def test_3_on(pi_device, flashed_device, config, device_rtt, log_paths):
    """Turn On command with full log verification."""
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    chip = resolve_chip_target(target_config)

    chip_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff on {chip['node_id']} {chip['endpoint_id']}"
    )

    run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, "Turn On")


def test_4_off(pi_device, flashed_device, config, device_rtt, log_paths):
    """Turn Off command with full log verification."""
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    chip = resolve_chip_target(target_config)

    chip_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff off {chip['node_id']} {chip['endpoint_id']}"
    )

    run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, "Turn Off")
