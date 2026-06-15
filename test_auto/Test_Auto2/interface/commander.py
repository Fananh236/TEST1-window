from utils.device_helper import DeviceHelper

import os


class CommanderInterface:
    def __init__(self, serial_config, project_root=None):
        self.serial_config = serial_config or {}
        self.project_root = project_root or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )

        self.commander_path = self.serial_config.get("commander_path")
        self.device = self.serial_config.get("device")
        self.firmware_dir = self.serial_config.get("firmware_dir", "resources/firmware")

        if not self.commander_path:
            raise ValueError("Missing 'commander_path' in serial_config")
        if not self.device:
            raise ValueError("Missing 'device' in serial_config")

        self.helper = DeviceHelper(self.commander_path, self.device)

    # =========================================================
    # ACTION WRAPPER
    # =========================================================
    def mass_erase(self, sn=None, ip=None):
        ok, _, _ = self.helper.mass_erase(sn, ip)
        return ok

    def mass_erase_by_ip(self, ip):
        ok, _, _ = self.helper.mass_erase(None, ip)
        return ok

    def flash_firmware(self, firmware, sn=None, ip=None):
        if sn is not None and self._looks_like_firmware_path(firmware) and not self._looks_like_firmware_path(sn):
            firmware, sn = sn, firmware
        ok, _, _ = self.helper.flash(firmware, sn, ip)
        return ok

    def flash_firmware_by_ip(self, firmware, ip):
        ok, _, _ = self.helper.flash(firmware, None, ip)
        return ok

    def reset_device(self, sn=None, ip=None):
        ok, _, _ = self.helper.reset(sn, ip)
        return ok

    def reset_device_by_ip(self, ip):
        ok, _, _ = self.helper.reset(None, ip)
        return ok

    def is_device_connected(self, sn):
        return self.helper.is_connected(sn)

    def get_serial_numbers(self):
        devices = self.serial_config.get("devices", [])
        if devices:
            serials = [d["sn"] for d in devices if isinstance(d, dict) and "sn" in d]
            if serials:
                return serials
        return []

    def get_ip_numbers(self):
        devices = self.serial_config.get("devices", [])
        if devices:
            ips = [d["ip"] for d in devices if isinstance(d, dict) and "ip" in d]
            if ips:
                return ips
        return []

    def get_firmware_file(self):
        firmware = self.serial_config.get("target_firmware")

        if not firmware:
            raise ValueError("Missing 'target_firmware' in config")

        if not os.path.isabs(firmware):
            firmware = os.path.abspath(os.path.join(self.project_root, firmware))

        if not os.path.exists(firmware):
            raise FileNotFoundError(f"Firmware not found: {firmware}")

        return firmware

    def _looks_like_firmware_path(self, value):
        if not isinstance(value, str):
            return False
        if os.path.exists(value):
            return True
        return value.lower().endswith((".s37", ".hex", ".bin"))

