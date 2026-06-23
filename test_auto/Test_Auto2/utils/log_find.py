import re
from pathlib import Path


# =========================
# File utils
# =========================
def find_log_dir():
    here = Path(__file__).resolve().parent.parent

    candidates = [
        here / "Log",
        here.parent / "Log",
        here.parents[1] / "Log",
        Path.cwd() / "Log",
    ]

    for c in candidates:
        if c.exists() and c.is_dir():
            return c

    return None


def read_file(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore")


# =========================
# PI log parser
# =========================
def extract_pi_commands(content: str):
    commands = []

    pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?"
        r"chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)",
        re.IGNORECASE,
    )

    for m in pattern.finditer(content):
        ts, action, node_id, endpoint_id = m.groups()
        commands.append({
            "timestamp": ts,
            "action": action.lower(),
            "node_id": node_id,
            "endpoint_id": endpoint_id,
        })

    if not commands:
        raise AssertionError("❌ No onoff commands found in PI log")

    return commands


# =========================
# RTT parser
# =========================
def extract_device_results(rtt_content: str):
    lines = rtt_content.splitlines()
    results = []

    turning_on_re = re.compile(r"Turning light On", re.IGNORECASE)
    turning_off_re = re.compile(r"Turning light Off", re.IGNORECASE)
    already_set_re = re.compile(
        r"Endpoint\s+\d+\s+On/off\s+already\s+set",
        re.IGNORECASE,
    )

    for line in lines:
        if turning_on_re.search(line):
            results.append("TURN_ON")

        elif turning_off_re.search(line):
            results.append("TURN_OFF")

        elif already_set_re.search(line):
            results.append("ALREADY_SET")

    return results