"""
FormNetwork Tests
- Mục đích: Kiểm tra quá trình hình thành Thread Network trên Raspberry Pi
- Bao gồm: Lấy Thread dataset hex, kiểm tra trạng thái mạng Thread
"""

import pytest
from utils.chip_tool_helper import fetch_thread_data_set


@pytest.fixture(scope="module")
def thread_dataset(pi_device):
    """
    Fixture: Lấy Thread dataset hex từ Pi một lần, dùng lại cho các test trong module.
    Tự động skip nếu Pi không kết nối được.
    """
    dataset, err = fetch_thread_data_set(pi_device)
    if err or not dataset:
        pytest.skip(f"Cannot retrieve Thread dataset from Pi: {err}")
    return dataset


# =============================================================================
# TEST: Kiểm tra Thread Network đang hoạt động
# =============================================================================



def test_thread_dataset_is_valid_hex(thread_dataset):
    """Kiểm tra phần hex trong dataset có hợp lệ không."""
    hex_part = thread_dataset.removeprefix("hex:")

    assert len(hex_part) > 0, "Dataset hex part is empty"
    assert all(c in "0123456789abcdefABCDEF" for c in hex_part), (
        f"Dataset contains non-hex characters: {hex_part}"
    )
    print(f"\n✅ Dataset hex valid, length: {len(hex_part)} chars")


def test_thread_channel(pi_device):
    """Kiểm tra kênh (channel) của mạng Thread."""
    cmd = f"echo '{pi_device.password}' | sudo -S -p '' ot-ctl channel"
    out, _ = pi_device.execute_command(cmd)

    # Loại bỏ 'Done' của ot-ctl
    lines = [l.strip() for l in out.splitlines() if l.strip() and l.strip().lower() != "done"]
    channel = lines[0] if lines else ""

    if not channel:
        pytest.skip("⏩ SKIP: Cannot get Thread channel (Pi not in Thread network)")

    assert channel.isdigit(), f"Invalid Thread channel: '{channel}'"
    print(f"\n✅ Thread channel: {channel}")


def test_thread_panid(pi_device):
    """Kiểm tra PAN ID của mạng Thread."""
    cmd = f"echo '{pi_device.password}' | sudo -S -p '' ot-ctl panid"
    out, _ = pi_device.execute_command(cmd)

    # Loại bỏ 'Done' của ot-ctl
    lines = [l.strip() for l in out.splitlines() if l.strip() and l.strip().lower() != "done"]
    panid = lines[0] if lines else ""

    if not panid:
        pytest.skip("⏩ SKIP: Cannot get PAN ID (Pi not in Thread network)")

    assert panid.startswith("0x"), f"Invalid PAN ID format: '{panid}'"
    print(f"\n✅ Thread PAN ID: {panid}")
