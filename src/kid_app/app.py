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


def _calc_max_consecutive_streak():
    """计算最长连续练习天数（断掉后重新接上也能恢复）"""
    today = dt.date.today()
    practices = db.get_daily_practices_in_range(dt.date(2020, 1, 1), today)
    # date -> total_minutes
    day_mins = {p["date"]: p.get("total_minutes", 0) for p in practices}

    # 从最早有练习的日期到今天，逐天扫描
    if not day_mins:
        return 0

    dates_sorted = sorted(day_mins.keys())
    first_day = dates_sorted[0]

    max_streak = 0
    cur_streak = 0
    d = first_day
    while d <= today:
        if day_mins.get(d, 0) > 0:
            cur_streak += 1
            max_streak = max(max_streak, cur_streak)
        else:
            cur_streak = 0
        d += dt.timedelta(days=1)
    return max_streak


def _calc_peak_week():
    """返回 (peak_mins, peak_label) peak_label='YYYY-MM-DD ~ YYYY-MM-DD'"""
    assignments = db.get_weekly_assignments_in_range(
        dt.date(2020, 1, 1), dt.date.today() + dt.timedelta(days=30)
    )
    if not assignments:
        return 0, ""

    best_mins = 0
    best_label = ""
    for a in assignments:
        ss = a.get("stage_start")
        se = a.get("stage_end")
        if not ss or not se:
            continue
        start = dt.date.fromisoformat(ss) if isinstance(ss, str) else ss
        end = dt.date.fromisoformat(se) if isinstance(se, str) else se
        practices = db.get_daily_practices_in_range(start, end)
        mins = sum(p.get("total_minutes", 0) for p in practices)
        if mins > best_mins:
            best_mins = mins
            best_label = f"{ss} ~ {se}"
    return best_mins, best_label


def _calc_peak_month():
    """返回 (peak_mins, peak_label) peak_label='YYYY年MM月'"""
    today = dt.date.today()
    start_year = 2020

    best_mins = 0
    best_label = ""
    for year in range(start_year, today.year + 2):
        for month in range(1, 13):
            if year == today.year and month > today.month:
                break
            if year == start_year and month < 1:
                continue
            sm = dt.date(year, month, 1)
            if month == 12:
                em = dt.date(year + 1, 1, 1) - dt.timedelta(days=1)
            else:
                em = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
            practices = db.get_daily_practices_in_range(sm, em)
            mins = sum(p.get("total_minutes", 0) for p in practices)
            if mins > best_mins:
                best_mins = mins
                best_label = f"{year}年{month}月"
    return best_mins, best_label


def _calc_top_items():
    """返回 [(item_name, total_mins), ...] 按累计时长降序，取前3"""
    practices = db.get_daily_practices_in_range(dt.date(2020, 1, 1), dt.date.today())
    item_mins = {}
    for p in practices:
        for it in p.get("items", []):
            name = it.get("item", "未知")
            item_mins[name] = item_mins.get(name, 0) + it.get("minutes", 0)
    sorted_items = sorted(item_mins.items(), key=lambda x: x[1], reverse=True)
    return sorted_items[:3]


def _get_current_week_range():
    """返回当前周（基于最近的 weekly_assignment）的 stage_start, stage_end"""
    today = dt.date.today()
    # 找包含今天的 weekly_assignment
    assignments = db.get_weekly_assignments_in_range(
        today - dt.timedelta(days=30), today + dt.timedelta(days=30)
    )
    for a in assignments:
        ss = a.get("stage_start")
        se = a.get("stage_end")
        if not ss or not se:
            continue
        start = dt.date.fromisoformat(ss) if isinstance(ss, str) else ss
        end = dt.date.fromisoformat(se) if isinstance(se, str) else se
        if start <= today <= end:
            return start, end
    # fallback: calendar week
    ws = today - dt.timedelta(days=today.weekday())
    we = ws + dt.timedelta(days=6)
    return ws, we


