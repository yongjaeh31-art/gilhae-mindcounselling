"""음력-양력 변환 보조 도구.

정밀한 한국 음력 변환은 연도별 삭망/윤달 데이터가 필요하다. 이 패키지는
외부 데이터가 없어도 설치 후 실패하지 않도록 2020-2030년 설날 기준표와
월 길이 근사를 사용한다. 절기 기준 사주 계산은 ``FourPillars``를 사용한다.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

try:
    from .lunar_data import LUNAR_MONTHS
except ImportError:
    from lunar_data import LUNAR_MONTHS


class LunarCalendar:
    """양력 날짜와 음력 날짜를 상호 변환하는 경량 클래스."""

    LUNAR_NEW_YEARS: Dict[int, datetime] = {
        2020: datetime(2020, 1, 25),
        2021: datetime(2021, 2, 12),
        2022: datetime(2022, 2, 1),
        2023: datetime(2023, 1, 22),
        2024: datetime(2024, 2, 10),
        2025: datetime(2025, 1, 29),
        2026: datetime(2026, 2, 17),
        2027: datetime(2027, 2, 6),
        2028: datetime(2028, 1, 26),
        2029: datetime(2029, 2, 13),
        2030: datetime(2030, 2, 3),
    }
    MONTH_PATTERN = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]

    def __init__(self, leap_months: Dict[int, List[int]] | None = None):
        self.leap_months = leap_months or {}

    def is_leap_month(self, year: int, month: int) -> bool:
        for row in LUNAR_MONTHS.get(year, []):
            if row["month"] == month and row["leap"]:
                return True
        return month in self.leap_months.get(year, [])

    def get_lunar_date(self, solar_date: datetime) -> Tuple[int, int, int, bool]:
        solar_date = solar_date.replace(hour=0, minute=0, second=0, microsecond=0)
        exact = self._get_lunar_date_from_table(solar_date)
        if exact:
            return exact

        lunar_year = self._lunar_year_for(solar_date)
        day_offset = (solar_date - self._new_year(lunar_year)).days

        month = 1
        for month_length in self.MONTH_PATTERN:
            if day_offset < month_length:
                return (lunar_year, month, day_offset + 1, False)
            day_offset -= month_length
            month += 1

        return (lunar_year, 12, min(day_offset + 1, 30), False)

    def get_solar_date(self, year: int, month: int, day: int, is_leap: bool = False) -> datetime:
        exact = self._get_solar_date_from_table(year, month, day, is_leap)
        if exact:
            return exact

        if is_leap:
            raise ValueError("해당 연도의 윤달 변환 데이터가 없습니다.")
        if not 1 <= month <= 12:
            raise ValueError("month는 1부터 12 사이여야 합니다.")
        if day < 1:
            raise ValueError("day는 1 이상이어야 합니다.")

        offset = sum(self.MONTH_PATTERN[: month - 1]) + (day - 1)
        return self._new_year(year) + timedelta(days=offset)

    def _get_solar_date_from_table(self, year: int, month: int, day: int, is_leap: bool) -> datetime | None:
        for row in LUNAR_MONTHS.get(year, []):
            if row["month"] == month and row["leap"] == is_leap:
                if not 1 <= day <= row["days"]:
                    raise ValueError(f"음력 {year}년 {month}월은 {row['days']}일까지 있습니다.")
                return datetime.fromisoformat(row["start"]) + timedelta(days=day - 1)
        return None

    def _get_lunar_date_from_table(self, solar_date: datetime) -> Tuple[int, int, int, bool] | None:
        candidates = []
        for months in LUNAR_MONTHS.values():
            for row in months:
                start = datetime.fromisoformat(row["start"])
                end = start + timedelta(days=row["days"])
                if start <= solar_date < end:
                    candidates.append((row, start))
        if not candidates:
            return None
        row, start = max(candidates, key=lambda item: item[1])
        lunar_day = (solar_date - start).days + 1
        return (row["year"], row["month"], lunar_day, row["leap"])

    def _lunar_year_for(self, solar_date: datetime) -> int:
        year = solar_date.year
        if solar_date < self._new_year(year):
            return year - 1
        return year

    def _new_year(self, year: int) -> datetime:
        if year in self.LUNAR_NEW_YEARS:
            return self.LUNAR_NEW_YEARS[year]

        # 알려진 기준표 밖에서는 평균 태음년 길이로 근사한다.
        base_year = 2024
        return self.LUNAR_NEW_YEARS[base_year] + timedelta(days=round((year - base_year) * 354.367))
