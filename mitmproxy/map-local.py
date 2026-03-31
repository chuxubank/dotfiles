import os
import re
import sys
import time
import json
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from mitmproxy import ctx, http
from functools import lru_cache
from dataclasses import dataclass, field


# --- Configuration ---
class Config:
    SCRIPT_DIR = Path(__file__).parent.resolve()
    HOST_ENV = os.environ.get("HOST_ENV", "aa")
    ENV_DIR = SCRIPT_DIR / HOST_ENV
    DATA_DIR = ENV_DIR / "data"

    DEFAULT_HEADERS = {"Content-Type": "application/json; charset=utf-8"}
    DEFAULT_STATUS = 200
    DEFAULT_DELAY_SECONDS = 1


# --- Route Definition ---
@dataclass
class Route:
    pattern_str: str
    handler_name: str
    file_path: Optional[Path] = None
    response_json: Optional[Dict[str, Any]] = None
    status_code: int = Config.DEFAULT_STATUS
    delay_seconds: float = Config.DEFAULT_DELAY_SECONDS
    compiled_pattern: re.Pattern = field(init=False)

    def __post_init__(self):
        self.compiled_pattern = re.compile(self.pattern_str)


# --- Handler Loading ---
def _load_env_handlers(env_dir: Path) -> Dict[str, Callable]:
    """Import handlers.py from the environment directory if it exists."""
    handlers_file = env_dir / "handlers.py"
    if not handlers_file.exists():
        return {}

    # Add env dir to sys.path so the module can be imported
    env_dir_str = str(env_dir)
    if env_dir_str not in sys.path:
        sys.path.insert(0, env_dir_str)

    module_name = f"handlers_{Config.HOST_ENV}"
    spec = importlib.util.spec_from_file_location(module_name, handlers_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Collect all handle_* functions
    handlers = {}
    for name in dir(module):
        if name.startswith("handle_"):
            key = name[len("handle_"):]  # handle_firmware -> firmware
            handlers[key] = getattr(module, name)

    return handlers


def _load_routes(env_handlers: Dict[str, Callable]) -> List[Route]:
    """Load routes from the environment-specific routes.json."""
    routes_file = Config.ENV_DIR / "routes.json"
    try:
        with open(routes_file, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except FileNotFoundError:
        ctx.log.error(f"Routes file not found: {routes_file}")
        return []
    except json.JSONDecodeError as e:
        ctx.log.error(f"Failed to parse routes file {routes_file}: {e}")
        return []

    routes: List[Route] = []
    for entry in entries:
        handler_name = entry.get("handler", "standard")
        file_path = Config.DATA_DIR / entry["file"] if "file" in entry else None
        routes.append(
            Route(
                pattern_str=entry["pattern"],
                handler_name=handler_name,
                file_path=file_path,
                status_code=entry.get("status_code", Config.DEFAULT_STATUS),
                delay_seconds=entry.get("delay_seconds", Config.DEFAULT_DELAY_SECONDS),
            )
        )
    return routes


# --- Core Handler ---
class RequestInterceptor:
    def __init__(self):
        self.config = Config
        self.firmware_call_count = 0

        # Load env-specific handlers, then routes
        self._env_handlers = _load_env_handlers(Config.ENV_DIR)
        self.routes = _load_routes(self._env_handlers)

        env_handler_names = list(self._env_handlers.keys()) or "(none)"
        ctx.log.info(
            f"HOST_ENV={Config.HOST_ENV!r}: "
            f"{len(self.routes)} routes, env handlers: {env_handler_names}"
        )

    @staticmethod
    @lru_cache(maxsize=16)
    def get_json_content(file_path: Path) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                ctx.log.info(f"Loaded and cached JSON from {file_path}")
                return json.dumps(content, ensure_ascii=False)
        except FileNotFoundError:
            ctx.log.error(f"JSON file not found: {file_path}")
            return json.dumps({"error": "Mock file not found."})
        except json.JSONDecodeError as e:
            ctx.log.error(f"Error parsing JSON from {file_path}: {e}")
            return json.dumps({"error": f"Failed to parse {file_path.name}"})

    def respond(
        self, flow: http.HTTPFlow, status_code: int, content: str,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Public helper for handlers to create responses."""
        flow.response = http.Response.make(
            status_code, content, headers or Config.DEFAULT_HEADERS
        )

    # --- Built-in Handler ---
    def _handle_standard(self, flow: http.HTTPFlow, rule: Route):
        ctx.log.info(f"Matched standard rule for: {flow.request.pretty_url}")
        if rule.delay_seconds > 0:
            time.sleep(rule.delay_seconds)

        content = ""
        if rule.response_json is not None:
            content = json.dumps(rule.response_json, ensure_ascii=False)
        elif rule.file_path:
            content = self.get_json_content(rule.file_path)

        self.respond(flow, rule.status_code, content)

    def _resolve_handler(self, name: str) -> Callable:
        """Resolve handler by name: env handlers take priority over built-in."""
        if name in self._env_handlers:
            fn = self._env_handlers[name]
            # Wrap env handler: fn(interceptor, flow, rule)
            return lambda flow, rule: fn(self, flow, rule)
        builtin = f"_handle_{name}"
        if hasattr(self, builtin):
            return getattr(self, builtin)
        raise AttributeError(f"Unknown handler: {name!r}")

    def process_request(self, flow: http.HTTPFlow):
        for rule in self.routes:
            if rule.compiled_pattern.search(flow.request.pretty_url):
                try:
                    handler = self._resolve_handler(rule.handler_name)
                    handler(flow, rule)
                except Exception as e:
                    ctx.log.error(f"Error in handler for '{rule.pattern_str}': {e}")
                    self.respond(
                        flow, 500, json.dumps({"error": "Internal server error"})
                    )
                return


# --- mitmproxy Addon Entrypoints ---
interceptor = RequestInterceptor()


def request(flow: http.HTTPFlow) -> None:
    ctx.log.info(f"--> Intercepted: {flow.request.method} {flow.request.pretty_url}")
    interceptor.process_request(flow)
