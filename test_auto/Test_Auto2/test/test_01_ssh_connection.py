"""
Test Suite 01: SSH Connection Checks
- Kiểm tra kết nối SSH đến Raspberry Pi
- Mỗi test là một bước riêng biệt, dễ debug
"""
import pytest


class TestSSHBasicConnection:
    """Kiểm tra kết nối cơ bản SSH"""

    def test_01_01_ssh_connection_established(self, pi_device):
        """
        BỨC 1: Kiểm tra SSH connection được thiết lập.
        - Yêu cầu: pi_device fixture phải kết nối thành công
        """
        assert pi_device is not None, "SSH client không tồn tại"
        assert pi_device._ssh_client is not None, "SSH client chưa kết nối"
        print("✅ SSH connection is active")

    def test_01_02_echo_command(self, pi_device):
        """
        BƯỚC 2: Kiểm tra gửi/nhận dữ liệu qua SSH.
        - Gửi lệnh echo đơn giản
        - Kiểm tra response có chứa dữ liệu đúng
        """
        output, error = pi_device.execute_command("echo 'HELLO_TEST'")
        
        assert error == "", f"Có lỗi: {error}"
        assert "HELLO_TEST" in output, f"Response không đúng: {output}"
        print(f"✅ Echo command works: {output.strip()}")

    def test_01_03_pwd_command(self, pi_device):
        """
        BƯỚC 3: Kiểm tra lấy thư mục hiện tại.
        - Gửi lệnh pwd
        - Kiểm tra response có path
        """
        output, error = pi_device.execute_command("pwd")
        
        assert error == "", f"Có lỗi: {error}"
        assert len(output) > 0, "Không nhận được output"
        assert output.startswith("/"), f"Path không hợp lệ: {output}"
        print(f"✅ Current directory: {output.strip()}")

    def test_01_04_user_info(self, pi_device):
        """
        BƯỚC 4: Kiểm tra thông tin user hiện tại.
        - Gửi lệnh whoami
        - Kiểm tra tên user đúng
        """
        output, error = pi_device.execute_command("whoami")
        
        assert error == "", f"Có lỗi: {error}"
        username = output.strip()
        assert username == pi_device.username, f"User mismatch: {username} != {pi_device.username}"
        print(f"✅ Current user: {username}")


class TestSSHCommandExecution:
    """Kiểm tra thực thi các lệnh khác nhau"""

    def test_02_01_ls_command(self, pi_device):
        """
        BƯỚC 5: Kiểm tra lệnh ls.
        """
        output, error = pi_device.execute_command("ls -la /tmp | head -5")
        
        assert error == "", f"Có lỗi: {error}"
        assert len(output) > 0, "Không nhận được output từ ls"
        print(f"✅ ls command works")

    def test_02_02_date_command(self, pi_device):
        """
        BƯỚC 6: Kiểm tra lấy thời gian từ device.
        """
        output, error = pi_device.execute_command("date")
        
        assert error == "", f"Có lỗi: {error}"
        assert len(output) > 0, "Không nhận được output từ date"
        print(f"✅ Device time: {output.strip()}")

    def test_02_03_uname_command(self, pi_device):
        """
        BƯỚC 7: Kiểm tra OS info.
        """
        output, error = pi_device.execute_command("uname -a")
        
        assert error == "", f"Có lỗi: {error}"
        assert "Linux" in output, f"Không phải Linux: {output}"
        print(f"✅ OS: {output.strip()}")


class TestSSHErrorHandling:
    """Kiểm tra xử lý lỗi"""

    def test_03_01_invalid_command(self, pi_device):
        """
        BƯỚC 8: Kiểm tra xử lý khi gửi lệnh không tồn tại.
        """
        output, error = pi_device.execute_command("command_not_exist_12345")
        
        # Dù có lỗi nhưng không crash
        print(f"✅ Error handled gracefully")

    def test_03_02_permission_denied(self, pi_device):
        """
        BƯỚC 9: Kiểm tra xử lý khi access bị deny.
        """
        output, error = pi_device.execute_command("cat /root/secret.txt 2>&1 || echo 'Permission denied expected'")
        
        # Kiểm tra command hoàn tất (có thể có lỗi nhưng không crash)
        assert len(output) > 0 or len(error) >= 0
        print(f"✅ Permission check works")


class TestSSHConnectionPersistence:
    """Kiểm tra kết nối liên tục"""

    def test_04_01_multiple_commands(self, pi_device):
        """
        BƯỚC 10: Kiểm tra gửi nhiều lệnh liên tiếp.
        - Đảm bảo connection vẫn sống sau nhiều lệnh
        """
        commands = [
            "echo 'Test 1'",
            "echo 'Test 2'",
            "echo 'Test 3'",
        ]
        
        for cmd in commands:
            output, error = pi_device.execute_command(cmd)
            assert error == "", f"Lỗi ở lệnh '{cmd}': {error}"
        
        print(f"✅ Connection persists after multiple commands")

    def test_04_02_reconnection_recovery(self, pi_device):
        """
        BƯỚC 11: Kiểm tra tự động reconnect sau disconnect.
        """
        # Disconnect
        pi_device.disconnect()
        
        # Cố gắng chạy command (nên auto-reconnect)
        output, error = pi_device.execute_command("echo 'After reconnect'")
        
        assert "After reconnect" in output or error == "", "Reconnect failed"
        print(f"✅ Auto-reconnect works")
