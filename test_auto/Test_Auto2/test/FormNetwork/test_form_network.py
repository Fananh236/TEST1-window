
import pytest
from utils.chiptool import fetch_thread_data_set


@pytest.fixture(scope="module")
def thread_dataset(pi_device):
   
    dataset, err = fetch_thread_data_set(pi_device)
    if err or not dataset:
        pytest.skip(f"Cannot retrieve Thread dataset from Pi: {err}")
    return dataset



def thread_dataset_is_valid_hex(thread_dataset):
    hex_part = thread_dataset.removeprefix("hex:")

    assert len(hex_part) > 0, "Dataset hex part is empty"
    assert all(c in "0123456789abcdefABCDEF" for c in hex_part), (
        f"Dataset contains non-hex characters: {hex_part}"
    )
    print(f"\n✅ Dataset hex valid, length: {len(hex_part)} chars")


def test_thread_channel(pi_device):
    cmd = "echo 1 | sudo ot-ctl channel"
    out, _ = pi_device.execute_command(cmd)

    # Loại bỏ 'Done' của ot-ctl
    lines = [l.strip() for l in out.splitlines() if l.strip() and l.strip().lower() != "done"]
    channel = lines[0] if lines else ""

    if not channel:
        pytest.skip("⏩ SKIP: Cannot get Thread channel (Pi not in Thread network)")

    assert channel.isdigit(), f"Invalid Thread channel: '{channel}'"
    print(f"\n✅ Thread channel: {channel}")


