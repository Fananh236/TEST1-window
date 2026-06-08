import os


def read_serials(serial_file):
    if not os.path.exists(serial_file):
        return []

    serials = []
    with open(serial_file, "r", encoding="utf-8") as f:
        for line in f:
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            serials.append(value)
    return serials
