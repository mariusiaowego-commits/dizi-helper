from datetime import date
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from .lesson_manager import LessonManager
from .payment import PaymentManager
from .models import LessonStatus

app = typer.Typer(help="🎵 竹笛学习助手 - 课程管理与缴费提醒")
console = Console()

lesson_app = typer.Typer(help="课程管理")
payment_app = typer.Typer(help="缴费管理")
stat_app = typer.Typer(help="统计报表")

app.add_typer(lesson_app, name="lesson")
app.add_typer(payment_app, name="payment")
app.add_typer(stat_app, name="stat")

lesson_manager = LessonManager()
payment_manager = PaymentManager()


def parse_date(date_str: str) -> date:
    """解析日期字符串 YYYY-MM-DD"""
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise typer.BadParameter(f"日期格式错误，请使用 YYYY-MM-DD 格式: {date_str}")


def parse_month(month_str: str) -> tuple[int, int]:
    """解析月份字符串 YYYY-MM"""
    try:
        year, month = map(int, month_str.split('-'))
        return year, month
    except ValueError:
        raise typer.BadParameter(f"月份格式错误，请使用 YYYY-MM 格式: {month_str}")


@lesson_app.command("generate")
def generate_lessons(
    month: str = typer.Argument(..., help="月份，格式 YYYY-MM"),
    overwrite: bool = typer.Option(False, "--overwrite", "-o", help="覆盖已存在的课程"),
):
    """生成指定月份的课程计划"""
    year, month_num = parse_month(month)
    plan = lesson_manager.generate_monthly_lessons(year, month_num, overwrite=overwrite)

    console.print(Panel(f"[green]✅ 已生成 {year}年{month_num}月 课程计划[/green]"))
    console.print(f"📚 总课程数: {plan.total_lessons} 节")
    console.print(f"⚠️  节假日冲突: {plan.holiday_conflicts} 节")
    console.print(f"💰 总学费: {plan.total_fee} 元")
    console.print()

    print_lesson_table(plan.lessons)


@lesson_app.command("list")
def list_lessons(month: Optional[str] = typer.Argument(None, help="月份，格式 YYYY-MM，默认当前月")):
    """列出课程"""
    if month:
        year, month_num = parse_month(month)
        lessons = lesson_manager.get_lessons(year, month_num)
        title = f"{year}年{month_num}月 课程列表"
    else:
        today = date.today()
        lessons = lesson_manager.get_lessons(today.year, today.month)
        title = f"{today.year}年{today.month}月 课程列表"

    if not lessons:
        console.print("[yellow]⚠️  暂无课程记录[/yellow]")
        return

    console.print(Panel(f"[blue]{title}[/blue]"))
    print_lesson_table(lessons)


def print_lesson_table(lessons):
    """打印课程表格"""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("日期", style="dim")
    table.add_column("时间")
    table.add_column("状态")
    table.add_column("学费")
    table.add_column("缴费")
    table.add_column("节假日")
    table.add_column("备注")

    for lesson in lessons:
        status_style = {
            LessonStatus.SCHEDULED: "blue",
            LessonStatus.ATTENDED: "green",
            LessonStatus.CANCELLED: "red",
        }

        status_text = Text(
            {
                LessonStatus.SCHEDULED: "已安排",
                LessonStatus.ATTENDED: "已上课",
                LessonStatus.CANCELLED: "已取消",
            }[lesson.status],
            style=status_style[lesson.status],
        )

        fee_paid_text = Text("已缴费", style="green") if lesson.fee_paid else Text("未缴费", style="red")
        holiday_text = Text("⚠️ 冲突", style="yellow") if lesson.is_holiday_conflict else ""

        table.add_row(
            str(lesson.date),
            str(lesson.time),
            status_text,
            f"{lesson.fee} 元",
            fee_paid_text,
            holiday_text,
            lesson.notes or "",
        )

    console.print(table)


@lesson_app.command("add")
def add_lesson(date_str: str = typer.Argument(..., help="日期，格式 YYYY-MM-DD")):
    """添加课程"""
    lesson_date = parse_date(date_str)
    try:
        lesson = lesson_manager.add_lesson(lesson_date)
        console.print(f"[green]✅ 已添加课程: {lesson.date}[/green]")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")


@lesson_app.command("cancel")
def cancel_lesson(date_str: str = typer.Argument(..., help="日期，格式 YYYY-MM-DD")):
    """取消课程"""
    lesson_date = parse_date(date_str)
    success = lesson_manager.cancel_lesson(lesson_date)
    if success:
        console.print(f"[green]✅ 已取消课程: {lesson_date}[/green]")
    else:
        console.print(f"[yellow]⚠️  未找到课程: {lesson_date}[/yellow]")


@lesson_app.command("reschedule")
def reschedule_lesson(
    from_date: str = typer.Argument(..., help="原日期，格式 YYYY-MM-DD"),
    to_date: str = typer.Argument(..., help="新日期，格式 YYYY-MM-DD"),
):
    """调课"""
    from_dt = parse_date(from_date)
    to_dt = parse_date(to_date)

    try:
        lesson = lesson_manager.reschedule_lesson(from_dt, to_dt)
        if lesson:
            console.print(f"[green]✅ 已调课: {from_dt} -> {to_dt}[/green]")
        else:
            console.print(f"[yellow]⚠️  未找到课程: {from_dt}[/yellow]")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")


@lesson_app.command("confirm")
def confirm_lesson(date_str: str = typer.Argument(..., help="日期，格式 YYYY-MM-DD")):
    """确认已上课"""
    lesson_date = parse_date(date_str)
    lesson = lesson_manager.confirm_attendance(lesson_date)
    if lesson:
        console.print(f"[green]✅ 已确认上课: {lesson_date}[/green]")
    else:
        console.print(f"[yellow]⚠️  未找到课程: {lesson_date}[/yellow]")


