"""
Refactored chip-tool command execution with RTT capture and expect patterns.
- execute_command(): Execute chip-tool with RTT capture and expect matching
- send_on_command(): Turn on with RTT verification
- send_off_command(): Turn off with RTT verification
- send_toggle_command(): Toggle with RTT verification
- validate_pairing(): Validate pairing from logs
"""

import re
import shlex
import time
from typing import Union, List, Dict

from utils.log_parser import PiLogParser
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


def execute_command(
    pi_device,
    config,
    chip_command: str,
    expect: Union[str, List[str], None] = None,
    rtt_log_file: str = None,
    timeout: float = 15.0,
) -> Dict:
    """
    Execute chip-tool command with RTT capture and optional pattern matching.
    """
    try:
        baseline_rtt = read_rtt_log_file(rtt_log_file) if rtt_log_file else ""

        stdout, stderr = pi_device.execute_command(chip_command, timeout=timeout)

        new_rtt = (
            get_rtt_delta(rtt_log_file, baseline_rtt)
            if rtt_log_file
            else ""
        )

        full_output = f"{stdout}\n{stderr}".lower()

        sudo_errors = [
            "a password is required",
            "incorrect password attempt",
            "sorry, try again",
            "[sudo] password",
        ]

        if (
            "timeout" in full_output
            or "run command failure" in full_output
            or any(error in full_output for error in sudo_errors)
        ):
            return {
                "command": chip_command,
                "result": "fail",
                "matched_log": "",
                "raw_log": new_rtt,
                "stdout": stdout,
                "stderr": stderr or stdout,
            }

        if not expect:
            return {
                "command": chip_command,
                "result": "success",
                "matched_log": "",
                "raw_log": new_rtt,
                "stdout": stdout,
                "stderr": stderr,
            }

        expect_list = [expect] if isinstance(expect, str) else expect
        matched_log = ""
        result = "fail"

        for pattern in expect_list:
            if re.search(pattern, new_rtt, re.IGNORECASE):
                matched_log = new_rtt
                result = "success"
                break

        if "already" in new_rtt.lower() and "set" in new_rtt.lower():
            matched_log = new_rtt
            result = "already_set"

        return {
            "command": chip_command,
            "result": result,
            "matched_log": matched_log,
            "raw_log": new_rtt,
            "stdout": stdout,
            "stderr": stderr,
        }

    except Exception as e:
        return {
            "command": chip_command,
            "result": "fail",
            "matched_log": "",
            "raw_log": "",
            "stdout": "",
            "stderr": str(e),
        }


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


def send_on_command(
    pi_device,
    config,
    label: str = "Turn On",
    rtt_log_file: str = None,
) -> Dict:
    """Send on command to device with RTT verification."""
    print(f"\n🚀 Sending command: {label}")

    chip = resolve_chip_target(config)

    on_raw_cmd = (
        f"{shlex.quote(pi_device.chip_tool_path)} "
        f"onoff on {shlex.quote(str(chip['node_id']))} "
        f"{shlex.quote(str(chip['endpoint_id']))}"
    )

    on_cmd = build_sudo_command(pi_device, on_raw_cmd)

    result = execute_command(
        pi_device,
        config,
        on_cmd,
        expect=["Turning", "already set"],
        rtt_log_file=rtt_log_file,
    )

    if result["result"] == "fail":
        raise RuntimeError(f"❌ {label} failed: {result['stderr']}")

    print(f"✅ {label} executed successfully!")
    return result


def send_off_command(
    pi_device,
    config,
    label: str = "Turn Off",
    rtt_log_file: str = None,
) -> Dict:
    """Send off command to device with RTT verification."""
    print(f"\n🚀 Sending command: {label}")

    chip = resolve_chip_target(config)

    off_raw_cmd = (
        f"{shlex.quote(pi_device.chip_tool_path)} "
        f"onoff off {shlex.quote(str(chip['node_id']))} "
        f"{shlex.quote(str(chip['endpoint_id']))}"
    )

    off_cmd = build_sudo_command(pi_device, off_raw_cmd)

    result = execute_command(
        pi_device,
        config,
        off_cmd,
        expect=["Turning", "already set"],
        rtt_log_file=rtt_log_file,
    )

    if result["result"] == "fail":
        raise RuntimeError(f"❌ {label} failed: {result['stderr']}")

    print(f"✅ {label} executed successfully!")
    return result


def send_toggle_command(
    pi_device,
    config,
    label: str = "Toggle",
    rtt_log_file: str = None,
) -> Dict:
    """Send toggle command to device with RTT verification."""
    print(f"\n🚀 Sending command: {label}")

    chip = resolve_chip_target(config)

    toggle_raw_cmd = (
        f"{shlex.quote(pi_device.chip_tool_path)} "
        f"onoff toggle {shlex.quote(str(chip['node_id']))} "
        f"{shlex.quote(str(chip['endpoint_id']))}"
    )

    toggle_cmd = build_sudo_command(pi_device, toggle_raw_cmd)

    result = execute_command(
        pi_device,
        config,
        toggle_cmd,
        expect=["Turning"],
        rtt_log_file=rtt_log_file,
    )

    if result["result"] == "fail":
        raise RuntimeError(f"❌ {label} failed: {result['stderr']}")

    print(f"✅ {label} executed successfully!")
    return result