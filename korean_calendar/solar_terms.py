"""
24절기(二十四節氣) 관련 기능을 제공하는 모듈
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import math

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
        # 1984년 절기 기준일
        base_dates = [
            ("소한", datetime(1984, 1, 6)),
            ("대한", datetime(1984, 1, 21)),
            ("입춘", datetime(1984, 2, 4)),
            ("우수", datetime(1984, 2, 19)),
            ("경칩", datetime(1984, 3, 5)),
            ("춘분", datetime(1984, 3, 21)),
            ("청명", datetime(1984, 4, 5)),
            ("곡우", datetime(1984, 4, 20)),
            ("입하", datetime(1984, 5, 6)),
            ("소만", datetime(1984, 5, 21)),
            ("망종", datetime(1984, 6, 6)),
            ("하지", datetime(1984, 6, 21)),
            ("소서", datetime(1984, 7, 7)),
            ("대서", datetime(1984, 7, 23)),
            ("입추", datetime(1984, 8, 8)),
            ("처서", datetime(1984, 8, 23)),
            ("백로", datetime(1984, 9, 8)),
            ("추분", datetime(1984, 9, 23)),
            ("한로", datetime(1984, 10, 8)),
            ("상강", datetime(1984, 10, 24)),
            ("입동", datetime(1984, 11, 8)),
            ("소설", datetime(1984, 11, 22)),
            ("대설", datetime(1984, 12, 7)),
            ("동지", datetime(1984, 12, 22))
        ]
        
        # 날짜 차이 계산
        year_diff = self.date.year - 1984
        
        # 해당 연도의 절기일 계산
        term_dates = [(term, base_date + timedelta(days=year_diff * 365.2422)) for term, base_date in base_dates]
        
        # 절기 찾기
        for i in range(len(term_dates)):
            current_term, current_date = term_dates[i]
            next_term, next_date = term_dates[(i + 1) % len(term_dates)]
            
            # 현재 절기일과 다음 절기일 사이의 중간점 계산
            if i == len(term_dates) - 1:
                next_date = next_date + timedelta(days=365.2422)
            mid_date = current_date + (next_date - current_date) / 2
            
            # 현재 날짜가 중간점보다 작으면 현재 절기
            if self.date < mid_date:
                return current_term
        
        # 마지막 절기 반환
        return term_dates[-1][0]
        
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