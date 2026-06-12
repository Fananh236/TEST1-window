"""
Pytest Configuration và Fixtures
- manage setup/teardown for test session
- provide fixtures: config, SSH, RTT
- log test result to file
"""

import os
import sys
import time
import pytest

# Add root path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.loader import ConfigLoader
from interface.rtt import DeviceRTT
from interface.ssh import SSHClient


# =============================================================================
# PATHS
# =============================================================================
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Log"))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "config.json"))


# =============================================================================
# 1. CONFIG FIXTURE
# =============================================================================
@pytest.fixture(scope="session", autouse=True)
def config():
    """Load configuration once per session"""
    loader = ConfigLoader.instance(CONFIG_PATH)
    return loader.config


# =============================================================================
# 2. SSH FIXTURE
# =============================================================================
@pytest.fixture(scope="session")
def pi_device(config):
    """SSH connection to Raspberry Pi"""
    log_dir = os.path.abspath(config.get("log_path", LOG_DIR))
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
        raise

    yield pi

    pi.disconnect()
    print("✅ SSH closed")


# =============================================================================
# 3. RTT FIXTURE (PER TEST)
# =============================================================================
@pytest.fixture(scope="function")
def device_rtt(config, tmp_path, request):
    """
    RTT handler per test
    - Isolated log per test
    """
    log_dir = str(tmp_path)

    rtt = DeviceRTT(
        serial_config=config.get("serial_config", {}),
        log_dir=log_dir
    )

    print(f"RTT log dir: {log_dir}")

    yield rtt

    rtt.stop_rtt()


# =============================================================================
# 4. TEST RESULT LOGGING
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