@payment_app.command("status")
def payment_status(month: Optional[str] = typer.Argument(None, help="月份，格式 YYYY-MM，默认当前月")):
    """查看缴费状态"""
    if month:
        year, month_num = parse_month(month)
    else:
        today = date.today()
        year, month_num = today.year, today.month

    status = payment_manager.get_monthly_payment_status(year, month_num)

    console.print(Panel(f"[blue]💰 {year}年{month_num}月 缴费状态[/blue]"))
    console.print(f"📚 本月课程: {status.total_lessons} 节")
    console.print(f"✅ 已上课: {status.attended_lessons} 节")
    console.print(f"💰 应缴总额: {status.total_fee} 元")
    console.print(f"💵 已缴金额: {status.paid_amount} 元")

    if status.balance > 0:
        console.print(f"[red]❌ 待缴余额: {status.balance} 元[/red]")
        if status.last_lesson_date:
            console.print(f"📆 最后上课日: {status.last_lesson_date}")
    else:
        console.print("[green]✅ 本月费用已缴清[/green]")


@payment_app.command("record")
def record_payment(
    amount: int = typer.Argument(..., help="缴费金额"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="备注"),
):
    """记录缴费（现金）"""
    payment = payment_manager.record_payment(amount=amount, notes=notes)
    console.print(f"[green]✅ 已记录缴费: {amount} 元（现金）[/green]")
    console.print(f"📅 缴费日期: {payment.payment_date}")
    if notes:
        console.print(f"📝 备注: {notes}")


@payment_app.command("history")
def payment_history():
    """查看缴费历史"""
    payments = payment_manager.get_payment_history()

    if not payments:
        console.print("[yellow]⚠️  暂无缴费记录[/yellow]")
        return

    console.print(Panel("[blue]💰 缴费历史[/blue]"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("日期")
    table.add_column("金额", justify="right")
    table.add_column("方式")
    table.add_column("备注")

    for p in payments:
        table.add_row(
            str(p.payment_date),
            f"{p.amount} 元",
            p.payment_method,
            p.notes or "",
        )

    console.print(table)
    console.print(f"\n[green]总计: {sum(p.amount for p in payments)} 元[/green]")


@stat_app.command("monthly")
def monthly_stat(month: Optional[str] = typer.Argument(None, help="月份，格式 YYYY-MM，默认当前月")):
    """本月统计"""
    if month:
        year, month_num = parse_month(month)
    else:
        today = date.today()
        year, month_num = today.year, today.month

    lessons = lesson_manager.get_lessons(year, month_num)
    payment_status = payment_manager.get_monthly_payment_status(year, month_num)

    console.print(Panel(f"[blue]📊 {year}年{month_num}月 统计报表[/blue]"))

    status_counts = {
        "已安排": len([l for l in lessons if l.status == LessonStatus.SCHEDULED]),
        "已上课": len([l for l in lessons if l.status == LessonStatus.ATTENDED]),
        "已取消": len([l for l in lessons if l.status == LessonStatus.CANCELLED]),
    }

    console.print("📚 课程统计:")
    for status, count in status_counts.items():
        console.print(f"  - {status}: {count} 节")

    console.print(f"\n💰 财务统计:")
    console.print(f"  - 应缴总额: {payment_status.total_fee} 元")
    console.print(f"  - 已缴金额: {payment_status.paid_amount} 元")
    console.print(f"  - 待缴余额: {payment_status.balance} 元")

    if payment_status.last_lesson_date:
        console.print(f"\n📆 最后上课日: {payment_status.last_lesson_date}")


@stat_app.command("quarterly")
def quarterly_stat():
    """季度统计"""
    today = date.today()
    quarter = (today.month - 1) // 3 + 1
    start_month = (quarter - 1) * 3 + 1

    console.print(Panel(f"[blue]📊 {today.year}年 Q{quarter} 季度统计[/blue]"))

    total_lessons = 0
    total_attended = 0
    total_fee = 0
    total_paid = 0

    for month in range(start_month, start_month + 3):
        if month > 12:
            continue
        status = payment_manager.get_monthly_payment_status(today.year, month)
        total_lessons += status.total_lessons
        total_attended += status.attended_lessons
        total_fee += status.total_fee
        total_paid += status.paid_amount

    console.print(f"📚 总课程数: {total_lessons} 节")
    console.print(f"✅ 已上课: {total_attended} 节")
    console.print(f"💰 应缴总额: {total_fee} 元")
    console.print(f"💵 已缴金额: {total_paid} 元")
    console.print(f"❌ 待缴余额: {total_fee - total_paid} 元")


@stat_app.command("yearly")
def yearly_stat():
    """年度统计"""
    today = date.today()

    console.print(Panel(f"[blue]📊 {today.year}年 度统计[/blue]"))

    total_lessons = 0
    total_attended = 0
    total_fee = 0
    total_paid = 0

    for month in range(1, 13):
        status = payment_manager.get_monthly_payment_status(today.year, month)
        total_lessons += status.total_lessons
        total_attended += status.attended_lessons
        total_fee += status.total_fee
        total_paid += status.paid_amount

    console.print(f"📚 总课程数: {total_lessons} 节")
    console.print(f"✅ 已上课: {total_attended} 节")
    console.print(f"💰 应缴总额: {total_fee} 元")
    console.print(f"💵 已缴金额: {total_paid} 元")
    console.print(f"❌ 待缴余额: {total_fee - total_paid} 元")


if __name__ == "__main__":
    app()
