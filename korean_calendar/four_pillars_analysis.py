"""
사주팔자(四柱八字) 분석 관련 기능을 제공하는 모듈
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
try:
    from .four_pillars import FourPillars
    from .five_elements import FiveElements, TenGods
except ImportError:
    from four_pillars import FourPillars
    from five_elements import FiveElements, TenGods
import math
import difflib

# 지역별 시간 보정(초 단위) 딕셔너리
REGION_TIME_OFFSET = {
    "백령도": 40*60+26, "홍도": 39*60+10, "흑산도": 38*60+14, "연평도": 36*60+34, "덕적도": 36*60+14,
    "신안군": 36*60+14, "목포": 35*60+14, "서산": 34*60+10, "제주": 33*60+52, "보령": 33*60+48, "서귀포": 33*60+44,
    "인천": 33*60+32, "원도": 33*60+32, "군산": 33*60+28, "장흥": 32*60+52, "광주": 32*60+17, "서울": 32*60+5,
    "수원": 31*60+53, "평택": 31*60+33, "전주": 31*60+24, "천안": 31*60+24, "남원": 30*60+28, "대전": 30*60+19,
    "청주": 30*60+3, "춘천": 29*60+4, "여수": 29*60+0, "홍주": 28*60+20, "원주": 28*60+12, "사천": 27*60+56,
    "상주": 26*60+56, "통영": 25*60+46, "마산": 25*60+40, "속초": 25*60+36, "대구": 25*60+36, "안동": 25*60+44,
    "강릉": 24*60+23, "태백": 23*60+56, "부산": 25*60+23, "동해": 25*60+28, "경주": 23*60+28, "울산": 22*60+36,
    "포항": 22*60+24, "울진": 22*60+24, "울릉도": 16*60+25, "독도": 12*60+21
}

def get_local_true_time(dt: datetime, region: str) -> datetime:
    """입력 datetime과 지역명을 받아, 실제 태양시로 보정된 datetime 반환
    지원하지 않는 지역명일 경우 가장 가까운 등록 지역으로 자동 대체"""
    offset = REGION_TIME_OFFSET.get(region)
    if offset is None:
        candidates = list(REGION_TIME_OFFSET.keys())
        similar = [r for r in candidates if region in r or r in region]
        if similar:
            region = similar[0]
        else:
            # 이름 유사도 기준, 없으면 fallback
            matches = difflib.get_close_matches(region, candidates, n=1)
            if matches:
                region = matches[0]
            else:
                region = '사천'  # fallback 지역
        offset = REGION_TIME_OFFSET[region]
    return dt - timedelta(seconds=offset)

class FourPillarsAnalysis:
    """사주팔자 분석 클래스"""
    
    # 대운 계산 기준
    BASE_YEAR = 1984  # 갑자년 기준
    
    # 대운 시작 연령 (성별, 연간 음양에 따른)
    LUCK_START_AGE = {
        "M": {  # 남자
            "양": 5,  # 양년생
            "음": 6   # 음년생
        },
        "F": {  # 여자
            "양": 4,  # 양년생
            "음": 4   # 음년생
        }
    }
    
    # 대운 방향
    LUCK_DIRECTION = {
        "갑": 1, "을": 1, "병": -1, "정": -1,
        "무": 1, "기": 1, "경": -1, "신": -1,
        "임": 1, "계": 1
    }
    
    # 십이운성 표 (천간: {지지: 운성})
    TWELVE_STAGE = {
        "甲": {"寅": "建祿", "卯": "帝旺", "辰": "衰", "巳": "病", "午": "死", "未": "墓", "申": "絶", "酉": "胎", "戌": "養", "亥": "長生", "子": "沐浴", "丑": "冠帶"},
        "乙": {"卯": "建祿", "寅": "帝旺", "丑": "衰", "子": "病", "亥": "死", "戌": "墓", "酉": "絶", "申": "胎", "未": "養", "午": "長生", "巳": "沐浴", "辰": "冠帶"},
        "丙": {"巳": "建祿", "午": "帝旺", "未": "衰", "申": "病", "酉": "死", "戌": "墓", "亥": "絶", "子": "胎", "丑": "養", "寅": "長生", "卯": "沐浴", "辰": "冠帶"},
        "丁": {"午": "建祿", "巳": "帝旺", "辰": "衰", "卯": "병", "寅": "死", "丑": "墓", "子": "絶", "亥": "胎", "戌": "養", "酉": "長生", "申": "沐浴", "未": "冠帶"},
        "戊": {"巳": "建祿", "午": "帝旺", "未": "衰", "申": "병", "酉": "死", "戌": "墓", "亥": "絶", "子": "胎", "丑": "養", "寅": "長生", "卯": "沐浴", "辰": "冠帶"},
        "己": {"午": "建祿", "巳": "帝旺", "辰": "衰", "卯": "병", "寅": "死", "丑": "墓", "子": "絶", "亥": "胎", "戌": "養", "酉": "長生", "申": "沐浴", "未": "冠帶"},
        "庚": {"申": "建祿", "酉": "帝旺", "戌": "衰", "亥": "병", "子": "死", "丑": "墓", "寅": "絶", "卯": "胎", "辰": "養", "巳": "長生", "午": "沐浴", "未": "冠帶"},
        "辛": {"酉": "建祿", "申": "帝旺", "未": "衰", "午": "병", "巳": "死", "辰": "墓", "卯": "絶", "寅": "胎", "丑": "養", "子": "長生", "亥": "沐浴", "戌": "冠帶"},
        "壬": {"亥": "建祿", "子": "帝旺", "丑": "衰", "寅": "병", "卯": "死", "辰": "墓", "巳": "絶", "午": "胎", "未": "養", "申": "長生", "酉": "沐浴", "戌": "冠帶"},
        "癸": {"子": "建祿", "亥": "帝旺", "戌": "衰", "酉": "병", "申": "死", "未": "墓", "午": "絶", "巳": "胎", "辰": "養", "卯": "長生", "寅": "沐浴", "丑": "冠帶"}
    }
    
    # 각종살 표 (년지: {일지: 살})
    VARIOUS_SAL_TABLE = {
        "子": {"寅": "검살", "午": "재살", "戌": "천살", "申": "지살", "子": "년살", "辰": "월살", "申": "망신", "午": "장성", "戌": "반안", "辰": "역마", "午": "육해", "未": "화개"},
        "丑": {"卯": "검살", "未": "재살", "丑": "천살", "巳": "지살", "酉": "년살", "丑": "월살", "巳": "망신", "未": "장성", "丑": "반안", "巳": "역마", "未": "육해", "辰": "화개"},
        "寅": {"辰": "검살", "申": "재살", "寅": "천살", "午": "지살", "戌": "년살", "寅": "월살", "午": "망신", "申": "장성", "寅": "반안", "午": "역마", "申": "육해", "丑": "화개"},
        "卯": {"巳": "검살", "酉": "재살", "卯": "천살", "未": "지살", "丑": "년살", "卯": "월살", "未": "망신", "酉": "장성", "卯": "반안", "未": "역마", "酉": "육해", "寅": "화개"},
        "辰": {"午": "검살", "戌": "재살", "辰": "천살", "申": "지살", "子": "년살", "辰": "월살", "申": "망신", "戌": "장성", "辰": "반안", "申": "역마", "戌": "육해", "亥": "화개"},
        "巳": {"未": "검살", "丑": "재살", "巳": "천살", "酉": "지살", "卯": "년살", "巳": "월살", "酉": "망신", "丑": "장성", "巳": "반안", "酉": "역마", "丑": "육해", "子": "화개"},
        "午": {"申": "검살", "寅": "재살", "午": "천살", "戌": "지살", "辰": "년살", "午": "월살", "戌": "망신", "寅": "장성", "午": "반안", "戌": "역마", "寅": "육해", "亥": "화개"},
        "未": {"酉": "검살", "卯": "재살", "未": "천살", "丑": "지살", "巳": "년살", "未": "월살", "丑": "망신", "卯": "장성", "未": "반안", "丑": "역마", "卯": "육해", "午": "화개"},
        "申": {"戌": "검살", "辰": "재살", "申": "천살", "午": "지살", "子": "년살", "申": "월살", "午": "망신", "辰": "장성", "申": "반안", "午": "역마", "辰": "육해", "巳": "화개"},
        "酉": {"亥": "검살", "巳": "재살", "酉": "천살", "丑": "지살", "未": "년살", "酉": "월살", "丑": "망신", "巳": "장성", "酉": "반안", "丑": "역마", "巳": "육해", "午": "화개"},
        "戌": {"子": "검살", "午": "재살", "戌": "천살", "寅": "지살", "申": "년살", "戌": "월살", "寅": "망신", "午": "장성", "戌": "반안", "寅": "역마", "午": "육해", "卯": "화개"},
        "亥": {"丑": "검살", "未": "재살", "亥": "천살", "卯": "지살", "巳": "년살", "亥": "월살", "卯": "망신", "未": "장성", "亥": "반안", "卯": "역마", "未": "육해", "申": "화개"}
    }
    
    # 귀인살 표 (천간: [지지])
    GUIIN_TABLE = {
        "천을귀인": {
            "甲": ["未", "丑"], "乙": ["子", "申"], "丙": ["酉", "亥"], "丁": ["酉", "亥"],
            "戊": ["丑", "未"], "己": ["子", "申"], "庚": ["丑", "未"], "辛": ["子", "申"],
            "壬": ["卯", "巳"], "癸": ["卯", "巳"]
        },
        "문창귀인": {
            "甲": ["巳"], "乙": ["午"], "丙": ["申"], "丁": ["酉"], "戊": ["申"], "己": ["酉"],
            "庚": ["亥"], "辛": ["子"], "壬": ["寅"], "癸": ["卯"]
        },
        "건록": {
            "甲": ["寅"], "乙": ["卯"], "丙": ["巳"], "丁": ["午"], "戊": ["巳"], "己": ["午"],
            "庚": ["申"], "辛": ["酉"], "壬": ["亥"], "癸": ["子"]
        },
        "양인살": {
            "甲": ["卯"], "乙": ["辰"], "丙": ["午"], "丁": ["未"], "戊": ["午"], "己": ["未"],
            "庚": ["酉"], "辛": ["戌"], "壬": ["子"], "癸": ["丑"]
        },
        "홍염살": {
            "甲": ["午"], "乙": ["午"], "丙": ["寅"], "丁": ["未"], "戊": ["辰"], "己": ["未"],
            "庚": ["戌"], "辛": ["酉"], "壬": ["子"], "癸": ["申"]
        }
    }
    
    # 삼합 표 (삼합조합: 오행)
    SAMHAP_TABLE = {
        ("인", "오", "술"): "화",
        ("사", "유", "축"): "금",
        ("신", "자", "진"): "수",
        ("해", "묘", "미"): "목"
    }
    # 천간삼기 표 (삼기조합: 종류)
    SAMGI_TABLE = {
        ("갑", "경", "무"): "천상삼기",
        ("을", "병", "정"): "지하삼기",
        ("신", "임", "계"): "인중삼기"
    }
    
    # 귀삼합 표 (지지조합: 오행)
    GWISAMHAP_TABLE = {
        ("인", "오", "술"): "화",
        ("사", "유", "축"): "금",
        ("신", "자", "진"): "수",
        ("해", "묘", "미"): "목"
    }
    
    # 천간 목록
    HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    
    def __init__(self, date: datetime, gender: str, region: str = "서울", use_true_solar_time: bool = True):
        """초기화
        
        Args:
            date: 생년월일시 (datetime 객체)
            gender: 성별 ("M" 또는 "F")
            region: 지역명 (선택 사항)
            
        Raises:
            ValueError: date나 gender가 유효하지 않은 경우
        """
        if not isinstance(date, datetime):
            raise ValueError("생년월일시는 datetime 객체여야 합니다.")
            
        if gender not in ["M", "F"]:
            raise ValueError("성별은 'M'(남) 또는 'F'(여)여야 합니다.")
            
        self.input_date = date
        self.gender = gender
        self.region = region
        self.pillars = FourPillars(date, region=region, use_true_solar_time=use_true_solar_time)
        self.date = self.pillars.date
        
    def get_day_master_analysis(self) -> Dict[str, str]:
        """일주 분석
        
        Returns:
            Dict[str, str]: 일주 분석 결과
        """
        day_stem = self.pillars.get_day_pillar().stem
        day_branch = self.pillars.get_day_pillar().branch
        five_elements = FiveElements()
        
        return {
            "일간": day_stem,
            "일지": day_branch,
            "오행": five_elements.get_element(day_stem),
            "음양": "양" if self.HEAVENLY_STEMS.index(day_stem) % 2 == 0 else "음",
            "특성": "의지가 강하고 리더십이 있다"
        }
        
    def get_pillars_relationship(self) -> Dict[str, List[str]]:
        """사주팔자 관계 분석
        
        Returns:
            Dict[str, List[str]]: 관계 분석 결과
        """
        relationships = {
            "비겁": [],  # 같은 오행
            "식상": [],  # 일간이 생하는 오행
            "생조": [],  # 일간을 생하는 오행
            "재성": [],  # 일간이 극하는 오행
            "관살": []   # 일간을 극하는 오행
        }
        
        day_stem = self.pillars.get_day_pillar().stem
        day_element = FiveElements().get_element(day_stem)
        
        # 천간 관계 분석
        for pillar_name, pillar in [
            ("년주 천간", self.pillars.get_year_pillar()),
            ("월주 천간", self.pillars.get_month_pillar()),
            ("일주 천간", self.pillars.get_day_pillar()),
            ("시주 천간", self.pillars.get_hour_pillar())
        ]:
            stem_element = FiveElements().get_element(pillar.stem)
            if stem_element == day_element:
                relationships["비겁"].append(pillar_name)
            elif FiveElements().generates(day_element, stem_element):
                relationships["식상"].append(pillar_name)
            elif FiveElements().generates(stem_element, day_element):
                relationships["생조"].append(pillar_name)
            elif FiveElements().controls(day_element, stem_element):
                relationships["재성"].append(pillar_name)
            elif FiveElements().controls(stem_element, day_element):
                relationships["관살"].append(pillar_name)
                
        # 지지 관계 분석
        for pillar_name, pillar in [
            ("년주 지지", self.pillars.get_year_pillar()),
            ("월주 지지", self.pillars.get_month_pillar()),
            ("일주 지지", self.pillars.get_day_pillar()),
            ("시주 지지", self.pillars.get_hour_pillar())
        ]:
            branch_element = FiveElements().get_element(pillar.branch)
            if branch_element == day_element:
                relationships["비겁"].append(pillar_name)
            elif FiveElements().generates(day_element, branch_element):
                relationships["식상"].append(pillar_name)
            elif FiveElements().generates(branch_element, day_element):
                relationships["생조"].append(pillar_name)
            elif FiveElements().controls(day_element, branch_element):
                relationships["재성"].append(pillar_name)
            elif FiveElements().controls(branch_element, day_element):
                relationships["관살"].append(pillar_name)
                
        return relationships
        
    def get_luck_cycle(self):
        """대운(10년 주기) 계산
        
        Returns:
            List[Dict]: 대운 정보 리스트
        """
        # 연간의 음양 판단
        year_stem = self.pillars.get_year_pillar().stem
        is_yang_year = year_stem in ["갑", "병", "무", "경", "임"]  # 양간: 갑(甲), 병(丙), 무(戊), 경(庚), 임(壬)

        # 성별과 연간에 따른 대운 방향 결정
        is_forward = (is_yang_year and self.gender == "M") or (not is_yang_year and self.gender == "F")

        # 절입 시각 기반 대운수 계산
        birth = self.date
        year_terms = self._get_year_terms(birth.year)
        # 12절기명 리스트
        major_term_names = [
            "입춘", "경칩", "청명", "입하", "망종", "소서",
            "입추", "백로", "한로", "입동", "대설", "소한"
        ]
        all_term_names = [
            "입춘", "우수", "경칩", "춘분", "청명", "곡우",
            "입하", "소만", "망종", "하지", "소서", "대서",
            "입추", "처서", "백로", "추분", "한로", "상강",
            "입동", "소설", "대설", "동지", "소한", "대한"
        ]
        major_terms = []
        for i, t in enumerate(year_terms):
            if all_term_names[i % 24] in major_term_names:
                major_terms.append(datetime.fromisoformat(t))
        major_terms.sort()
        
        # 출생월 절입, 다음달 절입 찾기
        this_month_term = None
        next_month_term = None
        prev_month_term = None
        
        # 출생일과 같은 절기 찾기
        for i, term in enumerate(major_terms):
            if term.date() == birth.date():
                this_month_term = term
                if is_forward:
                    if i+1 < len(major_terms):
                        next_month_term = major_terms[i+1]
                else:
                    if i-1 >= 0:
                        prev_month_term = major_terms[i-1]
                break
            elif term < birth:
                prev_month_term = term
            elif term > birth and not next_month_term:
                next_month_term = term
        
        # 대운수 계산
        if this_month_term and this_month_term.date() == birth.date():
            # 출생일이 절기와 같은 경우
            start_age = 1
        else:
            # 출생일이 절기와 다른 경우
            if is_forward:
                if next_month_term:
                    delta_days = (next_month_term - birth).total_seconds() / 86400
                else:
                    delta_days = 0
            else:
                if prev_month_term:
                    delta_days = (birth - prev_month_term).total_seconds() / 86400
                else:
                    delta_days = 0
            days = delta_days
            start_age = self._calculate_luck_start_age(days)
        
        # 대운 시작 연령 계산 (10년 단위로 증가)
        change_ages = [start_age + i*10 for i in range(10)]  # 10대운

        # 대운 정보 생성
        stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
        branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

        # 월주 기준으로 대운 시작 (월주 다음 간지부터 시작)
        if is_forward:
            stem_idx = (stems.index(self.pillars.get_month_pillar().stem) + 1) % 10
            branch_idx = (branches.index(self.pillars.get_month_pillar().branch) + 1) % 12
        else:
            stem_idx = (stems.index(self.pillars.get_month_pillar().stem) - 1) % 10
            branch_idx = (branches.index(self.pillars.get_month_pillar().branch) - 1) % 12

        result = []
        for i, age in enumerate(change_ages):
            # 대운 방향에 따라 인덱스 계산
            if is_forward:
                s = stems[(stem_idx + i) % 10]
                b = branches[(branch_idx + i) % 12]
            else:
                s = stems[(stem_idx - i) % 10]
                b = branches[(branch_idx - i) % 12]

            result.append({
                "시작연령": f"{age}세",
                "천간": s,
                "지지": b,
                "방향": "순행" if is_forward else "역행",
                "특성": self._get_luck_characteristics(f"{s}{b}")
            })

        return result

    def _get_day_master_characteristics(self, stem: str) -> str:
        """일간 특성 반환
        
        Args:
            stem: 일간
            
        Returns:
            str: 일간 특성
        """
        characteristics = {
            "갑": "의지가 강하고 리더십이 있다",
            "을": "부드럽고 융통성이 있다",
            "병": "밝고 활발하며 열정적이다",
            "정": "정의감이 강하고 원칙적이다",
            "무": "신중하고 책임감이 있다",
            "기": "부드럽고 포용력이 있다",
            "경": "강직하고 원칙적이다",
            "신": "예리하고 분석력이 있다",
            "임": "지혜롭고 유연하다",
            "계": "침착하고 신중하다"
        }
        return characteristics.get(stem, "알 수 없음")
        
    def _calculate_luck_pillar(self, year: int, offset: int) -> str:
        """대운 간지 계산
        
        Args:
            year: 기준 연도
            offset: 오프셋
            
        Returns:
            str: 대운 간지
        """
        # 갑자년 기준으로 계산
        base_year = self.BASE_YEAR
        year_diff = year - base_year + offset
        
        # 천간 계산
        stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
        stem_index = (year_diff % 10)
        stem = stems[stem_index]
        
        # 지지 계산
        branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
        branch_index = (year_diff % 12)
        branch = branches[branch_index]
        
        return f"{stem}{branch}"
        
    def _get_luck_characteristics(self, luck_pillar: str) -> str:
        """대운 특성 반환
        
        Args:
            luck_pillar: 대운 간지
            
        Returns:
            str: 대운 특성
        """
        characteristics = {
            "갑자": "새로운 시작과 변화의 시기",
            "을축": "안정과 발전의 시기",
            "병인": "활발한 활동과 성장의 시기",
            "정묘": "정신적 성장과 깨달음의 시기",
            "무진": "실질적인 성과와 안정의 시기",
            "기사": "조화와 균형의 시기",
            "경오": "도전과 성취의 시기",
            "신미": "성찰과 내면 성장의 시기",
            "임신": "지혜와 통찰의 시기",
            "계유": "완성과 성숙의 시기",
            "갑술": "변화와 새로운 도전의 시기",
            "을해": "휴식과 재정비의 시기",
            "병자": "새로운 시작과 도약의 시기",
            "정축": "안정과 성장의 시기",
            "무인": "실천과 성과의 시기",
            "기묘": "창의와 발전의 시기",
            "경진": "도전과 극복의 시기",
            "신사": "변화와 적응의 시기",
            "임오": "성취와 완성의 시기",
            "계미": "안정과 성숙의 시기",
            "갑신": "새로운 기회의 시기",
            "을유": "조화와 균형의 시기",
            "병술": "실천과 발전의 시기",
            "정해": "성찰과 정리의 시기",
            "무자": "새로운 시작과 도전의 시기",
            "기축": "안정과 발전의 시기",
            "경인": "도전과 성장의 시기",
            "신묘": "창의와 혁신의 시기",
            "임진": "실천과 성과의 시기",
            "계사": "변화와 적응의 시기",
            "갑오": "성취와 완성의 시기",
            "을미": "안정과 성숙의 시기",
            "병신": "새로운 기회의 시기",
            "정유": "조화와 균형의 시기",
            "무술": "실천과 발전의 시기",
            "기해": "성찰과 정리의 시기"
        }
        return characteristics.get(luck_pillar, "알 수 없음")
        
    def get_pattern(self) -> Dict[str, str]:
        """격(格) 찾기
        
        Returns:
            Dict[str, str]: 격 분석 결과
        """
        day_stem = self.pillars.get_day_pillar().stem
        day_element = FiveElements().get_element(day_stem)
        month_branch = self.pillars.get_month_pillar().branch
        month_element = FiveElements().get_element(month_branch)
        
        # 식신격 (일간이 월지를 생함)
        if FiveElements().generates(day_element, month_element):
            return {
                "격": "식신격",
                "특성": "재능과 창의성이 뛰어나고 표현력이 좋음",
                "장점": "예술성, 창의력, 표현력",
                "단점": "감정기복, 변덕, 실용성 부족"
            }
            
        # 비겁격 (일간과 월지가 같은 오행)
        if day_element == month_element:
            return {
                "격": "비겁격",
                "특성": "자신감이 강하고 독립적인 성향",
                "장점": "리더십, 결단력, 추진력",
                "단점": "고집, 독단, 융통성 부족"
            }
            
        # 생조격 (월지가 일간을 생함)
        if FiveElements().generates(month_element, day_element):
            return {
                "격": "생조격",
                "특성": "주변의 도움을 잘 받고 성장이 빠름",
                "장점": "성장성, 적응력, 발전력",
                "단점": "의존성, 수동성, 주체성 부족"
            }
            
        # 재성격 (일간이 월지를 극함)
        if FiveElements().controls(day_element, month_element):
            return {
                "격": "재성격",
                "특성": "재물운이 좋고 실행력이 강함",
                "장점": "재능, 부귀, 성공운",
                "단점": "사치, 낭비, 허영심"
            }
            
        # 관살격 (월지가 일간을 극함)
        if FiveElements().controls(month_element, day_element):
            return {
                "격": "관살격",
                "특성": "권위적이고 지도력이 있음",
                "장점": "권위, 지위, 명예",
                "단점": "고독, 외로움, 인간관계"
            }
            
        return {
            "격": "평평격",
            "특성": "평범하고 안정적인 성향",
            "장점": "안정, 평화, 무난함",
            "단점": "특출나지 않음, 평범함"
        }
            
    def get_missing_elements(self) -> Dict[str, List[str]]:
        """무자(無字) 찾기
        
        Returns:
            Dict[str, List[str]]: 무자 분석 결과
        """
        # 각 오행의 개수 계산
        elements_count = {
            "목": 0,
            "화": 0,
            "토": 0,
            "금": 0,
            "수": 0
        }
        
        # 각 주의 오행 분석
        for pillar in [
            self.pillars.get_year_pillar().stem,
            self.pillars.get_year_pillar().branch,
            self.pillars.get_month_pillar().stem,
            self.pillars.get_month_pillar().branch,
            self.pillars.get_day_pillar().stem,
            self.pillars.get_day_pillar().branch,
            self.pillars.get_hour_pillar().stem,
            self.pillars.get_hour_pillar().branch
        ]:
            element = FiveElements().get_element(pillar)
            elements_count[element] += 1
            
        # 없는 오행 찾기
        missing = []
        for element, count in elements_count.items():
            if count == 0:
                missing.append(element)
                
        # 영향 분석
        effects = []
        if "목" in missing:
            effects.append("창의성과 성장이 부족할 수 있음")
        if "화" in missing:
            effects.append("열정과 추진력이 부족할 수 있음")
        if "토" in missing:
            effects.append("안정성과 중심이 부족할 수 있음")
        if "금" in missing:
            effects.append("의지와 결단력이 부족할 수 있음")
        if "수" in missing:
            effects.append("지혜와 통찰력이 부족할 수 있음")
                
        return {
            "무자": missing,
            "영향": effects if effects else ["무자가 없어 균형잡힌 사주입니다"]
        }
        
    def get_climate_balance(self) -> Dict[str, Dict[str, int]]:
        """조후(調候) 분석
        
        Returns:
            Dict[str, Dict[str, int]]: 조후 분석 결과
        """
        # 각 조후의 점수 계산
        scores = {
            "한": 0,  # 차가움
            "난": 0,  # 따뜻함
            "조": 0,  # 건조함
            "습": 0   # 습함
        }
        
        five_elements = FiveElements()
        
        # 각 주의 조후 분석
        for pillar in [
            self.pillars.get_year_pillar().stem,
            self.pillars.get_year_pillar().branch,
            self.pillars.get_month_pillar().stem,
            self.pillars.get_month_pillar().branch,
            self.pillars.get_day_pillar().stem,
            self.pillars.get_day_pillar().branch,
            self.pillars.get_hour_pillar().stem,
            self.pillars.get_hour_pillar().branch
        ]:
            element = five_elements.get_element(pillar)
            
            # 오행별 조후 점수
            if element == "목":
                scores["난"] += 1
                scores["습"] += 1
            elif element == "화":
                scores["난"] += 2
                scores["조"] += 1
            elif element == "토":
                scores["조"] += 2
            elif element == "금":
                scores["한"] += 1
                scores["조"] += 1
            elif element == "수":
                scores["한"] += 2
                scores["습"] += 1
                
        # 가장 높은 점수의 조후 찾기
        max_score = max(scores.values())
        climate = [k for k, v in scores.items() if v == max_score][0]
        
        # 조후별 영향
        effects = {
            "한": "한기가 많아 차가운 기운이 강합니다",
            "난": "열기가 많아 따뜻한 기운이 강합니다",
            "조": "건조함이 많아 마른 기운이 강합니다",
            "습": "습기가 많아 축축한 기운이 강합니다"
        }
        
        return {
            "조후": climate,
            "영향": effects[climate],
            "점수": scores
        }
        
    def get_year_fortune(self, count: int = 10):
        """연운(10년치) 반환: 대운 첫 간지에서 1년 단위로 10개"""
        luck_cycle = self.get_luck_cycle()
        first_stem = luck_cycle[0]["천간"]
        first_branch = luck_cycle[0]["지지"]
        stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
        branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
        stem_idx = stems.index(first_stem)
        branch_idx = branches.index(first_branch)
        result = []
        for i in range(count):
            s = stems[(stem_idx + i) % 10]
            b = branches[(branch_idx + i) % 12]
            result.append(f"{s}{b}")
        return result

    def get_month_fortune(self, count: int = 12):
        """월운(12개월치) 반환: 대운 첫 간지에서 1개월 단위로 12개"""
        luck_cycle = self.get_luck_cycle()
        first_stem = luck_cycle[0]["천간"]
        first_branch = luck_cycle[0]["지지"]
        stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
        branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
        stem_idx = stems.index(first_stem)
        branch_idx = branches.index(first_branch)
        result = []
        for i in range(count):
            s = stems[(stem_idx + i) % 10]
            b = branches[(branch_idx + i) % 12]
            result.append(f"{s}{b}")
        return result

    def get_shinsal(self):
        """신살 간단 표 반환 (천을귀인, 화개살, 현침살, 양인살 등)"""
        # 예시: 각 기둥별로 대표 신살만 표기
        shinsal_table = {
            "천을귀인": ["축", "미"],
            "화개살": ["미", "해", "묘", "축"],
            "현침살": ["진", "술"],
            "양인살": ["인", "묘", "오", "유"],
            "금여성": ["신", "유"],
            "관귀학관": ["자", "오"],
            "역마살": ["신", "자", "진", "오"],
            "고신살": ["술", "미"],
            "괴강살": ["진", "술"],
            "천문성": ["인", "신"]
        }
        result = {}
        for name, branches in shinsal_table.items():
            result[name] = []
            for pillar in [self.pillars.get_year_pillar().branch, self.pillars.get_month_pillar().branch, self.pillars.get_day_pillar().branch, self.pillars.get_hour_pillar().branch]:
                if pillar in branches:
                    result[name].append(pillar)
        return result

    def get_use_god(self) -> Dict[str, str]:
        """용신(用神) 분석 (오행 과다/부족, 신강/신약, 일간 특성 종합)"""
        elements = self.get_five_elements_ratio()
        # 과다: 40% 이상, 부족: 10% 이하
        over = [k for k, v in elements.items() if v >= 40]
        lack = [k for k, v in elements.items() if v <= 10]
        # 신강/신약
        shin = self.get_shin_strength_index()
        # 기본 용신: 부족한 오행, 없으면 일간이 극하는 오행
        if lack:
            use = lack[0]
            reason = f"{lack[0]}이 부족하여 {lack[0]}을(를) 용신으로 삼음"
        else:
            day_element = FiveElements(self.pillars.get_day_pillar().stem).element
            use = FiveElements.CONQUERING[day_element]
            reason = f"일간({day_element})이 극하는 {use}을(를) 용신으로 삼음"
        # 종용신(과다한 오행이 있으면 그 오행을 억제하는 오행)
        if over:
            over_elem = over[0]
            counter = FiveElements.CONQUERING[over_elem]
            return {"용신": counter, "종용신": over_elem, "이유": f"{over_elem}이 과다하여 {counter}로 억제"}
        return {"용신": use, "이유": reason}

    def get_avoid_god(self) -> Dict[str, str]:
        """기신(忌神) 분석 (오행 과다/부족, 신강/신약, 일간 특성 종합)"""
        elements = self.get_five_elements_ratio()
        # 과다: 40% 이상, 부족: 10% 이하
        over = [k for k, v in elements.items() if v >= 40]
        lack = [k for k, v in elements.items() if v <= 10]
        # 신강/신약
        shin = self.get_shin_strength_index()
        # 기본 기신: 과다한 오행, 없으면 일간이 생하는 오행
        if over:
            avoid = over[0]
            reason = f"{over[0]}이 과다하여 {over[0]}을(를) 기신으로 삼음"
        else:
            day_element = FiveElements(self.pillars.get_day_pillar().stem).element
            avoid = FiveElements.GENERATING[day_element]
            reason = f"일간({day_element})이 생하는 {avoid}을(를) 기신으로 삼음"
        return {"기신": avoid, "이유": reason}
        
    def get_empty_death(self) -> Dict[str, str]:
        """공망(空亡) 분석
        
        Returns:
            Dict[str, str]: 공망 분석 결과
        """
        # 공망 지지 계산
        day_stem = self.pillars.get_day_pillar().stem
        stem_index = self.pillars.HEAVENLY_STEMS.index(day_stem)
        empty_branches = []
        
        # 천간의 십이운성에 따른 공망 지지
        if stem_index < 5:  # 갑을병정무
            empty_branches = ["신", "유"]
        else:  # 기경신임계
            empty_branches = ["진", "사"]
            
        # 공망이 있는 지지 찾기
        empty = []
        for pillar_name, pillar in [
            ("년지", self.pillars.get_year_pillar().branch),
            ("월지", self.pillars.get_month_pillar().branch),
            ("일지", self.pillars.get_day_pillar().branch),
            ("시지", self.pillars.get_hour_pillar().branch)
        ]:
            if pillar in empty_branches:
                empty.append(pillar_name)
                
        return {
            "공망": empty,
            "영향": "공망이 있는 지지는 그 기운이 약해지고, 해당 분야에서 어려움이 있을 수 있음"
        }
        
    def get_grave(self) -> Dict[str, str]:
        """입묘(入墓) 분석
        
        Returns:
            Dict[str, str]: 입묘 분석 결과
        """
        # 입묘 지지 계산
        grave_branches = {
            "목": "미",  # 목묘미
            "화": "술",  # 화묘술
            "토": "축",  # 토묘축
            "금": "묘",  # 금묘묘
            "수": "해"   # 수묘해
        }
        
        five_elements = FiveElements()
        
        # 입묘가 있는 간지 찾기
        grave = []
        for pillar_name, pillar in [
            ("년간", self.pillars.get_year_pillar().stem),
            ("년지", self.pillars.get_year_pillar().branch),
            ("월간", self.pillars.get_month_pillar().stem),
            ("월지", self.pillars.get_month_pillar().branch),
            ("일간", self.pillars.get_day_pillar().stem),
            ("일지", self.pillars.get_day_pillar().branch),
            ("시간", self.pillars.get_hour_pillar().stem),
            ("시지", self.pillars.get_hour_pillar().branch)
        ]:
            element = five_elements.get_element(pillar)
            if pillar == grave_branches[element]:
                grave.append(pillar_name)
                
        return {
            "입묘": grave,
            "영향": "입묘가 있는 간지는 그 기운이 묻혀져 있어 발휘되지 못하고, 해당 분야에서 어려움이 있을 수 있음"
        }
        
    def get_death_ground(self) -> Dict[str, str]:
        """절지(絶地) 분석
        
        Returns:
            Dict[str, str]: 절지 분석 결과
        """
        # 절지 지지 계산
        death_branches = {
            "목": "신",  # 목절신
            "화": "해",  # 화절해
            "토": "오",  # 토절오
            "금": "자",  # 금절자
            "수": "묘"   # 수절묘
        }
        
        five_elements = FiveElements()
        
        # 절지가 있는 간지 찾기
        death = []
        for pillar_name, pillar in [
            ("년간", self.pillars.get_year_pillar().stem),
            ("년지", self.pillars.get_year_pillar().branch),
            ("월간", self.pillars.get_month_pillar().stem),
            ("월지", self.pillars.get_month_pillar().branch),
            ("일간", self.pillars.get_day_pillar().stem),
            ("일지", self.pillars.get_day_pillar().branch),
            ("시간", self.pillars.get_hour_pillar().stem),
            ("시지", self.pillars.get_hour_pillar().branch)
        ]:
            element = five_elements.get_element(pillar)
            if pillar == death_branches[element]:
                death.append(pillar_name)
                
        return {
            "절지": death,
            "영향": "절지가 있는 간지는 그 기운이 끊어져 있어 힘을 발휘하지 못하고, 해당 분야에서 어려움이 있을 수 있음"
        }
        
    def get_five_elements_ratio(self):
        """오행별 비율(%) 반환 (지지의 지장간까지 포함)"""
        elements_count = {"목":0, "화":0, "토":0, "금":0, "수":0}
        five_elements = FiveElements()
        # 8글자(천간4+지지4) + 지지의 지장간까지 모두 카운트
        pillars = [
            self.pillars.get_year_pillar().stem, self.pillars.get_year_pillar().branch,
            self.pillars.get_month_pillar().stem, self.pillars.get_month_pillar().branch,
            self.pillars.get_day_pillar().stem, self.pillars.get_day_pillar().branch,
            self.pillars.get_hour_pillar().stem, self.pillars.get_hour_pillar().branch
        ]
        for p in pillars:
            elements_count[five_elements.get_element(p)] += 1
            # 지지라면 지장간까지 카운트
            if p in FiveElements.BRANCH_HIDDEN_STEMS:
                for h in FiveElements.BRANCH_HIDDEN_STEMS[p]:
                    elements_count[five_elements.get_element(h)] += 1
        total = sum(elements_count.values())
        return {k: round(v/total*100, 1) for k,v in elements_count.items()}

    def get_ten_gods_ratio(self):
        """십성별 비율(%) 반환 (지지의 지장간까지 포함)"""
        day_stem = self.pillars.get_day_pillar().stem
        ten_gods = TenGods(day_stem)
        five_elements = FiveElements()
        ten_gods_count = {k:0 for k in ten_gods.gods}
        pillars = [
            self.pillars.get_year_pillar().stem, self.pillars.get_year_pillar().branch,
            self.pillars.get_month_pillar().stem, self.pillars.get_month_pillar().branch,
            self.pillars.get_day_pillar().stem, self.pillars.get_day_pillar().branch,
            self.pillars.get_hour_pillar().stem, self.pillars.get_hour_pillar().branch
        ]
        for p in pillars:
            god = ten_gods.get_god(p)
            if god:
                ten_gods_count[god] += 1
            # 지지라면 지장간까지 십성 카운트
            if p in FiveElements.BRANCH_HIDDEN_STEMS:
                for h in FiveElements.BRANCH_HIDDEN_STEMS[p]:
                    god = ten_gods.get_god(h)
                    if god:
                        ten_gods_count[god] += 1
        total = sum(ten_gods_count.values())
        return {k: round(v/total*100, 1) for k,v in ten_gods_count.items()}

    def get_shin_strength_index(self):
        """신강/신약/중화 등 신강지수 반환 (만세력 표준 구간)"""
        # 비겁(일간과 같은 오행) 비율 기준
        elements = self.get_five_elements_ratio()
        day_element = FiveElements(self.pillars.get_day_pillar().stem).element
        ratio = elements[day_element]
        if ratio < 10:
            return "태약"
        elif ratio < 20:
            return "신약"
        elif ratio < 30:
            return "중화신약"
        elif ratio < 40:
            return "중화신강"
        elif ratio < 50:
            return "신강"
        else:
            return "태강"
        
    def get_twelve_fortune_stars(self):
        """12운성 계산"""
        day_stem = self.pillars.get_day_pillar().stem
        stems = [p.stem for p in self.pillars.get_all_pillars()]
        branches = [p.branch for p in self.pillars.get_all_pillars()]
        
        # 12운성 계산 로직
        fortune_stars = []
        for stem, branch in zip(stems, branches):
            # 12운성 계산 (예: 장생, 목욕, 관대 등)
            star = self._calculate_fortune_star(day_stem, stem, branch)
            fortune_stars.append(star)
        return fortune_stars

    def get_twelve_gods(self):
        """12신살 계산"""
        day_stem = self.pillars.get_day_pillar().stem
        stems = [p.stem for p in self.pillars.get_all_pillars()]
        branches = [p.branch for p in self.pillars.get_all_pillars()]
        
        # 12신살 계산 로직
        gods = []
        for stem, branch in zip(stems, branches):
            # 12신살 계산 (예: 태세, 장군, 소인 등)
            god = self._calculate_god(day_stem, stem, branch)
            gods.append(god)
        return gods

    def _calculate_fortune_star(self, day_stem, stem, branch):
        """12운성 계산 로직"""
        # 12운성 순서: 장생, 목욕, 관대, 건록, 제왕, 쇠, 병, 사, 묘, 절, 태, 양
        fortune_stars = ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]
        
        # 일간의 오행에 따른 시작 위치
        stem_to_start = {
            "갑": 0, "을": 0,  # 목
            "병": 2, "정": 2,  # 화
            "무": 4, "기": 4,  # 토
            "경": 6, "신": 6,  # 금
            "임": 8, "계": 8   # 수
        }
        
        # 지지의 순서
        branch_order = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
        
        # 시작 위치 계산
        start_idx = stem_to_start.get(day_stem, 0)
        branch_idx = branch_order.index(branch)
        
        # 12운성 계산
        fortune_idx = (start_idx + branch_idx) % 12
        return fortune_stars[fortune_idx]

    def _calculate_god(self, day_stem, stem, branch):
        """12신살 계산 로직"""
        # 12신살 순서: 태세, 장군, 소인, 백호, 천덕, 천덕합, 천마, 천형, 천파, 천해, 천살, 천문
        gods = ["태세", "장군", "소인", "백호", "천덕", "천덕합", "천마", "천형", "천파", "천해", "천살", "천문"]
        
        # 일간의 오행에 따른 시작 위치
        stem_to_start = {
            "갑": 0, "을": 0,  # 목
            "병": 2, "정": 2,  # 화
            "무": 4, "기": 4,  # 토
            "경": 6, "신": 6,  # 금
            "임": 8, "계": 8   # 수
        }
        
        # 지지의 순서
        branch_order = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
        
        # 시작 위치 계산
        start_idx = stem_to_start.get(day_stem, 0)
        branch_idx = branch_order.index(branch)
        
        # 12신살 계산
        god_idx = (start_idx + branch_idx) % 12
        return gods[god_idx]

    def print_manse_table(self):
        """만세력 표 출력 (음양, 색상 포함)"""
        pillars = [
            self.pillars.get_hour_pillar(),
            self.pillars.get_day_pillar(),
            self.pillars.get_month_pillar(),
            self.pillars.get_year_pillar()
        ]
        STEM_KOR_TO_HANJA = {"갑":"甲", "을":"乙", "병":"丙", "정":"丁", "무":"戊", "기":"己", "경":"庚", "신":"辛", "임":"壬", "계":"癸"}
        BRANCH_KOR_TO_HANJA = {"자":"子", "축":"丑", "인":"寅", "묘":"卯", "진":"辰", "사":"巳", "오":"午", "미":"未", "신":"申", "유":"酉", "술":"戌", "해":"亥"}
        # 오행별 색상(ANSI)
        ELEMENT_COLOR = {"목":"\033[32m", "화":"\033[31m", "토":"\033[33m", "금":"\033[37m", "수":"\033[34m"}
        RESET = "\033[0m"
        try:
            from .five_elements import FiveElements, TenGods
        except ImportError:
            from five_elements import FiveElements, TenGods
        five_elements = FiveElements()
        # 음양 판별
        def get_yinyang_stem(stem):
            idx = self.pillars.HEAVENLY_STEMS.index(stem)
            return "양" if idx % 2 == 0 else "음"
        def get_yinyang_branch(branch):
            idx = self.pillars.EARTHLY_BRANCHES.index(branch)
            return "양" if idx % 2 == 0 else "음"
        # 색상+음양+한자+오행 표기
        def colorize(text, elem):
            return f"{ELEMENT_COLOR[elem]}{text}{RESET}"
        def get_stem_info(stem):
            hanja = STEM_KOR_TO_HANJA.get(stem, stem)
            elem = five_elements.get_element(stem)
            yinyang = get_yinyang_stem(stem)
            txt = f"{stem}({hanja})+{elem}({yinyang})"
            return colorize(txt, elem)
        def get_branch_info(branch):
            hanja = BRANCH_KOR_TO_HANJA.get(branch, branch)
            elem = five_elements.get_element(branch)
            yinyang = get_yinyang_branch(branch)
            txt = f"{branch}({hanja})+{elem}({yinyang})"
            return colorize(txt, elem)
        stems = [get_stem_info(p.stem) for p in pillars]
        branches = [get_branch_info(p.branch) for p in pillars]
        day_stem = self.pillars.get_day_pillar().stem
        ten_gods = TenGods(day_stem)
        ten_gods_list = [ten_gods.get_god(p.stem) for p in pillars]
        hidden_stems_dict = FiveElements.BRANCH_HIDDEN_STEMS
        hidden_stems_list = [
            ''.join([h+"("+STEM_KOR_TO_HANJA.get(h,h)+")" for h in hidden_stems_dict.get(p.branch, [])]) for p in pillars
        ]
        fortune_stars = self.get_twelve_fortune_stars()
        gods = self.get_twelve_gods()
        
        result = []
        result.append("\n=== 만세력 표 ===")
        result.append("┌────┬────┬────┬────┐")
        result.append("│  시 │  일 │  월 │  년 │")
        result.append("├────┼────┼────┼────┤")
        result.append(f"│ {stems[0]:16} │ {stems[1]:16} │ {stems[2]:16} │ {stems[3]:16} │  ← 천간(+오행, 음양)")
        result.append(f"│ {ten_gods_list[0]:4} │ {ten_gods_list[1]:4} │ {ten_gods_list[2]:4} │ {ten_gods_list[3]:4} │  ← 십성")
        result.append(f"│ {branches[0]:16} │ {branches[1]:16} │ {branches[2]:16} │ {branches[3]:16} │  ← 지지(+오행, 음양)")
        result.append(f"│ {hidden_stems_list[0]:8} │ {hidden_stems_list[1]:8} │ {hidden_stems_list[2]:8} │ {hidden_stems_list[3]:8} │  ← 지장간")
        result.append(f"│ {fortune_stars[0]:4} │ {fortune_stars[1]:4} │ {fortune_stars[2]:4} │ {fortune_stars[3]:4} │  ← 12운성")
        result.append(f"│ {gods[0]:4} │ {gods[1]:4} │ {gods[2]:4} │ {gods[3]:4} │  ← 12신살")
        result.append("└────┴────┴────┴────┘")
        
        print("\n".join(result))

    def __str__(self) -> str:
        """문자열 표현
        
        Returns:
            str: 사주팔자 분석 결과
        """
        result = []
        
        # 1. 기본 정보
        result.append("=== 기본 정보 ===")
        result.append(f"생년월일시: {self.date.strftime('%Y년 %m월 %d일 %H시 %M분')}")
        result.append(f"성별: {'남' if self.gender == 'M' else '여'}")
        result.append(f"지역: {self.region if self.region else '미지정'}")
        result.append(f"띠: {self.get_zodiac_sign()}")
        result.append("")
        
        # 2. 사주팔자
        result.append("=== 사주팔자 ===")
        result.append(f"년주: {self.pillars.get_year_pillar().stem}{self.pillars.get_year_pillar().branch}")
        result.append(f"월주: {self.pillars.get_month_pillar().stem}{self.pillars.get_month_pillar().branch}")
        result.append(f"일주: {self.pillars.get_day_pillar().stem}{self.pillars.get_day_pillar().branch}")
        result.append(f"시주: {self.pillars.get_hour_pillar().stem}{self.pillars.get_hour_pillar().branch}")
        result.append("")
        
        # 3. 일주 분석
        day_master = self.get_day_master_analysis()
        result.append("=== 일주 분석 ===")
        result.append(f"일간: {day_master['일간']} ({day_master['오행']})")
        result.append(f"일지: {day_master['일지']}")
        result.append(f"특성: {day_master['특성']}")
        result.append("")
        
        # 4. 격 분석
        pattern = self.get_pattern()
        result.append("=== 격(格) 분석 ===")
        result.append(f"격: {pattern['격']}")
        result.append(f"특성: {pattern['특성']}")
        result.append(f"장점: {pattern['장점']}")
        result.append(f"단점: {pattern['단점']}")
        result.append("")
        
        # 5. 오행 관계
        relationships = self.get_pillars_relationship()
        result.append("=== 오행 관계 ===")
        for rel_type, rel_list in relationships.items():
            if rel_list:
                result.append(f"{rel_type}: {', '.join(rel_list)}")
        result.append("")
        
        # 6. 오행 비율
        elements = self.get_five_elements_ratio()
        result.append("=== 오행 비율 ===")
        for element, ratio in elements.items():
            result.append(f"{element}: {ratio}%")
        result.append("")
        
        # 7. 십성 비율
        ten_gods = self.get_ten_gods_ratio()
        result.append("=== 십성 비율 ===")
        for god, ratio in ten_gods.items():
            result.append(f"{god}: {ratio}%")
        result.append("")
        
        # 8. 신강지수
        result.append("=== 신강지수 ===")
        result.append(self.get_shin_strength_index())
        result.append("")
        
        # 9. 용신/기신
        use_god = self.get_use_god()
        avoid_god = self.get_avoid_god()
        result.append("=== 용신/기신 ===")
        result.append(f"용신: {use_god['용신']} ({use_god['이유']})")
        result.append(f"기신: {avoid_god['기신']} ({avoid_god['이유']})")
        result.append("")
        
        # 10. 신살
        shinsal = self.get_shinsal()
        result.append("=== 신살 ===")
        for name, branches in shinsal.items():
            if branches:
                result.append(f"{name}: {', '.join(branches)}")
        result.append("")
        
        # 11. 대운
        luck_cycle = self.get_luck_cycle()
        result.append("=== 대운 ===")
        for luck in luck_cycle:
            result.append(f"{luck['시작연령']}: {luck['천간']}{luck['지지']} ({luck['특성']})")
        result.append("")
        
        # 12. 연운
        year_fortune = self.get_year_fortune()
        result.append("=== 연운(10년) ===")
        result.append(", ".join(year_fortune))
        result.append("")
        
        # 13. 월운
        month_fortune = self.get_month_fortune()
        result.append("=== 월운(12개월) ===")
        result.append(", ".join(month_fortune))
        result.append("")
        
        # 14. 조후
        climate = self.get_climate_balance()
        result.append("=== 조후 ===")
        result.append(f"조후: {climate['조후']}")
        result.append(f"영향: {climate['영향']}")
        result.append("")
        
        # 15. 공망/입묘/절지
        empty_death = self.get_empty_death()
        grave = self.get_grave()
        death_ground = self.get_death_ground()
        result.append("=== 공망/입묘/절지 ===")
        result.append(f"공망: {', '.join(empty_death['공망']) if empty_death['공망'] else '없음'}")
        result.append(f"입묘: {', '.join(grave['입묘']) if grave['입묘'] else '없음'}")
        result.append(f"절지: {', '.join(death_ground['절지']) if death_ground['절지'] else '없음'}")
        result.append("")
        
        return "\n".join(result)

    def _get_year_terms(self, year: int) -> List[str]:
        """해당 연도의 절기 데이터 가져오기
        
        Args:
            year: 년도
            
        Returns:
            List[str]: 절기 날짜 목록 (ISO 8601 형식)
        """
        terms_data = {
            2020: [
                "2020-02-04T17:03:00",  # 입춘
                "2020-02-19T12:57:00",  # 우수
                "2020-03-05T10:57:00",  # 경칩
                "2020-03-20T11:49:00",  # 춘분
                "2020-04-04T15:38:00",  # 청명
                "2020-04-19T22:45:00",  # 곡우
                "2020-05-05T08:51:00",  # 입하
                "2020-05-20T21:49:00",  # 소만
                "2020-06-05T12:58:00",  # 망종
                "2020-06-21T05:43:00",  # 하지
                "2020-07-06T23:14:00",  # 소서
                "2020-07-22T16:37:00",  # 대서
                "2020-08-07T09:06:00",  # 입추
                "2020-08-22T23:45:00",  # 처서
                "2020-09-07T12:08:00",  # 백로
                "2020-09-22T21:31:00",  # 추분
                "2020-10-08T03:55:00",  # 한로
                "2020-10-23T06:59:00",  # 상강
                "2020-11-07T07:14:00",  # 입동
                "2020-11-22T04:40:00",  # 소설
                "2020-12-07T00:09:00",  # 대설
                "2020-12-21T18:02:00",  # 동지
                "2021-01-05T11:23:00",  # 소한
                "2021-01-20T04:40:00",  # 대한
                "2021-02-03T22:59:00"   # 다음해 입춘
            ],
            1979: [
                "1979-02-04T11:55:00",  # 입춘
                "1979-02-19T05:31:00",  # 우수
                "1979-03-06T00:46:00",  # 경칩
                "1979-03-20T22:22:00",  # 춘분
                "1979-04-05T22:31:00",  # 청명
                "1979-04-21T01:17:00",  # 곡우
                "1979-05-06T07:01:00",  # 입하
                "1979-05-21T15:49:00",  # 소만
                "1979-06-06T03:19:00",  # 망종
                "1979-06-21T17:56:00",  # 하지
                "1979-07-07T11:31:00",  # 소서
                "1979-07-23T07:49:00",  # 대서
                "1979-08-08T06:31:00",  # 입추
                "1979-08-24T07:31:00",  # 처서
                "1979-09-08T10:49:00",  # 백로
                "1979-09-23T16:37:00",  # 추분
                "1979-10-09T00:49:00",  # 한로
                "1979-10-24T11:19:00",  # 상강
                "1979-11-08T23:49:00",  # 입동
                "1979-11-23T14:19:00",  # 소설
                "1979-12-08T06:19:00",  # 대설
                "1979-12-22T23:49:00",  # 동지
                "1980-01-06T18:19:00",  # 소한
                "1980-01-21T13:19:00",  # 대한
                "1980-02-04T17:39:00"   # 다음해 입춘
            ],
            1980: [
                "1980-02-04T17:39:00",  # 입춘
                "1980-02-19T11:26:00",  # 우수
                "1980-03-05T06:39:00",  # 경칩
                "1980-03-20T04:14:00",  # 춘분
                "1980-04-05T04:26:00",  # 청명
                "1980-04-20T07:14:00",  # 곡우
                "1980-05-06T12:39:00",  # 입하
                "1980-05-21T21:26:00",  # 소만
                "1980-06-05T08:51:00",  # 망종
                "1980-06-20T23:39:00",  # 하지
                "1980-07-07T17:14:00",  # 소서
                "1980-07-23T13:26:00",  # 대서
                "1980-08-07T11:51:00",  # 입추
                "1980-08-23T11:51:00",  # 처서
                "1980-09-07T13:26:00",  # 백로
                "1980-09-23T16:51:00",  # 추분
                "1980-10-08T22:26:00",  # 한로
                "1980-10-24T06:14:00",  # 상강
                "1980-11-07T16:26:00",  # 입동
                "1980-11-22T04:51:00",  # 소설
                "1980-12-07T19:26:00",  # 대설
                "1980-12-22T12:14:00",  # 동지
                "1981-01-05T06:51:00",  # 소한
                "1981-01-20T02:51:00",  # 대한
                "1981-02-04T11:55:00"   # 다음해 입춘
            ],
            1983: [
                "1983-02-04T05:39:00",  # 입춘
                "1983-02-18T23:26:00",  # 우수
                "1983-03-05T18:39:00",  # 경칩
                "1983-03-20T16:14:00",  # 춘분
                "1983-04-05T16:26:00",  # 청명
                "1983-04-20T19:14:00",  # 곡우
                "1983-05-06T00:39:00",  # 입하
                "1983-05-21T09:26:00",  # 소만
                "1983-06-05T20:51:00",  # 망종
                "1983-06-21T11:39:00",  # 하지
                "1983-07-07T05:14:00",  # 소서
                "1983-07-23T01:26:00",  # 대서
                "1983-08-07T23:51:00",  # 입추
                "1983-08-23T23:51:00",  # 처서
                "1983-09-08T01:26:00",  # 백로
                "1983-09-23T04:51:00",  # 추분
                "1983-10-08T10:26:00",  # 한로
                "1983-10-23T18:14:00",  # 상강
                "1983-11-07T04:26:00",  # 입동
                "1983-11-22T16:51:00",  # 소설
                "1983-12-07T07:26:00",  # 대설
                "1983-12-22T00:14:00",  # 동지
                "1984-01-05T18:51:00",  # 소한
                "1984-01-20T14:51:00"   # 대한
            ]
            # ... 기존 다른 연도 데이터 ...
        }
        
        # 연도가 범위를 벗어나면 None 반환
        if year < 1900 or year > 2050:
            return None
            
        # 해당 연도의 절기 데이터가 없으면 가장 가까운 연도의 데이터 사용
        if year not in terms_data:
            closest_year = min(terms_data.keys(), key=lambda x: abs(x - year))
            terms = terms_data[closest_year]
            # 연도만 조정하여 반환
            adjusted_terms = []
            for term in terms:
                dt = datetime.fromisoformat(term)
                if dt.year < year:
                    dt = dt.replace(year=year)
                    if dt.month == 1:  # 소한, 대한은 다음 해의 절기
                        dt = dt.replace(year=year+1)
                else:
                    dt = dt.replace(year=year)
                    if dt.month == 1:  # 소한, 대한은 이전 해의 절기
                        dt = dt.replace(year=year-1)
                adjusted_terms.append(dt.isoformat())
            return adjusted_terms
            
        return terms_data[year]

    def _calculate_luck_start_age(self, days: float) -> int:
        """대운수 계산.

        절입까지의 일수 3일을 1년으로 보고, 남는 1일은 4개월로 본다.
        남은 기간이 4개월 이상이면 다음 나이로 올린다.
        예: 9.8일 -> 3년 3개월대 -> 대운수 3.
        예: 13.1일 -> 4년 4개월대 -> 대운수 5.
        """
        whole_years = int(days // 3)
        remainder_days = days - whole_years * 3
        start_age = whole_years + (1 if remainder_days >= 1 else 0)
        if start_age < 1:
            start_age = 1
        if start_age > 10:
            start_age = 10
        return start_age

    def get_zodiac_sign(self) -> str:
        """띠 정보 반환
        Returns:
            str: 띠 정보 (한자)
        """
        zodiac_signs = {
            "자": "鼠",
            "축": "牛",
            "인": "虎",
            "묘": "兔",
            "진": "龍",
            "사": "蛇",
            "오": "馬",
            "미": "羊",
            "신": "猴",
            "유": "雞",
            "술": "狗",
            "해": "豬"
        }
        year_branch = self.pillars.get_year_pillar().branch
        return zodiac_signs[year_branch]
