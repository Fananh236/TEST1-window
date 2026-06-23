import os
import signal
import subprocess
import threading
import time
import queue
from typing import Optional

from utils.jlink import _build_jlink_remote_server_cmd, _build_jlink_rtt_logger_cmd


class DeviceRTT:
    """Realtime RTT reader that starts JLinkRTTLogger and provides wait_for_command().

    - start_rtt(): launch processes and reader thread
    - stop_rtt(): stop processes and thread
    - wait_for_command(action, timeout): wait for receipt->start->done
    """

    def __init__(self, serial_config, log_dir):
        self.serial_config = serial_config or {}

        # device info
        self.device = self._resolve_device_value("device") or "EFR32MG24BXXXF1536"
        self.ip = self._resolve_device_value("ip")
        self.sn = self._resolve_device_value("sn")

        # log paths (legacy/debug)
        self.log_dir = os.path.abspath(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        self.jlink_server_log = os.path.join(self.log_dir, "JLinkRemoteServer.log")
        self.rtt_log_file = os.path.join(self.log_dir, "rtt_log.txt")
        self.jlink_rtt_logger_log = os.path.join(self.log_dir, "JLinkRTTLogger.log")

        # processes
        self.server_proc: Optional[subprocess.Popen] = None
        self.rtt_proc: Optional[subprocess.Popen] = None

        # realtime queue + reader
        self._line_queue: "queue.Queue[str]" = queue.Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def _resolve_device_value(self, field_name):
        if field_name in self.serial_config and self.serial_config.get(field_name):
            return self.serial_config[field_name]

        devices = self.serial_config.get("devices") or []
        if isinstance(devices, list):
            for device in devices:
                if isinstance(device, dict) and device.get(field_name):
                    return device[field_name]

        return None

    def _terminate(self, proc: Optional[subprocess.Popen]):
        if not proc:
            return
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except Exception:
            pass

    def start_rtt(self, timeout: float = 5.0):
        """Start JLinkRemoteServer and JLinkRTTLogger; spawn reader thread."""
        with self._lock:
            self._stop_event.clear()

            # start server (best-effort)
            server_cmd = _build_jlink_remote_server_cmd(self.sn or "")
            try:
                self.server_log_handle = open(self.jlink_server_log, "a", buffering=1, encoding="utf-8", errors="ignore")
            except Exception:
                self.server_log_handle = None
            try:
                self.server_proc = subprocess.Popen(
                    server_cmd,
                    stdout=self.server_log_handle or subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid if os.name == "posix" else None,
                )
            except Exception:
                self.server_proc = None

            # start JLinkRTTLogger with stdout pipe for realtime consumption
            rtt_cmd = _build_jlink_rtt_logger_cmd(self.device, self.ip or "", self.rtt_log_file)
            self.rtt_proc = subprocess.Popen(
                rtt_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                preexec_fn=os.setsid if os.name == "posix" else None,
            )

            # reader thread
            if self.rtt_proc and self.rtt_proc.stdout:
                self._reader_thread = threading.Thread(target=self._reader, args=(self.rtt_proc.stdout,), daemon=True)
                self._reader_thread.start()

            # wait for any output briefly
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    line = self._line_queue.get_nowait()
                    self._line_queue.put_nowait(line)
                    break
                except queue.Empty:
                    time.sleep(0.05)

    def stop_rtt(self):
        with self._lock:
            self._stop_event.set()
            if self.rtt_proc:
                self._terminate(self.rtt_proc)
                self.rtt_proc = None
            if self.server_proc:
                self._terminate(self.server_proc)
                self.server_proc = None
            if self._reader_thread and self._reader_thread.is_alive():
                self._reader_thread.join(timeout=1.0)
            self._reader_thread = None
            try:
                if hasattr(self, 'server_log_handle') and self.server_log_handle:
                    self.server_log_handle.close()
            except Exception:
                pass

    def _reader(self, stdout_pipe):
        """Read subprocess stdout line-by-line and enqueue raw lines; append to debug log."""
        try:
            with open(self.jlink_rtt_logger_log, "a", buffering=1, encoding="utf-8", errors="ignore") as dbg_f:
                while not self._stop_event.is_set():
                    line = stdout_pipe.readline()
                    if line == "" or line is None:
                        if self.rtt_proc and self.rtt_proc.poll() is not None:
                            break
                        time.sleep(0.01)
                        continue
                    raw = line.rstrip("\n")
                    dbg_f.write(raw + "\n")
                    try:
                        self._line_queue.put_nowait(raw)
                    except queue.Full:
                        pass
        except Exception:
            pass

    def wait_rtt_ready(self, timeout: float = 5.0) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            try:
                _ = self._line_queue.get(timeout=0.5)
                self._line_queue.put_nowait(_)
                return True
            except queue.Empty:
                continue
        return False

    def read_rtt_log(self) -> str:
        if not os.path.exists(self.rtt_log_file):
            return ""
        try:
            with open(self.rtt_log_file, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    def wait_for_command(self, action: str, timeout: float) -> bool:
        """Wait for receipt -> start -> done sequence for given action.

        action: 'on' | 'off' | 'toggle'
        """
        action = (action or "").lower()
        if action not in ("on", "off", "toggle"):
            raise ValueError("action must be 'on', 'off' or 'toggle'")

        # import unified pattern detector
        from utils.common import detect_pattern

        receipt_seen = False
        start_seen = False
        start_type = None

        end_time = time.time() + timeout
        while time.time() < end_time:
            remaining = end_time - time.time()
            try:
                line = self._line_queue.get(timeout=min(0.5, max(0.05, remaining)))
            except queue.Empty:
                continue

            # receipt -> start -> done
            if not receipt_seen and detect_pattern(line, "receipt"):
                receipt_seen = True
                print(f"[RTT DEBUG] receipt detected: {line}")
                continue

            if receipt_seen and not start_seen:
                if detect_pattern(line, "on_start") and action in ("on", "toggle"):
                    start_seen = True
                    start_type = "on"
                    print(f"[RTT DEBUG] start(on) detected: {line}")
                    continue
                if detect_pattern(line, "off_start") and action in ("off", "toggle"):
                    start_seen = True
                    start_type = "off"
                    print(f"[RTT DEBUG] start(off) detected: {line}")
                    continue

            if start_seen:
                if start_type == "on" and detect_pattern(line, "on_done"):
                    print(f"[RTT DEBUG] done(on) detected: {line}")
                    return True
                if start_type == "off" and detect_pattern(line, "off_done"):
                    print(f"[RTT DEBUG] done(off) detected: {line}")
                    return True

            # If a new receipt arrives before start, treat as reset for a new command
            if receipt_seen and not start_seen and detect_pattern(line, "receipt"):
                receipt_seen = True
                start_seen = False
                start_type = None
                print(f"[RTT DEBUG] new receipt detected (reset): {line}")

        return False
