"""dizical 儿童版 Web 应用"""

import datetime as dt
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.database import db
from src import practice as practice_module

# ─── App ───────────────────────────────────────────────────────────────────
app = FastAPI(title="Bamboo Flute Practice")

static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ─── 模板渲染 ───────────────────────────────────────────────────────────────
def render(tpl, **kwargs):
    path = Path(__file__).parent / "templates" / (tpl + ".html")
    html = path.read_text(encoding="utf-8")
    for k, v in kwargs.items():
        placeholder = "{{" + k + "}}"
        html = html.replace(placeholder, str(v))
    return html

# ─── 数据 helpers ───────────────────────────────────────────────────────────
def child_name():
    try:
        return db.get_setting("child_name") or "YoYo"
    except:
        return "YoYo"

def week_start_of(today):
    return today - dt.timedelta(days=today.weekday())

def streak_days():
    today = dt.date.today()
    days = 0
    d = today
    for _ in range(365):
        p = db.get_daily_practice(d)
        if p and p.get("total_minutes", 0) > 0:
            days += 1
            d -= dt.timedelta(days=1)
        else:
            break
    return days

def total_practice_minutes():
    practices = db.get_daily_practices_in_range(dt.date(2020, 1, 1), dt.date.today())
    return sum(p["total_minutes"] for p in practices)

# ─── API: 某日练习明细 ─────────────────────────────────────────────────────
@app.get("/api/practices/{date_str}")
def api_practice_day(date_str: str):
    """返回指定日期的练习明细"""
    try:
        day = dt.date.fromisoformat(date_str)
    except ValueError:
        return JSONResponse({"error": "无效日期格式"}, status_code=400)
    practice = db.get_daily_practice(day)
    if not practice:
        return JSONResponse({"date": date_str, "id": None, "items": [], "total_minutes": 0, "log": ""})
    return JSONResponse({
        "date": date_str,
        "id": practice.get("id"),
        "items": practice.get("items", []),
        "total_minutes": practice.get("total_minutes", 0),
        "log": practice.get("log", "")
    })

# ─── API: 练习项目列表 ─────────────────────────────────────────────────────
@app.get("/api/items")
def api_items(include_archived: bool = False):
    items = db.get_practice_items(active_only=True, include_archived=include_archived)
    categories = practice_module.get_categories()
    return JSONResponse({"items": items, "categories": categories})


# ─── API: 归档 / 取消归档练习项目 ───────────────────────────────────────────
@app.post("/api/items/{item_id}/archive")
async def api_archive_item(item_id: int):
    db.archive_practice_item(item_id)
    return JSONResponse({"ok": True})


@app.post("/api/items/{item_id}/unarchive")
async def api_unarchive_item(item_id: int):
    db.unarchive_practice_item(item_id)
    return JSONResponse({"ok": True})

# ─── API: 打卡 ─────────────────────────────────────────────────────────────
@app.post("/api/log")
async def api_log(request: Request):
    try:
        body = json.loads(await request.body())
        date_str = body.get("date")
        item_name = body.get("item")
        minutes = int(body.get("minutes", 0))
        log_note = body.get("log", "")
        is_extra = body.get("is_extra", False)

        date = dt.date.fromisoformat(date_str) if date_str else dt.date.today()

        if is_extra:
            # extra 追加：每次创建独立 item 条目（带唯一 id），不与同名合并
            # 直接操作 DB，绕过 save_daily_practice 的 merge 逻辑
            existing = db.get_daily_practice(date)
            existing_items = existing.get("items", []) if existing else []
            max_id = max([0] + [it.get('item_id', it.get('id', 0)) for it in existing_items])
            new_item = {"item_id": max_id + 1, "item": item_name, "minutes": minutes}
            all_items = existing_items + [new_item]
            total = sum(it.get('minutes', 0) for it in all_items)
            # 直接写 DB，不合并
            import sqlite3
            conn = sqlite3.connect('/Users/mt16/dev/dizical/data/dizi.db')
            conn.execute('''
                INSERT OR REPLACE INTO daily_practices (date, items, total_minutes, log, practiced)
                VALUES (?, ?, ?, ?, ?)
            ''', (date.isoformat(), json.dumps(all_items, ensure_ascii=False), total, '', 'Y'))
            conn.commit()
            conn.close()
            return JSONResponse({"ok": True})

        # 正常打卡：直接传给 save_daily_practice，由它处理合并逻辑
        # 注意：只传 [{item, minutes}]，不要预合并！save_daily_practice 内部会读 DB 合并
        items = [{"item": item_name, "minutes": minutes}]
        total = minutes  # save_daily_practice 会重新计算，这里只作返回值参考
        db.save_daily_practice(date, items, total, log_note)
        return JSONResponse({"ok": True, "total": total})

    except Exception as e:
        import traceback
        return JSONResponse({"ok": False, "error": str(e), "trace": traceback.format_exc()}, status_code=500)

