def run_chip_tool_cmd(pi_device, arguments):
    """Wrapper function to run chip-tool command."""
    full_cmd = f"echo '{pi_device.password}' | sudo -S {pi_device.chip_tool_path} {arguments}"
    return pi_device.execute_command(full_cmd)

def cleanup_kvs(pi_device):
    """Dedicated function to clean up KVS."""
    cmd = f"echo '{pi_device.password}' | sudo -S rm -rf /tmp/chip_*"
    return pi_device.execute_command(cmd)