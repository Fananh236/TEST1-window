import re
import time


def _select_target_device(config, device_name=None):
    serial_config = config.get("serial_config", {}) or {}
    devices = serial_config.get("devices", []) or []

    if device_name:
        for device in devices:
            if device.get("name") == device_name:
                return device

    return devices[0] if devices else None


def resolve_chip_target(config, device_name=None):
    """Resolve chip target values from chip_config or from serial_config.devices."""
    chip = dict(config.get("chip_config", {}) or {})
    target_device = _select_target_device(config, device_name)

    if target_device is not None:
        for key in ("node_id", "endpoint_id"):
            if key in target_device and (key not in chip or not chip.get(key)):
                chip[key] = str(target_device[key])

    return chip


# =========================================================
# FETCH THREAD DATASET
# =========================================================
def fetch_thread_data_set(pi_device):

    cmd = f"echo '{pi_device.password}' | sudo -S -p '' ot-ctl dataset active -x"

    out, err = pi_device.execute_command(cmd)

    # ✅ ignore sudo password prompt
    if err and "password" not in err.lower():
        return None, err

    if not out:
        return None, "no_output"

    # ✅ parse dataset (clean 'Done')
    dataset = None
    for line in out.splitlines():
        line = line.strip()
        if line and line.lower() != "done":
            dataset = line
            break

    if not dataset:
        return None, "invalid_dataset"

    # ✅ validate hex
    if not all(c in "0123456789abcdefABCDEF" for c in dataset):
        return None, f"invalid_hex: {dataset}"
    
    
    dataset = f"hex:{dataset}"
    print(f"[DEBUG] DATASET: {dataset}")
    
    
    return dataset , None


# =========================================================
# SEND TOGGLE COMMAND
# =========================================================
def send_toggle_command(pi_device, config, label):

    print(f"\n🚀 Sending command: {label}")

    chip = resolve_chip_target(config)

    toggle_cmd = (
        f"echo '{pi_device.password}' | sudo -S -p '' {pi_device.chip_tool_path} "
        f"onoff toggle {chip['node_id']} {chip['endpoint_id']}"
    )

    stdout, stderr = pi_device.execute_command(toggle_cmd)

    print("[DEBUG STDOUT]\n", stdout)
    print("[DEBUG STDERR]\n", stderr)

    full_response = (stdout + "\n" + stderr).lower()

    # ✅ detect lỗi thật
    if "timeout" in full_response:
        raise RuntimeError("❌ Timeout → device NOT reachable via Thread")
    if "run command failure" in full_response:
        raise RuntimeError("❌ chip-tool execution failed")

    print(f"✅ {label} executed successfully!\n")

    return stdout


# =========================================================
# RUN PAIRING
# =========================================================
def run_pairing(pi_device, config):

    chip = resolve_chip_target(config)

    print("\n=========== START PAIRING ===========")

    # ✅ CLEAN chip-tool KVS (rất quan trọng)
    pi_device.execute_command(
        f"echo '{pi_device.password}' | sudo -S rm -rf /tmp/chip_*"
    )

    # =====================================================
    # FETCH DATASET
    # =====================================================
    dataset, err = fetch_thread_data_set(pi_device)

    if err or not dataset:
        raise RuntimeError(f"❌ Thread dataset missing: {err}")

    # =====================================================
    # BUILD PAIRING CMD
    # =====================================================
    pairing_cmd = (
        f"echo '{pi_device.password}' | sudo -S -p '' {pi_device.chip_tool_path} "
        f"pairing {chip['discovery_type']} "
        f"{chip['node_id']} "
        f"{dataset} "
        f"{chip['setup_pin_code']} "
        f"{chip['discriminator']}"
    )

    print(f"[DEBUG] pairing_cmd = {pairing_cmd}")

    output, _ = pi_device.execute_command(pairing_cmd)

    print("[DEBUG PAIRING OUTPUT]\n", output)

    # =====================================================
    # CHECK PAIRING SUCCESS
    # =====================================================
    if "device commissioning completed with success" not in output.lower():
        raise RuntimeError("❌ Pairing FAILED")

    print("✅ Pairing SUCCESS")

    # =====================================================
    # 🔥 CRITICAL: WAIT NODE READY
    # =====================================================
    print("⏳ Waiting device ready...")
    time.sleep(5)

    # =====================================================
    # OPTIONAL: CHECK THREAD STATE (pi side)
    # =====================================================
    state_out, _ = pi_device.execute_command("ot-ctl state")
    print("[DEBUG] Thread state (Pi):", state_out)

    # không fail cứng vì Pi có thể leader/router
    # chỉ warning thôi
    if not any(x in state_out.lower() for x in ["leader", "router"]):
        print("⚠️ WARN: Thread network may not be ready")

    print("=========== PAIRING DONE ===========\n")

    return True, None
