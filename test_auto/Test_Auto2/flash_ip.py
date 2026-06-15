import os
import signal
import subprocess
import time

from config.loader import ConfigLoader


class DeviceFlasher:
    def __init__(self, config=None):
        config = config or ConfigLoader.instance().config
        cfg = config.get("serial_config", {})

        self.device = cfg.get("device", "EFR32MG24B220F1536IM48").replace("IM48", "")
        self.ip_device = cfg.get("ip")
        if not self.ip_device:
            devices = cfg.get("devices", [])
            if devices and isinstance(devices, list):
                self.ip_device = devices[0].get("ip")
        self.commander = cfg.get("commander_path", "commander")

        base_dir = os.path.abspath(os.path.dirname(__file__))
        firmware_path = cfg.get("target_firmware", "resources/firmware/bt_soc_blinky.s37")
        self.firmware = firmware_path if os.path.isabs(firmware_path) else os.path.abspath(os.path.join(base_dir, firmware_path))

    # ================= INTERNAL =================
    def _run(self, cmd):
        print("\n[CMD]", " ".join(cmd))
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(res.stdout)
        return res.returncode == 0

    def _add_conn(self, cmd):
        
        return cmd + ["--ip", self.ip_device]

    # ================= COMMAND =================
    def mass_erase(self):
        cmd = [
            self.commander,
            "device", "masserase",
            "--device", self.device
        ]
        return self._run(self._add_conn(cmd))

    def flash(self):
        cmd = [
            self.commander,
            "flash", self.firmware,
            "--device", self.device
        ]
        return self._run(self._add_conn(cmd))

    def reset(self):
        cmd = [
            self.commander,
            "device", "reset",
            "--device", self.device
        ]
        return self._run(self._add_conn(cmd))

    

    # ================= RUN =================
    def run(self):
        print("===== FLASH  =====")

        if not self.mass_erase():
            print("❌ Mass erase failed")
            return

        if not self.flash():
            print("❌ Flash failed")
            return

        if not self.reset():
            print("❌ Reset failed")
            return


# ===== MAIN =====
if __name__ == "__main__":
    flasher = DeviceFlasher()
    flasher.run()