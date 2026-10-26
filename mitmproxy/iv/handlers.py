"""Read-only, test-environment mocks for the three crush ritual reward UIs.

No account/token logging, no real reward writes, no production interception.
Loaded by map-local.py with HOST_ENV=iv. Each request rereads data/crush-ritual-scenario.json.
"""
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from mitmproxy import ctx

ROOT = Path(__file__).resolve().parent
SCENARIO = ROOT / "data" / "crush-ritual-scenario.json"
ASSETS = Path(os.environ.get(
    "IVC_MOCK_ASSETS",
    "/Users/misaka/Developer/InfinityValley/ivc.feat-love-journal/composeApp/src/commonMain/composeResources/drawable",
))
ITEMS = {99003001: 1, 99003002: 2, 99004501: 3}
NAMES = {1: "恋恋手账：恰逢其时", 2: "恋恋手账：心跳作证", 3: "恋恋手账：阵雨转晴"}
MODES = {"baseline", "list", "upgrade", "unlocked", "long", "detail-error"}


def config():
    value = json.loads(SCENARIO.read_text())
    if value["scenario"] not in MODES:
        raise ValueError("unknown crush mock scenario")
    return value


def role_id(flow, settings):
    # Match real server role selection without printing authentication material.
    query = parse_qs(urlsplit(flow.request.url).query)
    value = flow.request.cookies.get("role_id") or query.get("role_id", [settings["role_id"]])[0]
    return int(value)


def reply(interceptor, flow, data, status=200):
    interceptor.respond(flow, status, json.dumps(data, ensure_ascii=False), {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "X-IVC-Mock": "crush-ritual",
    })


def success(interceptor, flow, data):
    reply(interceptor, flow, {"code": 0, "message": "", "data": data})


def image_url(flow, role):
    cover = "sol" if role == 1100001 else "lu"
    # HTTPDNS may use an IP connection address; retain the matched HTTP host.
    return f"https://{flow.request.pretty_host}/__ivc_mock__/crush-cover-{cover}.webp"


def reward(flow, item_id, locked, role):
    return {
        "type": "item", "item_id": item_id, "item_num": 1, "item_type": 99,
        "name": NAMES[ITEMS[item_id]], "rarity": 2 if item_id == 99003001 else 1,
        "icon_url": image_url(flow, role), "is_locked": int(locked),
    }


def crush_info(settings):
    mode = settings["scenario"]
    current, required = settings["current_rounds"], settings["required_rounds"]
    unlocks = [
        {"description": "", "reward_description": NAMES[2], "type": 1},
        {"description": "", "reward_description": NAMES[1], "type": 2,
         "condition_description": f"(聊天轮次暂未达标：{current}/{required})"},
    ]
    if mode == "long":
        unlocks[1]["reward_description"] = "恋恋手账：一段很长的服务端奖励标题，用于检查窄屏换行"
        unlocks[1]["condition_description"] = f"(聊天轮次暂未达标：{current}/{required}，继续积累属于你们的回忆，条件说明不应被截断)"
    if mode == "unlocked":
        unlocks[1] = {"description": "", "reward_description": NAMES[1], "type": 0}
    return {
        "relationship": 3, "level": 29 if mode == "baseline" else 30,
        "current_exp": 40, "next_level_exp": 100,
        "added_exp": 1 if mode in {"upgrade", "long", "unlocked"} else 0,
        "level_up": 1 if mode in {"upgrade", "long", "unlocked"} else 0,
        "new_level_unlock_list": unlocks if mode != "baseline" else [],
        # Never post synthetic rewards into the normal obtained-reward overlay.
        "crush_reward_items": [],
    }


def handle_crush_ritual(interceptor, flow, rule):
    path = urlsplit(flow.request.url).path
    if flow.request.method != "GET":
        return
    if path.startswith("/__ivc_mock__/crush-cover-"):
        cover = {"/__ivc_mock__/crush-cover-lu.webp": "love_journal_cover_lu.webp",
                 "/__ivc_mock__/crush-cover-sol.webp": "love_journal_cover_sol.webp"}.get(path)
        if cover:
            interceptor.respond(flow, 200, (ASSETS / cover).read_bytes(), {
                "Content-Type": "image/webp", "Cache-Control": "no-store", "X-IVC-Mock": "crush-ritual",
            })
        return
    item_id = None
    if path == "/queen/game/get-item-detail":
        item_id = parse_qs(urlsplit(flow.request.url).query).get("item_id", [""])[0]
        if item_id not in {str(item) for item in ITEMS}:
            return  # Real mall items remain untouched.
        item_id = int(item_id)
    try:
        settings = config()
        mode = settings["scenario"]
        role = role_id(flow, settings)
        if path == "/queen/game/list-crush-configs":
            configs = []
            for level in range(1, 101):
                relationship = 1 if level < 10 else 2 if level < 25 else 3 if level < 50 else 4
                rewards = []
                if level == 30:
                    rewards = [reward(flow, 99003001, mode != "unlocked", role), reward(flow, 99003002, False, role)]
                elif level == 45:
                    rewards = [reward(flow, 99004501, mode != "unlocked", role)]
                configs.append({
                    "level": level, "exp": 100, "relationship": relationship,
                    "relationship_name": {1: "朋友", 2: "心动", 3: "信任", 4: "热恋"}[relationship],
                    "description": "" if rewards else f"等级 {level} 的成长奖励（Mock）",
                    "rewards": rewards, "more": "",
                })
            success(interceptor, flow, {"crush_configs": configs})
        elif path in {"/queen/game/get-crush-info", "/queen/script/crush-reward-info"}:
            success(interceptor, flow, {"crush_info": crush_info(settings)})
        else:
            if mode == "detail-error":
                reply(interceptor, flow, {"code": 503, "message": "模拟详情查询失败，请重试", "data": None}, 503)
            else:
                owned = mode == "unlocked" or item_id == 99003002
                rounds = settings["required_rounds"] if owned else settings["current_rounds"]
                success(interceptor, flow, {"item": {
                    "item_id": item_id, "item_type": 99, "item_type_name": "笔记本",
                    "quantity": 1, "name": NAMES[ITEMS[item_id]], "icon_url": image_url(flow, role),
                    "description": "将你们共同经历的每一份心动珍藏在手账里。此文案、拥有状态和轮次均来自代理模拟的详情响应。",
                    "rarity": 2 if item_id == 99003001 else 1, "is_unique": True,
                    "owned_num": 1 if owned else 0,
                    "obtain_path": [{"description": f"聊天轮次达到（{rounds}/{settings['required_rounds']}）",
                                     "jump": f"invalley://chat?role_id={role}", "type": 0}],
                }})
        ctx.log.info(f"crush-mock scenario={mode} path={path}")
    except Exception as error:
        ctx.log.error(f"crush-mock failed: {type(error).__name__}")
        reply(interceptor, flow, {"code": 500, "message": "crush mock configuration error", "data": None}, 500)
