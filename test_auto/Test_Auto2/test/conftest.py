"""
Pytest Configuration và Fixtures
- manage setup/teardown for test session
- provide fixtures: config, SSH, RTT
- log test result to file
"""

import os
import sys
import time
import subprocess
import pytest

# Add root path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.loader import ConfigLoader
from interface.rtt import DeviceRTT
from interface.ssh import SSHClient
from utils.common import resolve_log_directory


# =============================================================================
# PATHS
# =============================================================================
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Log"))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "config.json"))

# Project root for log path resolution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _resolve_log_dir(log_path):
    """Legacy wrapper for resolve_log_directory (for backward compatibility)."""
    return resolve_log_directory(log_path, PROJECT_ROOT)


# =============================================================================
# 1. CONFIG FIXTURE
# =============================================================================
@pytest.fixture(scope="session", autouse=True)
def config():
    """Load configuration once per session"""
    loader = ConfigLoader.instance(CONFIG_PATH)
    return loader.config


# =============================================================================
# 1b. FLASHED DEVICE FIXTURE
# =============================================================================
@pytest.fixture(scope="session")
def flashed_device(config):
    
    devices = config.get("serial_config", {}).get("devices", [])

    for device in devices:
        ip = device.get("ip")
        if not ip:
            continue

        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3
            )
            if result.returncode == 0:
                print(f"\n✅ Device online: {device['name']} ({ip})")
                return device
        except Exception:
            continue

    pytest.skip("⏩ SKIP: No flashed device is reachable via IP")


# =============================================================================
# 2. SSH FIXTURE
# =============================================================================
@pytest.fixture(scope="session")
def pi_device(config):
    """SSH connection to Raspberry Pi"""
    log_dir = config.get("log_path") or config.get("serial_config", {}).get("log_dir") or LOG_DIR
    log_dir = _resolve_log_dir(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    pi = SSHClient(config["pi_config"], log_dir=log_dir)

    print("\n" + "=" * 50)
    print("SSH CONNECTION INFO")
    print("=" * 50)
    print(f"Host: {pi.host}:{pi.port}")
    print(f"User: {pi.username}")
    print(f"Chip-tool: {pi.chip_tool_path}")
    print("=" * 50)

    try:
        pi.connect()
        print("✅ SSH connected")
    except Exception as e:
        print(f"❌ SSH failed: {e}")
        pytest.skip(f"SSH unavailable: {e}")

    yield pi

    pi.disconnect()
    print("✅ SSH closed")


# =============================================================================
# 3. RTT FIXTURE (SESSION-SCOPED FOR INIT/CLEANUP)
# =============================================================================
# NOTE: RTT logging is now captured per-function-call via execute_command()
# This fixture handles RTT setup/teardown only. Real-time log capture
# happens in utils.rtt_reader and through SSHClient execute_command_with_rtt()

@pytest.fixture(scope="session")
def device_rtt(config):
    

    # Kill old processes
    subprocess.run("pkill -f JLinkRemoteServer", shell=True)
    subprocess.run("pkill -f JLinkRTTLogger", shell=True)

    log_dir = config.get("log_path") or config.get("serial_config", {}).get("log_dir") or LOG_DIR
    log_dir = _resolve_log_dir(log_dir)
    os.makedirs(log_dir, exist_ok=True)

    rtt = DeviceRTT(
        serial_config=config.get("serial_config", {}),
        log_dir=log_dir
    )

    try:
        print("\n[GLOBAL RTT] Starting RTT (session-scoped init)...")
        rtt.start_rtt()
        time.sleep(3)
    except Exception as e:
        pytest.fail(f"RTT start failed: {e}")

    print(f"[GLOBAL RTT] Log dir: {log_dir}")
    print(f"[GLOBAL RTT] RTT log: {rtt.rtt_log_file}")

    yield rtt

    print("\n[GLOBAL RTT] Stopping RTT...")
    rtt.stop_rtt()

    subprocess.run("pkill -f JLinkRemoteServer", shell=True)
    subprocess.run("pkill -f JLinkRTTLogger", shell=True)


# =============================================================================
# 3b. LOG PATHS FIXTURE
# =============================================================================
@pytest.fixture(scope="session")
def log_paths(config, device_rtt):
    """Provide log file paths for RTT and Pi connection logs."""
    log_dir = config.get("log_path") or config.get("serial_config", {}).get("log_dir") or LOG_DIR
    log_dir = _resolve_log_dir(log_dir)
    
    return {
        "pi_log": os.path.join(log_dir, "pi_connection.log"),
        "rtt_log": device_rtt.rtt_log_file,
        "log_dir": log_dir,
    }

# =============================================================================
# 4. TEST ORDERING
# =============================================================================
def pytest_collection_modifyitems(items):
    order = {
        "test_flashing_ip.py": 0,
        "test_flashing_sn.py": 1,
        "test_rtt_logging.py": 2,
        "test_pi_connectivity.py": 3,
        "test_form_network.py": 4,
        "test_chiptool.py": 5,
        "test_log_verification.py": 6,
        "test_check_logs.py" : 7,
    }

    def sort_key(item):
        return (order.get(os.path.basename(str(item.fspath)), 99), str(item.fspath), item.name)

    items.sort(key=sort_key)


# =============================================================================
# 5. TEST RESULT LOGGING
# =============================================================================
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_logreport(report):
    yield

    if report.when in ("setup", "call", "teardown"):
        os.makedirs(LOG_DIR, exist_ok=True)

        test_file = report.nodeid.split("::")[0]
        test_name = os.path.splitext(os.path.basename(test_file))[0]
        log_file = os.path.join(LOG_DIR, f"{test_name}.log")

        with open(log_file, "a", encoding="utf-8") as f:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")

            f.write(f"\n{'='*80}\n")
            f.write(f"[{ts}] {report.when.upper()} {report.nodeid}\n")
            f.write(f"{'='*80}\n")

