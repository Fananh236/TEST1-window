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
                cls._instance._loaded = False
        return cls._instance

    def __init__(self, config_path=None):
        if self._loaded:
            return

        base_dir = os.path.abspath(os.path.dirname(__file__))
        default_path = os.path.join(base_dir, "config.json")

        self.config_path = os.path.abspath(config_path or default_path)

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.root_dir = os.path.abspath(
            os.path.join(os.path.dirname(self.config_path), "..")
        )

        self._validate()
        self._loaded = True

    # =========================
    # VALIDATION
    # =========================
    def _validate(self):
        required = ["pi_config", "chip_config", "serial_config"]
        for key in required:
            if key not in self.config:
                raise ValueError(f"Missing required config section: {key}")

    # =========================
    # GET VALUE (support nested)
    # =========================
    def get(self, key, default=None):
        """
        Support: "pi_config.pi_host"
        """
        
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    # =========================
    # SINGLETON ACCESS
    # =========================
    @classmethod
    def instance(cls, config_path=None):
        return cls(config_path)