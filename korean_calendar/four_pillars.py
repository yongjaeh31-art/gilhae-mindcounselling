"""
사주팔자(四柱八字) 계산과 기본 분석 기능.

이 모듈은 외부 패키지 없이 동작하도록 보수적인 표준 공식을 사용한다.
절기 시각까지 반영하는 전문 만세력 엔진은 아니지만, 패키지의 핵심 API가
설치 후 안정적으로 작동하도록 연/월/일/시주 계산을 제공한다.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Union

try:
    from .heavenly_stems_earthly_branches import HeavenlyStemsEarthlyBranches
except ImportError:  # 직접 파일 실행 호환
    from heavenly_stems_earthly_branches import HeavenlyStemsEarthlyBranches


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


def get_local_true_time(dt: datetime, region: str = "서울") -> datetime:
    """한국 표준시를 지역 진태양시 근사값으로 보정한다."""
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

    SOLAR_MONTH_STARTS = [
        (2, 4), (3, 6), (4, 5), (5, 6), (6, 6), (7, 7),
        (8, 8), (9, 8), (10, 8), (11, 7), (12, 7), (1, 6),
    ]

    def __init__(self, date: datetime, region: str | None = "서울", use_true_solar_time: bool = True):
        self.input_date = date
        self.region = region
        self.date = get_local_true_time(date, region or "서울") if use_true_solar_time else date
        calculation_date = self.date + timedelta(days=1) if self.date.hour >= 23 else self.date

        self.year_pillar = self.calculate_year_pillar_by_standard(calculation_date)
        self.month_pillar = self.calculate_month_pillar_by_standard(calculation_date)
        self.day_pillar = self.calculate_day_pillar_by_standard(calculation_date)
        self.hour_pillar = self.calculate_hour_pillar_by_standard(calculation_date)

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
        if date < datetime(year, 2, 4):
            year -= 1
        diff = year - 1864  # 갑자년
        return HeavenlyStemsEarthlyBranches(
            self.HEAVENLY_STEMS[diff % 10],
            self.EARTHLY_BRANCHES[diff % 12],
        )

    def _solar_month_index(self, date: datetime) -> int:
        """절입일 근사 기준으로 인월=0 ... 축월=11 인덱스를 반환한다."""
        current = date.replace(hour=0, minute=0, second=0, microsecond=0)
        starts = []
        for index, (month, day) in enumerate(self.SOLAR_MONTH_STARTS):
            year = date.year + (1 if month == 1 and date.month == 12 else 0)
            if month == 1 and date.month != 12:
                year = date.year
            start = datetime(year, month, day)
            starts.append((start, index))

        previous_year_sohan = datetime(date.year - 1, 1, 6)
        starts.append((previous_year_sohan, 11))
        starts.sort(key=lambda item: item[0])

        selected = 11
        for start, index in starts:
            if current >= start:
                selected = index
            else:
                break
        return selected

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

    def calculate_hour_pillar_by_standard(self, date: datetime) -> HeavenlyStemsEarthlyBranches:
        hour = date.hour
        branch_index = 0 if hour == 23 else ((hour + 1) // 2) % 12
        day_stem_index = self.HEAVENLY_STEMS.index(self.calculate_day_pillar_by_standard(date).stem)
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
        month_index = self._solar_month_index(self.date)
        month, day = self.SOLAR_MONTH_STARTS[month_index]
        year = self.date.year
        if month == 1 and self.date.month == 12:
            year += 1
        return datetime(year, month, day)

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
