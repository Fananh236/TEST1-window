import time
import pytest
from utils.chiptool import (
    validate_device_state,
    run_pairing,
    send_on_command,
    send_off_command,
    send_toggle_command,
)


@pytest.fixture(scope="module")
def log_paths(config):
    """Get log file paths from config."""
    log_dir = config.get("log_path") or config.get("serial_config", {}).get("log_dir")
    if not log_dir:
        log_dir = "Log"
    
    return {
        "pi_log": f"{log_dir}/pi_connection.log",
        "rtt_log": f"{log_dir}/rtt_log.txt",
    }


def test_0_device_state_check(pi_device, flashed_device, config):
    """
    STEP 1: Check device state FIRST
    - Verify device is reachable
    - Verify Thread network connectivity
    - Set target device in config
    """
    print(f"\n[STEP 1] Checking device state: {flashed_device['name']} (IP: {flashed_device['ip']})")
    
    # Override config chip target with device already flashed
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    
    # Validate device is reachable
    assert validate_device_state(pi_device), "❌ Device state validation failed"
    
    print(f"✅ Device state valid: {flashed_device['name']}")


def test_1_pairing_device(pi_device, flashed_device, config, log_paths):
    """
    STEP 2: Perform pairing
    - Run chip-tool pairing command
    - Validate pairing success from pi_connection.log
    - Raise exception if pairing fails
    """
    print(f"\n[STEP 2] Pairing with device: {flashed_device['name']} (IP: {flashed_device['ip']}, node_id: {flashed_device['node_id']})")
    
    # Override config chip target with device already flashed
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    
    # Run pairing with validation
    success, node_id = run_pairing(
        pi_device,
        target_config,
        pi_log_file=log_paths["pi_log"],
    )
    
    assert success, f"❌ Pairing failed for node {node_id}"
    print(f"✅ Pairing successful: node_id={node_id}")


def test_2_toggle_functionality(pi_device, flashed_device, config, log_paths):
    """
    STEP 3a: Test toggle command
    - Send toggle command
    - Capture RTT log
    - Verify expected response in RTT log
    """
    print(f"\n[STEP 3a] Testing toggle: {flashed_device['name']} (node_id: {flashed_device['node_id']})")
    
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    
    # Initial toggle
    result = send_toggle_command(
        pi_device,
        target_config,
        label="Initial Toggle",
        rtt_log_file=log_paths["rtt_log"],
    )
    
    assert result["result"] in ["success", "already_set"], f"❌ Toggle failed: {result}"
    print(f"✅ Toggle 1 result: {result['result']}")
    print(f"   RTT response: {result['matched_log'][:100] if result['matched_log'] else 'N/A'}")
    
    # Additional toggles
    for i in range(2):
        time.sleep(1)
        result = send_toggle_command(
            pi_device,
            target_config,
            label=f"Toggle iteration {i + 2}",
            rtt_log_file=log_paths["rtt_log"],
        )
        
        assert result["result"] in ["success", "already_set"], f"❌ Toggle {i+2} failed: {result}"
        print(f"✅ Toggle {i+2} result: {result['result']}")
    
    print("✅ All toggle commands executed successfully!")


def test_3_on_functionality(pi_device, flashed_device, config, log_paths):
    """
    STEP 3b: Test 'on' command
    - Send on command
    - Capture RTT log
    - Verify expected response in RTT log
    """
    print(f"\n[STEP 3b] Testing 'on' command: {flashed_device['name']} (node_id: {flashed_device['node_id']})")
    
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    
    result = send_on_command(
        pi_device,
        target_config,
        label="Turn On",
        rtt_log_file=log_paths["rtt_log"],
    )
    
    assert result["result"] in ["success", "already_set"], f"❌ Turn On failed: {result}"
    print(f"✅ Turn On result: {result['result']}")
    print(f"   RTT response: {result['matched_log'][:100] if result['matched_log'] else 'N/A'}")


def test_4_off_functionality(pi_device, flashed_device, config, log_paths):
    """
    STEP 3c: Test 'off' command
    - Send off command
    - Capture RTT log
    - Verify expected response in RTT log
    """
    print(f"\n[STEP 3c] Testing 'off' command: {flashed_device['name']} (node_id: {flashed_device['node_id']})")
    
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]
    
    result = send_off_command(
        pi_device,
        target_config,
        label="Turn Off",
        rtt_log_file=log_paths["rtt_log"],
    )
    
    assert result["result"] in ["success", "already_set"], f"❌ Turn Off failed: {result}"
    print(f"✅ Turn Off result: {result['result']}")
    print(f"   RTT response: {result['matched_log'][:100] if result['matched_log'] else 'N/A'}")
