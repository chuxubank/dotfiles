"""AA environment handlers."""

import time
from mitmproxy import ctx, http

FIRMWARE_DELAY_SECONDS = 1
FIRMWARE_REQUIRED_CALLS = 2


def handle_firmware(interceptor, flow: http.HTTPFlow, rule):
    """Firmware update request with delay and counting logic."""
    interceptor.firmware_call_count += 1
    ctx.log.info(
        f"Firmware request #{interceptor.firmware_call_count} "
        f"from {flow.client_conn.address[0]}"
    )

    time.sleep(FIRMWARE_DELAY_SECONDS)

    if interceptor.firmware_call_count >= FIRMWARE_REQUIRED_CALLS:
        ctx.log.info("Responding with 'success' state.")
    else:
        ctx.log.info("Responding with 'upgradable' state.")

    content = interceptor.get_json_content(rule.file_path) if rule.file_path else ""
    interceptor.respond(flow, 200, content)
