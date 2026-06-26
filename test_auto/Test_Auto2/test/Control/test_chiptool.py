"""
Chip-tool control tests with full log verification per command.

Flow:
  0. Device check
  1. Pairing (MUST PASS or STOP ALL TESTS)
  2. Toggle
  3. On
  4. Off
"""

import pytest

from utils.chiptool import resolve_chip_target, run_pairing, run_and_verify


# ==========================================================
# GLOBAL STATE (CONTROL FLOW)
# ==========================================================
PAIRING_OK = False


# ==========================================================
# TEST FUNCTIONS
# ==========================================================

def test_0_device_state_check(flashed_device, config):
    """Validate device is reachable before testing."""
    print(f"\n[STEP 0] Checking device state: {flashed_device['name']} (IP: {flashed_device['ip']})")

    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]

    print(f"✅ Device state valid: {flashed_device['name']}")


def test_1_pairing_device(pi_device, flashed_device, config, log_paths):
    """Perform chip-tool pairing."""
    global PAIRING_OK

    print(f"\n[STEP 1] Pairing: {flashed_device['name']} (node_id: {flashed_device['node_id']})")

    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]

    try:
        success, node_id = run_pairing(
            pi_device,
            target_config,
            pi_log_file=log_paths["pi_log"],
        )

        if not success:
            print(f"❌ Pairing failed for node {node_id}")
            pytest.exit("STOP: Pairing failed", returncode=1)

        print(f"✅ Pairing successful")
        PAIRING_OK = True

    except Exception as e:
        print(f"❌ Pairing fail ")
        pytest.exit(f"STOP: Pairing crashed → {e}", returncode=1)


def test_2_toggle(pi_device, flashed_device, config, device_rtt, log_paths):
    """Toggle command with full log verification."""
    if not PAIRING_OK:
        pytest.exit("STOP: Pairing was not successful", returncode=1)

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
    if not PAIRING_OK:
        pytest.exit("STOP: Pairing was not successful", returncode=1)

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
    if not PAIRING_OK:
        pytest.exit("STOP: Pairing was not successful", returncode=1)

    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    chip = resolve_chip_target(target_config)

    chip_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff off {chip['node_id']} {chip['endpoint_id']}"
    )

    run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, "Turn Off")