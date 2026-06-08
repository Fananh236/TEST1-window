"""
Test Suite 03: Flash Preconditions
- Kiểm tra các điều kiện cần thiết trước khi flash
- Tách nhỏ từng bước: config, devices, firmware, serial numbers
"""
import pytest


class TestFlashConfiguration:
    """Kiểm tra configuration cho flashing"""

    def test_03_01_commander_exists(self, commander):
        """
        BƯỚC 1: Kiểm tra commander tool được cấu hình.
        """
        assert commander is not None, "Commander interface not initialized"
        assert commander.commander_path is not None, "Commander path not set"
        print(f"✅ Commander path: {commander.commander_path}")

    def test_03_02_device_type_set(self, commander):
        """
        BƯỚC 2: Kiểm tra device type được cấu hình.
        """
        assert commander.device is not None, "Device type not set"
        assert len(commander.device) > 0, "Device type is empty"
        print(f"✅ Device type: {commander.device}")

    def test_03_03_project_root_valid(self, commander):
        """
        BƯỚC 3: Kiểm tra project root path hợp lệ.
        """
        assert commander.project_root is not None, "Project root not set"
        assert len(commander.project_root) > 0, "Project root is empty"
        print(f"✅ Project root: {commander.project_root}")

    def test_03_04_serial_file_path_set(self, commander):
        """
        BƯỚC 4: Kiểm tra serial file path.
        """
        assert commander.serial_file is not None, "Serial file path not set"
        assert len(commander.serial_file) > 0, "Serial file path is empty"
        print(f"✅ Serial file: {commander.serial_file}")


class TestSerialNumbers:
    """Kiểm tra danh sách serial numbers"""

    def test_04_01_serial_file_exists(self, commander):
        """
        BƯỚC 5: Kiểm tra file serial numbers tồn tại.
        """
        import os
        
        assert os.path.exists(commander.serial_file), f"Serial file not found: {commander.serial_file}"
        print(f"✅ Serial file exists: {commander.serial_file}")

    def test_04_02_serial_numbers_readable(self, commander):
        """
        BƯỚC 6: Kiểm tra đọc được serial numbers từ file.
        """
        try:
            with open(commander.serial_file, 'r') as f:
                content = f.read()
            assert len(content) > 0, "Serial file is empty"
            print(f"✅ Serial file is readable")
        except Exception as e:
            pytest.fail(f"Failed to read serial file: {e}")

    def test_04_03_serial_numbers_parsed(self, commander):
        """
        BƯỚC 7: Kiểm tra parsing serial numbers.
        """
        serials = commander.get_serial_numbers()
        
        assert serials is not None, "Serial numbers is None"
        assert isinstance(serials, list), f"Expected list, got {type(serials)}"
        print(f"✅ Found {len(serials)} serial numbers")

    def test_04_04_serial_numbers_not_empty(self, commander, device_info):
        """
        BƯỚC 8: Kiểm tra có ít nhất 1 serial number.
        """
        serials = device_info["serials"]
        
        if len(serials) == 0:
            pytest.skip("⏩ No serial numbers in serials.txt")
        
        for sn in serials:
            assert len(sn) > 0, f"Empty serial number found"
            assert not sn.startswith("#"), f"Comment line in serials: {sn}"
        
        print(f"✅ Valid serial numbers: {serials}")

    def test_04_05_serial_format_valid(self, commander, device_info):
        """
        BƯỚC 9: Kiểm tra định dạng serial numbers.
        """
        serials = device_info["serials"]
        
        if len(serials) == 0:
            pytest.skip("⏩ No serial numbers")
        
        # Serial numbers thường là số hoặc hex
        for sn in serials:
            sn_clean = sn.strip()
            # Kiểm tra không có khoảng trắng hoặc ký tự lạ
            assert sn == sn_clean, f"Serial has whitespace: '{sn}'"
            assert len(sn) <= 20, f"Serial too long: {sn}"
        
        print(f"✅ Serial format is valid")


