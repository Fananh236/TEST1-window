"""
Test Suite 04: Device Flashing
- Kiểm tra quá trình flashing từng bước
- Tách nhỏ: device selection, mass erase, flash, reset
"""
import pytest


class TestDeviceSelection:
    """Kiểm tra lựa chọn device để flash"""

    def test_04_01_get_serial_list(self, commander, device_info):
        """
        BƯỚC 1: Lấy danh sách serial numbers.
        """
        serials = device_info["serials"]
        
        assert isinstance(serials, list), "Serials not a list"
        print(f"✅ Found {len(serials)} devices in serials.txt")
        
        if len(serials) > 0:
            for i, sn in enumerate(serials, 1):
                print(f"   Device {i}: {sn}")

    def test_04_02_get_firmware_path(self, commander, device_info):
        """
        BƯỚC 2: Lấy đường dẫn firmware.
        """
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        assert len(firmware) > 0, "Firmware path is empty"
        print(f"✅ Firmware: {firmware}")

    def test_04_03_filter_connected_devices(self, commander, device_info):
        """
        BƯỚC 3: Lọc các device đang kết nối.
        """
        serials = device_info["serials"]
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        connected_devices = []
        for sn in serials:
            if commander.is_device_connected(sn):
                connected_devices.append(sn)
                print(f"✅ Device {sn} is connected")
            else:
                print(f"⚠️ Device {sn} is NOT connected")
        
        if len(connected_devices) == 0:
            pytest.skip("⏩ No devices connected")
        
        return connected_devices


class TestMassErase:
    """Kiểm tra mass erase từng device"""

    def test_05_01_mass_erase_first_device(self, commander, device_info):
        """
        BƯỚC 4: Thực hiện mass erase cho device đầu tiên.
        """
        serials = device_info["serials"]
        
        if len(serials) == 0:
            pytest.skip("⏩ No devices configured")
        
        first_sn = serials[0]
        
        # Kiểm tra device connected
        if not commander.is_device_connected(first_sn):
            pytest.skip(f"⏩ Device {first_sn} not connected")
        
        print(f"Erasing device {first_sn}...")
        result = commander.mass_erase(first_sn)
        
        assert result is True, f"Mass erase failed for {first_sn}"
        print(f"✅ Mass erase succeeded for {first_sn}")

    def test_05_02_mass_erase_all_connected(self, commander, device_info):
        """
        BƯỚC 5: Thực hiện mass erase cho tất cả connected devices.
        """
        serials = device_info["serials"]
        
        if len(serials) == 0:
            pytest.skip("⏩ No devices configured")
        
        for sn in serials:
            if not commander.is_device_connected(sn):
                print(f"⏩ Device {sn} not connected, skipping")
                continue
            
            print(f"Erasing device {sn}...")
            result = commander.mass_erase(sn)
            
            assert result is True, f"Mass erase failed for {sn}"
            print(f"✅ Mass erase succeeded for {sn}")


class TestFlashing:
    """Kiểm tra flash firmware từng device"""

    def test_06_01_flash_firmware_first_device(self, commander, device_info):
        """
        BƯỚC 6: Flash firmware cho device đầu tiên.
        """
        serials = device_info["serials"]
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        if len(serials) == 0:
            pytest.skip("⏩ No devices configured")
        
        first_sn = serials[0]
        
        # Kiểm tra device connected
        if not commander.is_device_connected(first_sn):
            pytest.skip(f"⏩ Device {first_sn} not connected")
        
        print(f"Flashing firmware to {first_sn}...")
        result = commander.flash_firmware(first_sn, firmware)
        
        assert result is True, f"Flash failed for {first_sn}"
        print(f"✅ Flash succeeded for {first_sn}")

    def test_06_02_flash_firmware_all_connected(self, commander, device_info):
        """
        BƯỚC 7: Flash firmware cho tất cả connected devices.
        """
        serials = device_info["serials"]
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        if len(serials) == 0:
            pytest.skip("⏩ No devices configured")
        
        for sn in serials:
            if not commander.is_device_connected(sn):
                print(f"⏩ Device {sn} not connected, skipping")
                continue
            
            print(f"Flashing firmware to {sn}...")
            result = commander.flash_firmware(sn, firmware)
            
            assert result is True, f"Flash failed for {sn}"
            print(f"✅ Flash succeeded for {sn}")


