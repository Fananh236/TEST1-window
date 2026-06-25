import os
import pytest

from utils.common import (
    resolve_log_directory,
    get_log_files,
    read_log_file,
    get_device_ip,
)


def test_rtt_fixture_active(device_rtt):
    print("✅ RTT fixture active")

def log_file_readable(config):
    log_path = resolve_log_directory(config.get("log_path"))
    log_files = get_log_files(log_path)

    if not log_files:
        pytest.skip("No log files yet")

    full_path = os.path.join(log_path, log_files[0])
    content = read_log_file(full_path)

    assert len(content) > 0, "Log file is empty"
    print(f"✅ Read OK: {log_files[0]}")


def rtt_config(config):
    ip = get_device_ip(config)
    assert ip is not None, "No device IP configured"
    print(f"✅ RTT IP: {ip}")
