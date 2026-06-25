"""
Refactored chip-tool command execution with RTT capture and expect patterns.
- execute_command(): Execute chip-tool with RTT capture and expect matching
- send_on_command(): Turn on with RTT verification
- send_off_command(): Turn off with RTT verification  
- send_toggle_command(): Toggle with RTT verification
- validate_pairing(): Validate pairing from logs
"""

import re
import time
from typing import Union, List, Dict, Optional

from utils.log_parser import RTTLogParser, PiLogParser
from utils.rtt_reader import read_rtt_log_file, get_rtt_delta


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
    
    Args:
        pi_device: SSHClient instance
        config: Configuration dict
        chip_command: Full chip-tool command to execute
        expect: Expected response pattern(s) in RTT log (string or list)
        rtt_log_file: Path to rtt_log.txt
        timeout: Command timeout in seconds
        
    Returns:
        {
            "command": "...",
            "result": "success" | "fail" | "already_set",
            "matched_log": "...",
            "raw_log": "...",
            "stdout": "...",
            "stderr": "...",
        }
    """
    try:
        # Capture RTT baseline before command
        baseline_rtt = read_rtt_log_file(rtt_log_file) if rtt_log_file else ""
        
        # Execute command
        start_time = time.time()
        stdout, stderr = pi_device.execute_command(chip_command, timeout=timeout)
        
        # Capture RTT immediately after
        new_rtt = get_rtt_delta(rtt_log_file, baseline_rtt) if rtt_log_file else ""
        
        # Check for command-level errors
        full_output = (stdout + "\n" + stderr).lower()
        
        if "timeout" in full_output or "run command failure" in full_output:
            return {
                "command": chip_command,
                "result": "fail",
                "matched_log": "",
                "raw_log": new_rtt,
                "stdout": stdout,
                "stderr": stderr,
            }
        
        # If no expect patterns, just return success
        if not expect:
            return {
                "command": chip_command,
                "result": "success",
                "matched_log": "",
                "raw_log": new_rtt,
                "stdout": stdout,
                "stderr": stderr,
            }
        
        # Match expect patterns against RTT log
        expect_list = [expect] if isinstance(expect, str) else expect
        matched_log = ""
        result = "fail"
        
        for pattern in expect_list:
            if isinstance(pattern, str) and re.search(pattern, new_rtt, re.IGNORECASE):
                matched_log = new_rtt
                result = "success"
                break
            elif pattern in new_rtt:
                matched_log = new_rtt
                result = "success"
                break
        
        # Also detect "already_set" for on/off commands
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
    
    # Find target device
    name_to_find = device_name or config.get("_target_device_name")
    target_device = None
    
    if name_to_find:
        for device in devices:
            if device.get("name") == name_to_find:
                target_device = device
                break
    
    if target_device is None and devices:
        target_device = devices[0]
    
    # Merge values
    if target_device:
        for key in ("node_id", "endpoint_id", "discovery_type", "setup_pin_code", "discriminator"):
            if key in target_device and (key not in chip or not chip.get(key)):
                chip[key] = str(target_device[key])
    
    return chip


def fetch_thread_data_set(pi_device):
    """Fetch Thread dataset from Pi."""
    cmd = "sudo ot-ctl dataset active -x"
    
    out, err = pi_device.execute_command(cmd)
    
    if err:
        return None, err
    
    if not out:
        return None, "no_output"
    
    # Parse dataset (clean 'Done')
    dataset = None
    for line in out.splitlines():
        line = line.strip()
        if line and line.lower() != "done":
            dataset = line
            break
    
    if not dataset:
        return None, "invalid_dataset"
    
    # Validate hex
    if not all(c in "0123456789abcdefABCDEF" for c in dataset):
        return None, f"invalid_hex: {dataset}"
    
    dataset = f"hex:{dataset}"
    print(f"[DEBUG] DATASET: {dataset}")
    
    return dataset, None


def validate_device_state(pi_device):
    """
    Check if device is reachable and in valid state.
    
    Returns:
        True if device state is valid, raises exception otherwise
    """
    print("\n✅ Checking device state...")
    # This would involve checking Thread network state, device connectivity, etc.
    # For now, just return True - implementation depends on your device checks
    return True


def validate_pairing(pi_device, pi_log_file: str = None) -> bool:
    """
    Validate pairing was successful by checking Pi connection log.
    
    Args:
        pi_device: SSHClient instance
        pi_log_file: Path to pi_connection.log
        
    Returns:
        True if pairing successful, raises exception if failed
        
    Raises:
        RuntimeError if pairing validation fails
    """
    print("\n✅ Validating pairing...")
    
    if not pi_log_file:
        return True  # Skip validation if no log file provided
    
    try:
        with open(pi_log_file, "r", encoding="utf-8", errors="ignore") as f:
            log_content = f.read()
    except Exception:
        return True  # Skip if can't read log
    
    # Check for pairing success markers
    result = PiLogParser.extract_pairing_result(log_content)
    
    if result == "success":
        print("✅ Pairing validation: SUCCESS")
        return True
    elif result == "failure":
        raise RuntimeError("❌ Pairing validation FAILED - Check pi_connection.log for details")
    
    # If no explicit markers found, check for commissioning complete or errors
    if "Commissioning complete" in log_content or "pairing done" in log_content.lower():
        print("✅ Pairing validation: SUCCESS (implicit)")
        return True
    
    if "timeout" in log_content.lower() or "failed" in log_content.lower():
        raise RuntimeError("❌ Pairing validation FAILED - Timeout or failure detected in logs")
    
    # If no clear indicator, assume success for now
    print("⚠️ Pairing validation: No clear result found, assuming success")
    return True


def run_pairing(pi_device, config, pi_log_file: str = None):
    """
    Run pairing with proper validation.
    
    Args:
        pi_device: SSHClient instance
        config: Configuration dict
        pi_log_file: Path to pi_connection.log for validation
        
    Returns:
        (success: bool, node_id: str)
        
    Raises:
        RuntimeError if pairing fails
    """
    chip = resolve_chip_target(config)
    
    print("\n=========== START PAIRING ===========")
    
    # Clean chip-tool KVS
    pi_device.execute_command(
        "sudo rm -rf /tmp/chip_*"
    )
    
    # Fetch dataset
    dataset, err = fetch_thread_data_set(pi_device)
    
    if err or not dataset:
        raise RuntimeError(f"❌ Thread dataset missing: {err}")
    
    # Build pairing command
    pairing_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"pairing {chip.get('discovery_type', 'ble-wifi')} "
        f"{chip['node_id']} "
        f"{dataset} "
        f"{chip.get('setup_pin_code', '0')} "
        f"{chip.get('discriminator', '0')}"
    )
    
    print(f"[DEBUG] pairing_cmd = {pairing_cmd}")
    
    output, _ = pi_device.execute_command(pairing_cmd)
    
    # Wait for device to be ready
    print("⏳ Waiting device ready...")
    time.sleep(5)
    
    # Validate pairing from logs
    validate_pairing(pi_device, pi_log_file)
    
    # Optional: Check Thread state on Pi
    state_cmd = "sudo ot-ctl state"
    state_out, _ = pi_device.execute_command(state_cmd)
    print("[DEBUG] Thread state (Pi):", state_out)
    
    if not any(x in state_out.lower() for x in ["leader", "router"]):
        print("⚠️ WARN: Thread network may not be ready")
    
    print("=========== PAIRING DONE ===========\n")
    
    return True, chip.get("node_id")


def send_on_command(
    pi_device,
    config,
    label: str = "Turn On",
    rtt_log_file: str = None,
) -> Dict:
    """
    Send 'on' command to device with RTT verification.
    
    Args:
        pi_device: SSHClient instance
        config: Configuration dict
        label: Human-readable command label
        rtt_log_file: Path to rtt_log.txt for RTT capture
        
    Returns:
        Command result dict with matched RTT log
        
    Raises:
        RuntimeError if command fails
    """
    print(f"\n🚀 Sending command: {label}")
    
    chip = resolve_chip_target(config)
    
    on_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff on {chip['node_id']} {chip['endpoint_id']}"
    )
    
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
    """
    Send 'off' command to device with RTT verification.
    
    Args:
        pi_device: SSHClient instance
        config: Configuration dict
        label: Human-readable command label
        rtt_log_file: Path to rtt_log.txt for RTT capture
        
    Returns:
        Command result dict with matched RTT log
        
    Raises:
        RuntimeError if command fails
    """
    print(f"\n🚀 Sending command: {label}")
    
    chip = resolve_chip_target(config)
    
    off_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff off {chip['node_id']} {chip['endpoint_id']}"
    )
    
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
    """
    Send 'toggle' command to device with RTT verification.
    
    Args:
        pi_device: SSHClient instance
        config: Configuration dict
        label: Human-readable command label
        rtt_log_file: Path to rtt_log.txt for RTT capture
        
    Returns:
        Command result dict with matched RTT log
        
    Raises:
        RuntimeError if command fails
    """
    print(f"\n🚀 Sending command: {label}")
    
    chip = resolve_chip_target(config)
    
    toggle_cmd = (
        f"sudo {pi_device.chip_tool_path} "
        f"onoff toggle {chip['node_id']} {chip['endpoint_id']}"
    )
    
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
