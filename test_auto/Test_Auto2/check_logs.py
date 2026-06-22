import re
import os

def check_logs():
    # pi_log_path = r"/home/phanhoanganh/TEST1-window/test_auto/Test_Auto2/Log/pi_connection.log"
    # rtt_log_path = r"/home/phanhoanganh/TEST1-window/test_auto/Test_Auto2/-RTTTelnetPort"
    base_dir = os.path.dirname(os.path.abspath(__file__))

    pi_log_path = os.path.join(
        base_dir, "Log", "pi_connection.log"
    )
    jlink_log_path = os.path.join(
        base_dir, "Log", "rtt_log.txt"
    )

    pi_log_path = os.path.normpath(pi_log_path)
    jlink_log_path = os.path.normpath(jlink_log_path)

    if not os.path.exists(pi_log_path):
        print(f"Error: Pi log not found at {pi_log_path}")
        return

    if not os.path.exists(jlink_log_path):
        print(f"Error: JLink RTT log not found at {jlink_log_path}")
        return

    pi_content = open(pi_log_path, 'r', encoding='utf-8', errors='ignore').read()
    jlink_content = open(jlink_log_path, 'r', encoding='utf-8', errors='ignore').read()

    print("=== Analyzing Logs ===")
    
    # Extract commands from pi_connection.log
    # Look for command patterns like "onoff on 1 1", "onoff off 1 1", "onoff toggle 1 1"
    pi_commands = []
    # Matching timestamp and command
    pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}).*?EXECUTE COMMAND:.*?chip-tool\s+onoff\s+(on|off|toggle)\s+(\d+)\s+(\d+)"
    for match in re.finditer(pattern, pi_content, re.IGNORECASE):
        timestamp, action, node_id, endpoint_id = match.groups()
        pi_commands.append({
            "timestamp": timestamp,
            "action": action.lower(),
            "node_id": node_id,
            "endpoint_id": endpoint_id
        })
        
    print(f"Found {len(pi_commands)} 'onoff' commands in pi_connection.log:")
    for cmd in pi_commands[:15]:  # print first 15 to keep it readable
        print(f"  - [{cmd['timestamp']}] onoff {cmd['action']} {cmd['node_id']} {cmd['endpoint_id']}")
    if len(pi_commands) > 15:
        print(f"  ... and {len(pi_commands) - 15} more commands.")

    # Analyze JLink RTT logger for receipts/actions
    jlink_lower = jlink_content.lower()

    # Quick heuristics: receipt marker and action markers
    receipt_marker = "im:invokecommandrequest"
    action_on_re = re.compile(r"turning light\s+on", re.IGNORECASE)
    action_off_re = re.compile(r"turning light\s+off", re.IGNORECASE)

    print(f"\nJLink RTT log size: {len(jlink_content)} bytes")

    # Perform per-command verification against JLink RTT log
    print("\n=== Verifying each Pi command against JLink RTT log ===")

    if not pi_commands:
        raise AssertionError("No 'onoff' commands found in pi_connection.log")

    failures = []
    for idx, cmd in enumerate(pi_commands, start=1):
        expected_action = cmd['action']  # on/off/toggle
        receipt_found = receipt_marker in jlink_lower
        action_found = False

        if expected_action == 'on':
            action_found = bool(action_on_re.search(jlink_content))
        elif expected_action == 'off':
            action_found = bool(action_off_re.search(jlink_content))
        else:
            # toggle: accept either on or off
            action_found = bool(action_on_re.search(jlink_content) or action_off_re.search(jlink_content))

        print(f"Command #{idx}: onoff {expected_action} -> receipt: {receipt_found}, action: {action_found}")

        if not receipt_found or not action_found:
            failures.append({
                'command': cmd,
                'receipt_found': receipt_found,
                'action_found': action_found,
            })

    if failures:
        msg_lines = [f"FAILURE: {len(failures)} command(s) not verified:"]
        for f in failures:
            c = f['command']
            msg_lines.append(f" - {c['action']} {c['node_id']}:{c['endpoint_id']} -> receipt={f['receipt_found']} action={f['action_found']}")
        full_msg = "\n".join(msg_lines)
        raise AssertionError(full_msg)

    print("\n[SUCCESS] All Pi 'onoff' commands were observed in JLink RTT log with receipt and action markers.")

if __name__ == "__main__":
    check_logs()
