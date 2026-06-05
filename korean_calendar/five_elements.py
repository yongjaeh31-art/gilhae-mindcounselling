"""
오행(五行) 관련 기능을 제공하는 모듈
"""
from typing import Dict, List, Tuple, Optional

class FiveElements:
    """오행 클래스"""
    
    # 오행 목록
    ELEMENTS = ["목", "화", "토", "금", "수"]
    
    # 천간의 오행 속성
    HEAVENLY_STEMS_ELEMENTS = {
        "갑": "목", "을": "목",
        "병": "화", "정": "화",
        "무": "토", "기": "토",
        "경": "금", "신": "금",
        "임": "수", "계": "수"
    }
    
    # 지지의 오행 속성
    EARTHLY_BRANCHES_ELEMENTS = {
        "자": "수", "축": "토", "인": "목", "묘": "목",
        "진": "토", "사": "화", "오": "화", "미": "토",
        "신": "금", "유": "금", "술": "토", "해": "수"
    }
    
    # 오행의 상생 관계 (생하는 오행)
    GENERATING = {
        "목": "화",  # 목생화
        "화": "토",  # 화생토
        "토": "금",  # 토생금
        "금": "수",  # 금생수
        "수": "목"   # 수생목
    }
    
    # 오행의 상극 관계 (극하는 오행)
    CONQUERING = {
        "목": "토",  # 목극토
        "토": "수",  # 토극수
        "수": "화",  # 수극화
        "화": "금",  # 화극금
        "금": "목"   # 금극목
    }
    
    # 오행의 음양 속성
    YIN_YANG = {
        "목": "양",
        "화": "양",
        "토": "음",
        "금": "음",
        "수": "음"
    }
    
    # 오행의 계절
    SEASONS = {
        "목": "봄",
        "화": "여름",
        "토": "사계절",
        "금": "가을",
        "수": "겨울"
    }
    
    # 지지별 지장간(천간) 목록
    BRANCH_HIDDEN_STEMS = {
        "자": ["계"],
        "축": ["기", "계", "신"],
        "인": ["갑", "병", "무"],
        "묘": ["을"],
        "진": ["무", "을", "계"],
        "사": ["병", "무", "경"],
        "오": ["정", "기"],
        "미": ["기", "을", "정"],
        "신": ["경", "임", "무"],
        "유": ["신"],
        "술": ["무", "신", "정"],
        "해": ["임", "갑"]
    }
    
    def __init__(self, element: Optional[str] = None):
        """초기화
        
        Args:
            element: 오행 (목, 화, 토, 금, 수) 또는 천간/지지 (선택적)
            
        Raises:
            ValueError: 잘못된 오행이나 천간/지지
        """
        if element is None:
            return
            
        # 천간이나 지지인 경우 오행으로 변환
        if element in self.HEAVENLY_STEMS_ELEMENTS:
            self.element = self.HEAVENLY_STEMS_ELEMENTS[element]
        elif element in self.EARTHLY_BRANCHES_ELEMENTS:
            self.element = self.EARTHLY_BRANCHES_ELEMENTS[element]
        elif element in self.ELEMENTS:
            self.element = element
        else:
            raise ValueError(f"잘못된 오행이나 천간/지지: {element}")
            
        # 상생 관계 (생하는 오행)
        self.generating = self.GENERATING[self.element]
        
        # 상생 관계 (생해주는 오행)
        for e, g in self.GENERATING.items():
            if g == self.element:
                self.generated = e
                break
                
        # 상극 관계 (극하는 오행)
        self.conquering = self.CONQUERING[self.element]
        
        # 상극 관계 (극해주는 오행)
        for e, c in self.CONQUERING.items():
            if c == self.element:
                self.conquered = e
                break
                
    def get_element(self, element: str) -> str:
        """오행 반환
        
        Args:
            element: 오행 (목, 화, 토, 금, 수) 또는 천간/지지
            
        Returns:
            str: 오행
            
        Raises:
            ValueError: 잘못된 오행이나 천간/지지
        """
        if element in self.HEAVENLY_STEMS_ELEMENTS:
            return self.HEAVENLY_STEMS_ELEMENTS[element]
        elif element in self.EARTHLY_BRANCHES_ELEMENTS:
            return self.EARTHLY_BRANCHES_ELEMENTS[element]
        elif element in self.ELEMENTS:
            return element
        else:
            raise ValueError(f"잘못된 오행이나 천간/지지: {element}")
            
    def generates(self, source: str, target: str) -> bool:
        """상생 관계 확인
        
        Args:
            source: 생하는 오행
            target: 생되는 오행
            
        Returns:
            bool: 상생 관계 여부
        """
        source_element = self.get_element(source)
        target_element = self.get_element(target)
        return self.GENERATING[source_element] == target_element
        
    def controls(self, source: str, target: str) -> bool:
        """상극 관계 확인
        
        Args:
            source: 극하는 오행
            target: 극되는 오행
            
        Returns:
            bool: 상극 관계 여부
        """
        source_element = self.get_element(source)
        target_element = self.get_element(target)
        return self.CONQUERING[source_element] == target_element
        
    def get_generating(self) -> str:
        """내가 생하는 오행 반환
        
        Returns:
            str: 내가 생하는 오행
        """
        return self.generating
        
    def get_generated(self) -> str:
        """나를 생하는 오행 반환
        
        Returns:
            str: 나를 생하는 오행
        """
        return self.generated
        
    def get_overcoming(self) -> str:
        """내가 극하는 오행 반환
        
        Returns:
            str: 내가 극하는 오행
        """
        return self.conquering
        
    def get_overcome(self) -> str:
        """나를 극하는 오행 반환
        
        Returns:
            str: 나를 극하는 오행
        """
        return self.conquered
        
    def get_yin_yang(self) -> str:
        """음양 속성 반환
        
        Returns:
            str: 음양 속성 (양/음)
        """
        return self.YIN_YANG[self.element]
        
    def get_season(self) -> str:
        """계절 반환
        
        Returns:
            str: 계절
        """
        return self.SEASONS[self.element]
        
    def __str__(self) -> str:
        """문자열 표현
        
        Returns:
            str: 오행 정보
        """
        return f"{self.element} ({self.get_yin_yang()})"

