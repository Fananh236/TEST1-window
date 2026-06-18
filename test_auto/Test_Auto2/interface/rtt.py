import os
import signal
import subprocess
import time
import threading

from ..utils.jlink import (
    build_jlink_remote_server_command,
    build_jlink_rtt_logger_command,
)


class DeviceRTT:
    def __init__(self, serial_config, log_dir):
        self.serial_config = serial_config or {}

        # Device info
        self.device = self.serial_config.get("device", "").replace("IM48", "")
        self.ip = self._resolve_device_value("ip")
        self.sn = self._resolve_device_value("sn")

        # Log directory (per-instance)
        self.log_dir = os.path.abspath(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)

        # Log files
        self.jlink_server_log = os.path.join(self.log_dir, "JLinkRemoteServer.log")
        
        # Project-level Log directory for RTT outputs (ensure RTT goes to project Log/)
        project_log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Log"))
        
        os.makedirs(project_log_dir, exist_ok=True)
        # expose project log dir on the instance
        self.project_log_dir = project_log_dir

        # Unified RTT log filename used across tools -> placed in project Log/
        self.rtt_log_file = os.path.join(self.project_log_dir, "rtt_log.txt")
        
        # Logger for the JLinkRTTLogger process (captures stdout/stderr)
        # place the JLinkRTTLogger debug log in the project Log dir so errors are visible
        self.jlink_rtt_logger_log = os.path.join(self.project_log_dir, "JLinkRTTLogger.log")
        self.jlink_rtt_logger_handle = None
        # Tail thread to extract RTT output from the JLinkRTTLogger debug log
        self._tail_thread = None
        self._tail_stop = threading.Event()

        # Process handlers
        self.server_proc = None
        self.rtt_proc = None
        self.server_log_file = None

        self.stopped = False

    # --------------------------------------------------
    # Resolve config value (support multi-device config)
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
    # Cleanup fallback (avoid using in multi-device)
    # --------------------------------------------------
    def _cleanup_processes(self):
        if os.name == "posix":
            subprocess.run(
                ["pkill", "-f", "JLinkRemoteServer"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["pkill", "-f", "JLinkRTTLogger"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    # --------------------------------------------------
    # Kill specific process safely
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Start RTT logging
    # --------------------------------------------------
    def start_rtt(self):
        # ⚠️ optional: disable nếu bạn chạy multi-device
        self._cleanup_processes()

        # ---- Start JLink Remote Server ----
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

        # ---- Start RTT Logger ----
        rtt_cmd = build_jlink_rtt_logger_command(
            self.device,
            self.ip,
            self.rtt_log_file,
        )

        # Capture JLinkRTTLogger stdout/stderr to file for debugging
        try:
            self.jlink_rtt_logger_handle = open(self.jlink_rtt_logger_log, "w", encoding="utf-8")
        except Exception:
            self.jlink_rtt_logger_handle = None

        self.rtt_proc = subprocess.Popen(
            rtt_cmd,
            stdout=self.jlink_rtt_logger_handle or subprocess.DEVNULL,
            stderr=subprocess.STDOUT if self.jlink_rtt_logger_handle else subprocess.DEVNULL,
            cwd=self.project_log_dir,
            preexec_fn=os.setsid if os.name == "posix" else None,
        )

        time.sleep(2)

        # Start a tailing thread that copies relevant RTT output from the debug log
        # into the canonical rtt_log_file so tests and tools can read it.
        def _tail_debug_log():
            try:
                with open(self.jlink_rtt_logger_log, "r", encoding="utf-8", errors="ignore") as src:
                    # seek to end of file to only capture new writes
                    src.seek(0, os.SEEK_END)
                    while not self._tail_stop.is_set():
                        line = src.readline()
                        if not line:
                            time.sleep(0.1)
                            continue
                        # Optionally filter lines; here we append all lines to RTT file
                        try:
                            with open(self.rtt_log_file, "a", encoding="utf-8", errors="ignore") as dst:
                                dst.write(line)
                        except Exception:
                            pass
            except Exception:
                return

        self._tail_stop.clear()
        self._tail_thread = threading.Thread(target=_tail_debug_log, daemon=True)
        self._tail_thread.start()

    # --------------------------------------------------
    # Stop RTT
    # --------------------------------------------------
    def stop_rtt(self):
        if self.stopped:
            return

        self.stopped = True

        # Stop RTT logger
        self._terminate_process(self.rtt_proc)

        # Stop server
        self._terminate_process(self.server_proc)

        # ⚠️ fallback cleanup
        self._cleanup_processes()

        # Close log file
        if self.server_log_file:
            self.server_log_file.close()
        if self.jlink_rtt_logger_handle:
            try:
                self.jlink_rtt_logger_handle.close()
            except Exception:
                pass
        # Stop tail thread
        try:
            if self._tail_thread and self._tail_thread.is_alive():
                self._tail_stop.set()
                self._tail_thread.join(timeout=2)
        except Exception:
            pass

    # --------------------------------------------------
    # Helper: get log paths (useful for pytest/report)
    # --------------------------------------------------
    def get_log_files(self):
        return {
            "server_log": self.jlink_server_log,
            "rtt_log": self.rtt_log_file,
        }