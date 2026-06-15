import time
import threading
import os
from utils.log_verifier import watch_logs_realtime

def simulate_appends():
    pi_log = r"c:\Users\phanh\Downloads\TEST1-window\test_auto\Test_Auto2\Log\pi_connection.log"
    rtt_log = r"c:\Users\phanh\Downloads\TEST1-window\test_auto\Test_Auto2\-RTTTelnetPort"
    
    # Wait for the monitor to start
    time.sleep(1)
    
    print("\n--- Simulating Realtime Command 1: onoff on 1 1 ---")
    with open(pi_log, "a", encoding="utf-8") as f:
        f.write("2026-06-15 18:00:00,000 - INFO - --- EXECUTE COMMAND: chip-tool onoff on 1 1 ---\n")
    
    time.sleep(0.5)
    with open(rtt_log, "a", encoding="utf-8") as f:
        f.write("[00:02:00.000][silabs ]Turning light On\n")
        
    time.sleep(1.5)
    
    print("\n--- Simulating Realtime Command 2: onoff off 1 1 ---")
    with open(pi_log, "a", encoding="utf-8") as f:
        f.write("2026-06-15 18:00:02,000 - INFO - --- EXECUTE COMMAND: chip-tool onoff off 1 1 ---\n")
        
    time.sleep(0.5)
    with open(rtt_log, "a", encoding="utf-8") as f:
        f.write("[00:02:02.000][silabs ]Turning light Off\n")

if __name__ == "__main__":
    # Start simulating in background thread
    t = threading.Thread(target=simulate_appends, daemon=True)
    t.start()
    
    # Start the monitor for 5 seconds to capture the events
    watch_logs_realtime(duration_seconds=5, poll_interval=0.2)