class TenGods:
    """십성(十神) 계산 클래스 (만세력 표준)"""
    gods = ["비견", "겁재", "식신", "상관", "정재", "편재", "정관", "편관", "정인", "편인"]

    def __init__(self, day_stem: str):
        self.day_stem = day_stem
        self.day_element = FiveElements.HEAVENLY_STEMS_ELEMENTS[day_stem]
        # 천간 음양: 갑, 병, 무, 경, 임(양), 을, 정, 기, 신, 계(음)
        self.day_yinyang = "양" if ["갑","병","무","경","임"].count(day_stem) else "음"

    def get_god(self, target: str) -> str:
        # 천간/지지 모두 지원
        if target in FiveElements.HEAVENLY_STEMS_ELEMENTS:
            target_element = FiveElements.HEAVENLY_STEMS_ELEMENTS[target]
            target_yinyang = "양" if ["갑","병","무","경","임"].count(target) else "음"
        elif target in FiveElements.EARTHLY_BRANCHES_ELEMENTS:
            target_element = FiveElements.EARTHLY_BRANCHES_ELEMENTS[target]
            # 지지는 음양이 고정(자, 인, 진, 오, 신, 술=양 / 축, 묘, 사, 미, 유, 해=음)
            yang_branches = ["자","인","진","오","신","술"]
            target_yinyang = "양" if target in yang_branches else "음"
        else:
            return None
        # 십성 결정
        if self.day_element == target_element:
            return "비견" if self.day_yinyang == target_yinyang else "겁재"
        elif FiveElements.GENERATING[self.day_element] == target_element:
            return "식신" if self.day_yinyang == target_yinyang else "상관"
        elif FiveElements.CONQUERING[self.day_element] == target_element:
            return "편재" if self.day_yinyang == target_yinyang else "정재"
        elif FiveElements.CONQUERING[target_element] == self.day_element:
            return "편관" if self.day_yinyang == target_yinyang else "정관"
        elif FiveElements.GENERATING[target_element] == self.day_element:
            return "편인" if self.day_yinyang == target_yinyang else "정인"
        else:
            return None 
