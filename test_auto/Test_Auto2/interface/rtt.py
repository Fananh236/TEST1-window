import os
import signal
import subprocess
import time

from utils.jlink import _build_jlink_remote_server_cmd, _build_jlink_rtt_logger_cmd

class DeviceRTT:
    def __init__(self, serial_config, log_dir):
        self.serial_config = serial_config or {}

        # -----------------------------
        # Device info
        # -----------------------------
        self.device = "EFR32MG24BXXXF1536"
        self.ip = self._resolve_device_value("ip")
        self.sn = self._resolve_device_value("sn")

        # -----------------------------
        # Log directory
        # -----------------------------
        self.log_dir = os.path.abspath(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)

        # -----------------------------
        # Log files
        # -----------------------------
        self.jlink_server_log = os.path.join(self.log_dir, "JLinkRemoteServer.log")

        # RTT log (QUAN TRỌNG: log thật nằm ở đây)
        self.rtt_log_file = os.path.join(self.log_dir, "rtt_log.txt")

        # Debug log của RTT logger
        self.jlink_rtt_logger_log = os.path.join(self.log_dir, "JLinkRTTLogger.log")

        self.server_proc = None
        self.rtt_proc = None

        self.server_log_handle = None
        self.rtt_logger_handle = None

        self.stopped = False

    # --------------------------------------------------
    # Resolve config (multi-device support)
    # --------------------------------------------------
    def _resolve_device_value(self, field_name):
        if field_name in self.serial_config and self.serial_config.get(field_name):
            return self.serial_config[field_name]

        devices = self.serial_config.get("devices") or []
        if isinstance(devices, list):
            for device in devices:
                if isinstance(device, dict) and device.get(field_name):
                    return device[field_name]

        return None

 
    # --------------------------------------------------
    # Kill process safely
    # --------------------------------------------------
    def _terminate(self, proc):
        if not proc:
            return

        try:
            if os.name == "posix":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except Exception:
            pass

    # --------------------------------------------------
    # Start RTT
    # --------------------------------------------------
    def start_rtt(self):
        self.stopped = False

        # -----------------------------
        # Start JLink Remote Server
        # -----------------------------
        server_cmd = _build_jlink_remote_server_cmd(self.sn)



        self.server_log_handle = open(self.jlink_server_log, "a", buffering=1)

        self.server_proc = subprocess.Popen(
            server_cmd,
            stdout=self.server_log_handle,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid if os.name == "posix" else None,
        )

        print("[RTT] JLinkRemoteServer started")
        time.sleep(2)

        # -----------------------------
        # Start RTT Logger
        # -----------------------------
        rtt_cmd = _build_jlink_rtt_logger_cmd(self.device,self.ip,self.rtt_log_file)

        self.rtt_logger_handle = open(self.jlink_rtt_logger_log, "a", buffering=1)

        self.rtt_proc = subprocess.Popen(
            rtt_cmd,
            stdout=self.rtt_logger_handle,   # debug log
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid if os.name == "posix" else None,
        )

        print("[RTT] RTT Logger started")

        # Chờ RTT ready
        if not self.wait_rtt_ready(timeout=5):
            print("[RTT WARNING] No RTT data detected")

    # --------------------------------------------------
    # Stop RTT
    # --------------------------------------------------
    def stop_rtt(self):
        if self.stopped:
            return

        self.stopped = True

        print("[RTT] Stopping...")

        self._terminate(self.rtt_proc)
        self._terminate(self.server_proc)

        if self.server_log_handle:
            self.server_log_handle.close()

        if self.rtt_logger_handle:
            self.rtt_logger_handle.close()

    # --------------------------------------------------
    # Wait RTT data
    # --------------------------------------------------
    def wait_rtt_ready(self, timeout=5):
        """
        Check if RTT file receives data
        """
        end_time = time.time() + timeout

        while time.time() < end_time:
            if os.path.exists(self.rtt_log_file):
                if os.path.getsize(self.rtt_log_file) > 0:
                    print("[RTT] RTT data detected")
                    return True
            time.sleep(0.5)

        return False

    # --------------------------------------------------
    # Read RTT log
    # --------------------------------------------------
    def read_rtt_log(self):
        if not os.path.exists(self.rtt_log_file):
            return ""

        try:
            with open(self.rtt_log_file, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    # --------------------------------------------------
    # Verify RTT markers
    # --------------------------------------------------
    def verify_rtt_status(self, markers=None, timeout=5):
        if markers is None:
            markers = ["invokecommand", "light"]

        end_time = time.time() + timeout

        while time.time() < end_time:
            content = self.read_rtt_log().lower()

            for m in markers:
                if m.lower() in content:
                    return True

            time.sleep(0.5)

        return False
