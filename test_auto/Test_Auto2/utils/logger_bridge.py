import subprocess
import os
import signal

class LoggerBridge:
    def __init__(self, sn, log_dir="Log"):
        self.sn = sn
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, f"log_{sn}.txt")
        self.process = None
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def start_logging(self):
        """Khởi động tiến trình lấy log RTT ngầm."""
        # Sử dụng JLinkRTTLogger để lấy log qua Serial Number (-s)
        cmd = [
            "JLinkRTTLogger",
            "-s", self.sn,           # Kết nối qua SN thay vì IP
            "-device", "EFR32MG24B220F1536IM48",
            "-if", "swd",
            "-speed", "4000",
            "-RTTChannel", "0",
            self.log_file
        ]
        
        # Chạy ngầm hoàn toàn, không output ra terminal
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )
        return self.log_file

    def stop_logging(self):
        """Dừng ghi log."""
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            self.process = None