# ─── API: 删除单条练习记录 ─────────────────────────────────────────────────
@app.delete("/api/log")
async def api_delete_log(request: Request):
    import traceback
    try:
        body = json.loads(await request.body())
        date_str = body.get("date")
        item_name = body.get("item")
        item_id = int(body.get("id", 0))
        if not date_str:
            return JSONResponse({"ok": False, "error": "缺少参数"}, status_code=400)
        date = dt.date.fromisoformat(date_str)
        if item_id:
            db.remove_daily_practice_record_by_id(date, item_id)
            after = db.get_daily_practice(date)
        elif item_name:
            db.remove_daily_practice_item(date, item_name)
            after = db.get_daily_practice(date)
        else:
            return JSONResponse({"ok": False, "error": "缺少参数"}, status_code=400)
        return JSONResponse({"ok": True, "items": after["items"] if after else [], "total_minutes": after["total_minutes"] if after else 0})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e), "trace": traceback.format_exc()}, status_code=500)

# ─── API: 更新练习项目排序 ─────────────────────────────────────────────────
@app.put("/api/items/order")
async def api_update_items_order(request: Request):
    body = json.loads(await request.body())
    orders = body.get("orders", [])
    for entry in orders:
        db.update_practice_item_sort_order(entry["item_id"], entry["sort_order"])
    return JSONResponse({"ok": True})

# ─── API: 表扬海报生成 ─────────────────────────────────────────────────────
# 已下线：图片生成需在 Hermes Agent 对话窗口进行，见 /praise 页面
@app.post("/api/praise")
async def api_praise(request: Request):
    return JSONResponse({
        "ok": False,
        "error": "Praise poster generation has moved to Hermes Agent. Open /praise and click '打开 Hermes Agent'."
    }, status_code=410)

# ─── 页面路由 ───────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    return prepare_page()

@app.get("/gsap-demo", response_class=HTMLResponse)
def gsap_demo():
    demo_path = Path(__file__).parent.parent.parent / "gsap-demo.html"
    return HTMLResponse(demo_path.read_text())

ENCOURAGEMENTS = [
    "今天也要加油哦！💪",
    "练习是最好的礼物 🎁",
    "吹笛子真好听 🎵",
    "坚持就是胜利 🏆",
    "爸爸相信你！🌟",
    "一天比一天进步 📈",
    "音乐小达人 🥁",
    "认真练习的样子真棒 👍",
    "加油！你是最棒的 ✨",
    "笛声悠扬，真好听 🎶",
    "练完就可以去玩啦 🎮",
    "今天的你比昨天更好 💐",
]

# 默认祝福语池（settings 表无数据时的 fallback）
_DEFAULT_BLESS_POOL = [
    {"main": "每一次练习",     "accent": "都是新的进步"},
    {"main": "坚持练习",       "accent": "让音乐自然流淌"},
    {"main": "今天的你",       "accent": "比昨天更棒"},
    {"main": "一步一步",       "accent": "奏出属于自己的旋律"},
    {"main": "认真吹过",       "accent": "就是最好的练习"},
    {"main": "每一次吹奏",     "accent": "都在靠近更好"},
    {"main": "认真对待",       "accent": "每一个音符"},
    {"main": "不必比较",       "accent": "你有你的节奏"},
    {"main": "慢慢积累",       "accent": "笛声会越来越好听"},
    {"main": "慢慢来",         "accent": "比较快"},
    {"main": "不怕慢",         "accent": "只怕站"},
    {"main": "音乐是",         "accent": "一辈子的朋友"},
    {"main": "吹笛真棒",       "accent": "为你鼓掌👏"},
    {"main": "音符在等你",     "accent": "去拥抱它"},
    {"main": "笛声响起",       "accent": "世界更美好"},
    {"main": "每天进步一点点", "accent": "就是最好的成长"},
    {"main": "练习时专注的你", "accent": "闪闪发光✨"},
    {"main": "音乐是魔法",     "accent": "你就是魔法师🪄"},
    {"main": "坚持吹奏",       "accent": "会越来越动听"},
    {"main": "累了休息一下",   "accent": "再继续也不迟"},
    {"main": "吹得真棒",       "accent": "再玩一会儿吧"},
    {"main": "音乐之路",       "accent": "你才刚开始"},
    {"main": "每个音符",       "accent": "都是小小的胜利"},
    {"main": "爸爸爱听",       "accent": "你吹的每一首曲子"},
    {"main": "不用和别人比",   "accent": "只要比昨天好"},
    {"main": "声音会说话",     "accent": "告诉世界你在"},
    {"main": "你的笛声",       "accent": "是家里最美的音乐"},
    {"main": "今天也坚持了",   "accent": "真了不起🌟"},
    {"main": "音乐相伴",       "accent": "快乐成长🎵"},
    {"main": "笛子会说",       "accent": "谢谢你的陪伴"},
    {"main": "吹久一些",       "accent": "也许会有新发现"},
]


