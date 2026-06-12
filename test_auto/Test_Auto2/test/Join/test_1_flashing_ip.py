import pytest

from config.loader import ConfigLoader
from interface.commander import CommanderInterface

serial_config = ConfigLoader.instance().get("serial_config")
commander_client = CommanderInterface(serial_config)
firmware_path = commander_client.get_firmware_file()


ip_list = commander_client.get_ip_numbers()
safe_ip_list = ip_list if (ip_list and firmware_path) else ["no_device"]





@pytest.fixture(scope="module")
def commander():
    return CommanderInterface(serial_config)

def test_check_flashing_preconditions(commander):
    assert commander.get_ip_numbers(), "❌ ip.txt list not found or file is empty!"
    assert commander.get_firmware_file(), f"❌ .s37 file not found in configuration directory: {commander.firmware_dir}"


@pytest.mark.parametrize("ip", safe_ip_list)
def test_mass_flashing_device(ip, commander):
    """Scenario to test automatic firmware flashing for each Serial Number."""
    if ip == "no_device" or not firmware_path:
        pytest.skip("⏩ SKIP: Skipped due to missing serials.txt data or missing .s37 firmware in the system")

    print(f"\n▶️ Processing device IP: {ip}")

   
    # 2. Erase chip
    print(f"   [1/3] Erasing chip...")
    assert commander.mass_erase_by_ip(ip) is True, f"❌ Erase chip {ip} failed!"

    # 3. Flash firmware
    print(f"   [2/3] Flashing firmware...")
    assert commander.flash_firmware_by_ip(ip, firmware_path) is True, f"❌ Firmware flash for {ip} failed!"

    # 4. Reset device
    print(f"   [3/3] Resetting device...")
    commander.reset_device_by_ip(ip)

    print(f"✅ Device {ip} flashed successfully!")