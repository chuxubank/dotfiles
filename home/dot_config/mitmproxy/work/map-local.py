import re
import time
import json
from pathlib import Path
from typing import Dict
from mitmproxy import ctx, http


# Configuration
class Config:
    # URL patterns
    FIRMWARE_URL_PATTERN = r".*/remotedevices/azureDragonModule/locks/.*/firmware"
    OTA_URL_PATTERN = r".*/remoteoperate/.*/ota"
    CAPABILITIES_PATTERN = r".*/devices/capabilities\?deviceType=lock.*"
    APP_VERSION_PATTERN = r".*/appversionok/android/.*"
    APP_FEATURE_PATTERN = r".*/appfeatures/android/.*"
    HOUSES_MANAGED_USER_PATTERN = r".*/houses/.*/manageduser/.*"

    # File paths
    CONFIG_DIR = Path.home() / ".config" / "mitmproxy" / "work"
    FIRMWARE_UPGRADABLE = CONFIG_DIR / "firmware_upgradable.json"
    FIRMWARE_UPGRADING = CONFIG_DIR / "firmware_upgrading.json"
    FIRMWARE_SUCCESS = CONFIG_DIR / "firmware_success.json"
    CAPABILITIES_RESPONSE = CONFIG_DIR / "capabilities.json"
    APP_VERSION_RESPONSE = CONFIG_DIR / "app_version.json"
    APP_FEATURE_RESPONSE = CONFIG_DIR / "app_feature.json"

    # Timing and counter settings
    DELAY_SECONDS = 1
    REQUIRED_CALLS = 2

    # Response settings
    DEFAULT_HEADERS = {"Content-Type": "application/json"}
    DEFAULT_STATUS = 200


class ResponseHandler:
    def __init__(self):
        self.call_count = 0

    def _read_json_file(self, file_path: Path) -> str:
        """Read JSON file content without caching."""
        with open(file_path, "r") as f:
            content = json.load(f)
            ctx.log.info(f"Successfully loaded and validated JSON from {file_path}")
            return json.dumps(content)

    def handle_firmware_request(self, flow: http.HTTPFlow) -> None:
        """Handle firmware update requests."""
        self.call_count += 1
        ctx.log.info(
            f"Firmware request #{self.call_count} from {flow.client_conn.address[0]}"
        )
        ctx.log.debug(f"Request headers: {dict(flow.request.headers)}")

        # Apply delay
        ctx.log.info(f"Applying {Config.DELAY_SECONDS}s delay")
        time.sleep(Config.DELAY_SECONDS)

        # Set response
        response_content = self._read_json_file(Config.FIRMWARE_UPGRADABLE)
        flow.response = http.Response.make(
            Config.DEFAULT_STATUS, response_content, Config.DEFAULT_HEADERS
        )

        response_type = (
            "success" if self.call_count >= Config.REQUIRED_CALLS else "regular"
        )
        ctx.log.info(
            f"Responded with {response_type} response to {flow.client_conn.address[0]}"
        )

    def handle_ota_request(self, flow: http.HTTPFlow) -> None:
        """Handle OTA update requests."""
        ctx.log.info(f"OTA request received from {flow.client_conn.address[0]}")
        ctx.log.debug(f"Request headers: {dict(flow.request.headers)}")

        ctx.log.info(f"Applying {Config.DELAY_SECONDS}s delay")
        time.sleep(Config.DELAY_SECONDS)

        flow.response = http.Response.make(
            Config.DEFAULT_STATUS, "", Config.DEFAULT_HEADERS
        )
        ctx.log.info(f"OTA request handled for {flow.client_conn.address[0]}")

    def handle_capabilities_request(self, flow: http.HTTPFlow) -> None:
        """Handle device capabilities requests."""
        ctx.log.info(
            f"Capabilities request received from {flow.client_conn.address[0]}"
        )

        # Set response
        response_content = self._read_json_file(Config.CAPABILITIES_RESPONSE)
        flow.response = http.Response.make(
            Config.DEFAULT_STATUS, response_content, Config.DEFAULT_HEADERS
        )

    def handle_app_version_request(self, flow: http.HTTPFlow) -> None:
        """Handle app version requests."""
        ctx.log.info(f"App version request received from {flow.client_conn.address[0]}")

        # Set response
        response_content = self._read_json_file(Config.APP_VERSION_RESPONSE)
        flow.response = http.Response.make(
            Config.DEFAULT_STATUS, response_content, Config.DEFAULT_HEADERS
        )

    def handle_app_feature_request(self, flow: http.HTTPFlow) -> None:
        """Handle app feature requests."""
        ctx.log.info(f"App feature request received from {flow.client_conn.address[0]}")

        # Set response
        response_content = self._read_json_file(Config.APP_FEATURE_RESPONSE)
        flow.response = http.Response.make(
            Config.DEFAULT_STATUS, response_content, Config.DEFAULT_HEADERS
        )

    def handle_houses_managed_user_request(self, flow: http.HTTPFlow) -> None:
        """Handle houses managed users request."""
        ctx.log.info(
            f"Houses managed users received from {flow.client_conn.address[0]}"
        )

        # Set response
        response_content = self._read_json_file(Config.APP_FEATURE_RESPONSE)
        flow.response = http.Response.make(
            Config.DEFAULT_STATUS, response_content, Config.DEFAULT_HEADERS
        )


# Global handler instance
handler = ResponseHandler()


def request(flow: http.HTTPFlow) -> None:
    """Main request handler."""
    try:
        ctx.log.info(f"Received request: {flow.request.pretty_url}")

        if re.search(Config.FIRMWARE_URL_PATTERN, flow.request.pretty_url):
            handler.handle_firmware_request(flow)
        elif re.search(Config.OTA_URL_PATTERN, flow.request.pretty_url):
            handler.handle_ota_request(flow)
        elif re.search(Config.CAPABILITIES_PATTERN, flow.request.pretty_url):
            handler.handle_capabilities_request(flow)
        elif re.search(Config.APP_VERSION_PATTERN, flow.request.pretty_url):
            handler.handle_app_version_request(flow)
        elif re.search(Config.APP_FEATURE_PATTERN, flow.request.pretty_url):
            handler.handle_app_feature_request(flow)
        elif re.search(Config.HOUSES_MANAGED_USER_PATTERN, flow.request.pretty_url):
            handler.handle_houses_managed_user_request(flow)
        else:
            ctx.log.warn(f"No handler found for URL: {flow.request.pretty_url}")
    except Exception as e:
        ctx.log.error(f"Error handling request: {e}")
        flow.response = http.Response.make(
            500, json.dumps({"error": "Internal server error"}), Config.DEFAULT_HEADERS
        )
