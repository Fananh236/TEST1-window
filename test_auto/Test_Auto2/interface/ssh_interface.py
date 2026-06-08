import paramiko
import json
import os
import logging
import datetime

class PI:
    def __init__(self, config_path="config.json"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"❌ Config file not found: {config_path}")
            
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.config = data.get("pi_config", data)
        self.host = self.config.get("pi_host")
        self.port = self.config.get("pi_port", 22)
        self.username = self.config.get("ssh_username")
        self.password = self.config.get("ssh_password")
        self.key_path = self.config.get("ssh_key_path")
        self.chip_tool_path = self.config.get("chip_tool_path")
        self._ssh_client = None


        # --- LOGGING CONFIGURATION ---
        log_directory = "/home/phanhoanganh/Downloads/Auto/test_auto/Test_Auto2/Log"
        
        # Create the directory if it does not exist
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
            
        log_filename = os.path.join(log_directory, "pi_connection.log")
        
        self.logger = logging.getLogger("PiSSH")
        self.logger.setLevel(logging.DEBUG)
        
        # mode= a is append, w for easre
        file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info("--- NEW SESSION STARTED ---")

    def connect(self):
        if self._ssh_client is None:
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                if self.key_path and os.path.exists(self.key_path):
                    self._ssh_client.connect(self.host, port=self.port, username=self.username, key_filename=self.key_path)
                else:
                    self._ssh_client.connect(self.host, port=self.port, username=self.username, password=self.password)
                self.logger.info(f"Successfully connected to {self.host}")
            except Exception as e:
                self.logger.error(f"Connection failed: {str(e)}")
                raise
        return self._ssh_client

    def execute_command(self, command):
        """
        Execute command, save log to full_output variable 
        and log everything to the file via logging module.
        """
        self.logger.info(f"--- START COMMAND: {command} ---")
        client = self.connect()
        transport = client.get_transport()
        channel = transport.open_session()
        channel.exec_command(command)
        
        full_output = ""
        full_error = ""
        
        # Read data from channel into output and error variables
        while not channel.exit_status_ready() or channel.recv_ready() or channel.recv_stderr_ready():
            if channel.recv_ready():
                chunk = channel.recv(1024).decode('utf-8', errors='ignore')
                full_output += chunk
                self.logger.debug(f"STDOUT: {chunk.strip()}")
            if channel.recv_stderr_ready():
                error_chunk = channel.recv_stderr(1024).decode('utf-8', errors='ignore')
                full_error += error_chunk
                self.logger.error(f"STDERR: {error_chunk.strip()}")
                
        self.logger.info(f"--- END COMMAND ---")
        return full_output.strip(), full_error.strip()

    def disconnect(self):
        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
            self.logger.info("SSH connection closed.")
            
            
