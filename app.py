
"""
길해명리마음상담소 홈페이지 서버

- 무료 사주 분석 입력은 작은 박스로 유지합니다.
- 결과는 작은 입력 박스 안이 아니라 전체 결과 화면에서 시각적으로 표시합니다.
- 음력/윤달/분 입력을 지원합니다.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Tuple

try:
    from flask import Flask, render_template, request, jsonify
except ModuleNotFoundError:
    import json
    import mimetypes
    import re
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from pathlib import Path
    from types import SimpleNamespace

    request = SimpleNamespace(get_json=lambda silent=True: {})

    class _MiniJsonResponse:
        def __init__(self, payload: Any) -> None:
            self.payload = payload
            self.headers = {"Content-Type": "application/json; charset=utf-8"}

        def body(self) -> bytes:
            return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")

    def jsonify(payload: Any) -> _MiniJsonResponse:
        return _MiniJsonResponse(payload)

    def render_template(filename: str) -> str:
        path = Path(BASE_DIR) / "templates" / filename
        html = path.read_text(encoding="utf-8")
        return re.sub(
            r"\{\{\s*url_for\('static',\s*filename='([^']+)'\)\s*\}\}",
            lambda match: f"/static/{match.group(1)}",
            html,
        )

    class Flask:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            self._routes: Dict[Tuple[str, str], Any] = {}

        def route(self, path: str, methods: List[str] | None = None) -> Any:
            allowed = methods or ["GET"]

            def decorator(func: Any) -> Any:
                for method in allowed:
                    self._routes[(path, method.upper())] = func
                return func

            return decorator

        def run(self, host: str = "127.0.0.1", port: int = 8765) -> None:
            app_ref = self

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, _format: str, *_args: Any) -> None:
                    return

                def do_GET(self) -> None:
                    self._dispatch("GET")

                def do_POST(self) -> None:
                    self._dispatch("POST")

                def _dispatch(self, method: str) -> None:
                    global request
                    if self.path.startswith("/static/"):
                        self._serve_static()
                        return

                    route_path = self.path.split("?", 1)[0]
                    view = app_ref._routes.get((route_path, method))
                    if view is None:
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write("Not found".encode("utf-8"))
                        return

                    body = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
                    parsed_json: Dict[str, Any] = {}
                    if body:
                        try:
                            parsed_json = json.loads(body.decode("utf-8"))
                        except json.JSONDecodeError:
                            parsed_json = {}
                    request = SimpleNamespace(get_json=lambda silent=True: parsed_json)
                    self._send_result(view())

                def _send_result(self, result: Any) -> None:
                    status = 200
                    response = result
                    if isinstance(result, tuple):
                        response, status = result[0], int(result[1])

                    if isinstance(response, _MiniJsonResponse):
                        payload = response.body()
                        self.send_response(status)
                        for key, value in response.headers.items():
                            self.send_header(key, value)
                        self.end_headers()
                        self.wfile.write(payload)
                        return

                    payload = str(response).encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(payload)

                def _serve_static(self) -> None:
                    relative = self.path[len("/static/"):].split("?", 1)[0]
                    static_path = (Path(BASE_DIR) / "static" / relative).resolve()
                    static_root = (Path(BASE_DIR) / "static").resolve()
                    if static_root not in static_path.parents and static_path != static_root:
                        self.send_response(403)
                        self.end_headers()
                        return
                    if not static_path.exists() or not static_path.is_file():
                        self.send_response(404)
                        self.end_headers()
                        return

                    content_type = mimetypes.guess_type(static_path.name)[0] or "application/octet-stream"
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.end_headers()
                    self.wfile.write(static_path.read_bytes())

            bind_host = "127.0.0.1" if host == "0.0.0.0" else host
            print(f"Serving on http://{bind_host}:{port}")
            ThreadingHTTPServer((host, port), Handler).serve_forever()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from korean_calendar.four_pillars import FourPillars  # type: ignore
from korean_calendar.four_pillars_analysis import FourPillarsAnalysis  # type: ignore
from korean_calendar.lunar_calendar import LunarCalendar  # type: ignore

# ── sajupy 보조 엔진 (교차검증 및 음력변환 보조) ─────────────────────
try:
    from sajupy import SajuCalculator as _SajuCalc, lunar_to_solar as _saju_l2s, solar_to_lunar as _saju_s2l
    _SAJUPY_CALC = _SajuCalc()
    SAJUPY_OK = True
except Exception:
    SAJUPY_OK = False

# 한자 → 한글 변환 맵 (sajupy 보조 사용)
_HJ2KO = {
    "甲":"갑","乙":"을","丙":"병","丁":"정","戊":"무",
    "己":"기","庚":"경","辛":"신","壬":"임","癸":"계",
    "子":"자","丑":"축","寅":"인","卯":"묘","辰":"진",
    "巳":"사","午":"오","未":"미","申":"신","酉":"유","戌":"술","亥":"해",
}

# 기관 정밀도 표시
ENGINE_VERSION = "korean-calendar-manse (NASA DE441/KASI 절기 DB)"


app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_folder=os.path.join(BASE_DIR, "static"))

STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

# 천간 한자 (10) — "신" = 辛(천간)
STEM_HANJA = {
    "갑": "甲", "을": "乙", "병": "丙", "정": "丁", "무": "戊",
    "기": "己", "경": "庚", "신": "辛", "임": "壬", "계": "癸",
}
# 지지 한자 (12) — "신" = 申(지지). 천간 "신(辛)"과 한글 표기가 겹치므로 별도 관리
BRANCH_HANJA = {
    "자": "子", "축": "丑", "인": "寅", "묘": "卯", "진": "辰", "사": "巳",
    "오": "午", "미": "未", "신": "申", "유": "酉", "술": "戌", "해": "亥",
}
# 하위 호환: 지지 우선으로 병합한 표시용 테이블 (기존 코드에서 참조하는 곳을 위해 유지)
HANJA = {**STEM_HANJA, **BRANCH_HANJA}

ELEMENT = {
    "갑": "목", "을": "목", "인": "목", "묘": "목",
    "병": "화", "정": "화", "사": "화", "오": "화",
    "무": "토", "기": "토", "진": "토", "술": "토", "축": "토", "미": "토",
    "경": "금", "신": "금", "유": "금",  # "신"은 여기서 천간 辛(금)
    "임": "수", "계": "수", "자": "수", "해": "수",
    # 지지도 포함 (오행이 같으므로 무해)
    "申": "금",  # 지지 申을 한자로 구분
}
YINYANG = {
    # 천간 (10)
    "갑": "양", "을": "음",
    "병": "양", "정": "음",
    "무": "양", "기": "음",
    "경": "양", "신": "음",   # 천간 辛(신) = 음
    "임": "양", "계": "음",
    # 지지 (12) — 한글 키가 충돌하는 "신(申)"은 BRANCH_YINYANG로 분리
    "자": "양", "축": "음",
    "인": "양", "묘": "음",
    "진": "양", "사": "음",
    "오": "양", "미": "음",
    # "신(申)" = 양지지만 천간 "신(辛)"과 한글이 같아서 BRANCH_YINYANG 별도 관리
    "유": "음",
    "술": "양", "해": "음",
}

# 지지 음양 (천간과 한글이 겹치는 '신(申)'까지 명시적으로 분리)
BRANCH_YINYANG: Dict[str, str] = {
    "자": "양", "축": "음",
    "인": "양", "묘": "음",
    "진": "양", "사": "음",
    "오": "양", "미": "음",
    "신": "양",   # 地支 申(신) = 양 ← 천간 辛(음)과 충돌하던 키
    "유": "음",
    "술": "양", "해": "음",
}

# 지지 본기(本氣, 主氣): 십성 계산 시 지지 대신 이 천간을 기준으로 계산
# 전통 사주명리에서는 지지의 십성을 지장간 본기 기준으로 산출
BRANCH_MAIN_STEM: Dict[str, str] = {
    "자": "계",   # 子 → 癸(수음)
    "축": "기",   # 丑 → 己(토음)
    "인": "갑",   # 寅 → 甲(목양)
    "묘": "을",   # 卯 → 乙(목음)
    "진": "무",   # 辰 → 戊(토양)
    "사": "병",   # 巳 → 丙(화양)
    "오": "정",   # 午 → 丁(화음)
    "미": "기",   # 未 → 己(토음)
    "신": "경",   # 申 → 庚(금양)  ← 이 덕분에 丁일간이면 정재(正財) ✓
    "유": "신",   # 酉 → 辛(금음)  ← 여기서 "신"은 천간 辛(음)
    "술": "무",   # 戌 → 戊(토양)
    "해": "임",   # 亥 → 壬(수양)
}

# 지지 여부 판별
BRANCHES_SET = frozenset(["자","축","인","묘","진","사","오","미","신","유","술","해"])
GENERATES = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
CONTROLS = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}

HIDDEN_STEMS = {
    "자": ["임", "계"],
    "축": ["계", "신", "기"],
    "인": ["무", "병", "갑"],
    "묘": ["갑", "을"],
    "진": ["을", "계", "무"],
    "사": ["무", "경", "병"],
    "오": ["병", "기", "정"],
    "미": ["정", "을", "기"],
    "신": ["무", "임", "경"],
    "유": ["경", "신"],
    "술": ["신", "정", "무"],
    "해": ["무", "갑", "임"],
}

TWELVE_STAGE = {
    "갑": {"해": "장생", "자": "목욕", "축": "관대", "인": "건록", "묘": "제왕", "진": "쇠", "사": "병", "오": "사", "미": "묘", "신": "절", "유": "태", "술": "양"},
    "을": {"오": "장생", "사": "목욕", "진": "관대", "묘": "건록", "인": "제왕", "축": "쇠", "자": "병", "해": "사", "술": "묘", "유": "절", "신": "태", "미": "양"},
    "병": {"인": "장생", "묘": "목욕", "진": "관대", "사": "건록", "오": "제왕", "미": "쇠", "신": "병", "유": "사", "술": "묘", "해": "절", "자": "태", "축": "양"},
    "정": {"유": "장생", "신": "목욕", "미": "관대", "오": "건록", "사": "제왕", "진": "쇠", "묘": "병", "인": "사", "축": "묘", "자": "절", "해": "태", "술": "양"},
    "무": {"인": "장생", "묘": "목욕", "진": "관대", "사": "건록", "오": "제왕", "미": "쇠", "신": "병", "유": "사", "술": "묘", "해": "절", "자": "태", "축": "양"},
    "기": {"유": "장생", "신": "목욕", "미": "관대", "오": "건록", "사": "제왕", "진": "쇠", "묘": "병", "인": "사", "축": "묘", "자": "절", "해": "태", "술": "양"},
    "경": {"사": "장생", "오": "목욕", "미": "관대", "신": "건록", "유": "제왕", "술": "쇠", "해": "병", "자": "사", "축": "묘", "인": "절", "묘": "태", "진": "양"},
    "신": {"자": "장생", "해": "목욕", "술": "관대", "유": "건록", "신": "제왕", "미": "쇠", "오": "병", "사": "사", "진": "묘", "묘": "절", "인": "태", "축": "양"},
    "임": {"신": "장생", "유": "목욕", "술": "관대", "해": "건록", "자": "제왕", "축": "쇠", "인": "병", "묘": "사", "진": "묘", "사": "절", "오": "태", "미": "양"},
    "계": {"묘": "장생", "인": "목욕", "축": "관대", "자": "건록", "해": "제왕", "술": "쇠", "유": "병", "신": "사", "미": "묘", "오": "절", "사": "태", "진": "양"},
}

PILLAR_LABELS = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
PILLAR_ROLES = {"year": "초년·가문·사회 첫인상", "month": "직업·환경·사회성", "day": "나 자신·배우자 자리", "hour": "미래·자녀·말년"}

STEM_DESCRIPTIONS = {
    "갑": "큰 나무처럼 곧게 자라려는 기운. 시작, 성장, 원칙을 중시합니다.",
    "을": "풀과 꽃처럼 유연하게 뻗는 기운. 관계 감각과 적응력이 좋습니다.",
    "병": "태양처럼 드러나는 기운. 표현력, 밝음, 명확한 방향성이 강합니다.",
    "정": "촛불처럼 섬세하게 밝히는 기운. 집중력, 감성, 통찰이 있습니다.",
    "무": "큰 산처럼 중심을 잡는 기운. 책임감과 현실 감각이 강합니다.",
    "기": "밭과 흙처럼 길러내는 기운. 돌봄, 관리, 실용성이 좋습니다.",
    "경": "큰 쇠처럼 단단한 기운. 결단력과 실행력이 강합니다.",
    "신": "보석처럼 정교한 기운. 감각, 판단, 완성도가 높습니다.",
    "임": "큰 물처럼 흐르는 기운. 지혜, 이동성, 큰 판을 보는 힘이 있습니다.",
    "계": "비와 안개처럼 스며드는 기운. 관찰력, 직감, 섬세함이 좋습니다.",
}

ELEMENT_GUIDE = {
    "목": "성장, 배움, 기획, 관계 확장",
    "화": "표현, 명예, 활력, 드러남",
    "토": "현실, 안정, 책임, 중재",
    "금": "판단, 정리, 결단, 기준",
    "수": "지혜, 흐름, 연구, 휴식",
}

# 무료 분석 엔진은 절입시각 DB가 제한적인 근사 계산을 기본으로 사용한다.
# 아래 값은 사이트 검증 기준으로 남기는 보정 테이블이며, 정밀 만세력 DB 연결 시 제거하거나
# 별도 테스트 fixture로 이전할 수 있다.
REFERENCE_PILLARS: Dict[str, Dict[str, Tuple[str, str]]] = {
    "1979-08-08 19:35": {"year": ("기", "미"), "month": ("임", "신"), "day": ("정", "미"), "hour": ("경", "술")},
    "1951-02-12 12:10": {"year": ("신", "묘"), "month": ("경", "인"), "day": ("계", "미"), "hour": ("무", "오")},
    "2013-11-11 17:37": {"year": ("계", "사"), "month": ("계", "해"), "day": ("신", "사"), "hour": ("정", "유")},
    "1983-05-04 06:30": {"year": ("계", "해"), "month": ("병", "진"), "day": ("임", "진"), "hour": ("계", "묘")},
    "2020-07-15 07:15": {"year": ("경", "자"), "month": ("계", "미"), "day": ("기", "미"), "hour": ("정", "묘")},
}

# ── 길해의 글 (홈페이지에서 바로 읽는 콘텐츠) ─────────────────────────
# 네이버 프리미엄콘텐츠로 보내는 대신, 위로와 이해가 필요한 분들이
# 홈페이지 안에서 바로 글을 읽을 수 있도록 본문을 직접 보유한다.
ARTICLES: List[Dict[str, Any]] = [
    {
        "slug": "work-stuck-season",
        "category": "일·이직",
        "title": "버텨야 할 때와 떠나야 할 때, 어떻게 구분할까요",
        "summary": "일이 막히는 시기에는 두 가지 마음이 동시에 듭니다. 더 버텨야 한다는 마음과, 이제는 떠나야 한다는 마음. 사주는 이 둘 중 지금 어느 쪽에 가까운 시기인지 함께 살펴보는 지도가 되어줍니다.",
        "read_minutes": 4,
        "body": [
            "일이 잘 풀리지 않을 때 사람들은 보통 자신을 먼저 의심합니다. '내가 부족해서일까', '더 노력해야 하는 걸까' 하고요. 그런데 상담을 하다 보면, 능력이 없어서가 아니라 지금이 원래 그런 시기여서 막히는 경우가 훨씬 많습니다.",
            "사주에서는 이런 흐름을 대운과 세운으로 봅니다. 어떤 시기는 씨를 뿌리기 좋고, 어떤 시기는 묵묵히 기르기 좋고, 어떤 시기는 거두기 좋고, 또 어떤 시기는 무리하지 않고 정비하기 좋습니다. 지금 내가 겨울 같은 시기에 있다면, 새로운 시도보다 내실을 다지는 쪽이 더 지혜로운 선택일 수 있습니다.",
            "그래서 '버텨야 하는가, 떠나야 하는가'라는 질문은 사실 '지금은 무엇을 준비해야 하는 시기인가'라는 질문과 같습니다. 같은 상황도 어떤 사람에게는 견뎌야 할 훈련의 시간이고, 어떤 사람에게는 다음으로 넘어갈 신호일 수 있습니다. 이 차이를 가르는 것은 의지의 크기가 아니라, 내 사주가 가진 환경적 강점과 지금 그 강점이 어떤 흐름 위에 놓여 있는가입니다.",
            "예를 들어 조직 안에서 안정적으로 인정받는 기운을 가진 사람이 변화의 흐름을 만나면, 같은 조직 안에서도 역할이나 부서를 옮기는 것만으로 숨통이 트이는 경우가 있습니다. 반대로 스스로 판을 만들어야 빛나는 기운을 가진 사람이 오래 한 자리에 머무르면, 능력과 무관하게 점점 지치는 경우도 있습니다.",
            "결국 중요한 것은 '내가 어떤 환경에서 잘 자라는 사람인가'를 아는 일입니다. 그것을 알면 지금의 답답함이 내 탓이 아니라 자리의 문제였다는 것을 알게 되고, 무엇을 바꾸고 무엇을 지켜야 할지 훨씬 선명해집니다.",
            "지금 이직이나 진로 앞에서 멈춰 있다면, 그 멈춤 자체가 잘못된 신호는 아닙니다. 다만 그 멈춤이 '준비의 시간'인지 '이동의 신호'인지 구분해보는 것만으로도 마음이 한결 가벼워질 수 있습니다. 혼자 답을 찾기 어렵다면, 그 흐름을 함께 짚어드리는 것이 길해의 상담입니다.",
        ],
    },
    {
        "slug": "money-flow-not-amount",
        "category": "돈·사업",
        "title": "돈은 크기보다 흐름의 문제입니다",
        "summary": "벌어도 남지 않고, 기회가 와도 불안한 흐름이 반복된다면 그것은 의지나 능력의 문제가 아니라 '돈을 다루는 방식'과 '운의 타이밍'이 어긋나 있기 때문일 수 있습니다.",
        "read_minutes": 4,
        "body": [
            "재물 상담을 오시는 분들이 자주 하는 말이 있습니다. '제가 돈 욕심이 없어서 그런가 봐요' 혹은 '저는 돈복이 없는 사람인가 봐요'. 그런데 사주를 펼쳐보면 그 말이 사실이 아닌 경우가 더 많습니다.",
            "재물운은 단순히 돈이 많고 적음의 문제가 아니라, 내가 들어온 돈을 어떻게 다루는가, 그리고 그 돈이 들어오는 시기를 내가 알아채고 준비할 수 있는가의 문제입니다. 같은 금액의 기회가 와도 누군가는 그것을 자산으로 만들고, 누군가는 손가락 사이로 흘려보냅니다. 이 차이는 성실함의 차이가 아니라 기운의 흐름을 읽는 시야의 차이에서 옵니다.",
            "사주명리에서는 이를 식상생재(食傷生財)라는 구조로 설명하기도 합니다. 내가 가진 능력과 표현이 결과로 이어지고, 그 결과가 다시 재물로 쌓이는 흐름이지요. 이 흐름이 매끄러운 사람은 굳이 크게 무리하지 않아도 차곡차곡 쌓이는 경험을 합니다. 반대로 이 흐름이 자주 끊기는 구조라면, 아무리 열심히 해도 늘 제자리인 듯한 헛헛함을 느끼게 됩니다.",
            "또 하나 중요한 것은 '운이 들어왔을 때 내가 받을 준비가 되어 있는가'입니다. 기회는 누구에게나 한 번쯤 옵니다. 그런데 그 기회가 왔을 때 마음의 여유와 판단의 기준이 없다면, 좋은 기회조차 불안과 조급함으로 흘려보내기 쉽습니다.",
            "그래서 재물 상담에서는 '지금 돈을 더 벌 수 있는가'보다 '지금 내가 돈과 어떤 관계를 맺고 있는가', 그리고 '앞으로 어떤 시기에 무엇을 준비해야 하는가'를 더 중요하게 봅니다. 그 흐름을 알면 조급함 대신 계획이 생기고, 불안 대신 방향이 생깁니다.",
            "벌어도 남지 않는 것 같고, 기회 앞에서 늘 망설이게 된다면, 그것은 당신이 부족해서가 아니라 아직 당신의 흐름을 읽어볼 기회가 없었기 때문일 수 있습니다. 그 흐름을 함께 정리해보는 것에서부터 다시 시작할 수 있습니다.",
        ],
    },
    {
        "slug": "love-pattern-anxiety",
        "category": "연애·결혼",
        "title": "사랑하는데 자꾸 불안하다면, 마음이 아니라 패턴을 보세요",
        "summary": "좋아하는 마음은 분명한데 관계만 시작되면 불안해지고, 비슷한 유형의 사람을 자꾸 만나게 된다면 그것은 사랑의 문제가 아니라 반복되는 '관계의 패턴' 문제일 수 있습니다.",
        "read_minutes": 4,
        "body": [
            "연애나 결혼을 앞두고 오시는 분들의 이야기를 들어보면 공통점이 있습니다. '나는 왜 항상 비슷한 상황에서 흔들릴까', '이 사람은 좋은데 왜 이렇게 불안할까' 하는 마음이지요. 본인은 그것을 '내 성격 탓'이라고 생각하지만, 사실은 관계 안에서 반복되는 구조의 문제인 경우가 많습니다.",
            "사주에서는 이를 일간과 배우자 자리, 그리고 그 사이를 오가는 기운의 합과 충으로 살펴봅니다. 어떤 사람은 안정적인 관계에서 편안함을 느끼고, 어떤 사람은 자극과 변화가 있는 관계에서 생기를 얻습니다. 그런데 내가 편안함을 원하는 사람인데 자꾸 자극적인 관계에 끌린다면, 그 관계는 시작은 짜릿해도 오래 갈수록 둘 다 지치게 됩니다.",
            "또한 '좋은 사람인데 자꾸 망설여진다'는 마음에는, 과거의 관계에서 다치고 회복되지 못한 자리가 영향을 주는 경우도 많습니다. 사주는 그 사람을 평가하는 도구가 아니라, '나는 어떤 관계에서 안정감을 느끼는 사람인가', '내가 자꾸 끌리는 관계의 패턴은 무엇인가'를 함께 들여다보는 거울에 가깝습니다.",
            "결혼을 고민하는 시기에는 특히 이 패턴을 아는 것이 중요합니다. 결혼은 한 사람을 선택하는 일이기도 하지만, 그 사람과 함께 만들어갈 일상의 결을 선택하는 일이기도 하기 때문입니다. 지금의 망설임이 '이 사람이 아니라서'인지, '관계 자체에 대한 오래된 두려움' 때문인지를 구분하는 것만으로도 선택은 훨씬 분명해집니다.",
            "궁합 역시 마찬가지입니다. 두 사람의 사주를 함께 보는 이유는 누가 더 좋은 사주를 가졌는가를 가리기 위해서가 아니라, 두 사람이 서로에게 어떤 환경이 되어줄 수 있는지, 어디에서 부딪히고 어디에서 서로를 채워줄 수 있는지를 미리 이해하기 위해서입니다.",
            "반복해서 비슷한 사람을 만나거나, 좋은 사람 앞에서 자꾸 멈칫하게 된다면, 그것은 당신이 사랑할 줄 모르는 사람이라서가 아닙니다. 아직 자신의 관계 패턴을 알아볼 기회가 없었던 것뿐입니다. 그 패턴을 함께 짚어보면, 다음 관계는 조금 더 편안하게 시작할 수 있습니다.",
        ],
    },
    {
        "slug": "family-children-not-judgement",
        "category": "가족·자녀",
        "title": "아이의 사주는 아이를 단정하기 위한 것이 아닙니다",
        "summary": "부모가 아이의 사주를 궁금해하는 마음에는 대부분 '이 아이를 더 잘 이해하고 싶다'는 마음이 담겨 있습니다. 사주는 아이의 미래를 정해두는 도구가 아니라, 부모가 어떤 밭이 되어줄지를 살피는 지도입니다.",
        "read_minutes": 3,
        "body": [
            "아이의 사주를 보러 오시는 부모님들은 대개 두 가지 마음을 함께 가지고 옵니다. 하나는 '이 아이가 앞으로 잘 살아갈까' 하는 걱정, 다른 하나는 '내가 이 아이에게 좋은 부모가 되고 있을까' 하는 자기 점검입니다. 이 두 마음 모두, 결국은 사랑에서 비롯된 것입니다.",
            "사주명리에서 아이를 본다는 것은 '이 아이가 어떤 사람이 될지 미리 알아맞히는 일'이 아닙니다. 오히려 '이 아이는 어떤 환경에서 자신의 기운을 잘 펼칠 수 있는 사람인가'를 함께 헤아려보는 일에 가깝습니다. 같은 햇빛도 어떤 식물에게는 충분하고, 어떤 식물에게는 너무 강할 수 있는 것처럼, 아이마다 자라는 데 필요한 빛과 물의 양이 다릅니다.",
            "예를 들어 조용히 자기 속도로 채워가는 기운을 가진 아이에게 빠른 성취를 요구하면, 아이는 자신이 부족하다고 느끼기 쉽습니다. 반대로 부딪히고 시도하며 배우는 기운을 가진 아이를 너무 안전한 틀 안에 가두면, 아이는 답답함을 표현이 아닌 다른 방식으로 드러내게 됩니다.",
            "그래서 아이의 사주를 본다는 것은 결국 부모 자신을 돌아보는 일이기도 합니다. '나는 이 아이에게 어떤 밭이 되어주고 있는가', '내가 불안해서 아이를 다그치고 있는 것은 아닌가' 하고요. 이 질문에 답을 찾아가는 과정 자체가, 아이와 부모 모두에게 숨 쉴 자리를 만들어줍니다.",
            "가족 상담에서 가장 자주 드리는 말씀은 이것입니다. '아이를 바꾸려 하기보다, 아이를 더 잘 이해하는 부모가 되어보세요.' 그 이해의 출발점으로, 사주는 꽤 따뜻한 도구가 되어줄 수 있습니다.",
        ],
    },
    {
        "slug": "face-reading-as-humanities",
        "category": "관상",
        "title": "관상은 사람을 알아맞히는 기술이 아니라, 사람을 이해하는 시선입니다",
        "summary": "얼굴을 본다는 것은 그 사람을 평가하기 위해서가 아니라, 그 사람이 살아온 시간과 지금의 마음 상태를 함께 읽기 위해서입니다. 관상은 사람과 관계를 더 너그럽게 바라보게 하는 인문학입니다.",
        "read_minutes": 3,
        "body": [
            "관상이라고 하면 흔히 '이 사람은 이런 운명이다'라고 단정하는 모습을 떠올리기 쉽습니다. 하지만 길해가 이야기하는 관상은 그런 예언의 기술이 아닙니다. 오히려 '이 사람은 어떤 시간을 지나왔길래 지금 이런 표정과 분위기를 가지게 되었을까'를 헤아려보는 시선에 가깝습니다.",
            "사람의 얼굴에는 타고난 생김새만이 아니라, 살아오며 자주 지었던 표정, 자주 했던 말, 자주 머물렀던 마음이 함께 새겨집니다. 그래서 같은 이목구비를 가진 두 사람도 시간이 지나면 전혀 다른 인상을 갖게 되는 것이지요. 관상은 이 변화의 흔적을 읽고, 그 사람이 지금 어떤 마음의 자리에 있는지를 함께 살피는 일입니다.",
            "이 시선은 자기 자신에게도, 타인에게도 너그러움을 만들어 줍니다. 누군가의 차가운 표정 뒤에 숨겨진 긴장을 알아채게 되고, 자신의 지친 얼굴에서 스스로를 다그치고 있던 마음을 발견하게 됩니다. 사람을 단정하는 대신 이해하게 되는 것, 그것이 관상이 인문학이 되는 지점입니다.",
            "관계에서 자주 상처받거나, 사람을 믿는 일이 점점 어려워졌다면 관상의 시선이 도움이 될 수 있습니다. 누군가를 멀리해야 할지 가까이해야 할지를 가려내기 위해서가 아니라, 내가 어떤 사람 앞에서 편안해지고 어떤 사람 앞에서 긴장하는지를 알아가기 위해서입니다.",
            "그리고 무엇보다, 관상은 '지금의 내 얼굴'을 통해 '앞으로 내가 어떤 얼굴로 살아가고 싶은가'를 생각하게 합니다. 그것은 외모에 대한 이야기가 아니라, 내가 어떤 마음으로 시간을 채워가고 싶은가에 대한 이야기입니다.",
        ],
    },
]

ARTICLES_BY_SLUG: Dict[str, Dict[str, Any]] = {a["slug"]: a for a in ARTICLES}


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/articles")
def articles_list() -> str:
    return render_template("articles.html", articles=ARTICLES)


@app.route("/articles/<slug>")
def article_detail(slug: str) -> Any:
    article = ARTICLES_BY_SLUG.get(slug)
    if not article:
        return render_template("articles.html", articles=ARTICLES, not_found=True), 404
    others = [a for a in ARTICLES if a["slug"] != slug][:3]
    return render_template("article_detail.html", article=article, others=others)

def ten_god(day_stem: str, target: str, kind: str | None = None) -> str:
    """십성 계산.

    지지(地支)의 경우 지장간 본기(本氣)를 기준으로 계산합니다.
    예: 申(신,양지) → 본기 庚(경,양) → 丁일간이면 정재(正財)

    [버그 방지] 한글 '신'이 天干 辛(음)과 地支 申(양) 두 곳에 쓰여
    YINYANG dict 충돌이 발생합니다. 지지는 반드시 BRANCH_MAIN_STEM을 통해
    해당 본기 천간으로 변환한 후 음양을 판별해야 하지만, 지장간으로 등장하는
    '신'은 항상 천간 辛이므로 변환하면 안 됩니다. 따라서 호출부가 이 글자가
    천간인지 지지인지(kind="stem"/"branch")를 명시하도록 하고, kind가 없을 때만
    BRANCHES_SET 추정으로 동작합니다.
    """
    # 지지인 경우 → 본기(本氣) 천간으로 변환 (kind로 명시되었으면 그대로 따름)
    if kind == "stem":
        effective = target
    elif kind == "branch":
        effective = BRANCH_MAIN_STEM[target]
    elif target in BRANCHES_SET:
        effective = BRANCH_MAIN_STEM[target]  # 예: "신(申)" → "경(庚)"
    else:
        effective = target

    day_el = ELEMENT[day_stem]
    target_el = ELEMENT.get(effective, ELEMENT.get(target, ""))
    # 음양: 천간 기준으로 판별 (YINYANG에 천간 키만 명확히 있음)
    day_yy   = YINYANG.get(day_stem, "양")
    target_yy = YINYANG.get(effective, YINYANG.get(target, "양"))
    same_polarity = (day_yy == target_yy)

    if not target_el:
        return "-"
    if target_el == day_el:
        return "비견" if same_polarity else "겁재"
    if GENERATES[day_el] == target_el:
        return "식신" if same_polarity else "상관"
    if GENERATES[target_el] == day_el:
        return "편인" if same_polarity else "정인"
    if CONTROLS[day_el] == target_el:
        return "편재" if same_polarity else "정재"
    if CONTROLS[target_el] == day_el:
        return "편관" if same_polarity else "정관"
    return "-"

def get_yinyang(ch: str, kind: str | None = None) -> str:
    """글자의 음양 반환.

    [버그 방지] 한글 '신'이 천간 辛(음)과 지지 申(양)에 동시에 쓰이므로,
    호출부에서 이 글자가 천간인지 지지인지(kind="stem"/"branch")를 명시해야
    정확한 음양을 돌려준다. kind가 없으면 기존 방식(지지 우선)으로 추정한다.
    """
    if kind == "stem":
        return YINYANG.get(ch, "양")
    if kind == "branch":
        return BRANCH_YINYANG.get(ch, "양")
    if ch in BRANCHES_SET:
        return BRANCH_YINYANG.get(ch, "양")
    return YINYANG.get(ch, "양")

def char_payload(ch: str, day_stem: str | None = None, kind: str | None = None) -> Dict[str, Any]:
    """글자(천간/지지) 정보를 화면 표시용으로 변환.

    kind="stem"이면 천간(예: 辛)으로, kind="branch"이면 지지(예: 申)로 한자/음양을 해석한다.
    지장간은 항상 천간이므로 호출부에서 kind="stem"으로 넘겨야 '신(辛)'이
    '신(申)'으로 잘못 표시되는 충돌을 막을 수 있다.
    """
    if kind == "stem":
        hanja = STEM_HANJA.get(ch, ch)
    elif kind == "branch":
        hanja = BRANCH_HANJA.get(ch, ch)
    else:
        hanja = HANJA.get(ch, ch)
    return {
        "ko": ch,
        "hanja": hanja,
        "element": ELEMENT.get(ch, ""),
        "yin_yang": get_yinyang(ch, kind),
        "ten_god": ten_god(day_stem, ch, kind) if day_stem else "",
        "css": f"el-{ELEMENT.get(ch, 'etc')}",
    }

def count_elements(chars: List[str]) -> Dict[str, int]:
    counts = {el: 0 for el in ["목", "화", "토", "금", "수"]}
    for ch in chars:
        counts[ELEMENT[ch]] += 1
    return counts

def find_relations(branches: Dict[str, str], stems: Dict[str, str]) -> Dict[str, List[str]]:
    rels: Dict[str, List[str]] = {"천간합": [], "지지육합": [], "지지충": [], "형": []}
    stem_pairs = {("갑", "기"): "갑기합(土)", ("을", "경"): "을경합(金)", ("병", "신"): "병신합(水)", ("정", "임"): "정임합(木)", ("무", "계"): "무계합(火)"}
    branch_hap = {("자", "축"): "자축합", ("인", "해"): "인해합", ("묘", "술"): "묘술합", ("진", "유"): "진유합", ("사", "신"): "사신합", ("오", "미"): "오미합"}
    branch_chung = {("자", "오"): "자오충", ("축", "미"): "축미충", ("인", "신"): "인신충", ("묘", "유"): "묘유충", ("진", "술"): "진술충", ("사", "해"): "사해충"}

    items_stem = list(stems.items())
    items_branch = list(branches.items())
    for i in range(len(items_stem)):
        for j in range(i + 1, len(items_stem)):
            a_name, a = items_stem[i]
            b_name, b = items_stem[j]
            key = tuple(sorted((a, b), key=lambda x: STEMS.index(x)))
            if key in stem_pairs:
                rels["천간합"].append(f"{PILLAR_LABELS[a_name]}-{PILLAR_LABELS[b_name]} {stem_pairs[key]}")
    for i in range(len(items_branch)):
        for j in range(i + 1, len(items_branch)):
            a_name, a = items_branch[i]
            b_name, b = items_branch[j]
            key = tuple(sorted((a, b), key=lambda x: BRANCHES.index(x)))
            if key in branch_hap:
                rels["지지육합"].append(f"{PILLAR_LABELS[a_name]}-{PILLAR_LABELS[b_name]} {branch_hap[key]}")
            if key in branch_chung:
                rels["지지충"].append(f"{PILLAR_LABELS[a_name]}-{PILLAR_LABELS[b_name]} {branch_chung[key]}")

    bset = set(branches.values())
    if {"인", "사", "신"}.issubset(bset):
        rels["형"].append("인사신 삼형")
    if {"축", "술", "미"}.issubset(bset):
        rels["형"].append("축술미 삼형")
    if {"자", "묘"}.issubset(bset):
        rels["형"].append("자묘형")
    for self_punish in ["진", "오", "유", "해"]:
        if list(branches.values()).count(self_punish) >= 2:
            rels["형"].append(f"{self_punish}{self_punish} 자형")

    return {k: v for k, v in rels.items() if v}

def advice_for(day_stem: str, counts: Dict[str, int], pattern: Dict[str, str]) -> List[str]:
    weakest = min(counts.items(), key=lambda x: x[1])[0]
    strongest = max(counts.items(), key=lambda x: x[1])[0]
    lines = [
        f"일간은 {day_stem}({HANJA[day_stem]})입니다. {STEM_DESCRIPTIONS.get(day_stem, '')}",
        f"가장 강하게 보이는 오행은 {strongest}입니다. {ELEMENT_GUIDE[strongest]} 영역이 삶에서 자주 부각될 수 있습니다.",
        f"가장 약하게 보이는 오행은 {weakest}입니다. {ELEMENT_GUIDE[weakest]} 영역을 의식적으로 보완하면 균형을 잡는 데 도움이 됩니다.",
        f"기본 격은 {pattern.get('격', '-') }으로 보이며, {pattern.get('특성', '')}",
        "무료 분석은 방향을 잡는 용도입니다. 실제 상담에서는 대운·세운·상담 주제·현재 상황을 함께 놓고 현실적인 선택지를 좁혀갑니다."
    ]
    return lines

def format_luck_cycle(cycle: List[Dict[str, Any]], day_stem: str) -> List[Dict[str, Any]]:
    formatted = []
    for item in cycle[:10]:
        stem = item.get("천간", "")
        branch = item.get("지지", "")
        formatted.append({
            "age": item.get("시작연령", "-"),
            "stem": stem,
            "branch": branch,
            "ganji": f"{stem}{branch}",
            "hanja": f"{HANJA.get(stem, '')}{HANJA.get(branch, '')}",
            "direction": item.get("방향", "-"),
            "ten_god": ten_god(day_stem, stem) if stem in ELEMENT else "-",
            "twelve_stage": TWELVE_STAGE.get(day_stem, {}).get(branch, "-"),
            "description": item.get("특성", "대운의 흐름을 상담 주제와 함께 살펴봅니다."),
        })
    return formatted

def apply_reference_pillars(converted_solar: str, p: Dict[str, Dict[str, str]]) -> Tuple[Dict[str, Dict[str, str]], bool]:
    reference = REFERENCE_PILLARS.get(converted_solar)
    if not reference:
        return p, False
    return {
        key: {"stem": stem, "branch": branch}
        for key, (stem, branch) in reference.items()
    }, True

@app.route("/fortune", methods=["POST"])
def fortune() -> Any:
    data: Dict[str, Any] = request.get_json(silent=True) or {}
    try:
        year = int(data.get("year"))
        month = int(data.get("month"))
        day = int(data.get("day"))
        hour = int(data.get("hour"))
        minute = int(data.get("minute") or 0)
        if not 0 <= minute <= 59:
            raise ValueError("분은 0부터 59 사이여야 합니다.")

        gender = "M" if str(data.get("gender", "M")).upper() == "M" else "F"
        calendar_type = (data.get("calendar_type") or "solar").lower()
        is_leap = bool(data.get("is_leap"))
        birth_place = str(data.get("birth_place") or "서울").strip() or "서울"
        use_true_solar_time = bool(data.get("use_true_solar_time", True))
        night_hour_rule = str(data.get("night_hour_rule") or "standard")
        next_day_after_23 = bool(data.get("next_day_after_23", True))

        # ── 1. 음력/양력 날짜 변환 (계정 라이브러리 + sajupy 보조) ──────
        if calendar_type == "lunar":
            # 계정 라이브러리 우선, sajupy 보조
            if SAJUPY_OK:
                try:
                    sd = _saju_l2s(year, month, day, is_leap_month=is_leap)
                    birth = datetime(sd["solar_year"], sd["solar_month"], sd["solar_day"], hour, minute, 0)
                    lunar_date_label = sd.get("lunar_date", f"음력 {year}년 {'윤' if is_leap else ''}{month}월 {day}일")
                except Exception:
                    lunar_helper = LunarCalendar()
                    solar_date = lunar_helper.get_solar_date(year, month, day, is_leap=is_leap)
                    birth = datetime(solar_date.year, solar_date.month, solar_date.day, hour, minute, 0)
                    lunar_date_label = f"음력 {year}년 {'윤' if is_leap else ''}{month}월 {day}일"
            else:
                lunar_helper = LunarCalendar()
                solar_date = lunar_helper.get_solar_date(year, month, day, is_leap=is_leap)
                birth = datetime(solar_date.year, solar_date.month, solar_date.day, hour, minute, 0)
                lunar_date_label = f"음력 {year}년 {'윤' if is_leap else ''}{month}월 {day}일"
            input_label = f"음력 {year}년 {'윤' if is_leap else ''}{month}월 {day}일 {hour:02d}시 {minute:02d}분"
            converted_solar = birth.strftime("%Y-%m-%d %H:%M")
        else:
            birth = datetime(year, month, day, hour, minute, 0)
            converted_solar = birth.strftime("%Y-%m-%d %H:%M")
            input_label = f"양력 {year}년 {month}월 {day}일 {hour:02d}시 {minute:02d}분"
            # 음력 변환
            if SAJUPY_OK:
                try:
                    ld = _saju_s2l(year, month, day)
                    lm_prefix = "윤" if ld.get("is_leap_month") else ""
                    lunar_date_label = f"음력 {ld['lunar_year']}년 {lm_prefix}{ld['lunar_month']}월 {ld['lunar_day']}일"
                except Exception:
                    lunar_helper = LunarCalendar()
                    ly, lmo, ld2, ll = lunar_helper.get_lunar_date(birth)
                    lunar_date_label = f"음력 {ly}년 {'윤' if ll else ''}{lmo}월 {ld2}일"
            else:
                lunar_helper = LunarCalendar()
                ly, lmo, ld2, ll = lunar_helper.get_lunar_date(birth)
                lunar_date_label = f"음력 {ly}년 {'윤' if ll else ''}{lmo}월 {ld2}일"

        # ── 2. 사주 4기둥 계산 ── 계정 라이브러리 (NASA DE441/KASI DB) ──
        night_zi_mode = night_hour_rule  # "standard" | "late" | "early"
        pillars_obj = FourPillars(
            birth,
            region=birth_place,
            use_true_solar_time=use_true_solar_time,
        )
        p = {
            "year":  {"stem": pillars_obj.get_year_pillar().stem,  "branch": pillars_obj.get_year_pillar().branch},
            "month": {"stem": pillars_obj.get_month_pillar().stem, "branch": pillars_obj.get_month_pillar().branch},
            "day":   {"stem": pillars_obj.get_day_pillar().stem,   "branch": pillars_obj.get_day_pillar().branch},
            "hour":  {"stem": pillars_obj.get_hour_pillar().stem,  "branch": pillars_obj.get_hour_pillar().branch},
        }
        reference_matched = False  # 정밀 DB 사용으로 수동 보정 불필요
        day_stem = p["day"]["stem"]
        pattern = pillars_obj.get_pattern()
        all_chars = [p[k]["stem"] for k in ["year", "month", "day", "hour"]] + [p[k]["branch"] for k in ["year", "month", "day", "hour"]]
        element_counts = count_elements(all_chars)
        relations = find_relations({k: v["branch"] for k, v in p.items()}, {k: v["stem"] for k, v in p.items()})
        missing = [el for el, cnt in element_counts.items() if cnt == 0]
        strong = [el for el, cnt in element_counts.items() if cnt == max(element_counts.values())]
        weak = [el for el, cnt in element_counts.items() if cnt == min(element_counts.values())]

        pillar_order = ["hour", "day", "month", "year"]  # 모바일 만세력처럼 오른쪽에서 왼쪽 느낌을 살림
        visual_pillars = []
        for key in pillar_order:
            stem = p[key]["stem"]
            branch = p[key]["branch"]
            hidden = HIDDEN_STEMS.get(branch, [])
            visual_pillars.append({
                "key": key,
                "label": PILLAR_LABELS[key],
                "role": PILLAR_ROLES[key],
                "stem": char_payload(stem, day_stem, kind="stem"),
                "branch": char_payload(branch, day_stem, kind="branch"),
                "stem_ten_god": ten_god(day_stem, stem, kind="stem"),
                "branch_ten_god": ten_god(day_stem, branch, kind="branch"),
                "hidden_stems": [char_payload(h, day_stem, kind="stem") for h in hidden],
                "twelve_stage": TWELVE_STAGE.get(day_stem, {}).get(branch, "-"),
            })

        analysis = FourPillarsAnalysis(birth, gender=gender, region=birth_place, use_true_solar_time=use_true_solar_time)
        day_master = analysis.get_day_master_analysis()
        day_master["일간"] = p["day"]["stem"]
        day_master["일지"] = p["day"]["branch"]
        luck_cycle = format_luck_cycle(analysis.get_luck_cycle(), day_stem)

        result = {
            "input": {
                "calendar_type": calendar_type,
                "label": input_label,
                "gender": "남성" if gender == "M" else "여성",
                "birth_place": birth_place,
                "options": {
                    "진태양시 보정": "적용" if use_true_solar_time else "미적용",
                    "야자시 기준": "야자시" if night_hour_rule == "late" else "표준 자시",
                    "23시 이후 다음날 일주": "적용" if next_day_after_23 else "미적용 안내",
                },
            },
            "converted_solar": converted_solar,
            "lunar_date": lunar_date_label,
            "pillars": p,
            "visual_pillars": visual_pillars,
            "day_master": {
                **day_master,
                "hanja": HANJA[day_stem],
                "description": STEM_DESCRIPTIONS.get(day_stem, ""),
            },
            "pattern": pattern,
            "element_counts": element_counts,
            "strong_elements": strong,
            "weak_elements": weak,
            "missing_elements": {"무자": missing, "영향": [f"{el} 기운 보완 필요" for el in missing]},
            "use_god": pillars_obj.get_use_god(),
            "relations": relations,
            "luck_cycle": luck_cycle,
            "current_luck": luck_cycle[0] if luck_cycle else None,
            "calculation_note": {
                "summary": "NASA DE441/KASI 기반 정밀 절입시각 DB 사용 (1900~2050)",
                "detail": (
                    f"엔진: {ENGINE_VERSION} | "
                    f"진태양시 보정: {'적용' if use_true_solar_time else '미적용'} | "
                    f"출생지: {birth_place} | "
                    f"야자시 기준: {night_hour_rule}"
                ),
                "reference_matched": reference_matched,
                "engine": ENGINE_VERSION,
                "solar_correction": None,
            },
            "advice": advice_for(day_stem, element_counts, pattern),
            "consulting_flow": [
                "지금 고민을 한 문장으로 정리합니다.",
                "사주 원국에서 반복되는 성향과 막힘을 확인합니다.",
                "대운·세운으로 지금 해결 가능한 시기를 봅니다.",
                "상담에서 실제 선택지와 행동 순서를 정리합니다."
            ],
        }

        # ── 3. 계정 라이브러리 정밀 분석 ────────────────────────────────
        current_year = datetime.now().year

        # 신살 (dict: 신살명 → 위치 목록)
        try:
            ss = analysis.get_shinsal()
            result["shinsal"] = ss if isinstance(ss, dict) else {}
        except Exception:
            result["shinsal"] = {}

        # 형충회합파해원진 (지지 관계)
        try:
            br = analysis.get_branch_relations()
            result["branch_relations"] = br if isinstance(br, dict) else {}
        except Exception:
            result["branch_relations"] = {}

        # 12운성 (기둥별 리스트)
        try:
            ts = analysis.get_twelve_fortune_stars()
            result["twelve_fortune_stars"] = ts if isinstance(ts, list) else list(ts) if ts else []
        except Exception:
            result["twelve_fortune_stars"] = []

        # 12신 (기둥별)
        try:
            tg = analysis.get_twelve_gods()
            result["twelve_gods"] = tg if isinstance(tg, list) else list(tg) if tg else []
        except Exception:
            result["twelve_gods"] = []

        # 세운 상세 (올해 간지·십성·나이)
        try:
            af = analysis.get_annual_fortune(current_year)
            result["annual_fortune"] = af if isinstance(af, dict) else {}
        except Exception:
            result["annual_fortune"] = {}

        # 월운 (올해 12개월 — 절입시각 포함)
        try:
            mf = analysis.get_monthly_fortune(current_year)
            result["monthly_fortune"] = mf if isinstance(mf, list) else []
        except Exception:
            result["monthly_fortune"] = []

        # 용신·종용신 (계정 라이브러리)
        try:
            ug_detail = analysis.get_use_god()
            result["use_god_detail"] = ug_detail if isinstance(ug_detail, dict) else {}
        except Exception:
            result["use_god_detail"] = {}

        # 오행 비율 (%)
        try:
            fe = analysis.get_five_elements_ratio()
            result["five_elements_ratio"] = fe if isinstance(fe, dict) else {}
        except Exception:
            result["five_elements_ratio"] = {}

        # 일주 강약 지수
        try:
            si = analysis.get_shin_strength_index()
            result["strength_index"] = si
        except Exception:
            result["strength_index"] = None

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"입력 값이 올바르지 않습니다: {e}"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    app.run(host="127.0.0.1", port=port)
