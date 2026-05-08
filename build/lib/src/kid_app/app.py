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
app = FastAPI(title="\U0001F3B5 竹笛练习助手")

static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# ─── 模板渲染 ───────────────────────────────────────────────────────────────
def render(tpl: str, **kwargs) -> str:
    path = Path(__file__).parent / "templates" / f"{tpl}.html"
    html = path.read_text(encoding="utf-8")
    for k, v in kwargs.items():
        html = html.replace(f"{{{{{k}}}}}", str(v))
    return html

# ─── 数据 helpers ───────────────────────────────────────────────────────────
def child_name() -> str:
    try:
        return db.get_setting("child_name") or "YoYo"
    except:
        return "YoYo"

def week_start_of(today: dt.date) -> dt.date:
    return today - dt.timedelta(days=today.weekday())

def streak_days() -> int:
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

def total_practice_minutes() -> int:
    practices = db.get_daily_practices_in_range(
        dt.date(2020, 1, 1), dt.date.today()
    )
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

    # 构建 prompt
    prompts = {
        "streak7": f"A celebratory badge for {cname} completing a 7-day bamboo flute practice streak. Show a flame icon, vibrant orange/red colors, Chinese-inspired decorative border, achievement text '7天连续练习', warm encouraging atmosphere. Child-friendly, colorful, cartoon style.",
        "streak30": f"A golden trophy illustration for {cname} achieving a 30-day bamboo flute practice streak. Show a gold trophy, sparkles, ribbon banner with '30天连续练习', celebratory confetti, warm golden tones, child-friendly cartoon style.",
        "teacher": f"A cheerful encouragement card for {cname} receiving teacher praise for bamboo flute practice. Show a friendly teacher character, musical notes, warm pastel colors, Chinese text '{custom or "老师表扬你啦！"}', encouraging smiley face, child-friendly cartoon style.",
        "dad": f"A warm encouragement card from dad to {cname} for excellent bamboo flute practice. Show a happy child playing flute, musical notes floating around, warm golden light, Chinese text '{custom or "爸爸觉得你练得真棒！"}', loving supportive atmosphere, child-friendly cartoon style.",
        "monthly": f"A monthly achievement certificate for {cname} completing monthly bamboo flute practice goals. Show a certificate with ribbon seals, star decorations, bamboo flute icon, Chinese text '月度练习目标完成', celebratory confetti, warm celebratory atmosphere, child-friendly cartoon style.",
    }

    prompt = prompts.get(ptype, prompts["dad"])

    # 调用 Hermes image generation
    try:
        from src.kid_app import images as kid_images
        image_url = kid_images.generate(prompt, ptype, cname)
        return JSONResponse({
            "ok": True,
            "image_url": image_url,
            "message": f"生成成功！{cname} 的表扬海报已生成"
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

    assign_html = ""
    if assign and assign.get("items"):
        for it in assign["items"]:
            assign_html += f"<li><strong>{it['item']}</strong>：{it['requirement']}</li>"
    if not assign_html:
        assign_html = "<li>暂无本周要求</li>"

    yesterday = today - dt.timedelta(days=1)
    y_practice = db.get_daily_practice(yesterday)
    suggestions = []
    if y_practice and y_practice.get("items"):
        for it in y_practice["items"]:
            if it["minutes"] < 10:
                suggestions.append(f"昨天 <strong>{it['item']}</strong> 只练了 {it['minutes']} 分钟，今天可以多练一会儿")

    today_p = db.get_daily_practice(today)
    practiced = "✅ 今日已完成" if today_p and today_p.get("total_minutes", 0) > 0 else "⏳ 还未打卡"

    return render(
        "prepare",
        child_name=child_name(),
        today_str=today.strftime("%m月%d日"),
        weekday=["周一","周二","周三","周四","周五","周六","周日"][today.weekday()],
        assign_html=assign_html,
        suggestions="\n".join(f"<li>{s}</li>" for s in suggestions) if suggestions else "<li>继续加油！</li>",
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
        cat = cat_map.get(cid, "其他")
        by_cat.setdefault(cat, []).append(it["name"])

    items_html = ""
    for cat, names in by_cat.items():
        items_html += f"<h3 style='font-size:16px;color:#4ECDC4;margin:12px 0 6px;'>{cat}</h3><div class=\"item-grid\">"
        for name in names:
            items_html += f'<button class="item-btn" onclick="selectItem(\'{name}\')">{name}</button>'
        items_html += "</div>"

    if not items_html:
        items_html = "<p style='color:#7F8C8D;text-align:center;'>暂无练习项目，请爸爸先用 dizical practice config 添加</p>"

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
        badges.append(("🔥", f"连续{streak}天", "flame"))
    if streak >= 7:
        badges.append(("🌟", f"连续{streak}天达成", "star"))
    if total_mins >= 60:
        badges.append(("⭐", "练习达人", "star2"))
    if week_mins >= 60:
        badges.append(("💪", "本周之星", "strong"))

    badge_html = "".join(
        f'<div class="badge {cls}">{icon}<br><small>{label}</small></div>'
        for icon, label, cls in badges
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
        cal_html += "<div class=\"cal-day empty\"></div>"
    for d in range(1, end.day + 1):
        day_date = dt.date(today.year, today.month, d)
        key = day_date.isoformat()
        p = practices.get(key)
        mins = p["total_minutes"] if p else 0
        cls = "cal-day"
        label = str(d)
        if mins == 0:
            cls = "cal-day"
        elif mins < 20:
            cls = "cal-day low"
            label = f"{d}<br><small>{mins}m</small>"
        elif mins < 40:
            cls = "cal-day mid"
            label = f"{d}<br><small>{mins}m</small>"
        else:
            cls = "cal-day high"
            label = f"{d}<br><small>{mins}m</small>"
        if day_date == today:
            cls += " today"
        cal_html += f'<div class="{cls}">{label}</div>'

    return render(
        "report",
        child_name=child_name(),
        month_str=today.strftime("%Y年%m月"),
        total_mins=str(data["total_minutes"]),
        practice_days=str(data["practice_days"]),
        cal_html=cal_html,
    )

@app.get("/praise", response_class=HTMLResponse)
def praise_page():
    return render("praise", child_name=child_name())
