"""
24절기 관련 기능을 제공하는 모듈
"""
from datetime import datetime
from typing import Optional, List, Dict

class SolarTerm:
    """24절기 클래스"""
    
    # 24절기 이름과 설명
    TERMS = {
        "소한": "작은 추위",
        "대한": "큰 추위",
        "입춘": "봄이 시작됨",
        "우수": "비가 내리기 시작함",
        "경칩": "겨울잠 자던 벌레가 깨어남",
        "춘분": "봄의 한가운데",
        "청명": "날씨가 맑고 밝음",
        "곡우": "곡식에 비가 내림",
        "입하": "여름이 시작됨",
        "소만": "만물이 생장하기 시작함",
        "망종": "보리를 거두고 벼를 심음",
        "하지": "여름의 한가운데",
        "소서": "작은 더위",
        "대서": "큰 더위",
        "입추": "가을이 시작됨",
        "처서": "더위가 그치기 시작함",
        "백로": "이슬이 맺히기 시작함",
        "추분": "가을의 한가운데",
        "한로": "찬 이슬이 내리기 시작함",
        "상강": "서리가 내리기 시작함",
        "입동": "겨울이 시작됨",
        "소설": "작은 눈이 내리기 시작함",
        "대설": "큰 눈이 내리기 시작함",
        "동지": "겨울의 한가운데"
    }
    
    # 계절별 절기
    SEASONS = {
        "봄": ["입춘", "우수", "경칩", "춘분", "청명", "곡우"],
        "여름": ["입하", "소만", "망종", "하지", "소서", "대서"],
        "가을": ["입추", "처서", "백로", "추분", "한로", "상강"],
        "겨울": ["입동", "소설", "대설", "동지", "소한", "대한"]
    }
    
    def __init__(self, date: datetime):
        """초기화
        
        Args:
            date: 날짜
        """
        self.date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
    def get_term(self) -> Optional[str]:
        """해당 날짜의 절기 이름 반환
        
        Returns:
            Optional[str]: 절기 이름 (절기가 아닌 경우 None)
        """
        year = self.date.year
        month = self.date.month
        day = self.date.day
        
        # 2024년 절기
        if year == 2024:
            if (month, day) in [
                (1, 6),   # 소한
                (1, 21),  # 대한
                (2, 4),   # 입춘
                (2, 19),  # 우수
                (3, 5),   # 경칩
                (3, 20),  # 춘분
                (4, 4),   # 청명
                (4, 20),  # 곡우
                (5, 5),   # 입하
                (5, 20),  # 소만
                (6, 5),   # 망종
                (6, 21),  # 하지
                (7, 7),   # 소서
                (7, 22),  # 대서
                (8, 7),   # 입추
                (8, 23),  # 처서
                (9, 7),   # 백로
                (9, 22),  # 추분
                (10, 7),  # 한로
                (10, 23), # 상강
                (11, 7),  # 입동
                (11, 21), # 소설
                (12, 7),  # 대설
                (12, 21)  # 동지
            ]:
                return list(self.TERMS.keys())[
                    (month - 1) * 2 + (0 if day < 15 else 1)
                ]
        return None
        
    def get_season(self) -> str:
        """해당 날짜의 계절 반환
        
        Returns:
            str: 계절 이름
        """
        term = self.get_term()
        if term:
            for season, terms in self.SEASONS.items():
                if term in terms:
                    return season
                    
        # 절기가 아닌 경우, 월을 기준으로 계절 판단
        month = self.date.month
        if 3 <= month <= 5:
            return "봄"
        elif 6 <= month <= 8:
            return "여름"
        elif 9 <= month <= 11:
            return "가을"
        else:
            return "겨울"
            
    def get_term_description(self) -> Optional[str]:
        """해당 날짜의 절기 설명 반환
        
        Returns:
            Optional[str]: 절기 설명 (절기가 아닌 경우 None)
        """
        term = self.get_term()
        return self.TERMS.get(term) if term else None
        
    def get_next_term(self) -> tuple:
        """다음 절기 정보 반환
        
        Returns:
            tuple: (절기 이름, 날짜)
        """
        year = self.date.year
        month = self.date.month
        day = self.date.day
        
        # 2024년 절기 날짜
        terms_2024 = [
            (1, 6, "소한"),
            (1, 21, "대한"),
            (2, 4, "입춘"),
            (2, 19, "우수"),
            (3, 5, "경칩"),
            (3, 20, "춘분"),
            (4, 4, "청명"),
            (4, 20, "곡우"),
            (5, 5, "입하"),
            (5, 20, "소만"),
            (6, 5, "망종"),
            (6, 21, "하지"),
            (7, 7, "소서"),
            (7, 22, "대서"),
            (8, 7, "입추"),
            (8, 23, "처서"),
            (9, 7, "백로"),
            (9, 22, "추분"),
            (10, 7, "한로"),
            (10, 23, "상강"),
            (11, 7, "입동"),
            (11, 21, "소설"),
            (12, 7, "대설"),
            (12, 21, "동지")
        ]
        
        # 현재 날짜 이후의 가장 가까운 절기 찾기
        for term_month, term_day, term_name in terms_2024:
            if (term_month > month) or (term_month == month and term_day > day):
                return (term_name, datetime(year, term_month, term_day))
                
        # 올해 남은 절기가 없으면 다음 해 첫 절기 반환
        return ("소한", datetime(year + 1, 1, 6))
        
    @classmethod
    def get_terms_in_month(cls, year: int, month: int) -> List[tuple]:
        """해당 월의 절기 목록 반환
        
        Args:
            year: 년도
            month: 월
            
        Returns:
            List[tuple]: [(절기 이름, 날짜)] 형식의 목록
        """
        # 2024년 절기 날짜
        terms_2024 = [
            (1, 6, "소한"),
            (1, 21, "대한"),
            (2, 4, "입춘"),
            (2, 19, "우수"),
            (3, 5, "경칩"),
            (3, 20, "춘분"),
            (4, 4, "청명"),
            (4, 20, "곡우"),
            (5, 5, "입하"),
            (5, 20, "소만"),
            (6, 5, "망종"),
            (6, 21, "하지"),
            (7, 7, "소서"),
            (7, 22, "대서"),
            (8, 7, "입추"),
            (8, 23, "처서"),
            (9, 7, "백로"),
            (9, 22, "추분"),
            (10, 7, "한로"),
            (10, 23, "상강"),
            (11, 7, "입동"),
            (11, 21, "소설"),
            (12, 7, "대설"),
            (12, 21, "동지")
        ]
        
        result = []
        for term_month, term_day, term_name in terms_2024:
            if term_month == month:
                result.append((term_name, datetime(year, term_month, term_day)))
        return result 