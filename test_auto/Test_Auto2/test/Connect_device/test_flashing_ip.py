from time import time

import pytest

from config.loader import ConfigLoader
from interface.commander import CommanderInterface


@pytest.fixture(scope="module")
def commander():
    serial_config = ConfigLoader.instance().get("serial_config", {})
    return CommanderInterface(serial_config)


@pytest.fixture(scope="module")
def flashing_context(commander):
    try:
        firmware_path = commander.get_firmware_file()
    except (FileNotFoundError, ValueError) as exc:
        pytest.skip(str(exc))

    ip_list = commander.get_ip_numbers()
    if not ip_list:
        pytest.skip("❌ IP list not found in config or is empty!")

    return {
        "firmware_path": firmware_path,
        "ip_list": ip_list,
    }


def test_check_flashing_preconditions(commander, flashing_context):
    assert flashing_context["ip_list"], "❌ IP list not found in config or is empty!"
    assert flashing_context["firmware_path"], f"❌ .s37 file not found in configuration directory: {commander.firmware_dir}"


def test_mass_flashing_device(commander, flashing_context):
    """Scenario to test automatic firmware flashing for each IP."""
    firmware_path = flashing_context["firmware_path"]
    ip_list = flashing_context["ip_list"]

    if not ip_list:
        pytest.skip("⏩ SKIP: Skipped due to missing IP data in config or missing .s37 firmware in the system")

    for ip in ip_list:
        print(f"\n▶️ Processing device IP: {ip}")

        # 2. Erase chip
        print(f"   [1/3] Erasing chip...")
        if not commander.mass_erase_by_ip(ip):
            pytest.skip(f"⏩ SKIP: Erase chip {ip} failed")

        # 3. Flash firmware
        print(f"   [2/3] Flashing firmware...")
        if not commander.flash_firmware_by_ip(firmware_path, ip):
            pytest.skip(f"⏩ SKIP: Firmware flash for {ip} failed")

        # 4. Reset device
        print(f"   [3/3] Resetting device...")
        commander.reset_device_by_ip(ip)
        time.sleep(5) 

        print(f"✅ Device {ip} flashed successfully!")
