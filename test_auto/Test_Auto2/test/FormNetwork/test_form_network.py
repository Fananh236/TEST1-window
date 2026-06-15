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

def test_thread_network_is_active(pi_device):
    """Kiểm tra Pi đang tham gia mạng Thread (leader hoặc router)."""
    out, _ = pi_device.execute_command("ot-ctl state")
    state = out.strip().lower()

    assert any(role in state for role in ["leader", "router", "child"]), (
        f"Pi Thread network not active. State: '{state}'"
    )
    print(f"\n✅ Thread state: {state}")


def test_thread_dataset_is_retrievable(thread_dataset):
    """Kiểm tra có lấy được dataset hex từ Pi không."""
    assert thread_dataset, "Thread dataset is empty"
    assert thread_dataset.startswith("hex:"), (
        f"Dataset format invalid, expected 'hex:...', got: {thread_dataset}"
    )
    print(f"\n✅ Thread dataset retrieved: {thread_dataset[:40]}...")


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
    out, _ = pi_device.execute_command("ot-ctl channel")
    channel = out.strip().split()[0] if out.strip() else ""

    assert channel.isdigit(), f"Invalid Thread channel: '{channel}'"
    print(f"\n✅ Thread channel: {channel}")


def test_thread_panid(pi_device):
    """Kiểm tra PAN ID của mạng Thread."""
    out, _ = pi_device.execute_command("ot-ctl panid")
    panid = out.strip().split()[0] if out.strip() else ""

    assert panid.startswith("0x"), f"Invalid PAN ID format: '{panid}'"
    print(f"\n✅ Thread PAN ID: {panid}")