def _get_bless_pool() -> list[dict]:
    """从 settings 表读取 bless_pool，fallback 到默认列表"""
    try:
        raw = db.get_setting("bless_pool")
        if raw:
            import json as _json
            return _json.loads(raw)
    except Exception:
        pass
    return _DEFAULT_BLESS_POOL


# 可配置的准备步骤（后端可通过设置表动态调整）
PREPARE_STEPS = [
    {"title": "热身呼吸",    "desc": "深呼吸 3~5 次，放松身体，让气息更顺畅。", "color": "sage"},
    {"title": "基础音阶练习", "desc": "从低音到高音慢速吹奏，熟悉指法位置。",    "color": "rose"},
    {"title": "复习老师要求", "desc": "查看本周练习重点，有针对性地练习。",        "color": "lavender"},
]


def _bless_for_today() -> dict:
    """每次调用随机选一条（每次打开页面都会刷新）"""
    import random
    pool = _get_bless_pool()
    return random.choice(pool)


def _daily_encouragement() -> str:
    """按今天日期 seed 选固定的鼓励语（同一天刷新也同一条）"""
    today = dt.date.today()
    seed = today.year * 10000 + today.month * 100 + today.day
    idx = seed % len(ENCOURAGEMENTS)
    return ENCOURAGEMENTS[idx]


def _build_steps_html(steps: list[dict]) -> str:
    """把步骤列表渲染成 HTML card 字符串"""
    html = ""
    for i, step in enumerate(steps, 1):
        cid = step['color']
        html += f"""
  <div class="step-card" id="step{i}" onclick="toggleStep(this)">
    <div class="step-num {cid}">{i}</div>
    <div class="step-body">
      <h3 class="step-title">{step['title']}</h3>
      <p class="step-desc">{step['desc']}</p>
    </div>
    <div class="step-check" id="check{i}">✓</div>
  </div>"""
    return html


@app.get("/prepare", response_class=HTMLResponse)
def prepare_page():
    today = dt.date.today()
    ws = week_start_of(today)

    # 祝福语
    bless = _bless_for_today()

    # 本周老师要求
    assign = db.get_weekly_assignment_for_week(today)
    if assign and assign.get("items"):
        assign_eyebrow = f"本周练习要求 · 第 {assign.get('stage_order', '?')} 课"
        stage_start = assign.get('stage_start', today)
        stage_end   = assign.get('stage_end', today)
        # 确保 start ≤ end（数据可能有误，统一兜底）
        if stage_start and stage_end:
            if hasattr(stage_start, 'strftime') and hasattr(stage_end, 'strftime'):
                if stage_start > stage_end:
                    stage_start, stage_end = stage_end, stage_start
                assign_title = f"{stage_start.strftime('%m月%d日')} ~ {stage_end.strftime('%m月%d日')}"
            else:
                assign_title = str(stage_start) + " ~ " + str(stage_end)
        else:
            assign_title = "本周练习安排"
        assign_items_html = ""
        for it in assign["items"]:
            assign_items_html += f"<li>{it['item']} {it.get('requirement', '')}</li>"
    else:
        assign_eyebrow  = "本周老师要求"
        assign_title    = "暂无老师要求"
        assign_items_html = "<li>直接开始练习吧！🎵</li>"

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    return render(
        "prepare",
        eyebrow="竹笛练习准备",
        bless_main=bless["main"],
        bless_accent=bless["accent"],
        today_str=today.strftime("%m月%d日"),
        weekday=weekday_names[today.weekday()],
        streak=streak_days(),
        encouragement=_daily_encouragement(),
        steps_html=_build_steps_html(PREPARE_STEPS),
        assign_eyebrow=assign_eyebrow,
        assign_title=assign_title,
        assign_items_html=assign_items_html,
        cta_title="准备好啦！",
        cta_sub="三个步骤都完成后，开始今天的练习。",
        cta_btn_text="开始行动",
    )

