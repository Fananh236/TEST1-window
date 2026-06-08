import os
import json
import subprocess
import time
import signal


class DeviceFlasher:
    """
    Clean RTT logging (no noisy stdout)
    """

    def __init__(self, config_path="config.json"):
        current_dir = os.path.abspath(os.path.dirname(__file__))
        project_root = os.path.dirname(current_dir)
        config_file = os.path.join(project_root, config_path)

        print("[INIT] Loading config:", config_file)

        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config not found: {config_file}")

        with open(config_file, "r") as f:
            data = json.load(f)

        cfg = data.get("serial_config", {})

        self.device = cfg.get("device").replace("IM48", "")
        self.sn = cfg.get("sn")
        self.ip = cfg.get("ip") 
        if not self.sn:
            raise Exception("❌ Missing SN")

        print(f"[INIT] Device: {self.device}")
        print(f"[INIT] SN: {self.sn}")

        log_dir = os.path.join(project_root, "Log")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "rtt_log.txt")

        print(f"[INIT] Log file: {self.log_file}")

        self.server_proc = None
        self.rtt_proc = None
        self.stopped = False

    # ================= START =================
    def start_rtt(self):
        print("\n[RTT] STARTING...")

        # ✅ cleanup old
        subprocess.run("pkill -f JLinkRemoteServer", shell=True)
        subprocess.run("pkill -f JLinkRTTLogger", shell=True)

        # ================= SERVER =================
        server_cmd = [ 
                      "JLinkRemoteServer",
                      "-SelectEmuBySN",
                      self.sn
            # "JLinkExe",
            
            # "-device", self.device,
            # "-if", "JTAG",
            # "-speed", "4000",
            # "autoconnect","1",
            # "-IP", "192.168.0.10",
            # "-RTTTelnetPort", "19020"
                 
            
        ]

        self.server_proc = subprocess.Popen(
            server_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )

        time.sleep(2)

        if self.server_proc.poll() is None:
            print("[RTT] Server ✅")
        else:
            print("[RTT] Server ❌")
            return

        # ================= RTT LOGGER =================
        rtt_cmd = [
            "JLinkRTTLogger",
            "-Device", self.device,
            "-If", "SWD",
            "-Speed", "4000",
            "-RTTChannel", "0",
            "-IP", "192.168.0.10",
            "-RTTTelnetPort", "19020",
            "-Silent",                  
            self.log_file
        ]

        self.rtt_proc = subprocess.Popen(
            rtt_cmd,
            stdout=subprocess.DEVNULL,   # ✅ HIDE OUTPUT
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )

        time.sleep(2)

        if self.rtt_proc.poll() is None:
            print("[RTT] Logging ✅")
        else:
            print("[RTT] Logger ❌")

        print("[RTT] READY 🚀\n")

    # ================= STOP =================
    def stop_rtt(self):
        if self.stopped:
            return
        self.stopped = True

        print("\n[RTT] STOPPING...")

        if self.rtt_proc:
            try:
                os.killpg(os.getpgid(self.rtt_proc.pid), signal.SIGKILL)
                print("[RTT] Logger stopped ✅")
            except Exception:
                pass

        if self.server_proc:
            try:
                os.killpg(os.getpgid(self.server_proc.pid), signal.SIGKILL)
                print("[RTT] Server stopped ✅")
            except Exception:
                pass

        subprocess.run("pkill -f JLinkRemoteServer", shell=True)
        subprocess.run("pkill -f JLinkRTTLogger", shell=True)

    # ================= RUN =================
    def run(self):
        print("===== RTT TEST =====")

        self.start_rtt()

        print("[INFO] Capturing 10s...")
        time.sleep(10)

        self.stop_rtt()

        print("✅ DONE")