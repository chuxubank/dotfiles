"""iv profile扩展：普通响应全部使用routes.json的standard文件路由。

仅保留二进制资源，以及请求后客户端立刻读取下一状态所需的JSON事务。
场景、业务响应和转换数据均放在data/；本文件不保存运行状态和审计日志。
"""
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "data"


def _data_file(name):
    # 仅允许读取或更新当前profile的data文件，禁止配置越界路径。
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("fixture path escapes data directory")
    return path


def handle_binary(interceptor, flow, rule):
    # 标准handler只读取JSON；本入口原样返回路由指定的本地图片。
    path = rule.file_path
    content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    interceptor.respond(flow, rule.status_code, path.read_bytes(), {
        "Content-Type": content_type,
        "Cache-Control": "no-store",
    })


def handle_json_transition(interceptor, flow, rule):
    # 仅用于POST后立刻GET：数据文件指定请求前置、响应及下一次读取的完整JSON。
    config = json.loads(rule.file_path.read_text(encoding="utf-8"))
    body = json.loads(flow.request.get_text() or "{}")
    expected = config.get("expected", {})
    if any(body.get(key) != value for key, value in expected.items()):
        response = config.get("on_mismatch", {
            "code": 1,
            "message": "Mock request does not match prepared transition",
            "data": {"error_code": "MOCK_TRANSITION_MISMATCH"},
        })
    else:
        # 先准备并验证全部路径，再切换文件；响应发送前下一次GET已可读取新内容。
        updates = [(_data_file(name), json.dumps(value, ensure_ascii=False, indent=2) + "\n")
                   for name, value in config.get("after", {}).items()]
        for path, text in updates:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        response = config["response"]
    interceptor.respond(flow, rule.status_code, json.dumps(response, ensure_ascii=False), {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
    })
