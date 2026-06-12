import pytest

from config.loader import ConfigLoader
from interface.commander import CommanderInterface

serial_config = ConfigLoader.instance().get("serial_config")
commander_client = CommanderInterface(serial_config)
firmware_path = commander_client.get_firmware_file()
serial_list = commander_client.get_serial_numbers()
safe_serial_list = serial_list if (serial_list and firmware_path) else ["no_device"]


@pytest.fixture(scope="module")
def commander():
    return CommanderInterface(serial_config)

def test_check_flashing_preconditions(commander):
    assert commander.get_serial_numbers(), "❌ serials.txt list not found or file is empty!"
    assert commander.get_firmware_file(), f"❌ .s37 file not found in configuration directory: {commander.firmware_dir}"


@pytest.mark.parametrize("sn", safe_serial_list)
def test_mass_flashing_device(sn, commander):
    """Scenario to test automatic firmware flashing for each Serial Number."""
    if sn == "no_device" or not firmware_path:
        pytest.skip("⏩ SKIP: Skipped due to missing serials.txt data or missing .s37 firmware in the system")

    print(f"\n▶️ Processing device SN: {sn}")

    # 1. Check USB connection of the device
    if not commander.is_device_connected(sn):
        pytest.skip(f"⏩ SKIP: Device {sn} is not connected via USB port.")

    # 2. Erase chip
    print(f"   [1/3] Erasing chip...")
    assert commander.mass_erase(sn) is True, f"❌ Erase chip {sn} failed!"

    # 3. Flash firmware
    print(f"   [2/3] Flashing firmware...")
    assert commander.flash_firmware(sn, firmware_path) is True, f"❌ Firmware flash for {sn} failed!"

    # 4. Reset device
    print(f"   [3/3] Resetting device...")
    commander.reset_device(sn)

    print(f"✅ Device {sn} flashed successfully!")