import time
import pytest
from utils.chip_tool_helper import send_toggle_command, run_pairing


def test_pairing_device(pi_device, flashed_device, config):
    """Cleanup KVS và thực hiện BLE-Thread Commissioning với thiết bị đã flash."""

    print(f"\n🔌 Pairing with device: {flashed_device['name']} (IP: {flashed_device['ip']}, node_id: {flashed_device['node_id']})")

    # Override config chip target với device đã flash
    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]

    success, _ = run_pairing(pi_device, target_config)

    assert success, "Commissioning failed!"
    print(f"\n✅ Commissioning status: SUCCESS")


def test_toggle_functionality(pi_device, flashed_device, config):
    """Verify OnOff toggle functionality với thiết bị đã pair."""

    print(f"\n🔁 Toggle device: {flashed_device['name']} (node_id: {flashed_device['node_id']})")

    target_config = dict(config)
    target_config["_target_device_name"] = flashed_device["name"]

    send_toggle_command(pi_device, target_config, "Initial Toggle")

    for i in range(2):
        time.sleep(2)
        send_toggle_command(pi_device, target_config, f"Toggle iteration {i + 2}")

    print("\n✅ All toggle commands executed successfully!")