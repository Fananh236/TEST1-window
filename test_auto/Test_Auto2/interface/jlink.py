def build_jlink_remote_server_command(sn):
    return ["JLinkRemoteServer", "-SelectEmuBySN", sn]


def build_jlink_rtt_logger_command(device, ip_address, log_file):
    return [
        "JLinkRTTLogger",
        "-Device",
        device,
        "-If",
        "SWD",
        "-Speed",
        "4000",
        "-RTTChannel",
        "0",
        "-IP",
        ip_address,
        "-RTTTelnetPort",
        "19020",
        "-Silent",
        log_file,
    ]