class TestDeviceReset:
    """Kiểm tra reset device sau flash"""

    def test_07_01_reset_first_device(self, commander, device_info):
        """
        BƯỚC 8: Reset device đầu tiên.
        """
        serials = device_info["serials"]
        
        if len(serials) == 0:
            pytest.skip("⏩ No devices configured")
        
        first_sn = serials[0]
        
        # Kiểm tra device connected
        if not commander.is_device_connected(first_sn):
            pytest.skip(f"⏩ Device {first_sn} not connected")
        
        print(f"Resetting device {first_sn}...")
        result = commander.reset_device(first_sn)
        
        assert result is True, f"Reset failed for {first_sn}"
        print(f"✅ Reset succeeded for {first_sn}")

    def test_07_02_reset_all_devices(self, commander, device_info):
        """
        BƯỚC 9: Reset tất cả devices.
        """
        serials = device_info["serials"]
        
        if len(serials) == 0:
            pytest.skip("⏩ No devices configured")
        
        for sn in serials:
            if not commander.is_device_connected(sn):
                print(f"⏩ Device {sn} not connected, skipping")
                continue
            
            print(f"Resetting device {sn}...")
            result = commander.reset_device(sn)
            
            assert result is True, f"Reset failed for {sn}"
            print(f"✅ Reset succeeded for {sn}")


class TestCompleteFlashSequence:
    """Kiểm tra toàn bộ quá trình flash từ đầu đến cuối"""

    def test_08_01_complete_flash_workflow_single_device(self, commander, device_info):
        """
        BƯỚC 10: Toàn bộ workflow flash cho 1 device.
        - Step 1: Mass erase
        - Step 2: Flash firmware
        - Step 3: Reset
        """
        serials = device_info["serials"]
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        if len(serials) == 0:
            pytest.skip("⏩ No devices configured")
        
        sn = serials[0]
        
        if not commander.is_device_connected(sn):
            pytest.skip(f"⏩ Device {sn} not connected")
        
        print(f"\n{'='*60}")
        print(f"COMPLETE FLASH WORKFLOW FOR {sn}")
        print(f"{'='*60}")
        
        # Step 1: Mass erase
        print(f"\n[1/3] Mass erase {sn}...")
        assert commander.mass_erase(sn) is True, f"Mass erase failed"
        print(f"✅ Step 1 complete")
        
        # Step 2: Flash
        print(f"\n[2/3] Flash firmware to {sn}...")
        assert commander.flash_firmware(sn, firmware) is True, f"Flash failed"
        print(f"✅ Step 2 complete")
        
        # Step 3: Reset
        print(f"\n[3/3] Reset {sn}...")
        assert commander.reset_device(sn) is True, f"Reset failed"
        print(f"✅ Step 3 complete")
        
        print(f"\n✅ COMPLETE FLASH WORKFLOW SUCCEEDED FOR {sn}")

    def test_08_02_complete_flash_workflow_all_devices(self, commander, device_info):
        """
        BƯỚC 11: Toàn bộ workflow flash cho tất cả devices.
        """
        serials = device_info["serials"]
        firmware = device_info["firmware"]
        
        if firmware is None:
            pytest.skip("⏩ Firmware file not found")
        
        if len(serials) == 0:
            pytest.skip("⏩ No devices configured")
        
        print(f"\n{'='*60}")
        print(f"FLASHING ALL CONNECTED DEVICES")
        print(f"{'='*60}")
        
        successful = []
        failed = []
        skipped = []
        
        for i, sn in enumerate(serials, 1):
            print(f"\n[Device {i}/{len(serials)}] Processing {sn}")
            
            if not commander.is_device_connected(sn):
                print(f"⏩ Device {sn} not connected, skipping")
                skipped.append(sn)
                continue
            
            try:
                # Mass erase
                print(f"  [1/3] Mass erase...")
                assert commander.mass_erase(sn) is True
                
                # Flash
                print(f"  [2/3] Flashing firmware...")
                assert commander.flash_firmware(sn, firmware) is True
                
                # Reset
                print(f"  [3/3] Reset...")
                assert commander.reset_device(sn) is True
                
                successful.append(sn)
                print(f"✅ Device {sn} flashed successfully")
                
            except AssertionError as e:
                failed.append(sn)
                print(f"❌ Device {sn} flash failed: {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"FLASH SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful: {len(successful)}")
        if successful:
            for sn in successful:
                print(f"   - {sn}")
        
        print(f"❌ Failed: {len(failed)}")
        if failed:
            for sn in failed:
                print(f"   - {sn}")
        
        print(f"⏩ Skipped: {len(skipped)}")
        if skipped:
            for sn in skipped:
                print(f"   - {sn}")
        
        print(f"{'='*60}")
        
        # At least one device should be successful
        assert len(successful) > 0 or len(skipped) == len(serials), \
            f"No devices flashed (successful: {len(successful)}, skipped: {len(skipped)})"
