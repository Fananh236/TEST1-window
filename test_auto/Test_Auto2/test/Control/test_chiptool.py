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

import os
import time
import pytest

from utils.common import read_log_file
from utils.log_parser import PiLogParser, RTTLogParser, LogMatcher
from utils.chiptool import resolve_chip_target, validate_device_state, run_pairing
from utils.rtt_reader import read_rtt_log_file, get_rtt_delta


# =====================================================================
# HELPER: Full 7-step workflow for one chip-tool command
# =====================================================================

def _run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, label):
    """
    Execute one chip-tool command and verify via the full workflow:
    open RTT → send → close Pi → check Pi log → close RTT → check RTT log → compare.

    After verification, reconnects SSH and restarts RTT for the next command.

    Reuses existing functions:
      - read_rtt_log_file(), get_rtt_delta()  (rtt_reader)
      - read_log_file()                       (common)
      - PiLogParser, RTTLogParser, LogMatcher  (log_parser)
    """
    rtt_log_file = log_paths["rtt_log"]
    pi_log_file = log_paths["pi_log"]

    # === STEP 1: Open RTT (ensure active, record baselines) ===
    print(f"\n{'='*60}")
    print(f"[{label}] STEP 1: Open RTT log")
    print(f"{'='*60}")

    if device_rtt.rtt_proc is None:
        device_rtt.start_rtt()
        time.sleep(3)
    if pi_device._ssh_client is None:
        pi_device.connect()

    rtt_baseline = read_rtt_log_file(rtt_log_file)
    pi_baseline = read_log_file(pi_log_file) if os.path.exists(pi_log_file) else ""
    print(f"  RTT baseline: {len(rtt_baseline)} bytes")
    print(f"  Pi  baseline: {len(pi_baseline)} bytes")
    print("✅ RTT active, baselines recorded")

    # === STEP 2: Send command ===
    print(f"\n{'='*60}")
    print(f"[{label}] STEP 2: Send command")
    print(f"{'='*60}")

    print(f"  → {chip_cmd}")
    pi_device.execute_command(chip_cmd, timeout=15)
    time.sleep(2)
    print("✅ Command sent")

    # === STEP 3: Close Pi ===
    print(f"\n{'='*60}")
    print(f"[{label}] STEP 3: Close Pi")
    print(f"{'='*60}")

    pi_device.disconnect()
    print("✅ SSH disconnected")

    # === STEP 4: Check Pi log ===
    print(f"\n{'='*60}")
    print(f"[{label}] STEP 4: Check Pi log")
    print(f"{'='*60}")

    assert os.path.exists(pi_log_file), f"Pi log not found: {pi_log_file}"
    pi_full = read_log_file(pi_log_file)
    assert len(pi_full) > 0, "Pi log is empty"

    # Extract delta (only new content since baseline)
    if pi_baseline and pi_full.startswith(pi_baseline):
        pi_new = pi_full[len(pi_baseline):]
    else:
        pi_new = pi_full

    pi_commands = PiLogParser.extract_commands(pi_new)
    assert len(pi_commands) >= 1, "No chip-tool commands found in Pi log delta"

    cmd_info = pi_commands[-1]
    print(
        f"  Pi sent: onoff {cmd_info['action']} "
        f"node={cmd_info['node_id']} ep={cmd_info['endpoint_id']}"
    )
    print("✅ Pi log verified")

    # === STEP 5: Close RTT ===
    print(f"\n{'='*60}")
    print(f"[{label}] STEP 5: Close RTT")
    print(f"{'='*60}")

    device_rtt.stop_rtt()
    time.sleep(1)
    print("✅ RTT stopped")

    # === STEP 6: Check RTT log (end device) ===
    print(f"\n{'='*60}")
    print(f"[{label}] STEP 6: Check end device RTT log")
    print(f"{'='*60}")

    assert os.path.exists(rtt_log_file), f"RTT log not found: {rtt_log_file}"
    rtt_new = get_rtt_delta(rtt_log_file, rtt_baseline)
    assert len(rtt_new) > 0, "No new RTT log content after command"

    device_results = RTTLogParser.extract_device_responses(rtt_new)
    assert len(device_results) >= 1, "No device responses found in RTT log delta"

    print(f"  Device responded: {device_results[-1]}")
    print("✅ RTT log verified")

    # === STEP 7: Compare Pi command ↔ Device response ===
    print(f"\n{'='*60}")
    print(f"[{label}] STEP 7: Compare Pi command ↔ Device response")
    print(f"{'='*60}")

    LogMatcher.verify_all_commands([pi_commands[-1]], [device_results[-1]])

    print(f"\n🎉 [{label}] VERIFICATION PASSED!")

    # === Reconnect for next command ===
    print(f"\n  ↻ Reconnecting SSH + RTT for next command...")
    pi_device.connect()
    device_rtt.start_rtt()
    time.sleep(2)
    print("  ✅ Ready for next command")


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

    _run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, "Toggle")


def test_3_on(pi_device, flashed_device, config, device_rtt, log_paths):
    """Turn On command with full log verification."""
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    chip = resolve_chip_target(target_config)

    chip_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff on {chip['node_id']} {chip['endpoint_id']}"
    )

    _run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, "Turn On")


def test_4_off(pi_device, flashed_device, config, device_rtt, log_paths):
    """Turn Off command with full log verification."""
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    chip = resolve_chip_target(target_config)

    chip_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff off {chip['node_id']} {chip['endpoint_id']}"
    )

    _run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, "Turn Off")
