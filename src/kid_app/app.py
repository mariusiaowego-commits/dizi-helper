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
        return JSONResponse({"date": date_str, "items": [], "total_minutes": 0, "log": ""})
    return JSONResponse({
        "date": date_str,
        "items": practice.get("items", []),
        "total_minutes": practice.get("total_minutes", 0),
        "log": practice.get("log", "")
    })

# ─── API: 练习项目列表 ─────────────────────────────────────────────────────
@app.get("/api/items")
def api_items():
    items = db.get_practice_items(active_only=True)
    categories = practice_module.get_categories()
    return JSONResponse({"items": items, "categories": categories})

# ─── API: 打卡 ─────────────────────────────────────────────────────────────
@app.post("/api/log")
async def api_log(request: Request):
    body = json.loads(await request.body())
    date_str = body.get("date")
    item_name = body.get("item")
    minutes = int(body.get("minutes", 0))
    log_note = body.get("log", "")

    date = dt.date.fromisoformat(date_str) if date_str else dt.date.today()
    existing = db.get_daily_practice(date)
    items = []
    if existing and existing.get("items"):
        items = existing["items"]

    found = False
    for it in items:
        if it["item"] == item_name:
            it["minutes"] += minutes
            found = True
            break
    if not found:
        items.append({"item": item_name, "minutes": minutes})

    total = sum(it["minutes"] for it in items)
    db.save_daily_practice(date, items, total, log_note)
    return JSONResponse({"ok": True, "total": total})

# ─── API: 删除单条练习记录 ─────────────────────────────────────────────────
@app.delete("/api/log")
async def api_delete_log(request: Request):
    body = json.loads(await request.body())
    date_str = body.get("date")
    item_name = body.get("item")
    if not date_str or not item_name:
        return JSONResponse({"ok": False, "error": "缺少参数"}, status_code=400)
    date = dt.date.fromisoformat(date_str)
    db.remove_daily_practice_item(date, item_name)
    return JSONResponse({"ok": True})

# ─── API: 更新练习项目排序 ─────────────────────────────────────────────────
@app.put("/api/items/order")
async def api_update_items_order(request: Request):
    body = json.loads(await request.body())
    orders = body.get("orders", [])
    for entry in orders:
        db.update_practice_item_sort_order(entry["id"], entry["sort_order"])
    return JSONResponse({"ok": True})

# ─── API: 表扬海报生成 ─────────────────────────────────────────────────────
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

@app.get("/prepare", response_class=HTMLResponse)
def prepare_page():
    today = dt.date.today()
    ws = week_start_of(today)
    assign = db.get_weekly_assignment_for_week(today)

    assign_html = "<li>还没录本周要求 💭 告诉爸爸帮你加上哦</li>"
    if assign and assign.get("items"):
        assign_html = ""
        for it in assign["items"]:
            assign_html += "<li><strong>" + it["item"] + "</strong>: " + it["requirement"] + "</li>"

    yesterday = today - dt.timedelta(days=1)
    y_practice = db.get_daily_practice(yesterday)
    suggestions_list = []
    if y_practice and y_practice.get("items"):
        for it in y_practice["items"]:
            if it["minutes"] < 10:
                suggestions_list.append(
                    "昨天" + it["item"] + "只练了" + str(it["minutes"]) + "分钟，今天加油多练一会儿呀！💪"
                )

    if not suggestions_list:
        suggestions_html = "<li>太棒啦！今天继续保持 ✨</li>"
    else:
        suggestions_html = ""
        for s in suggestions_list:
            suggestions_html += "<li>" + s + "</li>"

    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return render(
        "prepare",
        child_name=child_name(),
        today_str=today.strftime("%m/%d"),
        weekday=weekday_names[today.weekday()],
        assign_html=assign_html,
        suggestions=suggestions_html,
        streak=streak_days(),
    )

@app.get("/practice", response_class=HTMLResponse)
def practice_page():
    items = db.get_practice_items(active_only=True)
    categories = practice_module.get_categories()

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
            items_html += "<button class='item-btn' data-id='" + str(it["id"]) + "' onclick=\"selectItem('" + it["name"] + "', " + str(it["id"]) + ")\">" + it["name"] + "</button>"
        items_html += "</div>"

    if not items_html:
        items_html = "<p style='color:#7F8C8D;text-align:center;'>No practice items. Ask dad to add via dizical practice config</p>"

    today = dt.date.today()
    today_p = db.get_daily_practice(today)
    today_mins = today_p["total_minutes"] if today_p else 0

    return render(
        "practice",
        child_name=child_name(),
        items_html=items_html,
        today_mins=today_mins,
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
        badges.append(("flex", "本周之星", "strong"))

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

    return render(
        "achievements",
        child_name=child_name(),
        streak=str(streak),
        total_hours=str(total_mins // 60),
        total_mins=str(total_mins % 60),
        week_mins=str(week_mins),
        week_days=str(week_days),
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
    except:
        return default

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
    has_pin = bool(get_setting("dad_pin"))
    return render(
        "praise",
        child_name=child_name(),
        pin_locked="true" if has_pin else "false",
        PIN_OVERLAY_DISPLAY="display:flex" if has_pin else "display:none",
        PRAISE_CONTENT_DISPLAY="display:block" if not has_pin else "display:none",
    )
