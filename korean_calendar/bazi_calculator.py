"""사주팔자 계산용 간단한 공개 API."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Tuple

try:
    from .four_pillars import FourPillars
    from .lunar_calendar import LunarCalendar
except ImportError:
    from four_pillars import FourPillars
    from lunar_calendar import LunarCalendar


class BaziCalculator:
    """생년월일시를 네 기둥 정보로 변환한다."""

    def calculate_bazi(
        self,
        birth_date: datetime,
        birth_time: int | None = None,
        region: str | None = "서울",
        use_true_solar_time: bool = True,
    ) -> Dict[str, Tuple[str, str]]:
        """사주팔자를 계산한다.

        Args:
            birth_date: 생년월일. 시간 정보가 있으면 그대로 사용한다.
            birth_time: 0-23 사이 출생시. 지정하면 ``birth_date``의 hour를 대체한다.
            region: 진태양시 보정 지역. 기본값은 서울.
            use_true_solar_time: True이면 지역 보정을 적용한다.

        Returns:
            ``year_pillar``, ``month_pillar``, ``day_pillar``, ``time_pillar`` 키를 가진 딕셔너리.
        """
        if birth_time is not None:
            if not 0 <= birth_time <= 23:
                raise ValueError("birth_time은 0부터 23 사이여야 합니다.")
            birth_date = birth_date.replace(hour=birth_time)

        pillars = FourPillars(birth_date, region=region, use_true_solar_time=use_true_solar_time)
        return {
            "year_pillar": self._as_tuple(pillars.get_year_pillar()),
            "month_pillar": self._as_tuple(pillars.get_month_pillar()),
            "day_pillar": self._as_tuple(pillars.get_day_pillar()),
            "time_pillar": self._as_tuple(pillars.get_hour_pillar()),
        }

    @staticmethod
    def _as_tuple(pillar) -> Tuple[str, str]:
        return (pillar.stem, pillar.branch)

    def calculate_bazi_from_lunar(
        self,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        is_leap: bool = False,
        region: str | None = "서울",
        use_true_solar_time: bool = True,
    ) -> Dict[str, Tuple[str, str]]:
        """음력 생년월일시를 받아 사주팔자를 계산한다."""
        solar_date = LunarCalendar().get_solar_date(year, month, day, is_leap=is_leap)
        solar_date = solar_date.replace(hour=hour, minute=minute)
        return self.calculate_bazi(
            solar_date,
            region=region,
            use_true_solar_time=use_true_solar_time,
        )
