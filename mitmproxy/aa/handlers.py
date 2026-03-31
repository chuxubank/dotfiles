"""AA environment handlers."""

import time
import json
from mitmproxy import ctx, http


def handle_firmware(interceptor, flow: http.HTTPFlow, rule):
    """Firmware update request with delay and counting logic."""
    interceptor.firmware_call_count += 1
    ctx.log.info(
        f"Firmware request #{interceptor.firmware_call_count} "
        f"from {flow.client_conn.address[0]}"
    )

    time.sleep(interceptor.config.FIRMWARE_DELAY_SECONDS)

    if interceptor.firmware_call_count >= interceptor.config.FIRMWARE_REQUIRED_CALLS:
        ctx.log.info("Responding with 'success' state.")
    else:
        ctx.log.info("Responding with 'upgradable' state.")

    content = interceptor.get_json_content(rule.file_path) if rule.file_path else ""
    interceptor.respond(flow, interceptor.config.DEFAULT_STATUS, content)
