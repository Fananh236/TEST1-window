import subprocess
import os
import shlex


class DeviceHelper:
    def __init__(self, commander_path, device):
        self.commander = commander_path
        self.device = device

    # =========================
    # CORE EXECUTOR
    # =========================
    def _run(self, cmd, timeout=60):
        try:
            print(f"CMD: {' '.join(cmd)}")

            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            stdout = res.stdout.strip()
            stderr = res.stderr.strip()

            if res.returncode != 0:
                print(f"❌ FAIL ({res.returncode})")
                print(stderr)
                return False, stdout, stderr

            return True, stdout, stderr

        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {' '.join(cmd)}")
            return False, "", "timeout"

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False, "", str(e)

    # =========================
    # COMMAND BUILDER
    # =========================
    def _build_cmd(self, action, sn=None, ip=None, extra=None):
        cmd = [self.commander, action]

        if extra:
            cmd += extra

        if sn:
            cmd += ["-s", sn]

        if ip:
            cmd += ["--ip", ip]

        cmd += ["--device", self.device]

        return cmd

    # =========================
    # ACTIONS
    # =========================
    def mass_erase(self, sn=None, ip=None, retry=2):
        cmd = self._build_cmd("device", sn, ip, ["masserase"])
        return self._retry(cmd, retry)

    def reset(self, sn=None, ip=None, retry=2):
        cmd = self._build_cmd("device", sn, ip, ["reset"])
        return self._retry(cmd, retry)

    def flash(self, firmware_path, sn=None, ip=None, retry=2):
        if not firmware_path or not os.path.exists(firmware_path):
            print(f"❌ Firmware not found: {firmware_path}")
            return False, "", "invalid firmware"

        cmd = [self.commander, "flash", firmware_path]

        if sn:
            cmd += ["-s", sn]

        if ip:
            cmd += ["--ip", ip]

        cmd += ["--device", self.device]

        return self._retry(cmd, retry)

    # =========================
    # RETRY WRAPPER
    # =========================
    def _retry(self, cmd, retry):
        for i in range(retry):
            ok, out, err = self._run(cmd)

            if ok:
                return True, out, err

            print(f"🔁 Retry {i+1}/{retry}")

        return False, out, err

    # =========================
    # DEVICE CHECK
    # =========================
    def is_connected(self, sn):
        try:
            res = subprocess.run(
                [self.commander, "adapter", "list"],
                capture_output=True,
                text=True
            )

            lines = res.stdout.splitlines()

            for line in lines:
                if sn in line:
                    return True

            return False

        except Exception:
            return False