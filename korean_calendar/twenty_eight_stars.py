"""
28수(二十八宿) 관련 기능을 제공하는 모듈
"""
from typing import Dict, List, Tuple
from datetime import datetime

class TwentyEightStars:
    """28수(二十八宿) 클래스"""
    
    # 28수 목록 (동방청룡, 북방현무, 서방백호, 남방주작)
    STARS = [
        # 동방청룡 7수
        "각", "항", "저", "방", "심", "미", "기",
        # 북방현무 7수
        "두", "우", "여", "허", "위", "실", "벽",
        # 서방백호 7수
        "규", "루", "위", "묘", "필", "자", "삼",
        # 남방주작 7수
        "정", "귀", "류", "성", "장", "익", "진"
    ]
    
    # 28수의 오행 속성
    ELEMENTS = {
        # 동방청룡
        "각": "목", "항": "금", "저": "토", "방": "일", "심": "월", "미": "화", "기": "수",
        # 북방현무
        "두": "목", "우": "금", "여": "토", "허": "일", "위": "월", "실": "화", "벽": "수",
        # 서방백호
        "규": "목", "루": "금", "위": "토", "묘": "일", "필": "월", "자": "화", "삼": "수",
        # 남방주작
        "정": "목", "귀": "금", "류": "토", "성": "일", "장": "월", "익": "화", "진": "수"
    }
    
    # 28수의 음양 속성
    YIN_YANG = {
        # 동방청룡
        "각": "양", "항": "음", "저": "양", "방": "음", "심": "양", "미": "음", "기": "양",
        # 북방현무
        "두": "음", "우": "양", "여": "음", "허": "양", "위": "음", "실": "양", "벽": "음",
        # 서방백호
        "규": "양", "루": "음", "위": "양", "묘": "음", "필": "양", "자": "음", "삼": "양",
        # 남방주작
        "정": "음", "귀": "양", "류": "음", "성": "양", "장": "음", "익": "양", "진": "음"
    }
    
    # 28수의 길흉 속성
    FORTUNE = {
        # 동방청룡
        "각": "길", "항": "흉", "저": "길", "방": "흉", "심": "길", "미": "흉", "기": "길",
        # 북방현무
        "두": "흉", "우": "길", "여": "흉", "허": "길", "위": "흉", "실": "길", "벽": "흉",
        # 서방백호
        "규": "길", "루": "흉", "위": "길", "묘": "흉", "필": "길", "자": "흉", "삼": "길",
        # 남방주작
        "정": "흉", "귀": "길", "류": "흉", "성": "길", "장": "흉", "익": "길", "진": "흉"
    }
    
    # 28수의 방위
    DIRECTIONS = {
        # 동방청룡
        "각": "동", "항": "동", "저": "동", "방": "동", "심": "동", "미": "동", "기": "동",
        # 북방현무
        "두": "북", "우": "북", "여": "북", "허": "북", "위": "북", "실": "북", "벽": "북",
        # 서방백호
        "규": "서", "루": "서", "위": "서", "묘": "서", "필": "서", "자": "서", "삼": "서",
        # 남방주작
        "정": "남", "귀": "남", "류": "남", "성": "남", "장": "남", "익": "남", "진": "남"
    }
    
    def __init__(self, date: datetime):
        """초기화
        
        Args:
            date: 날짜
        """
        self.date = date
        
    def get_star(self) -> str:
        """해당 날짜의 28수 반환
        
        Returns:
            str: 28수
        """
        # 1984년 1월 1일은 각(角)수
        base_date = datetime(1984, 1, 1)
        days = (self.date - base_date).days
        
        # 28수 순환
        index = days % 28
        return self.STARS[index]
        
    def get_element(self) -> str:
        """해당 날짜의 28수 오행 반환
        
        Returns:
            str: 오행
        """
        star = self.get_star()
        return self.ELEMENTS[star]
        
    def get_yin_yang(self) -> str:
        """해당 날짜의 28수 음양 반환
        
        Returns:
            str: 음양
        """
        star = self.get_star()
        return self.YIN_YANG[star]
        
    def get_fortune(self) -> str:
        """해당 날짜의 28수 길흉 반환
        
        Returns:
            str: 길흉
        """
        star = self.get_star()
        return self.FORTUNE[star]
        
    def get_direction(self) -> str:
        """해당 날짜의 28수 방위 반환
        
        Returns:
            str: 방위
        """
        star = self.get_star()
        return self.DIRECTIONS[star]
        
    def get_constellation(self) -> str:
        """해당 날짜의 28수 사신 반환
        
        Returns:
            str: 사신 (청룡, 현무, 백호, 주작)
        """
        star = self.get_star()
        if star in ["각", "항", "저", "방", "심", "미", "기"]:
            return "청룡"
        elif star in ["두", "우", "여", "허", "위", "실", "벽"]:
            return "현무"
        elif star in ["규", "루", "위", "묘", "필", "자", "삼"]:
            return "백호"
        else:
            return "주작"
            
    def __str__(self) -> str:
        """문자열 표현
        
        Returns:
            str: 28수 정보
        """
        star = self.get_star()
        constellation = self.get_constellation()
        element = self.get_element()
        yin_yang = self.get_yin_yang()
        fortune = self.get_fortune()
        direction = self.get_direction()
        
        return f"{constellation} {star}수 ({direction}방, {element}행, {yin_yang}양, {fortune}일)" 