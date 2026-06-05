"""
24절기(二十四節氣) 관련 기능을 제공하는 모듈
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import math

try:
    from .solar_terms_data import SOLAR_TERMS
except ImportError:
    from solar_terms_data import SOLAR_TERMS


MAJOR_TERM_NAMES = [
    "입춘", "경칩", "청명", "입하", "망종", "소서",
    "입추", "백로", "한로", "입동", "대설", "소한",
]


def get_year_solar_terms(year: int) -> List[Tuple[str, datetime]]:
    """해당 양력 연도의 24절기 절입시각을 반환한다."""
    if year not in SOLAR_TERMS:
        raise ValueError("절기 DB는 1900년부터 2050년까지 지원합니다.")
    return [(row["name"], datetime.fromisoformat(row["datetime"])) for row in SOLAR_TERMS[year]]


def get_solar_term_datetime(year: int, name: str) -> datetime:
    """해당 연도와 절기명의 정확 절입시각을 반환한다."""
    for term_name, term_date in get_year_solar_terms(year):
        if term_name == name:
            return term_date
    raise ValueError(f"{year}년에 {name} 절기 데이터가 없습니다.")


def iter_solar_terms_around(date: datetime) -> List[Tuple[str, datetime]]:
    """날짜 주변 3개년 절기를 시간순으로 반환한다."""
    terms: List[Tuple[str, datetime]] = []
    for year in range(date.year - 1, date.year + 2):
        if year in SOLAR_TERMS:
            terms.extend(get_year_solar_terms(year))
    terms.sort(key=lambda item: item[1])
    return terms


def get_previous_major_term(date: datetime) -> Tuple[str, datetime] | None:
    """지정 시각 이전 또는 같은 12절 절입시각을 반환한다."""
    previous = None
    for name, term_date in iter_solar_terms_around(date):
        if name in MAJOR_TERM_NAMES and term_date <= date:
            previous = (name, term_date)
        elif term_date > date and previous:
            break
    return previous


def get_next_major_term(date: datetime) -> Tuple[str, datetime] | None:
    """지정 시각 이후의 다음 12절 절입시각을 반환한다."""
    for name, term_date in iter_solar_terms_around(date):
        if name in MAJOR_TERM_NAMES and term_date > date:
            return name, term_date
    return None


def get_major_term_index(date: datetime) -> int:
    """인월=0 ... 축월=11 절기 월 인덱스를 반환한다."""
    previous = get_previous_major_term(date)
    if previous is None:
        raise ValueError("해당 날짜의 이전 절입시각을 찾을 수 없습니다.")
    return MAJOR_TERM_NAMES.index(previous[0])


class SolarTerms:
    """24절기 클래스"""
    
    # 24절기 목록
    TERMS = [
        "입춘", "우수", "경칩", "춘분", "청명", "곡우",
        "입하", "소만", "망종", "하지", "소서", "대서",
        "입추", "처서", "백로", "추분", "한로", "상강",
        "입동", "소설", "대설", "동지", "소한", "대한"
    ]
    
    # 24절기의 오행 속성
    ELEMENTS = {
        "입춘": "목", "우수": "목", "경칩": "목", "춘분": "목",
        "청명": "화", "곡우": "화", "입하": "화", "소만": "화",
        "망종": "토", "하지": "토", "소서": "토", "대서": "토",
        "입추": "금", "처서": "금", "백로": "금", "추분": "금",
        "한로": "수", "상강": "수", "입동": "수", "소설": "수",
        "대설": "수", "동지": "수", "소한": "수", "대한": "수"
    }
    
    # 24절기의 음양 속성
    YIN_YANG = {
        "입춘": "양", "우수": "음", "경칩": "양", "춘분": "음",
        "청명": "양", "곡우": "음", "입하": "양", "소만": "음",
        "망종": "양", "하지": "음", "소서": "양", "대서": "음",
        "입추": "양", "처서": "음", "백로": "양", "추분": "음",
        "한로": "양", "상강": "음", "입동": "양", "소설": "음",
        "대설": "양", "동지": "음", "소한": "양", "대한": "음"
    }
    
    # 24절기의 계절
    SEASONS = {
        "입춘": "봄", "우수": "봄", "경칩": "봄", "춘분": "봄",
        "청명": "봄", "곡우": "봄", "입하": "여름", "소만": "여름",
        "망종": "여름", "하지": "여름", "소서": "여름", "대서": "여름",
        "입추": "가을", "처서": "가을", "백로": "가을", "추분": "가을",
        "한로": "가을", "상강": "가을", "입동": "겨울", "소설": "겨울",
        "대설": "겨울", "동지": "겨울", "소한": "겨울", "대한": "겨울"
    }
    
    def __init__(self, date: datetime):
        """초기화
        
        Args:
            date: 날짜
        """
        self.date = date
        
    def get_solar_term(self) -> str:
        """해당 날짜의 24절기 반환
        
        Returns:
            str: 24절기
        """
        previous = None
        for term_name, term_date in iter_solar_terms_around(self.date):
            if term_date <= self.date:
                previous = term_name
            else:
                break
        if previous is None:
            raise ValueError("해당 날짜의 절기 데이터를 찾을 수 없습니다.")
        return previous
        
    def get_element(self) -> str:
        """해당 날짜의 24절기 오행 반환
        
        Returns:
            str: 오행
        """
        term = self.get_solar_term()
        return self.ELEMENTS[term]
        
    def get_yin_yang(self) -> str:
        """해당 날짜의 24절기 음양 반환
        
        Returns:
            str: 음양
        """
        term = self.get_solar_term()
        return self.YIN_YANG[term]
        
    def get_season(self) -> str:
        """해당 날짜의 24절기 계절 반환
        
        Returns:
            str: 계절
        """
        term = self.get_solar_term()
        return self.SEASONS[term]
        
    def __str__(self) -> str:
        """문자열 표현
        
        Returns:
            str: 24절기 정보
        """
        term = self.get_solar_term()
        season = self.get_season()
        element = self.get_element()
        yin_yang = self.get_yin_yang()
        
        return f"{term} ({season}, {element}행, {yin_yang}양)" 
