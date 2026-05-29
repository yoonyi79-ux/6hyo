import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
import os
import io
import re
import base64
import json
import urllib.parse
from datetime import date, datetime
import pytz
from PIL import Image
from dotenv import load_dotenv
import httpx
from lectures import LECTURES, LECTURE_TITLES, QUIZZES
from style import inject_css, HERO_HTML

load_dotenv()

st.set_page_config(
    page_title="육효의 세계",
    page_icon="☯",
    layout="centered",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

# ──────────────────────────────────────────────
# Auth & Rate Limit 설정
# ──────────────────────────────────────────────
AUTH_ENABLED: bool = "GOOGLE_CLIENT_ID" in st.secrets
DAILY_LIMIT: int = 3

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


# ──────────────────────────────────────────────
# Google OAuth 헬퍼 (st.login() 미사용)
# ──────────────────────────────────────────────
def _make_google_login_url() -> str:
    params = urllib.parse.urlencode({
        "client_id":     st.secrets["GOOGLE_CLIENT_ID"],
        "redirect_uri":  st.secrets.get("REDIRECT_URI", ""),
        "response_type": "code",
        "scope":         "openid email profile",
        "prompt":        "select_account",
    })
    return f"{GOOGLE_AUTH_URL}?{params}"


def _handle_oauth_callback() -> None:
    """URL의 code 파라미터를 토큰으로 교환 → session_state에 저장 → rerun."""
    code = st.query_params.get("code", "")
    if not code:
        return
    try:
        resp = httpx.post(
            GOOGLE_TOKEN_URL,
            data={
                "code":          code,
                "client_id":     st.secrets["GOOGLE_CLIENT_ID"],
                "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                "redirect_uri":  st.secrets.get("REDIRECT_URI", ""),
                "grant_type":    "authorization_code",
            },
            timeout=10,
        )
        token_data = resp.json()
        id_token = token_data.get("id_token", "")
        if id_token:
            payload = id_token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            user_info = json.loads(base64.urlsafe_b64decode(payload))
            email = user_info.get("email", "")
            name  = user_info.get("name", "")
            if email:
                st.session_state["auth_email"] = email
                st.session_state["auth_name"]  = name
    except Exception:
        pass
    st.query_params.clear()
    st.rerun()


def get_current_email() -> str:
    """로그인된 이메일 반환. 없으면 빈 문자열."""
    if "auth_email" in st.session_state:
        return st.session_state["auth_email"]
    if "code" in st.query_params:
        _handle_oauth_callback()   # rerun 발생 → 이후 코드 실행 안 됨
    return ""


def _logout():
    st.session_state.pop("auth_email", None)
    st.session_state.pop("auth_name", None)
    st.rerun()


# ──────────────────────────────────────────────
# API 키 헬퍼
# ──────────────────────────────────────────────
def _get_api_key() -> str:
    """Streamlit Secrets → 환경변수 순서로 Gemini API 키 반환.
    여러 접근 방식을 순차 시도해 최대한 안정적으로 읽는다."""
    # 방법 1: .get() — KeyError를 피하는 가장 안전한 방법
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key and str(key).strip():
            return str(key).strip()
    except Exception:
        pass
    # 방법 2: 딕셔너리 직접 접근
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key and str(key).strip():
            return str(key).strip()
    except Exception:
        pass
    # 방법 3: getattr 접근 (섹션 없는 최상위 키)
    try:
        key = getattr(st.secrets, "GEMINI_API_KEY", "")
        if key and str(key).strip():
            return str(key).strip()
    except Exception:
        pass
    # 방법 4: 환경변수 폴백
    return os.getenv("GEMINI_API_KEY", "").strip()


# ──────────────────────────────────────────────
# 사용자 정보 바 (window.parent DOM에 JS로 주입)
# ──────────────────────────────────────────────
def _render_user_bar(email: str, is_owner: bool, remaining: int):
    """Streamlit 상단 헤더 영역에 이름·뱃지·로그아웃을 오버레이로 렌더링.
    st.markdown() position:fixed는 Streamlit CSS stacking context에 갇히므로
    components.html()로 window.parent.document.body에 직접 DOM 삽입한다."""
    if not AUTH_ENABLED or not email:
        return
    name = st.session_state.get("auth_name", "") or email.split("@")[0]

    if is_owner:
        badge_html = (
            "<span style='background:#ffd803;border:2px solid #272343;border-radius:7px;"
            "padding:3px 9px;font-weight:700;font-size:13px;color:#272343;"
            "white-space:nowrap;line-height:1.5;'>✨ 무제한</span>"
        )
    elif remaining > 0:
        badge_html = (
            f"<span style='background:#e3f6f5;border:2px solid #272343;border-radius:7px;"
            f"padding:3px 9px;font-weight:700;font-size:13px;color:#272343;"
            f"white-space:nowrap;line-height:1.5;'>오늘 {remaining}회 남음</span>"
        )
    else:
        badge_html = (
            "<span style='background:#fee2e2;border:2px solid #dc2626;border-radius:7px;"
            "padding:3px 9px;font-weight:700;font-size:13px;color:#dc2626;"
            "white-space:nowrap;line-height:1.5;'>오늘 사용완료</span>"
        )

    inner_html = (
        f"<span style='font-weight:700;color:#272343;font-size:14px;"
        f"white-space:nowrap;'>👤 {name}</span>"
        f"<span style='color:#6b7280;font-size:12px;white-space:nowrap;"
        f"margin:0 4px;'>({email})</span>"
        f"{badge_html}"
        f"<a href='?logout=1' style='display:inline-block;background:#272343;"
        f"color:#ffd803;border:2px solid #272343;border-radius:8px;"
        f"padding:4px 10px;font-weight:700;font-size:13px;text-decoration:none;"
        f"white-space:nowrap;box-shadow:3px 3px 0 #bae8e8;margin-left:4px;"
        f"'>로그아웃</a>"
    )

    # json.dumps → JS 문자열 리터럴에 안전하게 임베드
    inner_js = json.dumps(inner_html)

    components.html(
        f"""<script>
(function(){{
    try {{
        var old = window.parent.document.getElementById('hyo-topbar');
        if (old) old.remove();
        var bar = window.parent.document.createElement('div');
        bar.id = 'hyo-topbar';
        bar.style.cssText = [
            'position:fixed', 'top:0', 'right:0', 'height:58px',
            'display:flex', 'align-items:center', 'gap:8px', 'padding:0 18px',
            'z-index:2147483647', 'box-sizing:border-box',
            "font-family:-apple-system,'Malgun Gothic','Apple SD Gothic Neo',sans-serif"
        ].join(';') + ';';
        bar.innerHTML = {inner_js};
        window.parent.document.body.appendChild(bar);
    }} catch(e) {{
        console.warn('[hyo] topbar inject failed:', e);
    }}
}})();
</script>""",
        height=0,
    )


# ──────────────────────────────────────────────
# Session State 초기화
# ──────────────────────────────────────────────
def _init():
    defaults = {
        "page":         "main",   # "main" | "lecture"
        "cur_lec":      1,        # 1 ~ 7
        "content_done": set(),    # 강의 본문 완료한 강 번호들
        "quiz_done":    set(),    # 퀴즈까지 완료한 강 번호들
        "scroll_top":   False,    # 강의 이동 시 화면 상단 스크롤 트리거
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ──────────────────────────────────────────────
# Supabase 헬퍼
# ──────────────────────────────────────────────
@st.cache_resource
def _get_supabase():
    try:
        from supabase import create_client
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        return None


_KST = pytz.timezone("Asia/Seoul")

def _today_kst() -> str:
    """한국 시간(KST) 기준 오늘 날짜 — YYYY-MM-DD."""
    return datetime.now(_KST).date().isoformat()


def get_today_count(email: str) -> int:
    """오늘 사용 횟수 반환 — session_state 캐시 우선."""
    cache_key = f"usage_{email}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    count = 0
    try:
        sb = _get_supabase()
        if sb is not None and email:
            today = _today_kst()
            res = (
                sb.table("usage")
                .select("count")
                .eq("email", email)
                .eq("use_date", today)
                .execute()
            )
            count = res.data[0]["count"] if res.data else 0
    except Exception:
        count = 0
    st.session_state[cache_key] = count
    return count


def increment_usage(email: str):
    """사용 횟수 +1 기록 (실패해도 앱은 계속 동작)."""
    try:
        sb = _get_supabase()
        today = _today_kst()
        existing = (
            sb.table("usage")
            .select("count")
            .eq("email", email)
            .eq("use_date", today)
            .execute()
        )
        if existing.data:
            new_count = existing.data[0]["count"] + 1
            sb.table("usage").update({"count": new_count}).eq(
                "email", email
            ).eq("use_date", today).execute()
        else:
            new_count = 1
            sb.table("usage").insert(
                {"email": email, "use_date": today, "count": 1}
            ).execute()
        # 세션 캐시 갱신
        st.session_state[f"usage_{email}"] = new_count
    except Exception:
        pass


def save_progress(email: str):
    """학습 진도(quiz_done, cur_lec)를 Supabase에 저장."""
    try:
        sb = _get_supabase()
        if sb and email and email not in ("local@dev", ""):
            sb.table("progress").upsert({
                "email": email,
                "quiz_done": sorted(list(st.session_state.quiz_done)),
                "cur_lec": int(st.session_state.cur_lec),
            }).execute()
    except Exception:
        pass


def load_progress(email: str):
    """Supabase에서 학습 진도 로드 → session_state 갱신 (세션당 1회)."""
    try:
        sb = _get_supabase()
        if sb and email and email not in ("local@dev", ""):
            res = (
                sb.table("progress")
                .select("quiz_done,cur_lec")
                .eq("email", email)
                .execute()
            )
            if res.data:
                row = res.data[0]
                st.session_state.quiz_done = set(row.get("quiz_done") or [])
                saved_lec = int(row.get("cur_lec") or 1)
                # 저장된 강의 번호가 현재보다 앞서 있을 때만 복원
                if st.session_state.cur_lec == 1 and saved_lec > 1:
                    st.session_state.cur_lec = saved_lec
    except Exception:
        pass


# ──────────────────────────────────────────────
# 로그인 페이지
# ──────────────────────────────────────────────
def _render_login_page():
    inject_css()
    st.markdown(HERO_HTML, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            "<div style='text-align:center;padding:24px 0 16px;'>"
            "<div style='font-size:2.8rem;line-height:1;'>🔐</div>"
            "<div style='font-family:Montserrat,sans-serif;font-weight:800;"
            "font-size:1.25rem;color:#272343;margin:12px 0 8px;'>"
            "로그인이 필요합니다</div>"
            "<div style='font-size:0.93rem;color:#2d334a;line-height:1.75;'>"
            "Google 계정으로 로그인하면<br>"
            "매일 <strong>3회</strong> 무료로 육효 해석을 이용할 수 있습니다.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            st.link_button(
                "🔑  Google 계정으로 시작하기",
                url=_make_google_login_url(),
                use_container_width=True,
            )
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.caption(
            "로그인 정보(이메일)는 하루 사용 횟수 확인에만 쓰이며, 외부에 공유되지 않습니다."
        )

    st.stop()


# ──────────────────────────────────────────────
# 시스템 프롬프트
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """
당신은 육효(六爻) 전문 해석가입니다.
사용자가 육효 앱(도사폰 등) 화면 이미지와 질문을 제공하면,
이미지에서 육효 데이터를 정확히 읽고 일반인이 완전히 이해할 수 있는
쉽고 따뜻하고 상세한 한국어 해석을 제공합니다.

━━━━━━━━━━━━━━━━━━━━━━━━
📷  이미지에서 읽어야 할 정보
━━━━━━━━━━━━━━━━━━━━━━━━

도사폰 등 육효 앱 화면에는 보통 아래 정보가 표시됩니다:

[6개의 효 — 아래(1효=초효)에서 위(6효=상효)로]
각 효마다:
  - 육친: 兄(형제) / 孫(자손) / 財(처재) / 官(관귀) / 父(부모)
  - 지지(地支): 子丑寅卯辰巳午未申酉戌亥 중 하나
  - 천간(天干): 甲乙丙丁戊己庚辛壬癸 중 하나 (표시되는 경우)
  - 오행: 木火土金水
  - 世(세효 = 나) 또는 應(응효 = 상대) 표시
  - 동효(動爻) 여부: 빨간 빗금(×), 굵은 표시, 또는 "동" 표기
  - 변효(變爻): 동효가 변한 후의 육친·지지 (→ 오른쪽에 표시)
  - 십이포태(十二胞胎): 長生·沐浴·冠帶·臨官·帝旺·衰·病·死·墓·絶·胎·養

[보조 정보]
  - 월건(月建): 점을 친 달의 지지
  - 일진(日辰): 점을 친 날의 지지
  - 공망(空亡): 사기·속임수의 기운이 있는 두 글자 (예: 戌亥 공망)
  - 월파(月破): 월건과 충이 되는 효 표시
  - 파란 글자 = 월(月)의 영향 / 빨간 글자 = 일(日)의 영향

이미지를 최대한 꼼꼼히 읽어서 각 효의 정보를 파악하세요.
읽기 어려운 부분이 있으면 솔직하게 밝히고, 읽은 정보로 최선을 다해 해석하세요.

━━━━━━━━━━━━━━━━━━━━━━━━
📚  육효 핵심 이론
━━━━━━━━━━━━━━━━━━━━━━━━

## 1. 육친(六親) — 등장인물과 역할

| 육친 | 부르는 이름 | 핵심 의미 | 좋을 때 | 나쁠 때 |
|------|-----------|----------|---------|---------|
| 兄(형제) | 돈 쓰는 글자 | 동료·경쟁자·분산 | 협력·동업 | 돈 나감·손재수·라이벌 |
| 孫(자손) | 만사형통 글자 | 해결사·복·치유 | 모든 걱정 해소·약·의사 | 부모효만 못 고침 |
| 財(처재) | 돈·결과 글자 | 재물·결과물 | 수익·계약·선물·여자(남성 관점) | 없음(기본 좋음) |
| 官(관귀) | 양면성 글자 | 통제·압박·명예 | 직장·승진·남편(여성 관점) | 병·소송·압박·귀신 |
| 父(부모) | 우울·문서 글자 | 문서·지식·보호 | 계약·시험합격·집 | 우울·걱정·막힘 |

## 2. 세효(世)와 응효(應)

- 세효(世) = 나 / 질문하는 사람
- 응효(應) = 상대방 / 외부환경

세효가 강하면 내가 주도권. 응효가 강하면 상황이 외부에 달려 있음.

## 3. 질문 유형별 용신(用神) 선택

| 질문 유형 | 용신 |
|----------|------|
| 돈·재물·사업수익 | 財(처재효) |
| 취업·직장·승진 | 官(관귀효) |
| 시험·계약·문서·부동산 | 父(부모효) |
| 연애·재회 (남성 질문자) | 財(처재효) |
| 연애·재회 (여성 질문자) | 官(관귀효) |
| 건강·질병 | 官(관귀효) = 병, 孫(자손효) = 약·의사 |
| 소송·고소 | 官(관귀효) |
| 임신·자녀 | 孫(자손효) |
| 투자·주식 | 財(처재효) |

## 4. 동효(動爻) — 사건의 핵심

동효 = 움직이는 효 = 진짜 사건이 일어나는 곳

- 동효가 용신을 생(生) 하면 → 좋은 방향
- 동효가 용신을 극(克) 하면 → 방해·문제
- 동효 없음 → 변화 없이 조용한 상태

동효의 강도 판단:
- 파란 글자(월령의 생·합)를 받은 동효 → 힘이 강함
- 빨간 글자(일진의 생·합)를 받은 동효 → 힘이 강함

변효(變爻) 해석 원칙:
- 변효는 오직 본효(동효)를 생하는지 극하는지만 분석
- 회두생(回頭生): 변효가 본효를 생해줌 → 처음 힘들다가 결국 좋아짐
- 회두극(回頭克): 변효가 본효를 극함 → 발등 찍히는 상황, 매우 나쁨
- 본효가 변효를 극하는 경우: 변효는 본효에 아무 영향 없음 (무시)
- 진신(進神): 같은 오행의 더 강한 글자로 변함 → 기세가 점점 강해짐
- 퇴신(退神): 같은 오행의 더 약한 글자로 변함 → 기세가 꺾임

## 5. 오행 상생·상극

상생: 木(목)→火(화)→土(토)→金(금)→水(수)→木(목)
상극: 木극土 / 土극水 / 水극火 / 火극金 / 金극木

오행-지지 대응:
- 木(목): 寅(인)·卯(묘)  /  火(화): 巳(사)·午(오)
- 土(토): 辰(진)·戌(술)·丑(축)·未(미)
- 金(금): 申(신)·酉(유)  /  水(수): 子(자)·亥(해)

## 6. 5대 비지(非支) — 특수 상태 판독

| 상태 | 발생 조건 | 현실 번역 |
|------|---------|----------|
| 공망(空亡) | 월건에서 정해진 두 글자에 해당 | 사기·속임수·말뿐·약속 펑크·실체 없음 |
| 월파(月破) | 월건이 해당 효를 충(冲) | 이달만큼은 절대 안 됨 |
| 암동(暗動) | 정효(靜爻)인데 일진이 충함 | 겉은 조용, 속으로 몰래 진행 중 |
| 묘고(墓庫) | 十二胞胎 중 '墓'에 해당 | 갇혀서 못 나옴·답답함·연락두절 |
| 복신(伏神) | 공망·월파·암동으로 동하게 됨 | 드러나지 않은 숨은 진실이 발동 |

합(合): 결합·묶임 → 좋으면 계약, 나쁘면 집착·구속
충(沖): 깨짐·이동 → 좋으면 돌파, 나쁘면 파탄·이별
형(刑): 스트레스·법적 마찰

## 7. 십이포태(十二胞胎) — 효의 생명력

각 효가 월건·일진과의 관계로 결정되는 생명 단계.
이 단계로 해당 효가 현재 '힘이 넘치는지' vs '죽어가는지'를 판단한다.

6길신(吉神) — 힘이 있는 상태:
| 단계 | 한자 | 현실 번역 |
|------|------|----------|
| 養(양) | 태어나기 전 양육 | 준비·성장 직전, 아직 기회 있음 |
| 長生(장생) | 막 태어남 | 새로운 시작·신선한 에너지 |
| 沐浴(목욕) | 씻기 단계 | 변동·불안정하지만 활기참 |
| 冠帶(관대) | 성인식·취직 | 돈·월급·녹봉의 단계, 재물운 |
| 臨官(임관) | 직장 합격 | 관직·직장 합격·도전 성공 |
| 帝旺(제왕) | 최전성기 | 가장 강함·주도권 완전 장악 |

6살신(殺神) — 힘이 약한 상태:
| 단계 | 한자 | 현실 번역 |
|------|------|----------|
| 衰(쇠) | 쇠퇴 시작 | 전성기 지남·서서히 힘 빠짐 |
| 病(병) | 병든 상태 | 문제·장애·건강 이상 |
| 死(사) | 죽음 | 완전히 막힘·기운 없음 |
| 墓(묘) | 묘지 | 갇힘·연락두절·잠수·막힘 |
| 絶(절) | 끊어짐 | 인연 단절·포기·종료 |
| 胎(태) | 잉태 | 기본적으로 나쁨 (임신 점에서만 길) |

> 실전 적용: 용신이 帝旺·長生이면 강한 힘, 死·墓·絶이면 힘이 없는 상태.
> 세효가 6살신이면 내가 지쳐있거나 불리한 상황.

## 8. 효위(爻位) — 공간·환경 해석

각 효는 특정 공간/상황을 상징한다:

| 효위 | 상징 공간 | 현실 의미 |
|-----|---------|----------|
| 上爻(상효 6효) | 천신·하늘 영역 | 외국·타지·먼 곳·신의 영역 |
| 五爻(5효) | 도로·가족 영역 | 이동·가족 관계·사회적 위치 |
| 四爻(4효) | 대문 영역 | 외부와의 접점·관귀/귀신 영역 |
| 三爻(3효) | 현관문 영역 | 내외의 경계·귀신망상 영역 |
| 二爻(2효) | 안방·거실 | 가택효·동거·실질적 생활 공간 |
| 初爻(초효 1효) | 방바닥·부엌·터 | 가장 기초·터주·뿌리 |

## 9. 천간(天干) — 심리와 상황의 결 읽기

천간은 표면적 심리와 상황의 '색깔'을 드러낸다.

| 천간 | 오행 | 심리·상황 |
|------|------|----------|
| 甲·乙 | 木 | 새로운 시작·기획력·돌진·성장 욕구 |
| 丙·丁 | 火 | 화려함·감정 폭발·명예욕·급한 성격 |
| 戊·己 | 土 | 신용·타협·중재·안정·다소 느린 진행 |
| 庚·辛 | 金 | 결단력·냉정함·법적 공방·거래 |
| 壬·癸 | 水 | 물밑 작업·비밀 계획·유연함·의심 |

특수 규칙:
- 庚(경) + 문서효(父) = 소송·법적 분쟁 경고
- 천간합(甲己·乙庚·丙辛·丁壬·戊癸): 겉은 싸우나 속으로 타협 중
- 천간충(甲庚·乙辛·丙壬·丁癸·戊甲): 명분 충돌·명예 손상

지지 吉 + 천간 凶 조합: 결과는 얻지만 과정이 힘들고 구설수 있음
천간 吉 + 지지 凶 조합: 명분은 좋으나 실속이 없음

## 10. 특수 괘 구조 — 판의 성격 진단

이미지에서 전체 괘의 구조를 파악해 아래 특수 괘 여부를 반드시 확인하라:

| 괘 이름 | 조건 | 핵심 의미 |
|--------|------|----------|
| 육충괘(六沖卦) | 1·4효, 2·5효, 3·6효가 모두 충(冲) | 속전속결·분산·결별·빠른 결론 |
| 육합괘(六合卦) | 마주보는 효가 모두 합(合) | 끈끈한 묶임·장기화·집착 |
| 복음괘(伏吟卦) | 동효의 오행 = 본효의 오행 | 진퇴양난·제자리걸음·막막함 |
| 반음괘(反吟卦) | 변효 지지 = 본효 지지의 충 | 판이 계속 번복·막판 뒤집힘 |
| 유혼괘(遊魂卦) | 특정 공식 구조 8괘 | 방황·중심 상실·이탈 충동 |
| 귀혼괘(歸魂卦) | 유혼괘와 짝을 이루는 8괘 | 제자리 복귀·정착·회귀 |

## 11. 실전 해석 순서 (강화판)

1. 질문 확인 → 용신 선택
2. 특수 괘 구조 먼저 파악 (육충/육합/복음/반음/유혼/귀혼)
3. 세효 상태 (십이포태 단계, 공망인가)
4. 용신 상태 (십이포태 단계, 왕성한가·월파·공망인가)
5. 동효 확인 및 용신과의 생극 관계
6. 천간 분석 (어떤 색깔의 사건인가)
7. 5대 비지 체크 (공망·월파·암동·묘고·복신)
8. 타이밍 도출 (출공일·충실일·충개일·제복일)
9. 개운 방향 도출 (방위·인물·타이밍)
10. 현실 언어로 번역

━━━━━━━━━━━━━━━━━━━━━━━━
📝  해석 출력 형식 (반드시 이 형식 사용)
━━━━━━━━━━━━━━━━━━━━━━━━

---

## 【 괘반 정보 요약 】

- 월건 / 일진: [값 또는 "확인 어려움"]
- 공망: [해당 지지 또는 "없음"]
- 세효(나): [효 위치] [육친] [지지] — [십이포태 단계] [상태]
- 응효(상대): [효 위치] [육친] [지지] — [십이포태 단계] [상태]
- 동효: [몇 효, 육친, 지지] → 변효: [변화 결과]
- 용신: [육친] — [선택 이유]
- 특수 괘 구조: [해당 괘 또는 "없음"]

---

## 【 핵심 판단 】

[결론을 먼저 한 줄로]

---

## 【 상세 해석 】

### 지금 내 상황은?
(세효 상태와 십이포태 단계를 비유로 설명)

### 원하는 것(용신)의 상태는?
(용신의 십이포태 단계와 강약을 비유로 설명)

### 어떤 사건이 일어나고 있나요?
(동효가 없으면 "조용한 상태". 있으면:
① 동효 육친이 무엇인지
② 동효가 용신을 생하는지 극하는지
③ 동효의 강도: 파란·빨간 생합 표시
④ 변효 회두생/회두극·진신/퇴신 여부
⑤ 천간이 드러내는 심리와 상황의 색깔
⑥ 종합 스토리)

### 특별히 주의할 것
(공망·월파·합·충·암동·묘고·복신·특수괘 구조가 있으면 설명. 없으면 생략)

---

## 【 십이포태 진단 】

(용신과 세효의 십이포태 단계를 구체적으로 명시하고,
그것이 현재 상황에 어떤 의미인지 일상 언어로 설명)

---

## 【 실질적인 조언 】

1. ...
2. ...
3. ...

---

## 【 타이밍 】

(언제쯤 결과가 나타날지.
가능하면 아래 기준으로 구체적 날짜/월 유형 제시:
- 출공(出空): 공망인 글자의 날/달이 오면 현실화
- 충실(沖實): 공망을 충하는 날/달이 오면 더 빨리 열림
- 충개(沖開): 합으로 묶인 효를 충하는 날/달이 오면 풀림
- 제복(制伏): 흉신을 극하는 오행의 날/달이 오면 전환점)

---

## 【 개운(開運) 방향 】

(운을 여는 구체적 행동 지침. 아래 3가지로 나눠 제시:)

방위: [도움이 되는 방향 — 지지별 방위 공식:
子=북, 丑寅=동북, 卯=동, 辰巳=동남, 午=남, 未申=남서, 酉=서, 戌亥=북서]

인물(띠): [도움이 될 띠 — 용신을 생하거나 흉신을 제압하는 오행의 띠.
육합쌍(자축/인해/묘술/진유/사신/오미)·삼합(申子辰/亥卯未/寅午戌/巳酉丑) 활용]

행동: [공망이면 솔직하게 터놓기, 묘고이면 직접 만남 시도,
월파이면 이달은 잠시 보류, 암동이면 먼저 연락해보기 등]

---

## 【 한 줄 요약 】

> [가장 쉬운 말로 딱 한 문장]

---

*⚠️ 육효는 현재 에너지 흐름을 읽는 도구입니다. 최종 결정은 본인의 의지와 행동에 달려 있습니다.*

━━━━━━━━━━━━━━━━━━━━━━━━
🎨  해석 스타일 필수 준수
━━━━━━━━━━━━━━━━━━━━━━━━

1. 전문용어는 반드시 괄호로 번역
   예: "세효(나를 나타내는 자리)가 공망(사기·속임수의 기운)이어서..."

2. 비유를 풍부하게
   예: "관귀가 세효를 극한다" → "마치 직장 상사가 하루 종일 압박을 넣는 것처럼..."

3. 스토리 흐름: 지금 → 중간 → 결말

4. 따뜻하고 솔직하게: 나쁜 결과도 부드럽게, 대안 조언 포함

5. 충분히 상세하게 (해석 본문 최소 800자 이상)

6. 개운(開運) 섹션은 반드시 실질적이고 행동 가능한 내용으로 작성

7. 십이포태 단계는 해당 효마다 6길신/6살신 중 어느 쪽인지 명확히 판단

8. ** 또는 __ 또는 ≪ ≫ 같은 강조 기호를 절대 사용하지 않는다
   강조가 필요한 경우도 일반 텍스트로 자연스럽게 서술한다
   단, 섹션 제목(## 【 】)은 그대로 유지한다
"""


# ──────────────────────────────────────────────
# Gemini API 호출
# ──────────────────────────────────────────────
def call_gemini(uploaded_file, question: str, api_key: str, yongshin: str = "auto") -> str:
    client = genai.Client(api_key=api_key)
    uploaded_file.seek(0)
    image = Image.open(io.BytesIO(uploaded_file.read()))

    yongshin_hint = ""
    if yongshin != "auto":
        yongshin_hint = (
            f"\n\n[중요] 용신(用神)을 질문자가 직접 지정했습니다: {yongshin}. "
            "이 육친을 용신으로 삼아 해석해주세요. "
            "용신 선택 이유 항목에도 '질문자 직접 지정'으로 명시해주세요."
        )

    user_text = (
        f"질문: {question}{yongshin_hint}\n\n"
        "위 육효 앱 화면 이미지를 정확히 읽고, 이 질문에 대한 해석을 작성해 주세요."
    )

    response = client.models.generate_content(
        model="models/gemini-3.5-flash",
        contents=[image, user_text],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=65536,
        ),
    )
    # 잘림 감지 — finish_reason 이 MAX_TOKENS 이면 경고 추가
    try:
        reason = response.candidates[0].finish_reason
        if hasattr(reason, "name") and reason.name == "MAX_TOKENS":
            return response.text + "\n\n---\n⚠️ *응답이 최대 길이에 도달해 일부 내용이 생략되었을 수 있습니다.*"
    except Exception:
        pass
    return response.text


# ──────────────────────────────────────────────
# 퀴즈
# ──────────────────────────────────────────────
def _lec_quiz_key(lec_num: int, q_idx: int) -> str:
    return f"q_{lec_num}_{q_idx}"


def _saved_answer_key(lec_num: int, q_idx: int) -> str:
    return f"saved_q_{lec_num}_{q_idx}"


def show_quiz(lec_num: int) -> bool:
    """퀴즈 렌더링. True = 제출 완료."""
    lec_key = f"{lec_num}강"
    quizzes = QUIZZES.get(lec_key, [])
    if not quizzes:
        return True

    st.divider()
    st.markdown(
        "<div style='background:#e3f6f5;border:2px solid #272343;border-radius:16px;"
        "padding:16px 22px;margin-bottom:16px;box-shadow:4px 4px 0 #bae8e8;'>"
        "<span style='font-family:Montserrat,sans-serif;font-weight:800;"
        "font-size:1.0rem;color:#272343;'>📝 확인 퀴즈</span>"
        "<span style='font-size:0.84rem;color:#2d334a;margin-left:10px;'>"
        "모두 선택 후 제출하세요</span></div>",
        unsafe_allow_html=True,
    )

    submitted = lec_num in st.session_state.quiz_done
    all_answered = True

    for i, quiz in enumerate(quizzes):
        st.markdown(f"**Q{i + 1}.** {quiz['question']}")

        q_key = _lec_quiz_key(lec_num, i)
        sv_key = _saved_answer_key(lec_num, i)
        correct_label = quiz["options"][quiz["answer"]]

        if submitted:
            saved = st.session_state.get(sv_key)
            for opt in quiz["options"]:
                if opt == correct_label:
                    st.markdown(
                        f"<div style='color:#059669;font-weight:600;"
                        f"padding:3px 0 3px 4px;'>✅ {opt}</div>",
                        unsafe_allow_html=True,
                    )
                elif opt == saved:
                    st.markdown(
                        f"<div style='color:#dc2626;font-weight:600;"
                        f"padding:3px 0 3px 4px;'>❌ {opt}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='color:#6b7280;"
                        f"padding:3px 0 3px 4px;'>○ {opt}</div>",
                        unsafe_allow_html=True,
                    )
            st.caption(f"💡 {quiz['explanation']}")
        else:
            sel = st.radio(
                label="보기",
                options=quiz["options"],
                index=None,
                key=q_key,
                label_visibility="collapsed",
            )
            if sel is None:
                all_answered = False

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # 제출 버튼
    if not submitted:
        _, mid, _ = st.columns([2, 1, 2])
        with mid:
            if st.button(
                "답안 제출",
                disabled=not all_answered,
                use_container_width=True,
                key=f"submit_quiz_{lec_num}",
            ):
                correct_count = 0
                for i, quiz in enumerate(quizzes):
                    selected = st.session_state.get(_lec_quiz_key(lec_num, i))
                    st.session_state[_saved_answer_key(lec_num, i)] = selected
                    if selected == quiz["options"][quiz["answer"]]:
                        correct_count += 1
                st.session_state[f"score_{lec_num}"] = correct_count
                st.session_state.quiz_done.add(lec_num)
                save_progress(st.session_state.get("auth_email", ""))
                st.rerun()
        return False

    score = st.session_state.get(f"score_{lec_num}", 0)
    total = len(quizzes)
    if score == total:
        st.success(f"🎉 {total}/{total} 전부 정답! 완벽합니다.")
    elif score >= round(total * 0.6):
        st.info(f"📊 {total}문제 중 {score}문제 정답. 잘 하셨어요!")
    else:
        st.warning(f"📊 {total}문제 중 {score}문제 정답. 강의를 다시 복습해보세요.")
    return True


# ──────────────────────────────────────────────
# 진도 계산
# ──────────────────────────────────────────────
def _max_unlocked() -> int:
    unlocked = 1
    for i in range(1, 12):
        if i in st.session_state.quiz_done:
            unlocked = min(i + 1, 11)
        else:
            break
    return unlocked


def _scroll_to_top():
    """강의 페이지 이동 시 화면 상단으로 스크롤."""
    components.html(
        """
        <script>
            (function() {
                try {
                    var selectors = [
                        'section.main',
                        '[data-testid="stAppViewContainer"] > section',
                        '[data-testid="stAppViewContainer"]',
                        '.main'
                    ];
                    for (var i = 0; i < selectors.length; i++) {
                        var el = window.parent.document.querySelector(selectors[i]);
                        if (el) { el.scrollTop = 0; break; }
                    }
                    window.parent.scrollTo({top: 0, behavior: 'instant'});
                } catch(e) {}
            })();
        </script>
        """,
        height=0,
    )


# ──────────────────────────────────────────────
# 다운로드 — 마크다운 → HTML 변환
# ──────────────────────────────────────────────
def _md_to_html(text: str) -> str:
    """마크다운 텍스트를 다운로드 카드용 인라인 HTML로 변환."""
    lines = text.split('\n')
    out = []
    for line in lines:
        stripped = line.strip()
        # HR
        if re.match(r'^-{3,}$', stripped):
            out.append('<hr>')
            continue
        # h2
        m = re.match(r'^## (.+)', line)
        if m:
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', m.group(1))
            out.append(f'<h2>{content}</h2>')
            continue
        # h3
        m = re.match(r'^### (.+)', line)
        if m:
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', m.group(1))
            out.append(f'<h3>{content}</h3>')
            continue
        # blockquote
        m = re.match(r'^> (.+)', line)
        if m:
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', m.group(1))
            out.append(f'<blockquote>{content}</blockquote>')
            continue
        # bullet list
        m = re.match(r'^[*\-] (.+)', line)
        if m:
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', m.group(1))
            out.append(f'<li style="margin:2px 0 2px 16px;">{content}</li>')
            continue
        # numbered list
        m = re.match(r'^\d+\. (.+)', line)
        if m:
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', m.group(1))
            out.append(f'<li style="margin:2px 0 2px 16px;">{content}</li>')
            continue
        # empty line
        if not stripped:
            out.append('<div style="height:5px"></div>')
            continue
        # normal paragraph
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        out.append(f'<p style="margin:4px 0;line-height:1.7;">{content}</p>')
    return '\n'.join(out)


def _render_download_button(question: str, result: str):
    """해석 결과를 이미지로 저장하는 버튼 (html2canvas)."""
    today_str = date.today().strftime("%Y%m%d")
    safe_q = re.sub(r'[\\/:"*?<>|\n\r]', '', question[:20]).strip().replace(' ', '_')
    filename = f"{today_str}_{safe_q}.png"

    result_html = _md_to_html(result)
    q_safe = (question
               .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
               .replace('\n', '<br>'))

    # HTML template — placeholder replacement avoids f-string issues with { } in result
    tmpl = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
body{margin:0;padding:8px;background:#fffffe;font-family:-apple-system,'Malgun Gothic','Apple SD Gothic Neo',sans-serif;font-size:13px;}
#card{position:absolute;left:-10000px;top:0;width:700px;padding:28px;background:#fffffe;box-sizing:border-box;}
.app-hdr{background:#272343;border-radius:14px;padding:14px 18px;margin-bottom:18px;}
.app-hdr-t{font-family:'Montserrat',sans-serif;font-weight:900;font-size:1.1rem;color:#ffd803;}
.app-hdr-s{font-size:0.77rem;color:#bae8e8;margin-top:3px;}
.q-box{background:#e3f6f5;border:2px solid #272343;border-radius:12px;padding:12px 16px;margin-bottom:16px;box-shadow:4px 4px 0 #bae8e8;}
.q-lbl{font-size:0.73rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px;}
.q-txt{font-weight:700;font-size:0.95rem;color:#272343;line-height:1.5;}
.res-box{background:#fffffe;border:2px solid #272343;border-radius:12px;padding:16px 20px;box-shadow:5px 5px 0 #bae8e8;font-size:0.85rem;color:#2d334a;line-height:1.72;}
#card h2{font-size:.93rem;font-weight:800;color:#272343;margin:14px 0 5px;}
#card h3{font-size:.85rem;font-weight:700;color:#272343;margin:10px 0 4px;}
#card p{margin:4px 0;line-height:1.7;}
#card hr{border:none;border-top:1px solid #e5e7eb;margin:10px 0;}
#card blockquote{border-left:3px solid #ffd803;padding:7px 12px;background:#fffde7;margin:8px 0;font-weight:600;color:#272343;}
#card strong{font-weight:700;color:#272343;}
.footer{margin-top:14px;text-align:center;font-size:.7rem;color:#9ca3af;}
#dl-btn{display:block;width:100%;padding:11px 0;background:#ffd803;color:#272343;font-weight:700;font-size:.93rem;border:2px solid #272343;border-radius:12px;cursor:pointer;box-shadow:4px 4px 0 #272343;font-family:inherit;transition:transform .1s,box-shadow .1s;}
#dl-btn:hover{transform:translate(-1px,-1px);box-shadow:5px 5px 0 #272343;}
#dl-btn:active{transform:translate(1px,1px);box-shadow:2px 2px 0 #272343;}
#dl-btn:disabled{background:#e5e7eb;color:#9ca3af;border-color:#d1d5db;box-shadow:none;cursor:default;}
</style></head>
<body>
<div id="card">
  <div class="app-hdr"><div class="app-hdr-t">☯ 육효의 세계</div><div class="app-hdr-s">AI 육효 해석 결과</div></div>
  <div class="q-box"><div class="q-lbl">질문</div><div class="q-txt">__QUESTION__</div></div>
  <div class="res-box">__RESULT__</div>
  <div class="footer">육효의 세계 · __TODAY__ · powered by Yi Yul</div>
</div>
<button id="dl-btn" onclick="downloadImg()">📥 이미지로 저장</button>
<script>
function downloadImg(){
  var btn=document.getElementById('dl-btn');
  btn.textContent='⏳ 이미지 생성 중...'; btn.disabled=true;
  html2canvas(document.getElementById('card'),{scale:2,useCORS:true,backgroundColor:'#fffffe',logging:false,width:700,windowWidth:700}).then(function(canvas){
    var a=document.createElement('a'); a.download='__FILENAME__'; a.href=canvas.toDataURL('image/png');
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    btn.textContent='✅ 저장 완료!';
    setTimeout(function(){btn.textContent='📥 이미지로 저장';btn.disabled=false;},2500);
  }).catch(function(){btn.textContent='📥 이미지로 저장';btn.disabled=false;});
}
</script>
</body></html>"""

    html_content = (tmpl
                    .replace("__QUESTION__", q_safe)
                    .replace("__RESULT__", result_html)
                    .replace("__FILENAME__", filename)
                    .replace("__TODAY__", today_str))
    components.html(html_content, height=60)


# ──────────────────────────────────────────────
# 강의 페이지
# ──────────────────────────────────────────────
def page_lecture():
    # ── 화면 상단 스크롤 (강 이동 직후) ──────
    if st.session_state.get("scroll_top"):
        st.session_state.scroll_top = False
        _scroll_to_top()

    # ── 뒤로가기 ─────────────────────────────
    if st.button("← 홈으로", key="back_home"):
        st.session_state.page = "main"
        st.rerun()

    # ── 헤더 ─────────────────────────────────
    st.markdown(
        "<div style='background:#e3f6f5;border:2px solid #272343;border-radius:20px;"
        "padding:20px 24px;margin:10px 0 14px;box-shadow:5px 5px 0 #bae8e8;"
        "display:flex;align-items:center;gap:14px;'>"
        "<div style='width:44px;height:44px;background:#272343;border-radius:12px;"
        "display:flex;align-items:center;justify-content:center;"
        "color:#ffd803;font-size:1.2rem;flex-shrink:0;'>"
        "<i class='fa-solid fa-book-open'></i></div>"
        "<div><div style='font-family:Montserrat,sans-serif;font-weight:800;"
        "font-size:1.1rem;color:#272343;'>육효의 모든 것</div>"
        "<div style='font-size:0.83rem;color:#2d334a;margin-top:2px;'>"
        "기초 7강 + 심화 4강 — 총 11강으로 완성하는 육효</div></div></div>",
        unsafe_allow_html=True,
    )

    # ── 진도 도트 (한 줄 · 로그인 유지) ─────────
    # <a href> 방식은 페이지 새로고침 → 세션 초기화 → 로그아웃 발생.
    # 대신: 시각 도트(HTML) + 숨긴 Streamlit 버튼(11개) + JS 클릭 연결.
    cur = st.session_state.cur_lec
    max_ok = _max_unlocked()

    # ① 시각 도트 — cursor:pointer, class="hyo-dot", href 없음
    dots_html = (
        "<div id='hyo-dots-row' style='display:flex;align-items:center;gap:0;"
        "flex-wrap:nowrap;overflow-x:auto;padding:4px 0 8px;'>"
    )
    for i in range(1, 12):
        if i in st.session_state.quiz_done:
            bg, fg, bdr, symbol = "#ffd803", "#272343", "#272343", "✓"
        elif i == cur:
            bg, fg, bdr, symbol = "#272343", "#ffd803", "#272343", str(i)
        elif i <= max_ok:
            bg, fg, bdr, symbol = "#e3f6f5", "#272343", "#272343", str(i)
        else:
            bg, fg, bdr, symbol = "#f3f4f6", "#c4c9d4", "#e0e4ed", str(i)

        dots_html += (
            f"<div class='hyo-dot' data-lec='{i}' "
            f"style='width:28px;height:28px;background:{bg};"
            f"border:2px solid {bdr};border-radius:50%;cursor:pointer;"
            f"display:inline-flex;align-items:center;justify-content:center;"
            f"font-weight:700;font-size:0.7rem;color:{fg};flex-shrink:0;' "
            f"title='{i}강'>{symbol}</div>"
        )
        if i < 11:
            if i == 7:
                dots_html += (
                    "<div style='display:flex;align-items:center;flex-shrink:0;"
                    "margin:0 4px;gap:2px;'>"
                    "<div style='width:5px;height:1px;background:#d1d5db;'></div>"
                    "<span style='font-size:0.55rem;color:#9ca3af;font-weight:700;"
                    "white-space:nowrap;'>심화▷</span>"
                    "<div style='width:5px;height:1px;background:#d1d5db;'></div>"
                    "</div>"
                )
            else:
                line_color = "#272343" if i < max_ok else "#e5e7eb"
                dots_html += (
                    f"<div style='width:10px;height:2px;"
                    f"background:{line_color};flex-shrink:0;'></div>"
                )
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)

    # ② 숨긴 Streamlit 버튼 — 컬럼 없이 단일 렌더링
    # st.columns(11)을 쓰면 React가 page_main의 st.columns([3,2,3])와 동일한
    # 자동 key를 공유해 이전 JS style이 재사용되어 버튼이 사라지는 버그 발생.
    for _i in range(1, 12):
        if st.button(f"⊙{_i}", key=f"hbtn_{_i}"):
            st.session_state.cur_lec = _i
            st.session_state.page = "lecture"
            save_progress(st.session_state.get("auth_email", ""))
            st.rerun()

    # ③ JS: ⊙ 버튼 컨테이너를 개별 숨김 + 도트와 1:1 연결
    components.html("""<script>
(function() {
    function init() {
        var par = window.parent.document;
        var dotsRow = par.getElementById('hyo-dots-row');
        if (!dotsRow) { setTimeout(init, 80); return; }

        // ⊙ 레이블 버튼 수집 + 각 stButton 컨테이너 개별 숨김
        var hBtns = [];
        par.querySelectorAll('button').forEach(function(btn) {
            var txt = (btn.textContent || btn.innerText || '').trim();
            if (txt.charCodeAt(0) === 0x2299) { // ⊙ 시작
                var wrapper = btn.closest('[data-testid="stButton"]');
                if (wrapper) wrapper.style.cssText = 'display:none;margin:0;padding:0;height:0;';
                hBtns.push(btn);
            }
        });
        if (hBtns.length < 11) { setTimeout(init, 80); return; }

        // 시각 도트와 숨긴 버튼 1:1 연결
        var dots = dotsRow.querySelectorAll('.hyo-dot');
        dots.forEach(function(dot, idx) {
            dot.addEventListener('click', function() {
                if (hBtns[idx]) hBtns[idx].click();
            });
        });
    }
    init();
})();
</script>""", height=0)

    # ── 상단 이전/현재/다음 내비 ──────────────
    nav_prev, nav_title, nav_next = st.columns([1, 4, 1])
    lec_key = f"{cur}강"
    with nav_prev:
        if cur > 1:
            if st.button("← 이전", key="nav_prev", use_container_width=True):
                st.session_state.cur_lec -= 1
                save_progress(st.session_state.get("auth_email", ""))
                st.session_state.scroll_top = True
                st.rerun()
    with nav_title:
        st.markdown(
            f"<div style='text-align:center;font-weight:700;color:#272343;"
            f"font-size:0.9rem;padding:8px 0;'>"
            f"{lec_key} · {LECTURE_TITLES[lec_key]}</div>",
            unsafe_allow_html=True,
        )
    with nav_next:
        if cur < max_ok:
            if st.button("다음 →", key="nav_next", use_container_width=True):
                st.session_state.cur_lec += 1
                st.session_state.scroll_top = True
                st.rerun()

    st.divider()

    # ── 강의 본문 ────────────────────────────
    st.markdown(LECTURES[lec_key], unsafe_allow_html=False)

    # ── 학습 완료 버튼 ──────────────────────
    if cur not in st.session_state.content_done:
        st.divider()
        _, mid, _ = st.columns([2, 1, 2])
        with mid:
            if st.button(
                "✅ 학습 완료",
                use_container_width=True,
                key=f"done_{cur}",
            ):
                st.session_state.content_done.add(cur)
                st.rerun()
    else:
        # ── 퀴즈 ────────────────────────────
        quiz_passed = show_quiz(cur)

        if quiz_passed:
            st.divider()
            _, mid, _ = st.columns([2, 1, 2])
            with mid:
                if cur < 11:
                    if st.button(
                        f"{cur + 1}강으로 →",
                        use_container_width=True,
                        key=f"next_lec_{cur}",
                    ):
                        st.session_state.cur_lec = cur + 1
                        save_progress(st.session_state.get("auth_email", ""))
                        st.session_state.scroll_top = True
                        st.rerun()
                else:
                    st.success(
                        "🎉 기초 7강 + 심화 4강을 모두 완료했습니다! "
                        "이제 직접 육효 이미지를 업로드해서 해석해보세요."
                    )
                    if st.button(
                        "홈으로 돌아가기",
                        use_container_width=True,
                        key="go_home_final",
                    ):
                        st.session_state.page = "main"
                        st.session_state.scroll_top = True
                        st.rerun()


# ──────────────────────────────────────────────
# 메인 페이지 (육효 해석) — 단일 컬럼 카드
# ──────────────────────────────────────────────
def page_main(api_key: str, auth_enabled: bool, email: str, is_owner: bool, remaining: int):

    # ── 육효 해석 카드 ────────────────────────
    with st.container(border=True):
        st.markdown("### 🔮 육효 해석")
        st.divider()

        # 1. 사용 방법
        with st.expander("📖 사용 방법 보기"):
            st.markdown("""
1. 육효 앱(도사폰 등)에서 괘를 뽑으세요.
2. 앱 화면을 캡처해 아래에 업로드하세요.
3. 알고 싶은 내용을 질문란에 입력하세요.
4. (선택) 용신을 직접 지정할 수 있습니다.
5. '해석하기' 버튼을 누르면 육효의 세계가 상세히 해석해드립니다.
            """)

        # 2. 이미지 업로드
        st.markdown("#### 육효 화면 이미지")
        uploaded = st.file_uploader(
            label="이미지 업로드",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )
        # 이미지 컬럼은 항상 렌더링 — 컬럼 자동 key를 안정적으로 유지
        _, img_col, _ = st.columns([1, 2, 1])
        if uploaded:
            with img_col:
                st.image(uploaded, use_container_width=True)

        # 3. 질문
        st.markdown("#### 질문")
        question = st.text_area(
            label="질문",
            placeholder=(
                "예시:\n"
                "• 이번 달 안에 취업이 될까요?\n"
                "• 남자친구와 재회할 수 있을까요?\n"
                "• 이 사업 투자를 해도 괜찮을까요?\n"
                "• 소송에서 내가 이길 수 있을까요?"
            ),
            height=140,
            label_visibility="collapsed",
        )

        # 4. 용신 직접 지정 (optional)
        yongshin = "auto"
        with st.expander("⚙️ 용신 직접 지정 (선택사항)"):
            st.caption("자동으로 선택됩니다. 육효를 어느 정도 아신다면 직접 지정해 보세요.")
            yongshin_map = {
                "자동선택 (권장)": "auto",
                "처재(妻財) — 재물 · 사업 · 연애(남성)": "財",
                "관귀(官鬼) — 직장 · 승진 · 남편(여성) · 건강": "官",
                "부모(父母) — 문서 · 시험 · 계약 · 부동산": "父",
                "자손(子孫) — 자녀 · 건강 · 해결 · 복": "孫",
                "형제(兄弟) — 동료 · 경쟁 · 협력": "兄",
            }
            ys_label = st.selectbox(
                "용신 선택",
                list(yongshin_map.keys()),
                label_visibility="collapsed",
            )
            yongshin = yongshin_map[ys_label]
            if yongshin != "auto":
                st.info(f"선택된 용신: {yongshin} — 육효의 세계가 이 육친을 용신으로 해석합니다.")

        # 5. 사용량 초과 안내
        if auth_enabled and not is_owner and remaining == 0:
            st.warning(
                f"⚠️ 오늘 무료 사용량({DAILY_LIMIT}회)을 모두 사용했습니다. "
                "내일 다시 이용해주세요."
            )

        # 6. 해석하기 버튼
        can_use = is_owner or not auth_enabled or remaining > 0
        ready = bool(api_key and uploaded and question.strip() and can_use)
        clicked = st.button(
            "🔮 해석하기",
            type="primary",
            use_container_width=True,
            disabled=not ready,
        )

        if not api_key:
            try:
                secret_keys = list(st.secrets.keys())
            except Exception:
                secret_keys = ["(읽기 실패)"]
            st.warning(
                f"⚠️ GEMINI_API_KEY를 찾을 수 없습니다.  \n"
                f"현재 Secrets에 등록된 키: `{secret_keys}`  \n"
                "Streamlit Cloud › Settings › Secrets에서 **최상단 섹션 밖**에  \n"
                "`GEMINI_API_KEY = \"AIzaSy...\"` 형태로 입력했는지 확인하세요."
            )
        elif not uploaded:
            st.caption("이미지를 업로드해주세요.")
        elif not question.strip():
            st.caption("질문을 입력해주세요.")
        elif auth_enabled and not is_owner and remaining > 0:
            st.caption(f"오늘 {remaining}회 남았습니다.")

    # ── 해석 결과 (카드 외부) ─────────────────
    if clicked and ready:
        st.divider()
        with st.spinner("🔮 육효를 해석하고 있습니다... (20~40초 소요)"):
            try:
                result = call_gemini(uploaded, question.strip(), api_key, yongshin)
                # ** 마커 제거 — 쌍으로 된 것 먼저 제거, 남은 것 단순 삭제
                result = re.sub(r'\*\*(.+?)\*\*', r'\1', result, flags=re.DOTALL)
                result = result.replace('**', '')
                # 성공 시 사용 횟수 증가
                if auth_enabled and not is_owner:
                    increment_usage(email)
                with st.container(border=True):
                    st.subheader("🌟 해석 결과")
                    st.markdown(result)
                _render_download_button(question.strip(), result)
            except Exception as e:
                err = str(e)
                if "API_KEY_INVALID" in err or "api key" in err.lower():
                    st.error("❌ API 키가 올바르지 않습니다. 다시 확인해주세요.")
                elif "PERMISSION_DENIED" in err:
                    st.error("❌ API 키 권한이 없습니다.")
                elif "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                    st.error("❌ 오늘 무료 사용량을 초과했습니다. 내일 다시 시도해주세요.")
                else:
                    st.error(f"❌ 오류가 발생했습니다: {err}")

    # ── 강의 이동 버튼 ────────────────────────
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([3, 2, 3])
    with mid:
        if st.button("📚 육효의 모든 것", key="go_lecture", use_container_width=True):
            st.session_state.page = "lecture"
            st.rerun()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    _init()

    # ── 로그아웃 링크 처리 (?logout=1) ─────────
    if st.query_params.get("logout"):
        st.query_params.clear()
        st.session_state.pop("auth_email", None)
        st.session_state.pop("auth_name", None)
        st.rerun()

    # ── Auth Gate ────────────────────────────
    if AUTH_ENABLED:
        email: str = get_current_email()   # OAuth 콜백 처리 포함
        if not email:
            _render_login_page()
            return  # st.stop() 이미 호출됨

        owner_email = st.secrets.get("OWNER_EMAIL", "")
        is_owner: bool = bool(email and email == owner_email)
        remaining: int = 999 if is_owner else max(0, DAILY_LIMIT - get_today_count(email))
    else:
        # 로컬 개발 모드 — 인증 없이 전체 기능 사용
        email = "local@dev"
        is_owner = True
        remaining = 999

    # ── 학습 진도 복원 (세션당 1회, DB → session_state) ─
    if not st.session_state.get("progress_loaded"):
        load_progress(email)
        st.session_state["progress_loaded"] = True

    # ── 도트 클릭 이동 (?goto_lec=N) ────────────
    if "goto_lec" in st.query_params:
        try:
            n = int(st.query_params["goto_lec"])
            if 1 <= n <= 11:
                st.session_state.cur_lec = n
                st.session_state.page = "lecture"
        except (ValueError, TypeError):
            pass
        del st.query_params["goto_lec"]
        st.rerun()

    inject_css()
    api_key = _get_api_key()

    # ── 상단 헤더 오버레이 (모든 페이지에서 표시) ─
    _render_user_bar(email, is_owner, remaining)

    if st.session_state.page == "main":
        st.markdown(HERO_HTML, unsafe_allow_html=True)
        page_main(api_key, AUTH_ENABLED, email, is_owner, remaining)
    else:
        page_lecture()


if __name__ == "__main__":
    main()
