import os
import shutil
from pathlib import Path


def resolve_log_path(config):
    log_path = config.get("log_path", "./Log")

    if not os.path.isabs(log_path):
        base_dir = Path(__file__).resolve().parents[2]
        log_path = str(base_dir.joinpath(log_path))

    return log_path


def get_log_files(log_path):
    if not os.path.isdir(log_path):
        return []
    return [f for f in os.listdir(log_path) if f.endswith(".log")]


def read_log_file(full_path):
    with open(full_path, "r") as f:
        return f.read()


def get_device_ip(config):
    serial_config = config.get("serial_config", {})

    ip = serial_config.get("ip")
    if ip:
        return ip

    for d in serial_config.get("devices", []):
        if isinstance(d, dict) and d.get("ip"):
            return d["ip"]

    return None

