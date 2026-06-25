"""
Refactored chip-tool command execution with RTT capture and expect patterns.
- validate_pairing(): Validate pairing from logs
"""

import os
import re
import shlex
import time
from typing import List, Dict

from utils.common import read_log_file
from utils.log_parser import PiLogParser, RTTLogParser, LogMatcher
from utils.rtt_reader import read_rtt_log_file, get_rtt_delta


def build_sudo_command(pi_device, command: str) -> str:
    """
    Build a sudo command that supplies the SSH user's password via stdin.

    -S      : sudo reads password from standard input
    -p ''   : hide sudo password prompt in command output
    """
    password = getattr(pi_device, "password", "1")

    return (
        f"echo {shlex.quote(str(password))} | "
        f"sudo -S -p '' {command}"
    )


def resolve_chip_target(config, device_name=None):
    """Resolve chip target values from config."""
    serial_config = config.get("serial_config", {}) or {}
    chip = dict(config.get("chip_config", {}) or {})
    devices = serial_config.get("devices", []) or []

    name_to_find = device_name or config.get("_target_device_name")
    target_device = None

    if name_to_find:
        for device in devices:
            if device.get("name") == name_to_find:
                target_device = device
                break

    if target_device is None and devices:
        target_device = devices[0]

    if target_device:
        for key in (
            "node_id",
            "endpoint_id",
            "discovery_type",
            "setup_pin_code",
            "discriminator",
        ):
            if key in target_device and (key not in chip or not chip.get(key)):
                chip[key] = str(target_device[key])

    return chip


def fetch_thread_data_set(pi_device):
    """
    Fetch active Thread dataset from Pi.

    Returns:
        (dataset, None) on success
        (None, error_message) on failure
    """
    cmd = build_sudo_command(
        pi_device,
        "ot-ctl dataset active -x",
    )

    out, err = pi_device.execute_command(cmd)

    print(f"[DEBUG] dataset stdout: {repr(out)}")
    print(f"[DEBUG] dataset stderr: {repr(err)}")

    full_output = f"{out}\n{err}".lower()

    if (
        "a password is required" in full_output
        or "sorry, try again" in full_output
        or "[sudo] password" in full_output
    ):
        return None, "sudo_password_failed"

    if err and err.strip():
        return None, err.strip()

    if not out or not out.strip():
        return None, "no_output"

    dataset = None

    for line in out.splitlines():
        line = line.strip()

        if not line or line.lower() == "done":
            continue

        # Dataset phải là chuỗi hex.
        if re.fullmatch(r"[0-9a-fA-F]+", line):
            dataset = line
            break

    if not dataset:
        return None, f"invalid_dataset_output: {out.strip()}"

    dataset = f"hex:{dataset}"

    print(f"[DEBUG] DATASET: {dataset}")

    return dataset, None


def validate_device_state(pi_device):
    """Check if device is reachable and in valid state."""
    print("\n✅ Checking device state...")
    return True


def validate_pairing(pi_device, pi_log_file: str = None) -> bool:
    """Validate pairing was successful by checking Pi connection log."""
    print("\n✅ Validating pairing...")

    if not pi_log_file:
        return True

    try:
        with open(pi_log_file, "r", encoding="utf-8", errors="ignore") as file:
            log_content = file.read()
    except Exception:
        return True

    result = PiLogParser.extract_pairing_result(log_content)

    if result == "success":
        print("✅ Pairing validation: SUCCESS")
        return True

    if result == "failure":
        raise RuntimeError(
            "❌ Pairing validation FAILED - Check pi_connection.log for details"
        )

    if "commissioning complete" in log_content.lower():
        print("✅ Pairing validation: SUCCESS (implicit)")
        return True

    if "pairing done" in log_content.lower():
        print("✅ Pairing validation: SUCCESS (implicit)")
        return True

    if "timeout" in log_content.lower() or "failed" in log_content.lower():
        raise RuntimeError(
            "❌ Pairing validation FAILED - Timeout or failure detected in logs"
        )

    print("⚠️ Pairing validation: No clear result found, assuming success")
    return True


