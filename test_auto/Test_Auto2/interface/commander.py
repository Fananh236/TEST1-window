from utils.device_helper import DeviceHelper

import os


class CommanderInterface:
    def __init__(self, serial_config, project_root=None):
        self.serial_config = serial_config or {}
        self.project_root = project_root or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        self.commander_path = self.serial_config.get("commander_path", "commander")
        self.device = self.serial_config.get("device", "EFR32MG24B220F1536IM48")

        self.helper = DeviceHelper(self.commander_path, self.device)

        self.serial_file = os.path.join(self.project_root, "resources", "serials.txt")
        self.ip_file = os.path.join(self.project_root, "resources", "ip.txt")

    # =========================================================
    # ACTION WRAPPER
    # =========================================================
    def mass_erase(self, sn=None, ip=None):
        return self.helper.mass_erase(sn, ip)

    def flash_firmware(self, firmware, sn=None, ip=None):
        return self.helper.flash(firmware, sn, ip)

    def reset_device(self, sn=None, ip=None):
        return self.helper.reset(sn, ip)

    def is_device_connected(self, sn):
        return self.helper.is_connected(sn)
    
def get_firmware_file(self):
    firmware = self.serial_config.get("target_firmware")

    if not firmware:
        raise ValueError("Missing 'target_firmware' in config")

    if not os.path.isabs(firmware):
        firmware = os.path.abspath(os.path.join(self.project_root, firmware))

    if not os.path.exists(firmware):
        raise FileNotFoundError(f"Firmware not found: {firmware}")

    return firmware

