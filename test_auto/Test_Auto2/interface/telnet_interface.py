import subprocess
import os
import signal

from interface.commander import CommanderInterface

class JLinkLogBridge:
    def __init__(self, ip_address, device, log_dir):
        self.ip_address = ip_address
        self.device = device
        self.log_file = os.path.join(log_dir, f"log_{ip_address}.txt")
        self.process = None

    def start_logging(self):
        """Khởi động tiến trình lấy log RTT qua IP"""
        if self.process:
            return
        
        # Lệnh lấy log từ J-Link Remote Server qua IP
        cmd = [
            "JLinkRTTLogger",
            "-IPAddr", self.ip_address,
            "-device", self.device,
            "-if", "swd",
            "-speed", "4000",
            "-RTTChannel", "0",
            self.log_file
        ]
        
        # Chạy ngầm
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid # Để quản lý tiến trình dễ hơn
        )
        print(f"-> Logging started for {self.ip_address} into {self.log_file}")

    def stop_logging(self):
        """Dừng tiến trình lấy log"""
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process = None
            print(f"-> Logging stopped for {self.ip_address}")
            

            