import re
from typing import List, Dict


def parse_pi_commands(file_path: str) -> List[Dict[str, str]]:
    """Parse Pi log file and extract ordered chip-tool onoff commands.

    Returns list of dicts: {"action": "on"/"off"/"toggle", "node_id": str, "endpoint_id": str}
    """
    commands = []
    pattern = re.compile(r"chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)", re.IGNORECASE)

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = pattern.search(line)
            if not m:
                continue
            action, node_id, endpoint_id = m.group(1).lower(), m.group(2), m.group(3)
            commands.append({"action": action, "node_id": node_id, "endpoint_id": endpoint_id})

    return commands
