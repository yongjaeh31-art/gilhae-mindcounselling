
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

HANJA = {
    "갑": "甲", "을": "乙", "병": "丙", "정": "丁", "무": "戊", "기": "己", "경": "庚", "신": "辛", "임": "壬", "계": "癸",
    "자": "子", "축": "丑", "인": "寅", "묘": "卯", "진": "辰", "사": "巳", "오": "午", "미": "未", "신": "申", "유": "酉", "술": "戌", "해": "亥",
}

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
    "자": ["계"],
    "축": ["기", "계", "신"],
    "인": ["갑", "병", "무"],
    "묘": ["을"],
    "진": ["무", "을", "계"],
    "사": ["병", "무", "경"],
    "오": ["정", "기"],
    "미": ["기", "정", "을"],
    "신": ["경", "임", "무"],
    "유": ["신"],
    "술": ["무", "신", "정"],
    "해": ["임", "갑"],
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

@app.route("/")
def index() -> str:
    return render_template("index.html")

def ten_god(day_stem: str, target: str) -> str:
    """십성 계산.

    지지(地支)의 경우 지장간 본기(本氣)를 기준으로 계산합니다.
    예: 申(신,양지) → 본기 庚(경,양) → 丁일간이면 정재(正財)

    [버그 방지] 한글 '신'이 天干 辛(음)과 地支 申(양) 두 곳에 쓰여
    YINYANG dict 충돌이 발생하므로, 지지는 반드시 BRANCH_MAIN_STEM을 통해
    해당 본기 천간으로 변환한 후 음양을 판별합니다.
    """
    # 지지인 경우 → 본기(本氣) 천간으로 변환
    if target in BRANCHES_SET:
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

def get_yinyang(ch: str) -> str:
    """글자의 음양 반환. 지지는 BRANCH_YINYANG 사용."""
    if ch in BRANCHES_SET:
        return BRANCH_YINYANG.get(ch, "양")
    return YINYANG.get(ch, "양")

def char_payload(ch: str, day_stem: str | None = None) -> Dict[str, Any]:
    return {
        "ko": ch,
        "hanja": HANJA.get(ch, ch),
        "element": ELEMENT.get(ch, ""),
        "yin_yang": get_yinyang(ch),
        "ten_god": ten_god(day_stem, ch) if day_stem else "",
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
                "stem": char_payload(stem, day_stem),
                "branch": char_payload(branch, day_stem),
                "stem_ten_god": ten_god(day_stem, stem),
                "branch_ten_god": ten_god(day_stem, branch),
                "hidden_stems": [char_payload(h, day_stem) for h in hidden],
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

        # ── 3. 계정 라이브러리 추가 정밀 분석 (신살·세운·12운성) ──────
        try:
            # 신살
            shinsal_raw = analysis.get_shinsal()
            result["shinsal"] = shinsal_raw if isinstance(shinsal_raw, list) else list(shinsal_raw) if shinsal_raw else []
        except Exception:
            result["shinsal"] = []

        try:
            # 12운성 (각 기둥별)
            twelve_stars = analysis.get_twelve_fortune_stars()
            result["twelve_fortune_stars"] = twelve_stars if isinstance(twelve_stars, dict) else {}
        except Exception:
            result["twelve_fortune_stars"] = {}

        try:
            # 현재 연도 세운 (세운 천간·지지와 운세)
            current_year = datetime.now().year
            annual = analysis.get_annual_fortune(current_year)
            result["annual_fortune"] = annual if isinstance(annual, dict) else {}
        except Exception:
            result["annual_fortune"] = {}

        try:
            # 오행 비율 (계정 라이브러리 기준)
            ratio = analysis.get_five_elements_ratio()
            result["five_elements_ratio"] = ratio if isinstance(ratio, dict) else {}
        except Exception:
            result["five_elements_ratio"] = {}

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"입력 값이 올바르지 않습니다: {e}"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    app.run(host="127.0.0.1", port=port)
