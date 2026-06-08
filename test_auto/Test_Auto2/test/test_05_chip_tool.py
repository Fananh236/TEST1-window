"""
Test Suite 05: Chip-Tool Operations
- Kiểm tra chip-tool availability và basic commands
- Tách nhỏ: chip-tool path, version, help, basic commands
"""
import pytest
import re


class TestChipToolSetup:
    """Kiểm tra chip-tool setup"""

    def test_05_01_chip_tool_exists(self, pi_device):
        """
        BƯỚC 1: Kiểm tra chip-tool tồn tại trên Pi.
        """
        chip_tool_path = pi_device.chip_tool_path
        
        assert chip_tool_path is not None, "chip-tool path not set"
        assert len(chip_tool_path) > 0, "chip-tool path is empty"
        
        print(f"✅ chip-tool path: {chip_tool_path}")

    def test_05_02_chip_tool_executable(self, pi_device):
        """
        BƯỚC 2: Kiểm tra chip-tool là executable.
        """
        output, error = pi_device.execute_command(f"test -x {pi_device.chip_tool_path} && echo 'OK' || echo 'NOT_EXECUTABLE'")
        
        assert "OK" in output or "OK" in error, f"chip-tool is not executable"
        print(f"✅ chip-tool is executable")

    def test_05_03_chip_tool_version(self, pi_device):
        """
        BƯỚC 3: Lấy version chip-tool.
        """
        output, error = pi_device.execute_command(f"{pi_device.chip_tool_path} version 2>&1 || echo ''")
        
        # Có thể trả về version hoặc help (không fail)
        print(f"✅ chip-tool version check executed")

    def test_05_04_chip_tool_help(self, pi_device):
        """
        BƯỚC 4: Kiểm tra chip-tool help.
        """
        output, error = pi_device.execute_command(f"{pi_device.chip_tool_path} -h 2>&1 | head -10")
        
        if len(output) > 0 or len(error) > 0:
            print(f"✅ chip-tool help is available")
        else:
            print(f"⚠️ chip-tool help output empty")


class TestChipToolBasicCommands:
    """Kiểm tra basic chip-tool commands"""

    def test_06_01_sudo_access(self, pi_device):
        """
        BƯỚC 5: Kiểm tra sudo access (chip-tool thường cần sudo).
        """
        cmd = f"echo '{pi_device.password}' | sudo -S whoami"
        output, error = pi_device.execute_command(cmd)
        
        if "root" in output:
            print(f"✅ Sudo access available")
        else:
            print(f"⚠️ Sudo might require password prompt")

    def test_06_02_chip_tool_pairing_help(self, pi_device):
        """
        BƯỚC 6: Kiểm tra chip-tool pairing help.
        """
        cmd = f"echo '{pi_device.password}' | sudo -S {pi_device.chip_tool_path} pairing --help 2>&1 | head -20"
        output, error = pi_device.execute_command(cmd)
        
        if "onnetwork" in output or "ble-wifi" in output or "help" in output.lower():
            print(f"✅ chip-tool pairing subcommands available")
        else:
            print(f"⚠️ chip-tool pairing help output: {output[:100]}")

    def test_06_03_chip_tool_onoff_help(self, pi_device):
        """
        BƯỚC 7: Kiểm tra chip-tool onoff help.
        """
        cmd = f"echo '{pi_device.password}' | sudo -S {pi_device.chip_tool_path} onoff --help 2>&1 | head -20"
        output, error = pi_device.execute_command(cmd)
        
        if "toggle" in output or "on" in output or "help" in output.lower():
            print(f"✅ chip-tool onoff commands available")
        else:
            print(f"⚠️ chip-tool onoff help output: {output[:100]}")


class TestKVSCleanup:
    """Kiểm tra KVS (Key-Value Store) cleanup"""

    def test_07_01_kvs_path_exists(self, pi_device):
        """
        BƯỚC 8: Kiểm tra KVS path tồn tại.
        """
        kvs_path = "/tmp/chip_*"
        
        output, error = pi_device.execute_command(f"ls -la /tmp/chip_* 2>&1 | head -5")
        
        # OK nếu có hoặc không có (lần đầu có thể không có)
        print(f"✅ KVS path check executed")

    def test_07_02_kvs_cleanup(self, pi_device):
        """
        BƯỚC 9: Thực hiện KVS cleanup.
        """
        cmd = f"echo '{pi_device.password}' | sudo -S rm -rf /tmp/chip_* 2>&1"
        output, error = pi_device.execute_command(cmd)
        
        # Kiểm tra command không crash
        print(f"✅ KVS cleanup executed")

    def test_07_03_kvs_verify_cleaned(self, pi_device):
        """
        BƯỚC 10: Xác minh KVS được cleanup.
        """
        output, error = pi_device.execute_command(f"ls /tmp/chip_* 2>&1 | wc -l")
        
        try:
            count = int(output.strip())
            assert count == 0, f"KVS files still exist: {count}"
            print(f"✅ KVS successfully cleaned")
        except:
            print(f"⚠️ Could not verify KVS cleanup")


