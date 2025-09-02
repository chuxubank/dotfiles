import re
import time
import json
from pathlib import Path
from typing import (
    Dict,
    List,
    Optional,
    Callable,
    Any,
)
from mitmproxy import ctx, http
from functools import lru_cache
from dataclasses import dataclass, field


# --- Configuration Center ---
# Centralizes all configurations for clarity.
class Config:

    SCRIPT_DIR = Path(__file__).parent.resolve()
    CONFIG_DIR = SCRIPT_DIR / "data"

    # Response data file paths.
    # Managed by a dictionary for easy access by key.
    RESPONSE_FILES = {
        "FIRMWARE_UPGRADABLE": CONFIG_DIR / "firmware_upgradable.json",
        "CAPABILITIES": CONFIG_DIR / "capabilities.json",
        "APP_VERSION": CONFIG_DIR / "app_version.json",
        "APP_FEATURE": CONFIG_DIR / "app_feature.json",
        "HOUSES_MANAGED_USER": CONFIG_DIR / "houses_managed_user.json",
    }

    # Default response settings.
    DEFAULT_HEADERS = {"Content-Type": "application/json; charset=utf-8"}
    DEFAULT_STATUS = 200

    # Parameters for specific logic.
    FIRMWARE_DELAY_SECONDS = 1
    FIRMWARE_REQUIRED_CALLS = 2
    OTA_DELAY_SECONDS = 1


# --- Route Definition ---
@dataclass
class Route:
    """A dataclass to represent a URL routing rule with configurable responses."""

    pattern_str: str
    handler_name: str
    file_key: Optional[str] = None
    response_json: Optional[Dict[str, Any]] = None
    status_code: int = Config.DEFAULT_STATUS
    compiled_pattern: re.Pattern = field(init=False)

    def __post_init__(self):
        """Compile the regex pattern after the object is created."""
        self.compiled_pattern = re.compile(self.pattern_str)


# --- Core Handler ---
class RequestInterceptor:
    # Define rules using the structured Route dataclass.
    # This is very clean, self-documenting, and easy to expand.
    URL_ROUTES: List[Route] = [
        Route(
            r".*/remotedevices/azureDragonModule/locks/.*/firmware",
            "_handle_firmware_request",
            file_key="FIRMWARE_UPGRADABLE",
        ),
        Route(r".*/remoteoperate/.*/ota", "_handle_ota_request"),
        Route(
            r".*/devices/capabilities\?deviceType=lock.*",
            "_handle_standard_response",
            file_key="CAPABILITIES",
        ),
        Route(
            r".*/appversionok/android/.*",
            "_handle_standard_response",
            file_key="APP_VERSION",
        ),
        Route(
            r".*/appfeatures/android/.*",
            "_handle_standard_response",
            file_key="APP_FEATURE",
        ),
        Route(
            pattern_str=r".*/houses/.*/manageduser/.*",
            handler_name="_handle_standard_response",
            status_code=429,
            response_json={
                "code": "TooManyRequests",
                "message": "Request limit reached. Count: 66, Limit: 15 per 3600 second",
            },
        ),
    ]

    def __init__(self):
        # State counter for specific requests.
        self.firmware_call_count = 0
        # The routes are already defined and self-contained with compiled patterns.
        self.url_mapping = self.URL_ROUTES

    @staticmethod
    @lru_cache(maxsize=16)
    def _get_json_content(file_path: Path) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                ctx.log.info(f"✅ Successfully loaded and cached JSON from {file_path}")
                return json.dumps(content, ensure_ascii=False)
        except FileNotFoundError:
            ctx.log.error(
                f"❌ CRITICAL: JSON file not found at {file_path}. Make sure the file exists in the 'mock_data' directory next to the script."
            )
            return json.dumps(
                {"error": "Server configuration error: mock file not found."}
            )
        except json.JSONDecodeError as e:
            ctx.log.error(f"❌ Error parsing JSON from {file_path}: {e}")
            return json.dumps({"error": f"Failed to parse data from {file_path.name}"})

    def _create_response(
        self,
        flow: http.HTTPFlow,
        status_code: int,
        content: str,
        headers: Dict[str, str],
    ):
        """Helper function to create responses uniformly."""
        flow.response = http.Response.make(status_code, content, headers)

    # --- Request Handlers ---

    def _handle_standard_response(self, flow: http.HTTPFlow, rule: Route):
        """
        A powerful, generic handler that creates a response based on the Route's configuration.
        It can return from a file or a direct JSON object, with a custom status code.
        """
        ctx.log.info(f"Matched standard rule for: {flow.request.pretty_url}")
        content = ""
        # Priority 1: Use direct JSON response if provided.
        if rule.response_json is not None:
            content = json.dumps(rule.response_json, ensure_ascii=False)
            ctx.log.info(
                f"Responding with direct JSON content, status {rule.status_code}."
            )
        # Priority 2: Fallback to file-based response.
        elif rule.file_key:
            content = self._get_json_content(Config.RESPONSE_FILES[rule.file_key])
            ctx.log.info(
                f"Responding from file '{rule.file_key}', status {rule.status_code}."
            )

        self._create_response(flow, rule.status_code, content, Config.DEFAULT_HEADERS)

    def _handle_firmware_request(self, flow: http.HTTPFlow, file_key: str):
        """Handles firmware update requests with delay and counting logic."""
        self.firmware_call_count += 1
        ctx.log.info(
            f"🔥 Firmware request #{self.firmware_call_count} from {flow.client_conn.address[0]}"
        )

        time.sleep(Config.FIRMWARE_DELAY_SECONDS)

        if self.firmware_call_count >= Config.FIRMWARE_REQUIRED_CALLS:
            ctx.log.info("Responding with 'success' state logic.")
        else:
            ctx.log.info("Responding with 'upgradable' state logic.")

        content = self._get_json_content(Config.RESPONSE_FILES[file_key])
        self._create_response(
            flow, Config.DEFAULT_STATUS, content, Config.DEFAULT_HEADERS
        )

    def _handle_ota_request(self, flow: http.HTTPFlow, file_key: Optional[str] = None):
        """Handles OTA requests with a delay and an empty response body."""
        ctx.log.info(f"📡 OTA request from {flow.client_conn.address[0]}")
        time.sleep(Config.OTA_DELAY_SECONDS)
        self._create_response(flow, Config.DEFAULT_STATUS, "", Config.DEFAULT_HEADERS)

    # --- Main Request Processor ---
    def process_request(self, flow: http.HTTPFlow):
        """Main processing function."""
        for rule in self.url_mapping:
            if rule.compiled_pattern.search(flow.request.pretty_url):
                try:
                    handler: Callable = getattr(self, rule.handler_name)
                    # Pass the whole rule object to the handler
                    handler(flow, rule)
                except Exception as e:
                    ctx.log.error(f"Error in handler for '{rule.pattern_str}': {e}")
                    self._create_response(
                        flow,
                        500,
                        json.dumps({"error": "Internal server error"}),
                        Config.DEFAULT_HEADERS,
                    )
                return
        ctx.log.warn(f"No handler matched for URL: {flow.request.pretty_url}")


# --- mitmproxy Addon Entrypoints ---

# Create a global instance of the interceptor.
interceptor = RequestInterceptor()


def request(flow: http.HTTPFlow) -> None:
    """The 'request' event hook for mitmproxy."""
    ctx.log.info(
        f"--> Intercepted request: {flow.request.method} {flow.request.pretty_url}"
    )
    interceptor.process_request(flow)
