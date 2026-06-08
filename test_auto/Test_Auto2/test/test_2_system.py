import paramiko

def test_1_ssh_connection(pi_device):
    """Test case 1: Check if SSH connection succeeds or fails."""
    print("\n[TC1] Checking SSH connection...")
    ssh_client = pi_device.connect()
    
    assert ssh_client is not None, "❌ SSH connection failed (Client returned None)!"
    assert isinstance(ssh_client, paramiko.SSHClient), "❌ Connection object format is incorrect!"
    print("-> SSH connection actually successful!")