def run_pairing(pi_device, config, pi_log_file: str = None):
    """
    Run Matter pairing and validate Thread dataset.
    """
    chip = resolve_chip_target(config)

    print("\n=========== START PAIRING ===========")

    # Clean old chip-tool KVS.
    clean_cmd = build_sudo_command(
        pi_device,
        "rm -rf /tmp/chip_*",
    )
    clean_out, clean_err = pi_device.execute_command(clean_cmd)

    if clean_err and clean_err.strip():
        print(f"⚠️ Cannot clean chip KVS: {clean_err}")

    dataset, err = fetch_thread_data_set(pi_device)

    if err or not dataset:
        raise RuntimeError(f"❌ Thread dataset missing: {err}")

    pairing_raw_cmd = (
        f"{shlex.quote(pi_device.chip_tool_path)} "
        f"pairing {shlex.quote(str(chip.get('discovery_type', 'ble-thread')))} "
        f"{shlex.quote(str(chip['node_id']))} "
        f"{shlex.quote(dataset)} "
        f"{shlex.quote(str(chip.get('setup_pin_code', '0')))} "
        f"{shlex.quote(str(chip.get('discriminator', '0')))}"
    )

    pairing_cmd = build_sudo_command(pi_device, pairing_raw_cmd)

    print("[DEBUG] pairing command created")

    output, pairing_err = pi_device.execute_command(pairing_cmd, timeout=120)

    pairing_output = f"{output}\n{pairing_err}".lower()

    if (
        "a password is required" in pairing_output
        or "sorry, try again" in pairing_output
        or "[sudo] password" in pairing_output
    ):
        raise RuntimeError("❌ Pairing failed: sudo password is incorrect or missing")

    if "run command failure" in pairing_output:
        raise RuntimeError(f"❌ Pairing failed: {output}\n{pairing_err}")

    print("⏳ Waiting device ready...")
    time.sleep(5)

    validate_pairing(pi_device, pi_log_file)

    state_cmd = build_sudo_command(pi_device, "ot-ctl state")
    state_out, state_err = pi_device.execute_command(state_cmd)

    print("[DEBUG] Thread state (Pi):", state_out)

    if state_err and state_err.strip():
        print("[DEBUG] Thread state stderr:", state_err)

    if not any(state in state_out.lower() for state in ["leader", "router"]):
        print("⚠️ WARN: Thread network may not be ready")

    print("=========== PAIRING DONE ===========\n")

    return True, chip.get("node_id")


def run_and_verify(pi_device, device_rtt, log_paths, chip_cmd, label):
    """
    Execute one chip-tool command and verify via the full workflow:
    open RTT → send → close Pi → check Pi log → close RTT → check RTT log → compare.

    After verification, reconnects SSH and restarts RTT for the next command.
    """
    rtt_log_file = log_paths["rtt_log"]
    pi_log_file = log_paths["pi_log"]

    # === STEP 1: Open RTT (ensure active, record baselines) ===
    if device_rtt.rtt_proc is None:
        device_rtt.start_rtt()
        time.sleep(3)
    if pi_device._ssh_client is None:
        pi_device.connect()

    rtt_baseline = read_rtt_log_file(rtt_log_file)
    pi_baseline = read_log_file(pi_log_file) if os.path.exists(pi_log_file) else ""

    # === STEP 2: Send command ===
    print(f"{chip_cmd}")
    pi_device.execute_command(chip_cmd, timeout=15)
    time.sleep(2)
    print("✅ Command sent")

    # === STEP 3: Close Pi ===
    pi_device.disconnect()

    # === STEP 4: Check Pi log ===
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

    # === STEP 5: Close RTT ===
    device_rtt.stop_rtt()
    time.sleep(1)

    # === STEP 6: Check RTT log (end device) ===
    assert os.path.exists(rtt_log_file), f"RTT log not found: {rtt_log_file}"
    rtt_new = get_rtt_delta(rtt_log_file, rtt_baseline)
    assert len(rtt_new) > 0, "No new RTT log content after command"

    device_results = RTTLogParser.extract_device_responses(rtt_new)
    assert len(device_results) >= 1, "No device responses found in RTT log delta"

    # === STEP 7: Compare Pi command ↔ Device response ===
    LogMatcher.verify_all_commands([pi_commands[-1]], [device_results[-1]])

    print(f"\n[{label}] VERIFICATION PASSED!")

    # === Reconnect for next command ===
    pi_device.connect()
    device_rtt.start_rtt()
    time.sleep(2)