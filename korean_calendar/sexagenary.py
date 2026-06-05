"""
간지(干支) 계산을 위한 모듈
"""
from datetime import datetime
from typing import Tuple

class Sexagenary:
    """간지(干支) 계산 클래스"""
    
    # 천간(天干)
    HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    
    # 지지(地支)
    EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    # 12지신
    ZODIAC_ANIMALS = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    
    # 오행
    FIVE_ELEMENTS = {
        "갑": "목", "을": "목",
        "병": "화", "정": "화",
        "무": "토", "기": "토",
        "경": "금", "신": "금",
        "임": "수", "계": "수"
    }
    
    # 월의 천간 시작 인덱스
    MONTH_STEM_START = {
        "갑": 2, "을": 4, "병": 6, "정": 8, "무": 0,
        "기": 2, "경": 4, "신": 6, "임": 8, "계": 0
    }
    
    def __init__(self, date: datetime):
        """초기화
        
        Args:
            date: 날짜
        """
        self.date = date
        
    def get_year_stem_branch(self) -> Tuple[str, str]:
        """연도의 간지 반환
        
        Returns:
            Tuple[str, str]: (천간, 지지)
        """
        # 1984년은 갑자년
        year = self.date.year
        stem_index = (year - 1984) % 10
        branch_index = (year - 1984) % 12
        
        return (self.HEAVENLY_STEMS[stem_index], self.EARTHLY_BRANCHES[branch_index])
        
    def get_month_stem_branch(self) -> Tuple[str, str]:
        """월의 간지 반환
        
        Returns:
            Tuple[str, str]: (천간, 지지)
        """
        year_stem = self.get_year_stem_branch()[0]
        month = self.date.month
        
        # 월의 천간 계산
        stem_start = self.MONTH_STEM_START[year_stem]
        stem_index = (stem_start + month - 1) % 10
        
        # 월의 지지 계산 (정월은 인(寅)으로 시작)
        # 1월은 인(寅), 2월은 묘(卯), ..., 6월은 사(巳)
        branch_index = (month + 1) % 12  # 1월은 인(寅)부터 시작
        if month == 6:  # 6월은 사(巳)
            branch_index = 5
        
        return (self.HEAVENLY_STEMS[stem_index], self.EARTHLY_BRANCHES[branch_index])
        
    def get_day_stem_branch(self) -> Tuple[str, str]:
        """일의 간지 반환
        
        Returns:
            Tuple[str, str]: (천간, 지지)
        """
        # 1984년 1월 1일은 갑오일
        base_date = datetime(1984, 1, 1)
        days = (self.date - base_date).days
        
        # 60갑자 순환
        cycle_index = days % 60
        
        # 천간과 지지 계산
        stem_index = cycle_index % 10
        branch_index = (cycle_index + 6) % 12
        
        return (self.HEAVENLY_STEMS[stem_index], self.EARTHLY_BRANCHES[branch_index])
        
    def get_zodiac_animal(self) -> str:
        """12지신(띠) 반환
        
        Returns:
            str: 12지신
        """
        year = self.date.year
        return self.ZODIAC_ANIMALS[(year - 1984) % 12]
        
    def get_year_element(self) -> str:
        """연도의 오행 반환
        
        Returns:
            str: 오행
        """
        stem = self.get_year_stem_branch()[0]
        return self.FIVE_ELEMENTS[stem]
        
    def get_month_element(self) -> str:
        """월의 오행 반환
        
        Returns:
            str: 오행
        """
        stem = self.get_month_stem_branch()[0]
        return self.FIVE_ELEMENTS[stem]
        
    def get_day_element(self) -> str:
        """일의 오행 반환
        
        Returns:
            str: 오행
        """
        stem = self.get_day_stem_branch()[0]
        return self.FIVE_ELEMENTS[stem]
        
    def __str__(self) -> str:
        """문자열 표현
        
        Returns:
            str: 간지 문자열
        """
        year_stem, year_branch = self.get_year_stem_branch()
        month_stem, month_branch = self.get_month_stem_branch()
        day_stem, day_branch = self.get_day_stem_branch()
        
        return f"{year_stem}{year_branch}년 {month_stem}{month_branch}월 {day_stem}{day_branch}일" 
