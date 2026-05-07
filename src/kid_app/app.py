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

# ─── API: 表扬海报生成 ─────────────────────────────────────────────────────
@app.post("/api/praise")
async def api_praise(request: Request):
    body = json.loads(await request.body())
    ptype = body.get("type")
    custom = body.get("custom", "")
    cname = body.get("child_name", child_name())

    extra = custom if custom else {
        "teacher": "Teacher praised you!",
        "dad": "Dad thinks you did great!",
    }.get(ptype, "Well done!")

    prompts = {
        "streak7": (
            "A celebratory badge for " + cname + " completing a 7-day bamboo flute practice streak. "
            "Show a flame icon, vibrant orange/red colors, Chinese-inspired decorative border, "
            "achievement text, warm encouraging atmosphere. Child-friendly, colorful, cartoon style."
        ),
        "streak30": (
            "A golden trophy illustration for " + cname + " achieving a 30-day bamboo flute practice streak. "
            "Show a gold trophy, sparkles, ribbon banner, celebratory confetti, warm golden tones, "
            "child-friendly cartoon style."
        ),
        "teacher": (
            "A cheerful encouragement card for " + cname + " receiving teacher praise for bamboo flute practice. "
            "Show a friendly teacher character, musical notes, warm pastel colors, encouraging smiley face, "
            "child-friendly cartoon style. Include text: " + extra
        ),
        "dad": (
            "A warm encouragement card from dad to " + cname + " for excellent bamboo flute practice. "
            "Show a happy child playing flute, musical notes floating around, warm golden light, "
            "loving supportive atmosphere, child-friendly cartoon style. Include text: " + extra
        ),
        "monthly": (
            "A monthly achievement certificate for " + cname + " completing monthly bamboo flute practice goals. "
            "Show a certificate with ribbon seals, star decorations, bamboo flute icon, celebratory confetti, "
            "warm celebratory atmosphere, child-friendly cartoon style."
        ),
    }

    prompt = prompts.get(ptype, prompts["dad"])

    try:
        from src.kid_app import images as kid_images
        image_url = kid_images.generate(prompt, ptype, cname)
        return JSONResponse({
            "ok": True,
            "image_url": image_url,
            "message": "Generated! " + cname + "'s praise poster is ready"
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

# ─── 页面路由 ───────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home():
    return prepare_page()

@app.get("/prepare", response_class=HTMLResponse)
def prepare_page():
    today = dt.date.today()
    ws = week_start_of(today)
    assign = db.get_weekly_assignment(ws)

    assign_html = "<li>No requirements this week</li>"
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
                    "Yesterday <strong>" + it["item"] + "</strong> only " + str(it["minutes"]) + " min, practice more today!"
                )

    if not suggestions_list:
        suggestions_html = "<li>Keep going!</li>"
    else:
        suggestions_html = ""
        for s in suggestions_list:
            suggestions_html += "<li>" + s + "</li>"

    today_p = db.get_daily_practice(today)
    practiced = "Done today!" if today_p and today_p.get("total_minutes", 0) > 0 else "Not yet today"

    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return render(
        "prepare",
        child_name=child_name(),
        today_str=today.strftime("%m/%d"),
        weekday=weekday_names[today.weekday()],
        assign_html=assign_html,
        suggestions=suggestions_html,
        practiced=practiced,
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
        by_cat[cat].append(it["name"])

    items_html = ""
    for cat, names in by_cat.items():
        items_html += "<h3 style='font-size:16px;color:#4ECDC4;margin:12px 0 6px;'>" + cat + "</h3>"
        items_html += "<div class='item-grid'>"
        for name in names:
            items_html += "<button class='item-btn' onclick=\"selectItem('" + name + "')\">" + name + "</button>"
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
        badges.append(("fire", str(streak) + " days", "flame"))
    if streak >= 7:
        badges.append(("star", str(streak) + " day streak!", "star"))
    if total_mins >= 60:
        badges.append(("medal", "Practice Pro", "star2"))
    if week_mins >= 60:
        badges.append(("flex", "Week Star", "strong"))

    badge_html = ""
    for icon, label, cls in badges:
        badge_html += "<div class='badge " + cls + "'>" + icon + "<br><small>" + label + "</small></div>"
    if not badge_html:
        badge_html = "<p style='color:#7F8C8D;text-align:center;'>No badges yet, keep going!</p>"

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
        cal_html += "<div class='" + cls + "'>" + label + "</div>"

    return render(
        "report",
        child_name=child_name(),
        month_str=today.strftime("%Y/%m"),
        total_mins=str(data["total_minutes"]),
        practice_days=str(data["practice_days"]),
        cal_html=cal_html,
    )

@app.get("/praise", response_class=HTMLResponse)
def praise_page():
    return render("praise", child_name=child_name())
