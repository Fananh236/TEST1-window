"""
Pytest Configuration và Fixtures
- Quản lý setup/teardown của toàn bộ test session
- Cung cấp fixtures cho SSH connection, config, devices
- Ghi log chi tiết vào file
"""
import atexit
import os
import subprocess
import sys
import time

import pytest

# Add root path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.loader import ConfigLoader
from interface.commander import CommanderInterface
from interface.rtt import DeviceFlasher
from interface.ssh import SSHClient

# Paths
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Log"))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "config.json"))


# ============================================================================
# 1. CONFIG FIXTURE - Tải configuration từ file
# ============================================================================
@pytest.fixture(scope="session")
def config():
    """Tải configuration một lần cho toàn bộ session."""
    config_loader = ConfigLoader.instance(CONFIG_PATH)
    return config_loader.config


# ============================================================================
# 2. SSH CONNECTION FIXTURES
# ============================================================================
@pytest.fixture(scope="session")
def pi_device(config):
    """
    Tạo SSH connection đến Raspberry Pi.
    - Scope: session (kết nối một lần cho toàn bộ tests)
    - Tự động disconnect sau tests
    """
    log_dir = os.path.abspath(config.get("log_path", LOG_DIR))
    pi = SSHClient(config["pi_config"], log_dir=log_dir)

    print("\n" + "="*50)
    print("SSH CONNECTION INFO")
    print("="*50)
    print(f"Host: {pi.host}:{pi.port}")
    print(f"User: {pi.username}")
    print(f"Chip-tool: {pi.chip_tool_path}")
    print("="*50)

    try:
        pi.connect()
        print("✅ SSH connection established")
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        raise

    yield pi
    
    # Cleanup
    pi.disconnect()
    print("✅ SSH connection closed")


# ============================================================================
# 3. DEVICE FLASHING FIXTURES
# ============================================================================
@pytest.fixture(scope="session")
def commander(config):
    """
    Tạo CommanderInterface cho flashing operations.
    - Scope: session (một instance cho toàn bộ tests)
    """
    serial_config = config.get("serial_config", {})
    return CommanderInterface(serial_config)


@pytest.fixture(scope="function")
def device_info(commander):
    """
    Lấy thông tin device (serial numbers, firmware path).
    - Scope: function (cập nhật cho mỗi test nếu cần)
    """
    return {
        "serials": commander.get_serial_numbers(),
        "firmware": commander.get_firmware_file(),
        "firmware_dir": commander.firmware_dir,
    }


# ============================================================================
# 4. RTT LOGGER FIXTURE - Quản lý RTT logging
# ============================================================================
@pytest.fixture(scope="session", autouse=True)
def rtt_logger(config):
    """
    Khởi động RTT logger cho capture device logs.
    - autouse=True: Tự động chạy với mọi test
    - Scope: session (một lần cho toàn bộ session)
    """
    print("\n" + "="*50)
    print("RTT LOGGER SETUP")
    print("="*50)

    # Cleanup processes từ lần chạy trước
    if os.name == "posix":
        subprocess.run(["pkill", "-f", "JLinkRemoteServer"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", "JLinkRTTLogger"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run("taskkill /F /IM JLinkRemoteServer.exe", 
                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("taskkill /F /IM JLinkRTTLogger.exe", 
                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Tạo RTT logger
    log_dir = os.path.abspath(config.get("log_path", LOG_DIR))
    os.makedirs(log_dir, exist_ok=True)
    
    try:
        flasher = DeviceFlasher(config.get("serial_config", {}), log_dir=log_dir)
        flasher.start_rtt()
        print("✅ RTT logger started")
        
        # Register cleanup function
        atexit.register(flasher.stop_rtt)
        
    except Exception as e:
        print(f"⚠️ RTT logger failed to start: {e}")
        flasher = None

    yield

    # Cleanup
    print("\n" + "="*50)
    print("RTT LOGGER CLEANUP")
    print("="*50)
    
    if flasher:
        flasher.stop_rtt()
    
    # Force cleanup processes
    if os.name == "posix":
        subprocess.run(["pkill", "-f", "JLinkRemoteServer"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", "JLinkRTTLogger"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run("taskkill /F /IM JLinkRemoteServer.exe", 
                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run("taskkill /F /IM JLinkRTTLogger.exe", 
                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("✅ RTT logger stopped")


# ============================================================================
# 5. TEST REPORT LOGGING
# ============================================================================
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_logreport(report):
    """
    Hook để ghi chi tiết mỗi test vào file log.
    """
    yield

    if report.when in ["call", "setup", "teardown"]:
        os.makedirs(LOG_DIR, exist_ok=True)

        test_file_path = report.nodeid.split("::")[0]
        test_file_name = os.path.splitext(os.path.basename(test_file_path))[0]
        log_file_path = os.path.join(LOG_DIR, f"{test_file_name}.log")

        with open(log_file_path, "a", encoding="utf-8") as log_file:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            log_file.write(f"\n{'='*80}\n")
            log_file.write(f"[{timestamp}] {report.when.upper()}: {report.nodeid}\n")
            log_file.write(f"{'='*80}\n")

            if report.failed and report.longrepr:
                log_file.write(f"STATUS: ❌ FAILED\n")
                log_file.write(f"ERROR:\n{str(report.longrepr)}\n")
            elif report.passed:
                log_file.write(f"STATUS: ✅ PASSED\n")

            for section in report.sections:
                if "stdout" in section[0]:
                    log_file.write(f"\nSTDOUT:\n{section[1]}\n")