
import subprocess
import os


class DeviceHelper:
    def __init__(self, commander_path, device):
        self.commander = commander_path
        self.device = device

    # =========================================================
    # CORE EXECUTOR
    # =========================================================
    def _run(self, cmd, timeout=60):
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if res.returncode != 0:
                print(f"❌ FAIL: {' '.join(cmd)}")
                print(res.stderr)

            return res.returncode == 0

        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {' '.join(cmd)}")
            return False

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False

    # =========================================================
    # COMMAND BUILDER
    # =========================================================
    def _build_cmd(self, action, sn=None, ip=None):
        cmd = [self.commander, "device", action]

        if sn:
            cmd += ["-s", sn]

        if ip:
            cmd += ["--ip", ip]

        cmd += ["--device", self.device]

        return cmd

    # =========================================================
    # ACTIONS
    # =========================================================
    def mass_erase(self, sn=None, ip=None):
        cmd = self._build_cmd("masserase", sn, ip)
        return self._run(cmd)

    def reset(self, sn=None, ip=None):
        cmd = self._build_cmd("reset", sn, ip)
        return self._run(cmd)

    def flash(self, firmware_path, sn=None, ip=None):
        cmd = [self.commander, "flash", firmware_path]

        if sn:
            cmd += ["-s", sn]

        if ip:
            cmd += ["--ip", ip]

        cmd += ["--device", self.device]

        return self._run(cmd)

    def is_connected(self, sn):
        try:
            res = subprocess.run(
                [self.commander, "adapter", "list"],
                capture_output=True,
                text=True
            )
            return sn in res.stdout
        except Exception:
            return False