"""AA handlers for the mitmproxy-mock addon.

The firmware route counts calls in this module. The first response stays on
the route file; from the second call the log marks success, and the body is
still that file. The empty route returns no body.
"""

import json
import time

from mitmproxy import ctx, http

FIRMWARE_DELAY_SECONDS = 1
FIRMWARE_REQUIRED_CALLS = 2

_firmware_calls = 0


def handle_firmware(interceptor, flow: http.HTTPFlow, rule):
    global _firmware_calls
    _firmware_calls += 1
    ctx.log.info(
        f"Firmware request #{_firmware_calls} from {flow.client_conn.address[0]}"
    )
    time.sleep(FIRMWARE_DELAY_SECONDS)
    if _firmware_calls >= FIRMWARE_REQUIRED_CALLS:
        ctx.log.info("Responding with 'success' state.")
    else:
        ctx.log.info("Responding with 'upgradable' state.")
    if rule.file_path is None:
        raise RuntimeError("firmware handler requires file")
    content = rule.file_path.read_text(encoding="utf-8")
    json.loads(content)
    interceptor.respond(flow, 200, content)


def handle_empty(interceptor, flow: http.HTTPFlow, rule):
    if rule.delay_seconds > 0:
        time.sleep(rule.delay_seconds)
    interceptor.respond(flow, rule.status_code, b"")