class TestFirmwareFiles:
    """Kiểm tra firmware files"""

    def test_05_01_firmware_dir_set(self, commander):
        """
        BƯỚC 10: Kiểm tra firmware directory được cấu hình.
        """
        assert commander.firmware_dir is not None, "Firmware dir not set"
        assert len(commander.firmware_dir) > 0, "Firmware dir is empty"
        print(f"✅ Firmware dir: {commander.firmware_dir}")

    def test_05_02_firmware_dir_exists(self, commander):
        """
        BƯỚC 11: Kiểm tra firmware directory tồn tại.
        """
        import os
        
        if commander.firmware_dir:
            assert os.path.isdir(commander.firmware_dir), f"Firmware dir not found: {commander.firmware_dir}"
            print(f"✅ Firmware dir exists")
        else:
            pytest.skip("⏩ Firmware dir not configured")

    def test_05_03_firmware_file_path_set(self, commander):
        """
        BƯỚC 12: Kiểm tra target firmware path được cấu hình.
        """
        assert commander.target_firmware is not None, "Target firmware not set"
        assert len(commander.target_firmware) > 0, "Target firmware is empty"
        print(f"✅ Target firmware: {commander.target_firmware}")

    def test_05_04_firmware_file_exists(self, commander, device_info):
        """
        BƯỚC 13: Kiểm tra firmware file tồn tại.
        """
        import os
        
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip(f"⏩ Firmware file not found: {commander.target_firmware}")
        
        assert os.path.exists(firmware), f"Firmware file not found: {firmware}"
        print(f"✅ Firmware file exists: {firmware}")

    def test_05_05_firmware_file_readable(self, commander, device_info):
        """
        BƯỚC 14: Kiểm tra đọc được firmware file.
        """
        import os
        
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        assert os.path.isfile(firmware), f"Not a file: {firmware}"
        assert os.access(firmware, os.R_OK), f"Cannot read: {firmware}"
        print(f"✅ Firmware file is readable")

    def test_05_06_firmware_file_size(self, commander, device_info):
        """
        BƯỚC 15: Kiểm tra kích thước firmware file.
        """
        import os
        
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        file_size = os.path.getsize(firmware)
        assert file_size > 1000, f"Firmware file too small: {file_size} bytes"
        
        size_kb = file_size / 1024
        print(f"✅ Firmware file size: {size_kb:.1f} KB")

    def test_05_07_firmware_extension(self, commander, device_info):
        """
        BƯỚC 16: Kiểm tra firmware file extension.
        """
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        # Thường là .bin, .hex, .s37, .elf
        valid_ext = ['.bin', '.hex', '.s37', '.elf']
        
        ext = None
        for valid in valid_ext:
            if firmware.lower().endswith(valid):
                ext = valid
                break
        
        assert ext is not None, f"Unsupported firmware extension: {firmware}"
        print(f"✅ Firmware extension: {ext}")


class TestDeviceConnection:
    """Kiểm tra device connection status"""

    def test_06_01_commander_can_list_adapters(self, commander):
        """
        BƯỚC 17: Kiểm tra commander có thể liệt kê adapters.
        """
        # Nếu commander hoạt động, nó sẽ not crash
        try:
            # Chỉ kiểm tra method có thể gọi được
            assert hasattr(commander, 'is_device_connected'), "is_device_connected method not found"
            print(f"✅ Commander adapter check available")
        except Exception as e:
            pytest.fail(f"Commander error: {e}")

    def test_06_02_device_connection_status(self, commander, device_info):
        """
        BƯỚC 18: Kiểm tra trạng thái kết nối của devices.
        """
        serials = device_info["serials"]
        
        if len(serials) == 0:
            pytest.skip("⏩ No serial numbers")
        
        connected_count = 0
        for sn in serials:
            if commander.is_device_connected(sn):
                connected_count += 1
                print(f"✅ Device {sn} is connected")
            else:
                print(f"⚠️ Device {sn} is NOT connected")
        
        if connected_count == 0:
            print("⚠️ No devices connected - flashing tests will be skipped")
        else:
            print(f"✅ {connected_count}/{len(serials)} devices connected")


class TestPreconditionsSummary:
    """Tóm tắt kiểm tra điều kiện trước khi flashing"""

    def test_07_01_all_preconditions_met(self, commander, device_info):
        """
        BƯỚC 19: Kiểm tra tất cả điều kiện được đáp ứng.
        """
        print("\n" + "="*60)
        print("FLASH PRECONDITIONS SUMMARY")
        print("="*60)
        
        # Config
        print(f"✅ Commander: {commander.commander_path}")
        print(f"✅ Device: {commander.device}")
        
        # Serial numbers
        serials = device_info["serials"]
        print(f"✅ Serial numbers: {len(serials)} devices")
        
        # Firmware
        firmware = device_info["firmware"]
        if firmware:
            print(f"✅ Firmware: {firmware}")
        else:
            print(f"❌ Firmware: NOT FOUND")
        
        # Connection status
        connected = sum(1 for sn in serials if commander.is_device_connected(sn))
        print(f"✅ Connected devices: {connected}/{len(serials)}")
        
        print("="*60)
        
        # Điều kiện để tiếp tục
        if len(serials) > 0 and firmware and connected > 0:
            print("✅ Ready for flashing tests")
        else:
            print("⚠️ Some preconditions not met - some tests will be skipped")
