def verify_command_vs_device(pi_commands, device_results):
    print("\n=== STEP 3: MATCH COMMAND ↔ DEVICE RESULT ===\n")

    if len(device_results) < len(pi_commands):
        raise AssertionError(
            f"❌ Not enough device results ({len(device_results)}) "
            f"for commands ({len(pi_commands)})"
        )

    failures = []

    for i, cmd in enumerate(pi_commands):
        expected = cmd["action"]
        actual = device_results[i]

        success = False

        if expected == "toggle":
            success = actual in ["TURN_ON", "TURN_OFF"]

        elif expected == "on":
            success = actual in ["TURN_ON", "ALREADY_SET"]

        elif expected == "off":
            success = actual in ["TURN_OFF", "ALREADY_SET"]

        print(
            f"CMD #{i+1}: {expected:<6} -> {actual:<12} "
            f"=> {'✅ PASS' if success else '❌ FAIL'}"
        )

        if not success:
            failures.append((expected, actual))

    if failures:
        msg = "\n❌ FAILURES:\n"
        for exp, act in failures:
            msg += f" - expected={exp}, actual={act}\n"
        raise AssertionError(msg)

    print("\n✅ SUCCESS: All commands matched correctly!\n")
