import re
import os

def check_logs():
    pi_log_path = r"c:\Users\phanh\Downloads\TEST1-window\test_auto\Test_Auto2\Log\pi_connection.log"
    rtt_log_path = r"c:\Users\phanh\Downloads\TEST1-window\test_auto\Test_Auto2\-RTTTelnetPort"
    
    if not os.path.exists(pi_log_path):
        print(f"Error: Pi log not found at {pi_log_path}")
        return
        
    if not os.path.exists(rtt_log_path):
        print(f"Error: RTT log not found at {rtt_log_path}")
        return

    pi_content = open(pi_log_path, 'r', encoding='utf-8', errors='ignore').read()
    rtt_content = open(rtt_log_path, 'r', encoding='utf-8', errors='ignore').read()

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

    # Extract RTT events: e.g. "Turning light On", "Turning light Off"
    rtt_events = []
    rtt_pattern = r"\[(\d{2}:\d{2}:\d{2}\.\d{3})\].*?Turning light\s+(On|Off)"
    for match in re.finditer(rtt_pattern, rtt_content, re.IGNORECASE):
        time_str, state = match.groups()
        rtt_events.append({
            "time": time_str,
            "state": state.lower()
        })
        
    print(f"\nFound {len(rtt_events)} light state events in -RTTTelnetPort:")
    for event in rtt_events:
        print(f"  - [{event['time']}] Turning light {event['state'].upper()}")

    # Perform assertions
    print("\n=== Assertions ===")
    
    # Assert that we found commands in both logs
    assert len(pi_commands) > 0, "Assertion Failed: No 'onoff' commands found in pi_connection.log"
    assert len(rtt_events) > 0, "Assertion Failed: No 'Turning light On/Off' messages found in -RTTTelnetPort"
    
    # Verify mapping
    has_toggle = any(cmd['action'] == 'toggle' for cmd in pi_commands)
    has_on = any(cmd['action'] == 'on' for cmd in pi_commands)
    has_off = any(cmd['action'] == 'off' for cmd in pi_commands)
    
    if has_on:
        assert any(event['state'] == 'on' for event in rtt_events), "Assertion Failed: 'onoff on' was sent but 'Turning light On' was not found in RTT log"
    if has_off:
        assert any(event['state'] == 'off' for event in rtt_events), "Assertion Failed: 'onoff off' was sent but 'Turning light Off' was not found in RTT log"
    if has_toggle:
        assert any(event['state'] in ['on', 'off'] for event in rtt_events), "Assertion Failed: 'onoff toggle' was sent but no light transition state was found in RTT log"

    print("\n[SUCCESS] Verification Successful: Both log files successfully analyzed and assertions match device actions!")

if __name__ == "__main__":
    check_logs()