def _week_progress():
    """本周练习进度：返回 (pct, text)"""
    start, end = _get_current_week_range()
    today = dt.date.today()
    # 不超出今天
    end = min(end, today)
    if end < start:
        return 0, "0/7 天"
    practices = db.get_daily_practices_in_range(start, end)
    days = len([p for p in practices if p.get("total_minutes", 0) > 0])
    goal = 7
    pct = min(int(days / goal * 100), 100)
    return pct, f"{days}/{goal} 天"


def _calc_yesterday_mins():
    yesterday = dt.date.today() - dt.timedelta(days=1)
    p = db.get_daily_practice(yesterday)
    return p.get("total_minutes", 0) if p else 0


def _calc_week_mins_and_days():
    today = dt.date.today()
    ws = today - dt.timedelta(days=today.weekday())
    practices = db.get_daily_practices_in_range(ws, today)
    mins = sum(p.get("total_minutes", 0) for p in practices)
    days = len([p for p in practices if p.get("total_minutes", 0) > 0])
    return mins, days


def _calc_month_mins_and_days():
    today = dt.date.today()
    start = dt.date(today.year, today.month, 1)
    if today.month == 12:
        end = dt.date(today.year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        end = dt.date(today.year, today.month + 1, 1) - dt.timedelta(days=1)
    end = min(end, today)
    practices = db.get_daily_practices_in_range(start, end)
    mins = sum(p.get("total_minutes", 0) for p in practices)
    days = len([p for p in practices if p.get("total_minutes", 0) > 0])
    return mins, days


def _ring_diff(current, previous):
    """计算环比差异文字和方向: (diff_text, is_positive)"""
    if previous == 0:
        return "", False
    diff = current - previous
    if diff == 0:
        return "与上周持平", False
    sign = "+" if diff > 0 else ""
    unit = "分" if current < 100 else "天"
    return f"{sign}{diff}{unit} vs上周", diff > 0


def _milestone_html():
    """生成勋章展示区 HTML（v3: 全部成就，含未解锁）
    输出: .card-v3 (unlocked/locked) + .badge-wrap + .info + .type-pill
    """
    from src.database import db as _db

    streak = streak_days()
    total_mins = total_practice_minutes()
    peak_week_mins, _ = _calc_peak_week()
    peak_month_mins, _ = _calc_peak_month()
    top_items = _calc_top_items()

    # 查询 achievements 全部数据（按 sort_order 排序）
    with _db._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, type, category, display_format, description, threshold FROM achievements ORDER BY sort_order, id")
        all_achievements = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]

    # 查询 achievement_stats（achieved 状态）
    with _db._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT achievement_id, achieved, computed_value FROM achievement_stats")
        stats = {row[0]: {"achieved": row[1], "computed_value": row[2]} for row in cur.fetchall()}

    # 查询 badge URL（is_current=1）
    with _db._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT b.achievement_id, b.url, b.is_locked
            FROM achievement_badges b WHERE b.is_current=1
        """)
        badge_rows = cur.fetchall()
    # 按 (achievement_id, is_locked) 索引
    badge_map = {}  # (achievement_id, is_locked=0/1) -> url
    for row in badge_rows:
        bid, url, is_locked = row
        badge_map[(bid, is_locked)] = url

    # 分离 display 类型和 milestone 类型
    display_items = [a for a in all_achievements if a.get("category") == "display"]
    milestone_items = [a for a in all_achievements if a.get("category") == "milestone"]

    html_parts = []

    def _fmt_value(ach, stats_rec):
        """根据 display_format 格式化数值"""
        dfmt = ach.get("display_format", "minutes")
        achieved = stats_rec.get("achieved") == "Y" if stats_rec else False

        if dfmt == "time_hours_minutes":
            if not achieved:
                return None
            # 用 computed_value 或重新计算
            cv = stats_rec.get("computed_value") if stats_rec else None
            if cv:
                try:
                    total = int(cv)
                except:
                    total = total_mins
            else:
                total = total_mins
            h = total // 60
            m = total % 60
            if h > 0:
                return f"<span class='value-num'>{h}</span><span class='value-unit'>小时</span><span class='value-num'>{m}</span><span class='value-unit'>分钟</span>"
            else:
                return f"<span class='value-num'>{m}</span><span class='value-unit'>分钟</span>"

        elif dfmt == "minutes":
            val = peak_week_mins if "week" in ach["id"] else (peak_month_mins if "month" in ach["id"] else total_mins)
            if not achieved or val == 0:
                return "<span class='value-num'>暂无数据</span>"
            return f"<span class='value-num'>{val}</span><span class='value-unit'>分钟</span>"

        elif dfmt == "days":
            val = streak
            if not achieved:
                return None
            return f"<span class='value-num'>{val}</span><span class='value-unit'>天</span>"

        elif dfmt == "top_items":
            if not top_items:
                return "<span class='value-num'>暂无数据</span>"
            pills = "".join(
                f"<span class='item-pill'>{n}<span class='item-pill-mins'>{mm}分钟</span></span>"
                for n, mm in top_items
            )
            return f"<div class='value-list'>{pills}</div>"

        elif dfmt == "achieved_flag":
            if not achieved:
                return None
            return "<span class='value-num'>✓</span>"

        return "<span class='value-num'>-</span>"

    def _card_v3(ach, stats_rec):
        ach_id = ach["id"]
        ach_type = ach.get("type", "突破")
        achieved = stats_rec.get("achieved") == "Y" if stats_rec else False

        # 选择 badge URL（locked 也用 unlocked 图，CSS 灰化处理）
        unlocked_url = badge_map.get((ach_id, 0)) or f"/static/badges/{ach_id}.png"
        badge_url = unlocked_url

        # v3 class
        state_cls = "unlocked" if achieved else "locked"
        type_cls = ach_type  # 用于 .type-pill.段位 等

        # type-pill（无 emoji 前缀）
        pill_html = f"<span class='type-pill {type_cls}'>{ach_type}</span>"

        # 数值
        value_html = _fmt_value(ach, stats_rec)
        if value_html is None:
            value_html = f"<span class='value-num'>{ach.get('threshold', '-')}</span>"

        # 描述
        desc = ach.get("description", "")

        # HTML 结构
        lock_html = "" if achieved else "<svg class='lock-icon' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><rect x='3' y='11' width='18' height='11' rx='2' ry='2'/><path d='M7 11V7a5 5 0 0 1 10 0v4'/></svg>"

        return (
            f"<div class='card-v3 {state_cls}' data-badge='{ach_id}' data-type='{ach_type}'>"
            f"  <div class='badge-wrap'><img class='badge-img' src='{badge_url}' alt='{ach['name']}'></div>"
            f"  <div class='info'>"
            f"    <div class='label-row'>{pill_html}<span class='label-text'>{ach['name']}</span></div>"
            f"    <div class='value-row'>{value_html}</div>"
            f"    <div class='desc'>{desc}</div>"
            f"  </div>"
            f"  {lock_html}"
            f"</div>"
        )

    # display 类型（已解锁的才有意义）
    for ach in display_items:
        stats_rec = stats.get(ach["id"])
        achieved = stats_rec.get("achieved") == "Y" if stats_rec else False
        if achieved:
            html_parts.append(_card_v3(ach, stats_rec))

    # milestone 类型（全部显示，含未解锁）
    for ach in milestone_items:
        stats_rec = stats.get(ach["id"])
        html_parts.append(_card_v3(ach, stats_rec))

    return "".join(html_parts)

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

    # ── 卡片1: 本周目标进度 ─────────────────────────────
    week_pct, week_pct_text = _week_progress()

    # ── 卡片2: 练习看板 ────────────────────────────────
    streak = streak_days()
    yesterday_mins = _calc_yesterday_mins()
    yesterday_prev = 0  # 简化：暂无上周数据

    week_mins, week_days_count = _calc_week_mins_and_days()
    # 上上周
    ws_prev = today - dt.timedelta(days=today.weekday() + 7)
    we_prev = ws_prev + dt.timedelta(days=6)
    practices_prev = db.get_daily_practices_in_range(ws_prev, we_prev)
    week_mins_prev = sum(p.get("total_minutes", 0) for p in practices_prev)
    week_days_prev = len([p for p in practices_prev if p.get("total_minutes", 0) > 0])

    month_mins, month_days_count = _calc_month_mins_and_days()
    # 上月同周期
    if today.month == 1:
        month_start_prev = dt.date(today.year - 1, 12, 1)
    else:
        month_start_prev = dt.date(today.year, today.month - 1, 1)
    if today.month == 12:
        month_end_prev = dt.date(today.year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        month_end_prev = dt.date(today.year, today.month, 1) - dt.timedelta(days=1)
    month_end_prev = min(month_end_prev, today - dt.timedelta(days=28))  # 粗略
    practices_m_prev = db.get_daily_practices_in_range(month_start_prev, month_end_prev)
    month_mins_prev = sum(p.get("total_minutes", 0) for p in practices_m_prev)

    # 环比文字
    yd_diff_txt, yd_pos = _ring_diff(yesterday_mins, yesterday_prev)
    wm_diff_txt, wm_pos = _ring_diff(week_days_count, week_days_prev)
    mm_diff_txt, mm_pos = _ring_diff(month_days_count, len([p for p in practices_m_prev if p.get("total_minutes", 0) > 0]))

    # ── 卡片3: 勋章展示 ────────────────────────────────
    milestone_html = _milestone_html()

    # ── 卡片4: 更多勋章入口 ────────────────────────────
    recent_badges_html = ""  # 暂留空，勋章生成后补

    return render(
        "achievements",
        child_name=child_name(),
        week_pct=week_pct,
        week_pct_text=week_pct_text,
        streak=str(streak),
        yesterday_mins=str(yesterday_mins),
        yesterday_diff=yd_diff_txt,
        yesterday_pos="up" if yd_pos else "",
        week_days=str(week_days_count),
        week_diff=wm_diff_txt,
        week_pos="up" if wm_pos else "",
        month_days=str(month_days_count),
        month_diff=mm_diff_txt,
        month_pos="up" if mm_pos else "",
        milestone_html=milestone_html,
        recent_badges_html=recent_badges_html,
    )

@app.get("/badges", response_class=HTMLResponse)
def badges_page():
    """勋章墙完整页 — v3 卡片样式"""
    today = dt.date.today()
    conn = db._get_connection()

    # ── 统计数据 ──────────────────────────────────────────────
    # 连续天数
    cur = conn.execute(
        "SELECT date FROM daily_practices ORDER BY date DESC")
    dates = [r[0] for r in cur.fetchall()]
    streak = 0
    check = today
    for d in dates:
        if d == check.isoformat():
            streak += 1
            check -= dt.timedelta(days=1)
        else:
            break

    # 累计分钟
    cur = conn.execute("SELECT SUM(total_minutes) FROM daily_practices")
    total_mins = cur.fetchone()[0] or 0

    # TOP 科目
    cur = conn.execute("""
        SELECT pi.name, SUM(json_each.value->'$.minutes') as m
        FROM daily_practices dp, json_each(dp.items)
        JOIN practice_items pi ON pi.item_id = json_each.value->'$.item_id'
        GROUP BY pi.name ORDER BY m DESC LIMIT 3
    """)
    top_items = [(r[0], int(r[1])) for r in cur.fetchall()]

    # 全科练习日
    cur = conn.execute("SELECT DISTINCT date FROM daily_practices")
    all_dates = set(r[0] for r in cur.fetchall())
    cur = conn.execute("SELECT item_id FROM practice_items WHERE is_active=1")
    all_item_ids = set(r[0] for r in cur.fetchall())
    has_all_items = False
    if all_item_ids:
        cur = conn.execute("SELECT date, json_each.value->'$.item_id' FROM daily_practices dp, json_each(dp.items)")
        day_items = {}
        for day, item_id in cur.fetchall():
            iid = item_id if isinstance(item_id, int) else None
            if iid:
                day_items.setdefault(day, set()).add(iid)
        has_all_items = any(day_items.get(d, set()) == all_item_ids for d in all_dates)

    # 加练（同日≥2次）
    cur = conn.execute("SELECT COUNT(*) FROM (SELECT date FROM daily_practices GROUP BY date HAVING COUNT(*)>=2)")
    has_double = cur.fetchone()[0] > 0

    # 满月
    has_full_month = False
    cur = conn.execute("SELECT strftime('%Y-%m', date) as ym FROM daily_practices GROUP BY ym ORDER BY ym DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        import calendar
        y, m = map(int, row[0].split('-'))
        _, days_in_month = calendar.monthrange(y, m)
        cur = conn.execute("SELECT COUNT(DISTINCT date) FROM daily_practices WHERE strftime('%Y-%m', date)=?", (row[0],))
        has_full_month = cur.fetchone()[0] >= days_in_month

    # 本周满5天（每天≥10分钟）
    week_start = today - dt.timedelta(days=today.weekday())
    cur = conn.execute("""
        SELECT COUNT(DISTINCT dp.date) FROM daily_practices dp, json_each(dp.items) je
        WHERE dp.date >= ? AND dp.date <= ?
        AND je.value->>'$.minutes' >= 10
    """, (week_start.isoformat(), today.isoformat()))
    has_week_champ = cur.fetchone()[0] >= 5

    # ── 预取 grade 数据（连接关闭前）───────────────────────────
    cur = conn.execute(
        "SELECT achievement_id, achieved, computed_value FROM achievement_stats WHERE achievement_id LIKE 'grade_%'")
    grade_stats = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    # 注意：不关闭 conn，因为它是单例共享连接

    # ── 28 个成就定义 ─────────────────────────────────────────
    ALL_ACHIEVEMENTS = [
        # id, name, type, placeholder, condition, display_format, badge_file
        ("streak_1",    "初试啼声",   "突破", "开始你的练习之旅！",           "连续 ≥ 1 天",   "days",         "streak_1.png"),
        ("streak_3",    "小火焰",     "执着", "连续打卡，笛子都被你吹服了！",   "连续 ≥ 3 天",   "days",         "streak_3.png"),
        ("streak_7",    "周冠军",     "执着", "坚持一周，你就是时间管理大师！",  "连续 ≥ 7 天",   "days",         "streak_7.png"),
        ("streak_14",   "双周传说",   "执着", "两周坚持，传说初现！",           "连续 ≥ 14 天",  "days",         "streak_14.png"),
        ("streak_30",   "月度王者",   "晋级", "整月打卡，王者风范！",           "连续 ≥ 30 天",  "days",         "streak_30.png"),
        ("streak_100",  "百日传奇",   "晋级", "百日坚持，传奇诞生！",           "连续 ≥ 100 天", "days",         "streak_100.png"),
        ("total_60",    "初露锋芒",   "突破", "一屁股坐下去，笛子都认识你了！", "累计 ≥ 60 分钟","time_hours",   "total_60.png"),
        ("total_300",   "五小时战士", "突破", "五小时积累，小试牛刀！",         "累计 ≥ 300 分钟","time_hours",  "total_300.png"),
        ("total_600",   "十小时大师", "巅峰", "十小时磨砺，大师初成！",         "累计 ≥ 600 分钟","time_hours",  "total_600.png"),
        ("total_1000",  "千分钟传奇", "巅峰", "千分钟传奇前无古人！",           "累计 ≥ 1000 分钟","time_hours", "total_1000.png"),
        ("first_log",   "第一声",     "突破", "第一次吹响你的笛子！",           "完成第一次练习","flag",         "first_log.png"),
        ("all_items",   "全能选手",   "神秘", "全能选手，样样精通！",           "同一天练所有科目","flag",        "all_items.png"),
        ("double",      "加练狂魔",   "执着", "同一天两次练习，卷王诞生！",     "同日 ≥ 2 次打卡","flag",        "double.png"),
        ("week_champ",  "周末冠军",   "巅峰", "那一周，你就是时间管理大师！",    "本周 ≥ 5 天","minutes",       "week_champ.png"),
        ("full_month",  "满月战士",   "巅峰", "整月打卡，整条街最亮的笛子！",   "当月每天打卡","flag",           "full_month.png"),
        ("top1",        "TOP1 之王",  "突破", "你跟这些科目最熟，它们也最想你！","累计时长第 1","top_items",    "top1.png"),
        ("top2",        "TOP2 卷王",  "突破", "练习时长第二多，同样出色！",     "累计时长第 2","top_items",    "top2.png"),
        ("top3",        "TOP3 新星",  "突破", "练习时长第三名，新星升起！",     "累计时长第 3","top_items",    "top3.png"),
        ("grade_1",     "一级",       "段位", "恭喜考取一级！竹笛之路，正式开始！","考取一级","date",        "grade_1-u.png"),
        ("grade_2",     "二级",       "段位", "恭喜考取二级！",                  "考取二级","date",        "grade_2-u.png"),
        ("grade_3",     "三级",       "段位", "恭喜考取三级！",                  "考取三级","date",        "grade_3-u.png"),
        ("grade_4",     "四级",       "段位", "恭喜考取四级！",                  "考取四级","date",        "grade_4-u.png"),
        ("grade_5",     "五级",       "段位", "恭喜考取五级！",                  "考取五级","date",        "grade_5-u.png"),
        ("grade_6",     "六级",       "段位", "恭喜考取六级！",                  "考取六级","date",        "grade_6-u.png"),
        ("grade_7",     "七级",       "段位", "恭喜考取七级！",                  "考取七级","date",        "grade_7-u.png"),
        ("grade_8",     "八级",       "段位", "恭喜考取八级！",                  "考取八级","date",        "grade_8-u.png"),
        ("grade_9",     "九级",       "段位", "恭喜考取九级！",                  "考取九级","date",        "grade_9-u.png"),
        ("grade_10",    "十级",       "段位", "恭喜考取十级！",                 "考取十级","date",        "grade_10-u.png"),
    ]

    # ── 计算每个成就的达成状态 + 数值 ─────────────────────────
    def check_achievement(aid, display_fmt):
        if aid == "streak_1":    return (streak >= 1,    streak,    None)
        if aid == "streak_3":    return (streak >= 3,    streak,    None)
        if aid == "streak_7":    return (streak >= 7,    streak,    None)
        if aid == "streak_14":   return (streak >= 14,   streak,    None)
        if aid == "streak_30":   return (streak >= 30,   streak,    None)
        if aid == "streak_100":  return (streak >= 100,  streak,    None)
        if aid == "total_60":    return (total_mins >= 60,  total_mins, None)
        if aid == "total_300":   return (total_mins >= 300, total_mins, None)
        if aid == "total_600":   return (total_mins >= 600, total_mins, None)
        if aid == "total_1000":  return (total_mins >= 1000,total_mins, None)
        if aid == "first_log":   return (total_mins > 0,  total_mins, None)
        if aid == "all_items":   return (has_all_items,   1 if has_all_items else 0, None)
        if aid == "double":      return (has_double,      1 if has_double else 0, None)
        if aid == "week_champ":  return (has_week_champ,  0, None)
        if aid == "full_month":  return (has_full_month,  0, None)
        if aid in ("top1","top2","top3"):
            rank = int(aid[-1])
            if len(top_items) >= rank:
                return (True, 0, top_items[:rank])
            return (False, 0, None)
        # grade: 查预取的 grade_stats
        if aid.startswith("grade_"):
            row2 = grade_stats.get(aid)
            if row2:
                return (row2[0] == "Y", row2[1], None)
            return (False, None, None)
        return (False, 0, None)

    # ── 渲染单个卡片 ─────────────────────────────────────────
    def render_card(aid, name, ach_type, desc, badge_file, display_fmt, achieved, val, extra):
        cls = "card-v3 unlocked" if achieved else "card-v3 locked"
        badge_url = f"/static/badges/{badge_file}"
        pill_cls = f"pill type-{ach_type}"
        pill_icon = {"突破":"🏅","执着":"🔥","巅峰":"🏆","神秘":"🌈","段位":"🎓","晋级":"⭐"}.get(ach_type,"🏅")
        pill_html = f"<span class='{pill_cls}'>{pill_icon} {ach_type}</span>"
        label_html = f"<span class='label-text'>{name}</span>"

        # 数值渲染
        value_html = ""
        if display_fmt == "days":
            value_html = f"<span class='value-num'>{val}</span><span class='value-unit'>天</span>"
        elif display_fmt == "time_hours":
            h = val // 60
            m = val % 60
            if h > 0:
                value_html = f"<span class='value-num'>{h}</span><span class='value-unit'>小时</span>"
            if m > 0 or not value_html:
                value_html += f"<span class='value-num'>{m}</span><span class='value-unit'>分钟</span>"
        elif display_fmt == "minutes":
            value_html = f"<span class='value-num'>{val}</span><span class='value-unit'>分钟</span>"
        elif display_fmt == "date":
            if val:
                try:
                    d = dt.date.fromisoformat(str(val))
                    value_html = f"<span class='value-num'>{d.year}</span><span class='value-unit'>年</span><span class='value-num'>{d.month:02d}</span><span class='value-unit'>月</span><span class='value-num'>{d.day:02d}</span><span class='value-unit'>日</span>"
                except:
                    value_html = ""
            else:
                value_html = "<span class='value-empty'>—</span>"
        elif display_fmt == "top_items" and extra:
            items_html = "".join(
                f"<span class='item-pill'>{name}<span class='mins'>({mins}分钟)</span></span>"
                for name, mins in extra
            )
            value_html = f"<div class='value-list'>{items_html}</div>"
        elif display_fmt == "flag":
            value_html = "<span class='value-empty'>✓ 已达成</span>" if achieved else "<span class='value-empty'>—</span>"

        if not value_html:
            value_html = "<span class='value-empty'>—</span>"

        lock_icon = "<svg class='lock-icon' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'><rect x='3' y='11' width='18' height='11' rx='2'/><path d='M7 11V7a5 5 0 0 1 10 0v4'/></svg>" if not achieved else ""

        return f"""
    <div class="{cls}" data-id="{aid}">
      <div class="badge-wrap">
        <img class="badge-img" src="{badge_url}" alt="{name}" onerror="this.src='/static/badges/medal_badge.png'">
      </div>
      <div class="info">
        <div class="label-row">{pill_html}{label_html}</div>
        <div class="value-row">{value_html}</div>
        <div class="desc">{desc}</div>
      </div>
      {lock_icon}
    </div>"""

    # ── 渲染全部卡片 ─────────────────────────────────────────
    cards_html = []
    earned_count = 0
    for (aid, name, ach_type, desc, condition, display_fmt, badge_file) in ALL_ACHIEVEMENTS:
        achieved, val, extra = check_achievement(aid, display_fmt)
        if achieved:
            earned_count += 1
        cards_html.append(render_card(aid, name, ach_type, desc, badge_file, display_fmt, achieved, val, extra))

    body_html = "\n".join(cards_html)
    total_count = len(ALL_ACHIEVEMENTS)

    return render(
        "badges",
        child_name=child_name(),
        body_html=body_html,
        total_count=total_count,
        earned_count=earned_count,
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
