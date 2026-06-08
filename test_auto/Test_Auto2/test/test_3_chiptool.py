import time
import re
import json

def send_toggle_command(pi_device, config, label):
    """Sends a toggle command to the device and validates the response."""
    print(f"\n[TC3.2] Sending command: {label}")
    
    chip = config['chip_config']
    toggle_cmd = (
        f"echo '{pi_device.password}' | sudo -S {pi_device.chip_tool_path} "
        f"onoff toggle {chip['node_id']} {chip['endpoint_id']}"
    )
    
    stdout, stderr = pi_device.execute_command(toggle_cmd)
    full_response = (stdout + "\n" + stderr).lower()
    
    # Error Handling
    
    assert "timeout" not in full_response, "Error: Command timed out!"
    assert "run command failure" not in full_response, "Error: chip-tool execution failed!"
    
    print(f"✅ {label} executed successfully!")
    return stdout

def test_pairing_device(pi_device, config):
    """TC3.1: Cleanup KVS and perform BLE-Thread Commissioning."""
    chip = config['chip_config']
    
    print(f"\n[TC3.1] Cleaning up KVS files...")
    pi_device.execute_command(f"echo '{pi_device.password}' | sudo -S rm -rf /tmp/chip_*")
    
    print(f"\n[TC3.1] Starting commissioning process...")
    pairing_cmd = (
        f"echo '{pi_device.password}' | sudo -S {pi_device.chip_tool_path} "
        f"pairing {chip['discovery_type']} {chip['node_id']} {chip['thread_dataset']} "
        f"{chip['setup_pin_code']} {chip['discriminator']}"
    )
    
    output, _ = pi_device.execute_command(pairing_cmd)
    
    # --- EXTRACT INFORMATION FROM LOGS ---
    # Search for "New device scanned" and extract the MAC address
    device_match = re.search(r"new device scanned:\s*([0-9a-fA-F:]{17})", output, re.IGNORECASE)
    
    if device_match:
        device_address = device_match.group(1)
        # Use print to capture into pytest report sections
        print(f"\n[TC3.1] ✅ FOUND DEVICE ADDRESS: {device_address}")
    else:
        print(f"\n[TC3.1] ⚠️ WARNING: Device address not found in logs!")
    
    # Validation
    is_success = "device commissioning completed with success" in output.lower()
    assert is_success, "Commissioning failed!"
    print(f"\n[TC3.1] Commissioning status: SUCCESS")

def test_toggle_functionality(pi_device, config):
    """TC3.2: Verify OnOff toggle functionality."""
    # First toggle
    send_toggle_command(pi_device, config, "Initial Toggle")
    
    # Sequential toggles
    for i in range(2):
        time.sleep(2)
        send_toggle_command(pi_device, config, f"Toggle iteration {i + 2}")
    
    print("\n🎉 All toggle commands executed successfully!")