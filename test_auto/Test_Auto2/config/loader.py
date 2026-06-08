import json
import os
import threading


class ConfigLoader:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_path=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path=None):
        if self._initialized:
            return

        base_dir = os.path.abspath(os.path.dirname(__file__))
        default_path = os.path.join(base_dir, "config.json")
        self.config_path = os.path.abspath(config_path or default_path)

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self._initialized = True

    @classmethod
    def instance(cls, config_path=None):
        return cls(config_path)

    @property
    def root(self):
        return os.path.abspath(os.path.join(os.path.dirname(self.config_path), ".."))

    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_log_path(self):
        log_path = self.config.get("log_path", "./Log")
        if not os.path.isabs(log_path):
            log_path = os.path.abspath(os.path.join(self.root, log_path))
        os.makedirs(log_path, exist_ok=True)
        return log_path

    def resolve_path(self, path):
        if not path:
            return None
        return path if os.path.isabs(path) else os.path.abspath(os.path.join(self.root, path))
