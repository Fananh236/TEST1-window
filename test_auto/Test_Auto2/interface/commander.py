import os
import subprocess

from utils.parser import read_serials


class CommanderInterface:
    def __init__(self, serial_config, project_root=None):
        self.serial_config = serial_config or {}
        self.project_root = project_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.commander_path = self.serial_config.get("commander_path", "commander")
        self.device = self.serial_config.get("device", "EFR32MG24B220F1536IM48")

        self.serial_file = os.path.join(self.project_root, "resources", "serials.txt")
        self.firmware_dir = self._resolve_path(self.serial_config.get("firmware_dir", "resources/firmware"))
        self.target_firmware = self._resolve_path(
            self.serial_config.get("target_firmware", "resources/firmware/bt_soc_blinky.s37")
        )

    def _resolve_path(self, path):
        if not path:
            return None
        return path if os.path.isabs(path) else os.path.abspath(os.path.join(self.project_root, path))

    def get_firmware_file(self):
        if self.target_firmware and os.path.exists(self.target_firmware):
            return self.target_firmware
        return None

    def get_serial_numbers(self):
        return read_serials(self.serial_file)

    def is_device_connected(self, sn):
        try:
            result = subprocess.run(
                [self.commander_path, "adapter", "list"],
                capture_output=True,
                text=True,
                check=True,
            )
            return sn in result.stdout
        except subprocess.SubprocessError:
            return False

    def mass_erase(self, sn):
        cmd = [
            self.commander_path,
            "device",
            "masserase",
            "-s",
            sn,
            "--device",
            self.device,
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0

    def flash_firmware(self, sn, firmware_path):
        cmd = [
            self.commander_path,
            "flash",
            firmware_path,
            "-s",
            sn,
            "--device",
            self.device,
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0

    def reset_device(self, sn):
        cmd = [
            self.commander_path,
            "device",
            "reset",
            "-s",
            sn,
            "--device",
            self.device,
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
