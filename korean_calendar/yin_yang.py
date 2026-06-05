"""
음양오행 관련 기능을 제공하는 모듈
"""
from typing import Dict, List, Optional, Set

class YinYangFiveElements:
    """음양오행 클래스"""
    
    # 음양
    YIN_YANG = {
        # 천간의 음양
        "갑": "양", "을": "음",
        "병": "양", "정": "음",
        "무": "양", "기": "음",
        "경": "양", "신": "음",
        "임": "양", "계": "음",
        
        # 지지의 음양
        "자": "양", "축": "음",
        "인": "양", "묘": "음",
        "진": "양", "사": "음",
        "오": "양", "미": "음",
        "신": "양", "유": "음",
        "술": "양", "해": "음",
        
        # 절기의 음양
        "입춘": "양", "우수": "음",
        "경칩": "양", "춘분": "음",
        "청명": "양", "곡우": "음",
        "입하": "양", "소만": "음",
        "망종": "양", "하지": "음",
        "소서": "양", "대서": "음",
        "입추": "양", "처서": "음",
        "백로": "양", "추분": "음",
        "한로": "양", "상강": "음",
        "입동": "양", "소설": "음",
        "대설": "양", "동지": "음",
        "소한": "양", "대한": "음"
    }
    
    # 오행
    FIVE_ELEMENTS = {
        # 천간의 오행
        "갑": "목", "을": "목",
        "병": "화", "정": "화",
        "무": "토", "기": "토",
        "경": "금", "신": "금",
        "임": "수", "계": "수",
        
        # 지지의 오행
        "자": "수", "축": "토",
        "인": "목", "묘": "목",
        "진": "토", "사": "화",
        "오": "화", "미": "토",
        "신": "금", "유": "금",
        "술": "토", "해": "수",
        
        # 계절의 오행
        "봄": "목",
        "여름": "화",
        "가을": "금",
        "겨울": "수"
    }
    
    # 오행의 상생 관계
    GENERATING = {
        "목": "화",  # 목생화
        "화": "토",  # 화생토
        "토": "금",  # 토생금
        "금": "수",  # 금생수
        "수": "목"   # 수생목
    }
    
    # 오행의 상극 관계
    OVERCOMING = {
        "목": "토",  # 목극토
        "토": "수",  # 토극수
        "수": "화",  # 수극화
        "화": "금",  # 화극금
        "금": "목"   # 금극목
    }
    
    # 오행 관계 매트릭스
    RELATIONSHIP_MATRIX = {
        "목": {
            "목": "동일",
            "화": "상생",
            "토": "상극",
            "금": "무관",
            "수": "피생"
        },
        "화": {
            "목": "피생",
            "화": "동일",
            "토": "상생",
            "금": "상극",
            "수": "무관"
        },
        "토": {
            "목": "피극",
            "화": "피생",
            "토": "동일",
            "금": "상생",
            "수": "상극"
        },
        "금": {
            "목": "무관",
            "화": "피극",
            "토": "피생",
            "금": "동일",
            "수": "상생"
        },
        "수": {
            "목": "상생",
            "화": "무관",
            "토": "피극",
            "금": "피생",
            "수": "동일"
        }
    }
    
    @classmethod
    def get_yin_yang(cls, char: str) -> str:
        """문자의 음양 속성 반환
        
        Args:
            char: 천간, 지지, 절기 등의 문자
            
        Returns:
            str: 음양 ("음" 또는 "양")
        """
        return cls.YIN_YANG.get(char)
        
    @classmethod
    def get_element(cls, char: str) -> str:
        """문자의 오행 속성 반환
        
        Args:
            char: 천간, 지지, 계절 등의 문자
            
        Returns:
            str: 오행 ("목", "화", "토", "금", "수")
        """
        return cls.FIVE_ELEMENTS.get(char)
        
    @classmethod
    def get_generating_element(cls, element: str) -> str:
        """해당 오행이 생성하는 오행 반환
        
        Args:
            element: 오행 ("목", "화", "토", "금", "수")
            
        Returns:
            str: 생성되는 오행
        """
        return cls.GENERATING.get(element)
        
    @classmethod
    def get_overcoming_element(cls, element: str) -> str:
        """해당 오행이 극하는 오행 반환
        
        Args:
            element: 오행 ("목", "화", "토", "금", "수")
            
        Returns:
            str: 극해지는 오행
        """
        return cls.OVERCOMING.get(element)
        
    @classmethod
    def is_yin(cls, char: str) -> bool:
        """음의 속성인지 확인
        
        Args:
            char: 천간, 지지, 절기 등의 문자
            
        Returns:
            bool: 음의 속성이면 True
        """
        return cls.get_yin_yang(char) == "음"
        
    @classmethod
    def is_yang(cls, char: str) -> bool:
        """양의 속성인지 확인
        
        Args:
            char: 천간, 지지, 절기 등의 문자
            
        Returns:
            bool: 양의 속성이면 True
        """
        return cls.get_yin_yang(char) == "양"
        
    @classmethod
    def get_element_relationship(cls, element1: str, element2: str) -> str:
        """두 오행 사이의 관계 반환
        
        Args:
            element1: 첫 번째 오행
            element2: 두 번째 오행
            
        Returns:
            str: 관계 설명 ("상생", "상극", "피생", "피극", "동일", "무관")
        """
        return cls.RELATIONSHIP_MATRIX[element1][element2] 