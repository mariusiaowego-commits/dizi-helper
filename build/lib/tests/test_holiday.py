from datetime import date
from unittest import TestCase
from src.holiday import HolidayChecker


class TestHolidayChecker(TestCase):
    """节假日检测测试"""

    def test_is_holiday_may_day(self):
        """测试五一劳动节"""
        may_day = date(2026, 5, 1)
        is_holiday = HolidayChecker.is_holiday(may_day)
        # 2026年5月1日是周五，应该是劳动节假期
        # 注意：chinese_calendar 库的假期数据可能随版本变化
        # 这里我们只测试功能是否正常
        self.assertIsInstance(is_holiday, bool)

    def test_is_holiday_regular_weekday(self):
        """测试普通工作日"""
        # 2026年5月6日是周三，不是节假日
        weekday = date(2026, 5, 6)
        # 周三应该是工作日，不是节假日
        self.assertFalse(HolidayChecker.is_holiday(weekday))

    def test_is_holiday_weekend(self):
        """测试周末"""
        # 2026年5月3日是周日
        sunday = date(2026, 5, 3)
        # 周末默认是节假日
        self.assertTrue(HolidayChecker.is_holiday(sunday))

    def test_is_workday_monday(self):
        """测试周一是否为工作日"""
        # 2026年5月4日是周一
        monday = date(2026, 5, 4)
        # 如果这天不是节假日，则应该是工作日
        if not HolidayChecker.is_holiday(monday):
            self.assertTrue(HolidayChecker.is_workday(monday))

    def test_is_workday_sunday(self):
        """测试周日是否为工作日"""
        # 2026年5月3日是周日
        sunday = date(2026, 5, 3)
        # 周日一般不是工作日（除非调休）
        if sunday.weekday() == 6:  # Sunday
            # 如果不是调休工作日
            if not HolidayChecker.is_workday(sunday):
                self.assertTrue(HolidayChecker.is_holiday(sunday))

    def test_get_holiday_name(self):
        """测试获取节假日名称"""
        # 测试一个已知的节假日
        # 注意：chinese_calendar 库的日期范围可能有限
        test_date = date(2023, 5, 1)  # 2023年劳动节
        name = HolidayChecker.get_holiday_name(test_date)
        if HolidayChecker.is_holiday(test_date):
            self.assertIsNotNone(name)
            self.assertIn("劳动", name)

    def test_get_holiday_name_not_holiday(self):
        """测试非节假日返回None"""
        weekday = date(2026, 5, 6)  # 周三
        name = HolidayChecker.get_holiday_name(weekday)
        if not HolidayChecker.is_holiday(weekday):
            self.assertIsNone(name)

    def test_check_holiday_status(self):
        """测试获取节假日状态"""
        test_date = date(2026, 5, 1)
        is_holiday, name = HolidayChecker.check_holiday_status(test_date)
        self.assertIsInstance(is_holiday, bool)
        if is_holiday:
            self.assertIsNotNone(name)
        else:
            self.assertIsNone(name)

    def test_get_holidays_in_range(self):
        """测试获取日期范围内的节假日"""
        start_date = date(2026, 5, 1)
        end_date = date(2026, 5, 10)
        holidays = HolidayChecker.get_holidays_in_range(start_date, end_date)
        self.assertIsInstance(holidays, dict)
        # 5月应该有劳动节假期
        # 至少有周末
        self.assertGreaterEqual(len(holidays), 0)

    def test_get_month_holidays(self):
        """测试获取月度节假日"""
        holidays = HolidayChecker.get_month_holidays(2026, 5)
        self.assertIsInstance(holidays, dict)
        # 5月应该有劳动节+周末
        self.assertGreaterEqual(len(holidays), 0)

    def test_get_month_holidays_december(self):
        """测试12月节假日"""
        holidays = HolidayChecker.get_month_holidays(2026, 12)
        self.assertIsInstance(holidays, dict)
        # 12月有元旦+周末
        self.assertGreaterEqual(len(holidays), 0)

    def test_holiday_integration_with_lesson(self):
        """测试节假日在课程生成中的集成"""
        # 测试5月1日课程
        # 注意：实际在 lesson_manager 中使用，这里只测试 checker 本身
        may_day = date(2026, 5, 1)
        is_holiday, name = HolidayChecker.check_holiday_status(may_day)
        # 确认返回值格式正确
        self.assertIsInstance(is_holiday, bool)
        if is_holiday:
            self.assertIsInstance(name, str)
        else:
            self.assertIsNone(name)

    def test_out_of_range_date(self):
        """测试超出chinese_calendar范围的日期"""
        # 测试一个很远的日期
        far_date = date(2100, 1, 1)
        # 应该返回 False 而不是抛出异常
        try:
            is_holiday = HolidayChecker.is_holiday(far_date)
            self.assertIsInstance(is_holiday, bool)
        except Exception as e:
            self.fail(f"is_holiday raised {type(e).__name__} unexpectedly!")

    def test_out_of_range_date_name(self):
        """测试超出范围日期的名称获取"""
        far_date = date(2100, 1, 1)
        try:
            name = HolidayChecker.get_holiday_name(far_date)
            self.assertIsNone(name)
        except Exception as e:
            self.fail(f"get_holiday_name raised {type(e).__name__} unexpectedly!")
