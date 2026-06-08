# Test_Auto2 Architecture Refactor

## Overview
The `Test_Auto2` project has been refactored to follow a clean, modular architecture with centralized configuration, interface abstraction, and reusable utilities.

## Module Structure

### 1. **config/** - Centralized Configuration
- **`config/loader.py`**: Singleton configuration loader
  - Reads from `config/config.json`
  - Handles path resolution (relative to project root)
  - Single instance across the application
  
- **`config/config.json`**: Configuration file
  - `pi_config`: Raspberry Pi SSH settings
  - `chip_config`: Chip-tool and device parameters
  - `serial_config`: Commander tool and flashing settings
  - `log_path`: Output log directory

### 2. **interface/** - Hardware/Remote Device Abstractions
- **`interface/ssh.py`** (`SSHClient`): SSH connection wrapper
  - Manages Paramiko client lifecycle
  - Executes remote commands
  - Logs to file for debugging
  
- **`interface/commander.py`** (`CommanderInterface`): Device flashing operations
  - Queries connected devices
  - Performs mass-erase, flash, and reset operations
  - Reads firmware and serial numbers from configured paths
  
- **`interface/rtt.py`** (`DeviceFlasher`): RTT (Real-Time Tracing) logging
  - Starts JLink remote server and RTT logger
  - Captures device logs to file
  - Cleanup and process management
  
- **`interface/jlink.py`**: JLink command builders
  - Helper functions to construct JLink CLI commands
  
- **`interface/serial_interface.py`**: Compatibility shim
  - Deprecated; imports `CommanderInterface` from `commander.py`
  - Maintained for backward compatibility

### 3. **utils/** - Reusable Helpers
- **`utils/logger.py`**: File logger setup
  - Creates timestamped file loggers
  - Avoids duplicate handlers
  
- **`utils/parser.py`**: Configuration data parsing
  - Reads serial numbers from text files
  - Handles comments and blank lines
  
- **`utils/retry.py`**: Retry decorator (if needed)
  
- **`utils/helper_test.py`**: Test helpers
  - `run_chip_tool_cmd()`: Execute chip-tool commands
  - `cleanup_kvs()`: Clean up persistent key-value storage

### 4. **test/** - Pytest Test Suite
- **`test/conftest.py`**: Pytest fixtures and hooks
  - `config`: Session-wide config loader
  - `pi_device`: SSH connection to Raspberry Pi (session scope)
  - `rtt_logger`: RTT logging lifecycle (session scope, auto-use)
  - `pytest_runtest_logreport`: Test result logging hook
  
- **`test/test_0_pi_connectivity.py`**: PI SSH connectivity tests
  - SSH connection verification
  - Internet access validation
  - Disk space checks
  - chip-tool availability
  - Reboot and reconnection tests
  
- **`test/test_1_flashing.py`**: Device flashing tests
  - Device connection checks
  - Firmware flashing procedures
  
- **`test/test_2_system.py`**: System tests
- **`test/test_3_chiptool.py`**: Chip-tool pairing and operation tests

### 5. **Top-Level Scripts**
- **`flash_ip.py`**: Standalone device flashing script
  - Uses `DeviceFlasher` for IP-based flashing (not USB)

---

## Key Design Patterns

### Singleton Configuration
```python
from config.loader import ConfigLoader

config = ConfigLoader.instance()
pi_cfg = config.get("pi_config")
```

### Interface Abstraction
Each hardware interaction is abstracted:
```python
# SSH
from interface.ssh import SSHClient
ssh = SSHClient(config["pi_config"], log_dir=log_dir)
output, error = ssh.execute_command("ls -la")

# Device Flashing
from interface.commander import CommanderInterface
cmd = CommanderInterface(config["serial_config"])
cmd.flash_firmware(serial_number, firmware_path)

# RTT Logging
from interface.rtt import DeviceFlasher
flasher = DeviceFlasher(config["serial_config"], log_dir=log_dir)
flasher.start_rtt()
```

### Test Fixtures
Pytest fixtures manage resource lifecycle:
```python
@pytest.fixture(scope="session")
def pi_device(config):
    pi = SSHClient(config["pi_config"], log_dir=...)
    pi.connect()
    yield pi  # Test code runs here
    pi.disconnect()  # Cleanup after all tests
```

---

## Migration Notes

### Old vs New Module Names
| Old | New | Status |
|-----|-----|--------|
| `interface.ssh_interface.PI` | `interface.ssh.SSHClient` | Deprecated |
| `interface.serial_interface.CommanderInterface` | `interface.commander.CommanderInterface` | Moved |
| `utils.rtt_logger.DeviceFlasher` | `interface.rtt.DeviceFlasher` | Moved |
| `utils.helper_test` | Removed old `PI` import | Updated |

### Update Your Code
**Before:**
```python
from interface.ssh_interface import PI
from utils.helper_test import run_chip_tool_cmd

pi = PI("config.json")
```

**After:**
```python
from config.loader import ConfigLoader
from interface.ssh import SSHClient
from utils.helper_test import run_chip_tool_cmd

config = ConfigLoader.instance()
pi = SSHClient(config["pi_config"], log_dir=log_dir)
```

---

## Configuration File (`config.json`)

```json
{
  "pi_config": {
    "pi_host": "192.168.0.246",
    "pi_port": 22,
    "ssh_username": "ubuntu",
    "ssh_password": "password",
    "ssh_key_path": "",
    "chip_tool_path": "/usr/local/bin/chip-tool"
  },
  "chip_config": {
    "node_id": "1",
    "endpoint_id": "1",
    "setup_pin_code": "20202021",
    "discovery_type": "ble-thread"
  },
  "serial_config": {
    "commander_path": "/path/to/commander",
    "device": "EFR32MG24BXXXF1536",
    "ip": "192.168.0.10",
    "firmware_dir": "resources/firmware",
    "target_firmware": "resources/firmware/bt_soc_blinky.s37"
  },
  "log_path": "./Log"
}
```

---

## Running Tests

```bash
# Run all tests
pytest test/

# Run specific test file
pytest test/test_0_pi_connectivity.py

# Run with verbose output
pytest -v test/

# Run with log capture
pytest --tb=short test/
```

---

## Benefits of This Architecture

1. **Centralized Configuration**: All settings in one place (`config.json`)
2. **Interface Abstraction**: Swap implementations without changing tests
3. **Reusable Components**: Utils, loggers, and helpers shared across tests
4. **Clean Separation**: Config, interfaces, utils, and tests are independent
5. **Maintainability**: New developers can understand structure quickly
6. **Testability**: Easy to mock interfaces for unit testing
7. **Logging**: Centralized file logging for debugging
