import time
import json
import pytest
from utils.chip_tool_helper import send_toggle_command, run_pairing


@pytest.mark.skip(reason="Skipping hardware-dependent test in CI environment")
def test_pairing_device(pi_device, config):
    """Cleanup KVS and perform BLE-Thread Commissioning."""
    success, device_address = run_pairing(pi_device, config)


    if device_address:
        print(f"\nFOUND DEVICE ADDRESS: {device_address}")
    else:
        print(f"\n WARNING: Device address not found in logs!")



    assert success, "Commissioning failed!"
    print(f"\n Commissioning status: SUCCESS")


@pytest.mark.skip(reason="Skipping hardware-dependent test in CI environment")
def test_toggle_functionality(pi_device, config):
    """verify OnOff toggle functionality."""
    send_toggle_command(pi_device, config, "Initial Toggle")

    for i in range(2):
        time.sleep(2)
        send_toggle_command(pi_device, config, f"Toggle iteration {i + 2}")



    print("\n All toggle commands executed successfully!")