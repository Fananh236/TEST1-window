import logging
import os


def setup_file_logger(name, log_dir, file_name, level=logging.DEBUG, mode="w"):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    target_path = os.path.abspath(os.path.join(log_dir, file_name))
    existing_handlers = [
        h for h in logger.handlers
        if isinstance(h, logging.FileHandler) and os.path.abspath(h.baseFilename) == target_path
    ]
    if not existing_handlers:
        handler = logging.FileHandler(target_path, mode=mode, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
