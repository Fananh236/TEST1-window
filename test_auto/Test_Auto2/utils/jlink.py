def _build_jlink_remote_server_cmd(sn):
        return [
            "JLinkRemoteServer",
            "-SelectEmuBySN",
            sn,
        ]


def _build_jlink_rtt_logger_cmd(device, ip ,rtt_log_file):
        ip_port = f"{ip}:19020"
        return [
            "JLinkRTTLogger",
            "-Device", device,
            "-If", "SWD",
            "-Speed", "4000",
            "-RTTChannel", "0",
            "-IP", ip_port,rtt_log_file ,
            "-Silent"
            
        ]