@app.get("/practice", response_class=HTMLResponse)
def practice_page():
    today = dt.date.today()
    items = db.get_practice_items(active_only=True, include_archived=False)
    categories = practice_module.get_categories()

    # 本周老师要求（date 字段转字符串避免 JSON 序列化报错）
    assign = db.get_weekly_assignment_for_week(today)
    import json as _json
    if assign:
        assign = dict(assign)
        for k in ('lesson_date', 'stage_start', 'stage_end'):
            if assign.get(k):
                assign[k] = str(assign[k])
    assign_json = _json.dumps(assign) if assign else "null"

    assign_item_names = {}
    if assign and assign.get("items"):
        for a in assign["items"]:
            assign_item_names[a["item"]] = a.get("requirement", "")

    # 建立 practice_item_id → requirement 的映射（精确匹配）
    assign_by_pi_id = {}
    if assign and assign.get("items"):
        for a in assign["items"]:
            pid = a.get("item_id")
            if pid:
                assign_by_pi_id[pid] = a.get("requirement", "")

    def _find_requirement(item_name):
        """精确匹配 name（不用模糊，避免 '长音' 错误匹配 '吸气长音'）"""
        return assign_item_names.get(item_name, "")

    cat_map = {c["id"]: c["name"] for c in categories}
    by_cat = {}
    for it in items:
        cid = it.get("category_id")
        cat = cat_map.get(cid, "Other")
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(it)

    items_html = ""
    for cat, cat_items in sorted(by_cat.items(), key=lambda x: next((c["sort_order"] for c in categories if c["name"] == x[0]), 99)):
        items_html += "<h3 style='font-size:16px;color:#4ECDC4;margin:12px 0 6px;'>" + cat + "</h3>"
        items_html += "<div class='item-grid'>"
        for it in sorted(cat_items, key=lambda x: x.get("sort_order", 0)):
            name = it["name"]
            pid = it.get("item_id")
            # 优先用 practice_item_id 精确匹配，fallback 用名称模糊匹配
            req_text = assign_by_pi_id.get(pid) or _find_requirement(name)
            has_req = bool(req_text)
            tooltip_html = ""
            if has_req and req_text:
                tooltip_html = "<div class='req-tooltip'>" + req_text + "</div>"
            wrap_class = "item-btn-wrap" if has_req else ""
            has_req_class = "has-req" if has_req else ""
            items_html += (
                "<div class='" + wrap_class + "'>"
                + "<button class='item-btn " + has_req_class + "' data-id='" + str(it["item_id"]) + "' "
                + "data-req='" + req_text.replace("'", "&#39;") + "' "
                + "onclick=\"selectItem('" + name.replace("'", "\\'") + "', " + str(it["item_id"]) + ")\">"
                + name + " <span style='font-size:11px;color:rgba(255,255,255,0.6)'>[" + str(it["item_id"]) + "]</span>"
                + tooltip_html
                + "</button></div>"
            )
        items_html += "</div>"

    if not items_html:
        items_html = "<p style='color:#7F8C8D;text-align:center;'>No practice items. Ask dad to add via dizical practice config</p>"

    today_p = db.get_daily_practice(today)
    today_mins = today_p["total_minutes"] if today_p else 0

    return render(
        "practice",
        child_name=child_name(),
        items_html=items_html,
        today_mins=today_mins,
        assign_json=assign_json,
        today_date=today.isoformat(),
    )

