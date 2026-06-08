def build_jlink_remote_server_command(ip_address):
    return ["JLinkRemoteServer", "-SelectEmuByIP", ip_address]


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
