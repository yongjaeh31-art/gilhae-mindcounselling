"""
천간(天干)과 지지(地支) 관련 기능을 제공하는 모듈
"""
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime

class HeavenlyStemsEarthlyBranches:
    """천간과 지지 클래스"""
    
    # 천간 목록
    HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    
    # 지지 목록
    EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    # 한자 형태의 천간을 한글 형태로 변환하는 매핑
    HANJA_TO_HANGUL_STEMS = {
        "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
        "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계"
    }
    
    # 한자 형태의 지지를 한글 형태로 변환하는 매핑
    HANJA_TO_HANGUL_BRANCHES = {
        "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
        "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해"
    }
    
    # 천간의 오행 속성
    STEM_ELEMENTS = {
        "갑": "목", "을": "목", "병": "화", "정": "화",
        "무": "토", "기": "토", "경": "금", "신": "금",
        "임": "수", "계": "수"
    }
    
    # 지지의 오행 속성
    BRANCH_ELEMENTS = {
        "자": "수", "축": "토", "인": "목", "묘": "목",
        "진": "토", "사": "화", "오": "화", "미": "토",
        "신": "금", "유": "금", "술": "토", "해": "수"
    }
    
    # 천간의 음양 속성
    STEM_YIN_YANG = {
        "갑": "양", "을": "음", "병": "양", "정": "음",
        "무": "양", "기": "음", "경": "양", "신": "음",
        "임": "양", "계": "음"
    }
    
    # 지지의 음양 속성
    BRANCH_YIN_YANG = {
        "자": "양", "축": "음", "인": "양", "묘": "음",
        "진": "양", "사": "음", "오": "양", "미": "음",
        "신": "양", "유": "음", "술": "양", "해": "음"
    }
    
    # 오행의 상생 관계
    ELEMENT_GENERATION = {
        "목": "화",  # 목생화
        "화": "토",  # 화생토
        "토": "금",  # 토생금
        "금": "수",  # 금생수
        "수": "목"   # 수생목
    }
    
    # 오행의 상극 관계
    ELEMENT_CONQUEST = {
        "목": "토",  # 목극토
        "토": "수",  # 토극수
        "수": "화",  # 수극화
        "화": "금",  # 화극금
        "금": "목"   # 금극목
    }
    
    # 삼합 관계
    TRIPLE_HARMONY = {
        "인": {"묘", "오"},  # 인묘오 삼합
        "사": {"유", "축"},  # 사유축 삼합
        "신": {"자", "진"},  # 신자진 삼합
        "해": {"미", "술"}   # 해미술 삼합
    }
    
    # 육합 관계
    SIX_HARMONY = {
        "자": "축",  # 자축합
        "인": "해",  # 인해합
        "묘": "술",  # 묘술합
        "진": "유",  # 진유합
        "사": "신",  # 사신합
        "오": "미"   # 오미합
    }
    
    def __init__(self, stem: str, branch: str):
        """초기화
        
        Args:
            stem: 천간
            branch: 지지
        """
        # 한자 형태의 천간/지지를 한글 형태로 변환
        if stem in self.HANJA_TO_HANGUL_STEMS:
            stem = self.HANJA_TO_HANGUL_STEMS[stem]
        if branch in self.HANJA_TO_HANGUL_BRANCHES:
            branch = self.HANJA_TO_HANGUL_BRANCHES[branch]
            
        if stem not in self.HEAVENLY_STEMS:
            raise ValueError(f"잘못된 천간: {stem}")
        if branch not in self.EARTHLY_BRANCHES:
            raise ValueError(f"잘못된 지지: {branch}")
            
        self.stem = stem
        self.branch = branch
        
    def get_stem_element(self) -> str:
        """천간의 오행 반환
        
        Returns:
            str: 오행
        """
        return self.STEM_ELEMENTS[self.stem]
        
    def get_branch_element(self) -> str:
        """지지의 오행 반환
        
        Returns:
            str: 오행
        """
        return self.BRANCH_ELEMENTS[self.branch]
        
    def get_stem_yin_yang(self) -> str:
        """천간의 음양 반환
        
        Returns:
            str: 음양
        """
        return self.STEM_YIN_YANG[self.stem]
        
    def get_branch_yin_yang(self) -> str:
        """지지의 음양 반환
        
        Returns:
            str: 음양
        """
        return self.BRANCH_YIN_YANG[self.branch]
        
    def is_generating(self, other: 'HeavenlyStemsEarthlyBranches') -> bool:
        """상생 관계인지 확인
        
        Args:
            other: 다른 천간지지
            
        Returns:
            bool: 상생 관계이면 True
        """
        element1 = self.get_stem_element()
        element2 = other.get_stem_element()
        return self.ELEMENT_GENERATION[element1] == element2
        
    def is_conquering(self, other: 'HeavenlyStemsEarthlyBranches') -> bool:
        """상극 관계인지 확인
        
        Args:
            other: 다른 천간지지
            
        Returns:
            bool: 상극 관계이면 True
        """
        element1 = self.get_stem_element()
        element2 = other.get_stem_element()
        return self.ELEMENT_CONQUEST[element1] == element2
        
    def is_triple_harmony(self, other1: 'HeavenlyStemsEarthlyBranches', 
                         other2: 'HeavenlyStemsEarthlyBranches') -> bool:
        """삼합 관계인지 확인
        
        Args:
            other1: 첫 번째 다른 지지
            other2: 두 번째 다른 지지
            
        Returns:
            bool: 삼합 관계이면 True
        """
        if self.branch in self.TRIPLE_HARMONY:
            return (other1.branch in self.TRIPLE_HARMONY[self.branch] and 
                    other2.branch in self.TRIPLE_HARMONY[self.branch])
        return False
        
    def is_six_harmony(self, other: 'HeavenlyStemsEarthlyBranches') -> bool:
        """육합 관계인지 확인
        
        Args:
            other: 다른 지지
            
        Returns:
            bool: 육합 관계이면 True
        """
        return self.SIX_HARMONY.get(self.branch) == other.branch
        
    def __str__(self) -> str:
        """문자열 표현
        
        Returns:
            str: 천간지지 정보
        """
        stem_element = self.get_stem_element()
        stem_yin_yang = self.get_stem_yin_yang()
        branch_element = self.get_branch_element()
        branch_yin_yang = self.get_branch_yin_yang()
        
        return (f"{self.stem}{self.branch} "
                f"({stem_element}{stem_yin_yang} {branch_element}{branch_yin_yang})") 