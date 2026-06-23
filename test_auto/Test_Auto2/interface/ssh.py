import os
import paramiko

from test_auto.Test_Auto2.utils.pi_logger import setup_file_logger


class SSHClient:
    def __init__(self, pi_config, log_dir):
        self.host = pi_config.get("pi_host")
        self.port = pi_config.get("pi_port", 22)
        self.username = pi_config.get("ssh_username")
        self.password = pi_config.get("ssh_password")
        self.key_path = pi_config.get("ssh_key_path") or None
        self.chip_tool_path = pi_config.get("chip_tool_path")
        self._ssh_client = None
        self.otl_path = pi_config.get("otl_path")
        self.log_dir = os.path.abspath(log_dir)
        self.logger = setup_file_logger("PiSSH", self.log_dir, "pi_connection.log")
        self.logger.info("--- NEW SSH SESSION ---")

    def connect(self):
        if self._ssh_client is not None:
            return self._ssh_client

        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if self.key_path and os.path.exists(self.key_path):
                self._ssh_client.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                )
            else:
                self._ssh_client.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                )
            self.logger.info(f"Successfully connected to {self.host}:{self.port}")
        except Exception as exc:
            self.logger.error(f"SSH connection failed: {exc}")
            self._ssh_client = None
            raise

        return self._ssh_client

    def execute_command(self, command, timeout=None):
        self.logger.info(f"--- EXECUTE COMMAND: {command} ---")
        client = self.connect()
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

        out = stdout.read().decode("utf-8", errors="ignore").strip()
        err = stderr.read().decode("utf-8", errors="ignore").strip()

        if out:
            self.logger.debug(f"STDOUT: {out}")
        if err:
            self.logger.error(f"STDERR: {err}")

        self.logger.info("--- COMMAND COMPLETED ---")
        return out, err

    def disconnect(self):
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
            self.logger.info("SSH connection closed.")
    
