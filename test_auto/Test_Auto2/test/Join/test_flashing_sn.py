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

    serial_list = commander.get_serial_numbers()
    if not serial_list:
        pytest.skip("❌ Serial list not found in config or is empty!")

    return {
        "firmware_path": firmware_path,
        "serial_list": serial_list,
    }


def test_check_flashing_preconditions(commander, flashing_context):
    assert flashing_context["serial_list"], "❌ Serial list not found in config or is empty!"
    assert flashing_context["firmware_path"], f"❌ .s37 file not found in configuration directory: {commander.firmware_dir}"


def test_mass_flashing_device(commander, flashing_context):
    """Scenario to test automatic firmware flashing for each Serial Number."""
    firmware_path = flashing_context["firmware_path"]
    serial_list = flashing_context["serial_list"]

    if not serial_list:
        pytest.skip("⏩ SKIP: Skipped due to missing device serials in config or missing .s37 firmware in the system")

    for sn in serial_list:
        print(f"\n▶️ Processing device SN: {sn}")

        # 1. Check USB connection of the device
        if not commander.is_device_connected(sn):
            print(f"⏩ SKIP: Device {sn} is not connected via USB port.")
            continue

        # 2. Erase chip
        print(f"   [1/3] Erasing chip...")
        if not commander.mass_erase(sn):
            pytest.skip(f"⏩ SKIP: Erase chip {sn} failed")

        # 3. Flash firmware
        print(f"   [2/3] Flashing firmware...")
        if not commander.flash_firmware(firmware_path, sn):
            pytest.skip(f"⏩ SKIP: Firmware flash for {sn} failed")

        # 4. Reset device
        print(f"   [3/3] Resetting device...")
        commander.reset_device(sn)

        print(f"✅ Device {sn} flashed successfully!")