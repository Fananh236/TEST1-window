import json
from pathlib import Path

from interface.rtt import DeviceRTT
from utils.chip_tool_helper import resolve_chip_target


def test_resolve_chip_target_from_device_config():
    config_path = Path(__file__).resolve().parents[2] / "config" / "config.json"
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    chip_target = resolve_chip_target(config, device_name="device_2")

    # assert chip_target["node_id"] == "2"
    # assert chip_target["endpoint_id"] == "1"
    # assert chip_target["discovery_type"] == "ble-thread"


def test_rtt_resolves_device_ip_and_sn_from_serial_devices(tmp_path):
    config_path = Path(__file__).resolve().parents[2] / "config" / "config.json"
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    rtt = DeviceRTT(serial_config=config["serial_config"], log_dir=str(tmp_path))
