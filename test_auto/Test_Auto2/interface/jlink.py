def build_jlink_remote_server_command(sn):
    return ["JLinkRemoteServer", "-SelectEmuBySN", sn]


def build_jlink_rtt_logger_command(device, ip_address, log_file):
    cmd = [
        "JLinkRTTLogger",
        "-Device",
        device,
        "-If",
        "SWD",
        "-Speed",
        "4000",
        "-RTTChannel",
        "0",
    ]
    if ip_address:
        if ":" not in ip_address:
            cmd += ["-IP", f"{ip_address}:19020"]
        else:
            cmd += ["-IP", ip_address]
    cmd += [log_file]
    return cmd
