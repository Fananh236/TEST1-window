import pytest

from utils.log_parser import (
    find_log_dir,
    read_file,
    extract_pi_commands,
    extract_device_results,
)
from utils.verifier import verify_command_vs_device


def check_logs():
    log_dir = find_log_dir()

    if log_dir is None:
        raise RuntimeError("Log directory not found")

    pi_log = log_dir / "pi_connection.log"
    rtt_log = log_dir / "rtt_log.txt"

    if not pi_log.exists():
        raise RuntimeError(f"Missing {pi_log}")

    if not rtt_log.exists():
        raise RuntimeError(f"Missing {rtt_log}")

    pi_content = read_file(pi_log)
    rtt_content = read_file(rtt_log)

    print("\n=== STEP 1: PI COMMANDS ===")
    pi_commands = extract_pi_commands(pi_content)

    for i, cmd in enumerate(pi_commands, 1):
        print(
            f"{i}. [{cmd['timestamp']}] "
            f"onoff {cmd['action']} {cmd['node_id']} {cmd['endpoint_id']}"
        )

    print("\n=== STEP 2: DEVICE RESULTS ===")
    device_results = extract_device_results(rtt_content)

    for i, r in enumerate(device_results, 1):
        print(f"{i}. {r}")

    verify_command_vs_device(pi_commands, device_results)


def test_check_logs():
    try:
        check_logs()
    except RuntimeError as e:
        pytest.skip(str(e))