@app.get("/achievements", response_class=HTMLResponse)
def achievements_page():
    today = dt.date.today()
    ws = week_start_of(today)

    week_prac = db.get_daily_practices_in_range(ws, today)
    week_mins = sum(p["total_minutes"] for p in week_prac)
    week_days = len([p for p in week_prac if p.get("total_minutes", 0) > 0])

    streak = streak_days()
    total_mins = total_practice_minutes()

    badges = []
    if streak >= 3:
        badges.append(("fire", str(streak) + " 天连续", "flame"))
    if streak >= 7:
        badges.append(("star", "7天连续达成！", "star"))
    if total_mins >= 60:
        badges.append(("medal", "练习达人", "star2"))
    if week_mins >= 60:
        badges.append(("week_star", "本周之星", "strong"))

    badge_html = ""
    for icon_type, label, cls in badges:
        badge_html += (
            "<div class='badge-wrap'>"
            "<img src='/static/badges/" + icon_type + "_badge.png' alt='" + label + "' class='badge-img " + cls + "'>"
            "<div class='badge-label " + cls + "'>" + label + "</div>"
            "</div>"
        )
    if not badge_html:
        badge_html = "<p style='color:#7F8C8D;text-align:center;'>还没有徽章，继续加油！</p>"

    # 本周目标进度（默认目标：每周5天，每天≥10分钟）
    WEEK_GOAL_DAYS = 5
    week_progress = min(week_days / WEEK_GOAL_DAYS, 1.0)
    week_progress_pct = int(week_progress * 100)
    week_progress_text = f"{week_days}/{WEEK_GOAL_DAYS} 天"

    # 徽章距离提示
    badge_hints = []
    # 火徽章（连续streak）
    next_fire = None
    if streak < 3:
        next_fire = 3 - streak
    elif streak < 7:
        next_fire = 7 - streak
    if next_fire is not None:
        badge_hints.append(("fire", next_fire, "🔥"))
    # 练习达人（总分钟）
    if total_mins < 60:
        mins_left = 60 - total_mins
        badge_hints.append(("medal", mins_left, "🏅"))
    # 本周之星（本周分钟）
    if week_mins < 60:
        mins_left_w = 60 - week_mins
        badge_hints.append(("week_star", mins_left_w, "⭐"))

    badge_hint_html = ""
    for _btype, remaining, icon in badge_hints:
        if _btype == "fire":
            badge_hint_html += f"<div style='text-align:center;padding:6px 0;font-size:14px;color:#7F8C8D;'>距离 🔥 下一徽章还差 <strong style='color:#FF6B35;'>{remaining} 天</strong></div>"
        elif _btype == "medal":
            badge_hint_html += f"<div style='text-align:center;padding:6px 0;font-size:14px;color:#7F8C8D;'>距离 🏅 练习达人还差 <strong style='color:#FF6B35;'>{remaining} 分钟</strong></div>"
        elif _btype == "week_star":
            badge_hint_html += f"<div style='text-align:center;padding:6px 0;font-size:14px;color:#7F8C8D;'>距离 ⭐ 本周之星还差 <strong style='color:#FF6B35;'>{remaining} 分钟</strong></div>"

    return render(
        "achievements",
        child_name=child_name(),
        streak=str(streak),
        total_hours=str(total_mins // 60),
        total_mins_rem=str(total_mins % 60),
        week_mins=str(week_mins),
        week_days=str(week_days),
        week_progress_pct=week_progress_pct,
        week_progress_text=week_progress_text,
        badge_hint_html=badge_hint_html,
        badge_html=badge_html,
    )

@app.get("/report", response_class=HTMLResponse)
def report_page():
    today = dt.date.today()
    data = practice_module.get_month_summary(today.year, today.month)

    start = dt.date(today.year, today.month, 1)
    if today.month == 12:
        end = dt.date(today.year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        end = dt.date(today.year, today.month + 1, 1) - dt.timedelta(days=1)

    practices = {p["date"].isoformat(): p for p in db.get_daily_practices_in_range(start, end)}

    cal_html = ""
    for _ in range(start.weekday()):
        cal_html += "<div class='cal-day empty'></div>"
    for d in range(1, end.day + 1):
        day_date = dt.date(today.year, today.month, d)
        key = day_date.isoformat()
        p = practices.get(key)
        mins = p["total_minutes"] if p else 0
        if mins == 0:
            cls = "cal-day"
            label = str(d)
        elif mins < 20:
            cls = "cal-day low"
            label = str(d) + "<br><small>" + str(mins) + "m</small>"
        elif mins < 40:
            cls = "cal-day mid"
            label = str(d) + "<br><small>" + str(mins) + "m</small>"
        else:
            cls = "cal-day high"
            label = str(d) + "<br><small>" + str(mins) + "m</small>"
        if day_date == today:
            cls += " today"
        cal_html += "<div class='" + cls + "' data-date='" + key + "'>" + label + "</div>"

    return render(
        "report",
        child_name=child_name(),
        month_str=today.strftime("%Y/%m"),
        total_mins=str(data["total_minutes"]),
        practice_days=str(data["practice_days"]),
        cal_html=cal_html,
    )

# ─── PIN 验证 ───────────────────────────────────────────────────────────────
def get_setting(key, default=""):
    try:
        return db.get_setting(key) or default
    except Exception:
        return default


@app.get("/api/bless-pool", response_class=JSONResponse)
def api_get_bless_pool():
    """返回当前祝福语池（需 PIN 验证）"""
    pin = get_setting("dad_pin")
    if not pin:
        pool = _get_bless_pool()
        return JSONResponse({"pool": pool})
    # 无 PIN 时也返回池内容（编辑需验证）
    return JSONResponse({"pool": _get_bless_pool()})


@app.put("/api/bless-pool", response_class=JSONResponse)
async def api_put_bless_pool(request: Request):
    """更新祝福语池（需 PIN 验证）"""
    body = json.loads(await request.body())
    pin = body.get("pin", "")
    stored_pin = get_setting("dad_pin")
    if stored_pin and pin != stored_pin:
        return JSONResponse({"ok": False, "error": "PIN 不对"}, status_code=401)

    new_pool = body.get("pool", [])
    if not isinstance(new_pool, list):
        return JSONResponse({"ok": False, "error": "格式错误"}, status_code=400)

    db.set_setting("bless_pool", json.dumps(new_pool, ensure_ascii=False))
    return JSONResponse({"ok": True})

@app.post("/api/verify-pin")
async def api_verify_pin(request: Request):
    body = json.loads(await request.body())
    pin = body.get("pin", "")
    stored_pin = get_setting("dad_pin")
    if stored_pin and pin == stored_pin:
        return JSONResponse({"ok": True, "role": "dad"})
    return JSONResponse({"ok": False}, status_code=401)

@app.get("/praise", response_class=HTMLResponse)
def praise_page():
    # 获取当前成就数据
    today = dt.date.today()
    streak = streak_days()
    total_mins = total_practice_minutes()
    ws = week_start_of(today)
    week_prac = db.get_daily_practices_in_range(ws, today)
    week_mins = sum(p["total_minutes"] for p in week_prac)
    week_days = len([p for p in week_prac if p.get("total_minutes", 0) > 0])

    # 当前解锁的徽章
    unlocked = []
    if streak >= 3:
        unlocked.append({"type": "fire", "label": f"🔥 {streak}天连续", "desc": "坚持练习"})
    if streak >= 7:
        unlocked.append({"type": "star7", "label": "⭐ 7天连续达成", "desc": "超棒毅力"})
    if total_mins >= 60:
        unlocked.append({"type": "medal", "label": "🏅 练习达人", "desc": "累计60分钟+"})
    if week_mins >= 60:
        unlocked.append({"type": "weekstar", "label": "⭐ 本周之星", "desc": "本周60分钟+"})

    # 预设表扬语
    PRAISE_MSGS = [
        "太棒了！今天的你比昨天更好！🌟",
        "坚持就是胜利，你是最棒的！💪",
        "笛声悠扬，继续加油！🎵",
        "认真练习的样子真美！✨",
        "今天的进步爸爸都看到了！👍",
        "音乐小达人就是你！🥁",
        "练完就可以开心去玩啦！🎮",
    ]
    import random
    seed = today.year * 10000 + today.month * 100 + today.day
    random.seed(seed)
    daily_praise = random.choice(PRAISE_MSGS)
    random.seed()  # 恢复随机种子

    return render(
        "praise",
        child_name=child_name(),
        pin_locked="true" if get_setting("dad_pin") else "false",
        PIN_OVERLAY_DISPLAY="display:flex" if get_setting("dad_pin") else "display:none",
        PRAISE_CONTENT_DISPLAY="display:block" if not get_setting("dad_pin") else "display:none",
        unlocked=unlocked,
        daily_praise=daily_praise,
    )
