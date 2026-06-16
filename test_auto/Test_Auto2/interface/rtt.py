import os
import signal
import subprocess
import time

from .jlink import build_jlink_remote_server_command, build_jlink_rtt_logger_command


class DeviceRTT:
    def __init__(self, serial_config, log_dir):
        self.serial_config = serial_config or {}
        self.device = self.serial_config.get("device", "").replace("IM48", "")
        self.ip = self._resolve_device_value("ip")
        self.log_dir = os.path.abspath(log_dir)
        self.sn = self._resolve_device_value("sn")
        self.log_file = os.path.join(self.log_dir, "rtt_log.txt")
        self.jlink_server_log = os.path.join(self.log_dir, "JLinkRemoteServer.log")

        self.server_proc = None
        self.rtt_proc = None
        self.server_log_file = None
        self.stopped = False

    def _resolve_device_value(self, field_name):
        if field_name in self.serial_config and self.serial_config.get(field_name):
            return self.serial_config[field_name]

        devices = self.serial_config.get("devices") or []
        if isinstance(devices, list):
            for device in devices:
                if isinstance(device, dict) and device.get(field_name):
                    return device[field_name]

        return None

    def _cleanup_processes(self):
        if os.name == "posix":
            subprocess.run(["pkill", "-f", "JLinkRemoteServer"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-f", "JLinkRTTLogger"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _terminate_process(self, proc):
        if proc is None:
            return
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except Exception:
            pass

    def start_rtt(self):
        self._cleanup_processes()

        server_cmd = build_jlink_remote_server_command(self.sn)
        self.server_log_file = open(self.jlink_server_log, "w")
        self.server_proc = subprocess.Popen(
            server_cmd,
            stdout=self.server_log_file,
            stderr=subprocess.STDOUT,
            cwd=self.log_dir,
            preexec_fn=os.setsid if os.name == "posix" else None,
        )

        time.sleep(2)

        rtt_cmd = build_jlink_rtt_logger_command(self.device, self.ip, self.log_file)
        self.rtt_proc = subprocess.Popen(
            rtt_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=self.log_dir,
            preexec_fn=os.setsid if os.name == "posix" else None,
        )

        time.sleep(2)

    def stop_rtt(self):
        if self.stopped:
            return
        self.stopped = True

        self._terminate_process(self.rtt_proc)
        self._terminate_process(self.server_proc)
        self._cleanup_processes()
        
        if self.server_log_file:
            self.server_log_file.close()
