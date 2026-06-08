import pytest
import time 

def test_pi_ssh_connection(pi_device):
    """Check if SSH connection is successful."""
    try:
        # Simplest 'echo' command to test response
        output, _ = pi_device.execute_command("echo 'OK'")
        assert "OK" in output
        print("\n✅ SSH connected successfully.")
    except Exception as e:
        pytest.fail(f"❌ Failed to connect SSH to Pi: {e}")

def test_pi_internet_access(pi_device):
    """Check if Pi has internet access."""
    # Try pinging Google DNS
    output, _ = pi_device.execute_command("ping -c 1 8.8.8.8")
    assert "1 received" in output, "❌ Pi has no internet/network connection!"
    print("\n✅ Pi has network connection (Internet OK).")
    
    
def test_2_execute_df_command(pi_device):
    """Test case 2: Run [df -h] command to check success or failure."""
    print("\n[TC2] Sending 'df -h' command to Pi...")
    stdout, stderr = pi_device.execute_command("df -h")
    
    assert stderr == "", f"❌ Running 'df -h' error: {stderr}"
    assert stdout != "", "❌ Running 'df -h' successful but returned no data (Empty)!"
    assert "Filesystem" in stdout or "Use%" in stdout, "❌ Output format of 'df -h' command is incorrect!"
    
    print("\n--- LOG DF -H ---")
    print(stdout)
    print("-----------------")
    print("-> 'df -h' command ran successfully! Detailed disk usage response is good.")

def test_chip_tool_availability(pi_device):
    """Check if chip-tool is installed and can be run."""
    # Command to check version to confirm file exists
    output, _ = pi_device.execute_command(f"{pi_device.chip_tool_path} --version")
    assert "help" in output or "version" in output.lower(), "❌ chip-tool not found or cannot be run!"
    print(f"\n✅ chip-tool at '{pi_device.chip_tool_path}' is ready to operate.")
    
def test_reboot_and_reconnect(pi_device):
    """[TC0.4] Check Pi's reboot and automatic reconnection capability."""
    print("\n⏳ Sending REBOOT command to Raspberry Pi...")
    
    # 1. Send reboot command
    # Use 'sudo reboot' command and close SSH connection immediately
    reboot_cmd = f"echo '{pi_device.password}' | sudo -S reboot"
    try:
        pi_device.execute_command(reboot_cmd)
    except:
        # Reboot command usually causes 'EOFError' because SSH is closed, 
        # so we catch this exception and consider the command sent successfully.
        pass
    
    # 2. Disconnect current connection to refresh the object
    pi_device.disconnect()
    
    # 3. Wait for Pi to restart
    print("⏳ Waiting for Pi to restart (expected 40-60s)...")
    time.sleep(40) # Minimum wait of 40s
    
    max_retries = 10
    connected = False
    for i in range(max_retries):
        try:
            # Try reconnecting and running a simple command
            pi_device._ssh_client = None # Reset client to create a new one
            output, _ = pi_device.execute_command("echo 'Reconnected'")
            if "Reconnected" in output:
                connected = True
                print(f"\n✅ Pi is back online after {i*5} extra seconds of waiting!")
                break
        except:
            time.sleep(5) # Retry every 5s
            
    assert connected, "❌ Timeout: Pi did not respond after reboot!"    