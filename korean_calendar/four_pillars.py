"""
사주팔자(四柱八字) 계산과 기본 분석 기능.

이 모듈은 외부 패키지 없이 동작하도록 보수적인 표준 공식을 사용한다.
1900년부터 2050년까지의 음력/절기 DB를 기준으로 연/월/일/시주 계산을 제공한다.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Union

try:
    from .heavenly_stems_earthly_branches import HeavenlyStemsEarthlyBranches
    from .solar_terms import get_major_term_index, get_previous_major_term, get_solar_term_datetime
except ImportError:  # 직접 파일 실행 호환
    from heavenly_stems_earthly_branches import HeavenlyStemsEarthlyBranches
    from solar_terms import get_major_term_index, get_previous_major_term, get_solar_term_datetime


REGION_TIME_OFFSET = {
    "서울": 32 * 60 + 5,
    "인천": 33 * 60 + 32,
    "수원": 31 * 60 + 53,
    "대전": 30 * 60 + 19,
    "대구": 25 * 60 + 36,
    "부산": 25 * 60 + 23,
    "광주": 32 * 60 + 17,
    "제주": 33 * 60 + 52,
    "울산": 22 * 60 + 36,
    "포항": 22 * 60 + 24,
}

REGION_LONGITUDE = {
    "서울": 126.9780,
    "인천": 126.7052,
    "수원": 127.0286,
    "대전": 127.3845,
    "대구": 128.6014,
    "부산": 129.0756,
    "광주": 126.8526,
    "제주": 126.5312,
    "울산": 129.3114,
    "포항": 129.3650,
}


def get_local_true_time(
    dt: datetime,
    region: str = "서울",
    longitude: float | None = None,
    standard_meridian: float = 135.0,
) -> datetime:
    """한국 표준시를 지역 진태양시 근사값으로 보정한다."""
    if longitude is not None:
        offset_minutes = (standard_meridian - longitude) * 4
        return dt - timedelta(minutes=offset_minutes)
    if region in REGION_LONGITUDE:
        offset_minutes = (standard_meridian - REGION_LONGITUDE[region]) * 4
        return dt - timedelta(minutes=offset_minutes)
    offset = REGION_TIME_OFFSET.get(region, REGION_TIME_OFFSET["서울"])
    return dt - timedelta(seconds=offset)


class FourPillars:
    """생년월일시를 기준으로 사주 네 기둥을 계산한다."""

    HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    MONTH_BRANCHES = ["인", "묘", "진", "사", "오", "미", "신", "유", "술", "해", "자", "축"]
    ELEMENTS = ["목", "화", "토", "금", "수"]

    STEM_ELEMENTS = {
        "갑": "목", "을": "목", "병": "화", "정": "화", "무": "토",
        "기": "토", "경": "금", "신": "금", "임": "수", "계": "수",
    }
    BRANCH_ELEMENTS = {
        "자": "수", "축": "토", "인": "목", "묘": "목", "진": "토", "사": "화",
        "오": "화", "미": "토", "신": "금", "유": "금", "술": "토", "해": "수",
    }
    GENERATING = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
    CONTROLLING = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}

    MONTH_STEM_START = {
        "갑": 2, "기": 2,  # 병인월
        "을": 4, "경": 4,  # 무인월
        "병": 6, "신": 6,  # 경인월
        "정": 8, "임": 8,  # 임인월
        "무": 0, "계": 0,  # 갑인월
    }

    def __init__(
        self,
        date: datetime,
        region: str | None = "서울",
        use_true_solar_time: bool = True,
        longitude: float | None = None,
        standard_meridian: float = 135.0,
        day_change: str = "zi",
        use_true_solar_for_terms: bool = False,
    ):
        self.input_date = date
        self.region = region
        self.day_change = day_change
        if day_change not in {"zi", "midnight", "split_zi"}:
            raise ValueError("day_change는 'zi', 'midnight', 'split_zi' 중 하나여야 합니다.")

        self.date = (
            get_local_true_time(date, region or "서울", longitude=longitude, standard_meridian=standard_meridian)
            if use_true_solar_time else date
        )
        self.term_date = self.date if use_true_solar_for_terms else date
        day_date = self._day_calculation_date(self.date)

        self.year_pillar = self.calculate_year_pillar_by_standard(self.term_date)
        self.month_pillar = self.calculate_month_pillar_by_standard(self.term_date)
        self.day_pillar = self.calculate_day_pillar_by_standard(day_date)
        self.hour_pillar = self.calculate_hour_pillar_by_standard(self.date, self.day_pillar.stem)

    def get_year_pillar(self) -> HeavenlyStemsEarthlyBranches:
        return self.year_pillar

    def get_month_pillar(self) -> HeavenlyStemsEarthlyBranches:
        return self.month_pillar

    def get_day_pillar(self) -> HeavenlyStemsEarthlyBranches:
        return self.day_pillar

    def get_hour_pillar(self) -> HeavenlyStemsEarthlyBranches:
        return self.hour_pillar

    def get_day_master(self) -> HeavenlyStemsEarthlyBranches:
        return self.day_pillar

    def get_all_pillars(self) -> List[HeavenlyStemsEarthlyBranches]:
        return [self.year_pillar, self.month_pillar, self.day_pillar, self.hour_pillar]

    def calculate_year_pillar_by_standard(self, date: datetime) -> HeavenlyStemsEarthlyBranches:
        year = date.year
        if date < get_solar_term_datetime(year, "입춘"):
            year -= 1
        diff = year - 1864  # 갑자년
        return HeavenlyStemsEarthlyBranches(
            self.HEAVENLY_STEMS[diff % 10],
            self.EARTHLY_BRANCHES[diff % 12],
        )

    def _day_calculation_date(self, date: datetime) -> datetime:
        if self.day_change == "zi" and date.hour >= 23:
            return date + timedelta(days=1)
        return date

    def _solar_month_index(self, date: datetime) -> int:
        """정확 절입시각 기준으로 인월=0 ... 축월=11 인덱스를 반환한다."""
        return get_major_term_index(date)

    def calculate_month_pillar_by_solar_term(self, date: datetime) -> HeavenlyStemsEarthlyBranches:
        return self.calculate_month_pillar_by_standard(date)

    def calculate_month_pillar_by_standard(self, date: datetime) -> HeavenlyStemsEarthlyBranches:
        month_index = self._solar_month_index(date)
        year_stem = self.calculate_year_pillar_by_standard(date).stem
        stem_start = self.MONTH_STEM_START[year_stem]
        stem = self.HEAVENLY_STEMS[(stem_start + month_index) % 10]
        branch = self.MONTH_BRANCHES[month_index]
        return HeavenlyStemsEarthlyBranches(stem, branch)

    def calculate_day_pillar_by_standard(self, date: datetime) -> HeavenlyStemsEarthlyBranches:
        # 1984-01-01을 갑오일로 두는 60갑자 순환 근사.
        base_date = datetime(1984, 1, 1)
        days = (date.replace(hour=0, minute=0, second=0, microsecond=0) - base_date).days
        return HeavenlyStemsEarthlyBranches(
            self.HEAVENLY_STEMS[days % 10],
            self.EARTHLY_BRANCHES[(days + 6) % 12],
        )

    def calculate_hour_pillar_by_standard(self, date: datetime, day_stem: str | None = None) -> HeavenlyStemsEarthlyBranches:
        hour = date.hour
        branch_index = 0 if hour == 23 else ((hour + 1) // 2) % 12
        if day_stem is None:
            day_stem = self.calculate_day_pillar_by_standard(self._day_calculation_date(date)).stem
        day_stem_index = self.HEAVENLY_STEMS.index(day_stem)
        stem_index = (day_stem_index * 2 + branch_index) % 10
        return HeavenlyStemsEarthlyBranches(
            self.HEAVENLY_STEMS[stem_index],
            self.EARTHLY_BRANCHES[branch_index],
        )

    def get_strong_elements(self) -> List[str]:
        counts = self._element_counts()
        max_count = max(counts.values())
        return [element for element, count in counts.items() if count == max_count]

    def get_weak_elements(self) -> List[str]:
        counts = self._element_counts()
        min_count = min(counts.values())
        return [element for element, count in counts.items() if count == min_count]

    def get_pillars_relationship(self) -> Dict[str, List[str]]:
        return self._get_element_relationships(self.day_pillar.stem)

    def get_pattern(self) -> Dict[str, str]:
        day_element = self.STEM_ELEMENTS[self.day_pillar.stem]
        month_element = self.BRANCH_ELEMENTS[self.month_pillar.branch]
        if self.GENERATING[day_element] == month_element:
            return {"격": "식상격", "특성": "표현력과 생산성이 강한 구조"}
        if self.GENERATING[month_element] == day_element:
            return {"격": "인성격", "특성": "학습, 보호, 지원의 기운이 강한 구조"}
        if self.CONTROLLING[day_element] == month_element:
            return {"격": "재성격", "특성": "현실 감각과 자원 운용 성향이 강한 구조"}
        if self.CONTROLLING[month_element] == day_element:
            return {"격": "관성격", "특성": "규범, 책임, 조직성이 강한 구조"}
        return {"격": "비겁격", "특성": "자기 주도성과 독립성이 강한 구조"}

    def get_missing_elements(self) -> Dict[str, List[str]]:
        counts = self._element_counts()
        missing = [element for element, count in counts.items() if count == 0]
        return {"무자": missing, "영향": [f"{element} 기운 보완 필요" for element in missing]}

    def get_use_god(self) -> Dict[str, str]:
        counts = self._element_counts()
        weakest = min(counts.items(), key=lambda item: item[1])[0]
        return {"용신": weakest, "이유": f"오행 분포에서 {weakest} 기운이 가장 약함"}

    def get_avoid_god(self) -> Dict[str, Union[str, List[float]]]:
        counts = self._element_counts()
        strongest = max(counts.items(), key=lambda item: item[1])[0]
        return {
            "기신": strongest,
            "이유": f"오행 분포에서 {strongest} 기운이 가장 강함",
            "점수": [round(counts[element] / 8, 2) for element in self.ELEMENTS],
        }

    def get_month_solar_term(self) -> datetime:
        previous = get_previous_major_term(self.term_date)
        if previous is None:
            raise ValueError("해당 날짜의 절입시각을 찾을 수 없습니다.")
        return previous[1]

    def _element_counts(self) -> Dict[str, int]:
        counts = {element: 0 for element in self.ELEMENTS}
        for pillar in self.get_all_pillars():
            counts[pillar.get_stem_element()] += 1
            counts[pillar.get_branch_element()] += 1
        return counts

    def _get_element_relationships(self, day_stem: str) -> Dict[str, List[str]]:
        day_element = self.STEM_ELEMENTS[day_stem]
        relationships = {"비겁": [], "식상": [], "재성": [], "관성": [], "인성": [], "생조": []}
        labels = [("년주", self.year_pillar), ("월주", self.month_pillar), ("일주", self.day_pillar), ("시주", self.hour_pillar)]

        for label, pillar in labels:
            for place, element in [("천간", pillar.get_stem_element()), ("지지", pillar.get_branch_element())]:
                if element == day_element:
                    relationships["비겁"].append(f"{label} {place}")
                elif self.GENERATING[day_element] == element:
                    relationships["식상"].append(f"{label} {place}")
                elif self.GENERATING[element] == day_element:
                    relationships["인성"].append(f"{label} {place}")
                elif self.CONTROLLING[day_element] == element:
                    relationships["재성"].append(f"{label} {place}")
                elif self.CONTROLLING[element] == day_element:
                    relationships["관성"].append(f"{label} {place}")
        return relationships

    def __str__(self) -> str:
        return (
            f"년주: {self.year_pillar}\n"
            f"월주: {self.month_pillar}\n"
            f"일주: {self.day_pillar}\n"
            f"시주: {self.hour_pillar}"
        )