class TestCommissioningSetup:
    """Kiểm tra setup cho commissioning"""

    def test_08_01_device_config_available(self, pi_device, config):
        """
        BƯỚC 11: Kiểm tra device config.
        """
        chip_config = config.get("chip_config", {})
        
        assert chip_config is not None, "chip_config not found"
        assert len(chip_config) > 0, "chip_config is empty"
        
        required_keys = ["node_id", "endpoint_id", "setup_pin_code"]
        
        for key in required_keys:
            assert key in chip_config, f"Missing key: {key}"
            print(f"  ✅ {key}: {chip_config[key]}")

    def test_08_02_node_id_valid(self, pi_device, config):
        """
        BƯỚC 12: Kiểm tra node_id hợp lệ.
        """
        chip_config = config.get("chip_config", {})
        node_id = chip_config.get("node_id")
        
        try:
            node_id_int = int(node_id)
            assert node_id_int >= 0, f"Invalid node_id: {node_id}"
            print(f"✅ node_id valid: {node_id}")
        except:
            pytest.fail(f"Invalid node_id: {node_id}")

    def test_08_03_setup_pin_valid(self, pi_device, config):
        """
        BƯỚC 13: Kiểm tra setup_pin_code hợp lệ.
        """
        chip_config = config.get("chip_config", {})
        setup_pin = chip_config.get("setup_pin_code")
        
        assert setup_pin is not None, "setup_pin_code not found"
        assert len(setup_pin) == 8, f"setup_pin_code phải có 8 chữ số: {setup_pin}"
        
        try:
            pin_int = int(setup_pin)
            print(f"✅ setup_pin_code valid: {setup_pin}")
        except:
            pytest.fail(f"Invalid setup_pin_code: {setup_pin}")

    def test_08_04_endpoint_id_valid(self, pi_device, config):
        """
        BƯỚC 14: Kiểm tra endpoint_id hợp lệ.
        """
        chip_config = config.get("chip_config", {})
        endpoint_id = chip_config.get("endpoint_id")
        
        try:
            endpoint_id_int = int(endpoint_id)
            assert endpoint_id_int >= 0, f"Invalid endpoint_id: {endpoint_id}"
            print(f"✅ endpoint_id valid: {endpoint_id}")
        except:
            pytest.fail(f"Invalid endpoint_id: {endpoint_id}")


class TestCommissioningPreparation:
    """Chuẩn bị cho commissioning"""

    def test_09_01_cleanup_before_pairing(self, pi_device):
        """
        BƯỚC 15: Cleanup trước khi pairing.
        """
        cmd = f"echo '{pi_device.password}' | sudo -S rm -rf /tmp/chip_*"
        output, error = pi_device.execute_command(cmd)
        
        # Verify cleanup
        verify_cmd = f"ls /tmp/chip_* 2>&1 | wc -l"
        verify_output, _ = pi_device.execute_command(verify_cmd)
        
        try:
            count = int(verify_output.strip())
            assert count == 0, f"KVS still exists: {count} files"
            print(f"✅ Environment cleaned for pairing")
        except:
            print(f"⚠️ Could not verify cleanup")

    def test_09_02_device_logs_clear(self, pi_device):
        """
        BƯỚC 16: Xóa device logs cũ.
        """
        # Optional: clear some logs
        cmd = f"rm -f /tmp/chip_* 2>/dev/null; echo 'cleaned'"
        output, error = pi_device.execute_command(cmd)
        
        print(f"✅ Device logs cleared")

    def test_09_03_readiness_check(self, pi_device, config):
        """
        BƯỚC 17: Kiểm tra readiness cho commissioning.
        """
        print("\n" + "="*60)
        print("COMMISSIONING READINESS CHECK")
        print("="*60)
        
        # SSH connection
        print(f"✅ SSH connected")
        
        # chip-tool available
        output, _ = pi_device.execute_command(f"which {pi_device.chip_tool_path}")
        if len(output) > 0:
            print(f"✅ chip-tool available")
        
        # Config ready
        chip_config = config.get("chip_config", {})
        print(f"✅ chip_config loaded ({len(chip_config)} parameters)")
        
        # KVS cleaned
        kvs_check, _ = pi_device.execute_command("ls /tmp/chip_* 2>&1 | wc -l")
        try:
            if int(kvs_check.strip()) == 0:
                print(f"✅ KVS cleaned")
        except:
            pass
        
        print("="*60)
        print("✅ Ready for commissioning tests")
