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
from datetime import date
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
    """Streamlit Secrets → 환경변수 순서로 Gemini API 키 반환."""
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")


# ──────────────────────────────────────────────
# 사용자 정보 바 (메인 페이지 상단)
# ──────────────────────────────────────────────
def _render_user_bar(email: str, is_owner: bool, remaining: int):
    """메인 페이지 상단 — 이름·이메일·사용량 뱃지·로그아웃 버튼."""
    if not AUTH_ENABLED or not email:
        return
    name = st.session_state.get("auth_name", "") or email.split("@")[0]
    c1, c2, c3 = st.columns([5, 3, 1])
    with c1:
        st.markdown(
            f"<div style='padding:5px 0;line-height:1.4;'>"
            f"<span style='font-weight:700;color:#272343;font-size:0.93rem;'>👤 {name}</span>"
            f"<span style='color:#6b7280;font-size:0.78rem;margin-left:8px;'>({email})</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c2:
        if is_owner:
            st.markdown(
                "<div style='background:#ffd803;border:2px solid #272343;border-radius:10px;"
                "padding:4px 10px;font-weight:700;font-size:0.82rem;color:#272343;"
                "text-align:center;margin-top:3px;'>✨ 무제한</div>",
                unsafe_allow_html=True,
            )
        elif remaining > 0:
            st.markdown(
                f"<div style='background:#e3f6f5;border:2px solid #272343;border-radius:10px;"
                f"padding:4px 10px;font-weight:700;font-size:0.82rem;color:#272343;"
                f"text-align:center;margin-top:3px;'>오늘 {remaining}회 남음</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:#fee2e2;border:2px solid #dc2626;border-radius:10px;"
                "padding:4px 10px;font-weight:700;font-size:0.82rem;color:#dc2626;"
                "text-align:center;margin-top:3px;'>오늘 사용완료</div>",
                unsafe_allow_html=True,
            )
    with c3:
        if st.button("로그아웃", key="logout_top", use_container_width=True):
            _logout()
    st.divider()


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


def get_today_count(email: str) -> int:
    """오늘 사용 횟수 반환 — session_state 캐시 우선."""
    cache_key = f"usage_{email}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    count = 0
    try:
        sb = _get_supabase()
        if sb is not None and email:
            today = date.today().isoformat()
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
        today = date.today().isoformat()
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
  - 오행: 木火土金水
  - 世(세효 = 나) 또는 應(응효 = 상대) 표시
  - 동효(動爻) 여부: 빨간 빗금(×), 굵은 표시, 또는 "동" 표기
  - 변효(變爻): 동효가 변한 후의 육친·지지 (→ 오른쪽에 표시)
  - 장생12신: 長生·沐浴·冠帶·臨官·帝旺·衰·病·死·墓·絶·胎·養

[보조 정보]
  - 월건(月建): 점을 친 달의 지지
  - 일진(日辰): 점을 친 날의 지지
  - 공망(空亡): 비어 있는 두 글자 (예: 戌亥 공망)
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

- **세효(世)** = 나 / 질문하는 사람
- **응효(應)** = 상대방 / 외부환경

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

- 동효가 용신을 **생(生)** 하면 → 좋은 방향
- 동효가 용신을 **극(克)** 하면 → 방해·문제
- 동효 없음 → 변화 없이 조용한 상태

**동효의 강도 판단:**
- 파란 글자(월령의 생·합)를 받은 동효 → 힘이 강함
- 빨간 글자(일진의 생·합)를 받은 동효 → 힘이 강함

**변효(變爻) 해석 원칙:**
- 변효는 오직 본효(동효)를 생하는지 극하는지만 분석
- **회두생(回頭生)**: 변효가 본효를 생해줌 → 처음 힘들다가 결국 좋아짐
- **회두극(回頭克)**: 변효가 본효를 극함 → 발등 찍히는 상황, 매우 나쁨
- **본효가 변효를 극하는 경우**: 변효는 본효에 아무 영향 없음 (무시)
- **진신(進神)**: 같은 오행의 더 강한 글자로 변함 → 기세가 점점 강해짐
- **퇴신(退神)**: 같은 오행의 더 약한 글자로 변함 → 기세가 꺾임

## 5. 오행 상생·상극

상생: 木(목)→火(화)→土(토)→金(금)→水(수)→木(목)
상극: 木극土 / 土극水 / 水극火 / 火극金 / 金극木

오행-지지 대응:
- 木(목): 寅(인)·卯(묘)  /  火(화): 巳(사)·午(오)
- 土(토): 辰(진)·戌(술)·丑(축)·未(미)
- 金(금): 申(신)·酉(유)  /  水(수): 子(자)·亥(해)

## 6. 특수 상태 — 5대 비지

| 상태 | 핵심 의미 | 현실 번역 |
|------|---------|----------|
| 공망(空亡) | 비어있음·허상 | 말뿐·약속 펑크·속임·실체 없음 |
| 월파(月破) | 이번 달 깨짐 | 이달은 절대 안 됨 |
| 암동(暗動) | 겉은 조용·속은 움직임 | 몰래 진행·숨은 감정 |
| 입묘(入墓) | 갇혀서 못 나옴 | 연락 두절·잠수·막힘 |
| 복신(伏神) | 숨은 효 | 드러나지 않은 진실 |

합(合): 결합·묶임 → 좋으면 계약, 나쁘면 집착·구속
충(沖): 깨짐·이동 → 좋으면 돌파, 나쁘면 파탄·이별
형(刑): 스트레스·법적 마찰

## 7. 실전 해석 순서

1. 질문 확인 → 용신 선택
2. 세효 상태 (강한가·공망인가)
3. 용신 상태 (왕성한가·월파·공망인가)
4. 동효 확인
5. 동효↔용신 생극 관계
6. 특수 상태 체크
7. 타이밍 도출
8. 현실 언어로 번역

━━━━━━━━━━━━━━━━━━━━━━━━
📝  해석 출력 형식 (반드시 이 형식 사용)
━━━━━━━━━━━━━━━━━━━━━━━━

---

## 📊 괘반 정보 요약

- **월건 / 일진**: [값 또는 "확인 어려움"]
- **공망**: [해당 지지 또는 "없음"]
- **세효(나)**: [효 위치] [육친] [지지] — [상태]
- **응효(상대)**: [효 위치] [육친] [지지] — [상태]
- **동효**: [몇 효, 육친, 지지] → 변효: [변화 결과]
- **용신**: [육친] — [선택 이유]

---

## 🎯 핵심 판단

**[결론을 먼저 한 줄로]**

---

## 🔮 상세 해석

### 지금 내 상황은?
(세효 상태를 비유로 설명)

### 원하는 것(용신)의 상태는?
(용신이 강한지·약한지·공망인지를 비유로)

### 어떤 사건이 일어나고 있나요?
(동효가 없으면 "조용한 상태". 있으면:
① 동효 육친이 무엇인지
② 동효가 용신을 생하는지 극하는지
③ 동효의 강도: 파란·빨간 생합 표시
④ 변효 회두생/회두극 여부
⑤ 종합 스토리)

### 특별히 주의할 것
(공망·월파·합·충·암동이 있으면 설명. 없으면 생략)

---

## 💡 실질적인 조언

1. ...
2. ...
3. ...

---

## 🕐 타이밍

(언제쯤 결과가 나타날지)

---

## ✨ 한 줄 요약

> **[가장 쉬운 말로 딱 한 문장]**

---

*⚠️ 육효는 현재 에너지 흐름을 읽는 도구입니다. 최종 결정은 본인의 의지와 행동에 달려 있습니다.*

━━━━━━━━━━━━━━━━━━━━━━━━
🎨  해석 스타일 필수 준수
━━━━━━━━━━━━━━━━━━━━━━━━

1. 전문용어는 반드시 괄호로 번역
   예: "세효(나를 나타내는 자리)가 공망(텅 빈 상태)이어서..."

2. 비유를 풍부하게
   예: "관귀가 세효를 극한다" → "마치 직장 상사가 하루 종일 압박을 넣는 것처럼..."

3. 스토리 흐름: 지금 → 중간 → 결말

4. 따뜻하고 솔직하게: 나쁜 결과도 부드럽게, 대안 조언 포함

5. 충분히 상세하게 (해석 본문 최소 600자 이상)
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
            f"\n\n[중요] 용신(用神)을 질문자가 직접 지정했습니다: **{yongshin}**. "
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
            max_output_tokens=8192,
        ),
    )
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
    for i in range(1, 8):
        if i in st.session_state.quiz_done:
            unlocked = min(i + 1, 7)
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
  <div class="footer">육효의 세계 · __TODAY__ · powered by Google Gemini</div>
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
        "기초부터 실전까지 — 7강으로 완성하는 육효 입문</div></div></div>",
        unsafe_allow_html=True,
    )

    # ── 진도 도트 ─────────────────────────────
    cur = st.session_state.cur_lec
    max_ok = _max_unlocked()

    dots_html = "<div style='display:flex;align-items:center;gap:5px;margin:4px 0 14px;'>"
    for i in range(1, 8):
        if i in st.session_state.quiz_done:
            bg, fg, symbol, bdr = "#ffd803", "#272343", "✓", "#272343"
        elif i == cur:
            bg, fg, symbol, bdr = "#272343", "#ffd803", str(i), "#272343"
        elif i <= max_ok:
            bg, fg, symbol, bdr = "#e3f6f5", "#272343", str(i), "#272343"
        else:
            bg, fg, symbol, bdr = "#fffffe", "#9ca3af", str(i), "#d1d5db"

        dots_html += (
            f"<div style='width:34px;height:34px;background:{bg};"
            f"border:2px solid {bdr};border-radius:50%;"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-weight:700;font-size:0.8rem;color:{fg};flex-shrink:0;'>{symbol}</div>"
        )
        if i < 7:
            line_color = "#272343" if i < max_ok else "#e5e7eb"
            dots_html += (
                f"<div style='flex:1;max-width:24px;height:2px;"
                f"background:{line_color};'></div>"
            )
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)

    # ── 상단 이전/현재/다음 내비 ──────────────
    nav_prev, nav_title, nav_next = st.columns([1, 4, 1])
    lec_key = f"{cur}강"
    with nav_prev:
        if cur > 1:
            if st.button("← 이전", key="nav_prev", use_container_width=True):
                st.session_state.cur_lec -= 1
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
                if cur < 7:
                    if st.button(
                        f"{cur + 1}강으로 →",
                        use_container_width=True,
                        key=f"next_lec_{cur}",
                    ):
                        st.session_state.cur_lec = cur + 1
                        st.session_state.scroll_top = True
                        st.rerun()
                else:
                    st.success(
                        "🎉 모든 강의를 완료했습니다! "
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

    # ── 사용자 정보 바 ────────────────────────
    _render_user_bar(email, is_owner, remaining)

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
5. **해석하기** 버튼을 누르면 AI가 상세히 해석해드립니다.
            """)

        # 2. 이미지 업로드
        st.markdown("#### 육효 화면 이미지")
        uploaded = st.file_uploader(
            label="이미지 업로드",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )
        if uploaded:
            _, img_col, _ = st.columns([1, 2, 1])
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
            st.caption("AI가 자동으로 선택합니다. 육효를 어느 정도 아신다면 직접 지정해 보세요.")
            yongshin_map = {
                "AI가 자동 선택 (권장)": "auto",
                "財(재) — 재물 · 사업 · 연애(남성)": "財",
                "官(관) — 직장 · 승진 · 남편(여성) · 건강": "官",
                "父(부) — 문서 · 시험 · 계약 · 부동산": "父",
                "孫(손) — 자녀 · 건강 · 해결 · 복": "孫",
                "兄(형) — 동료 · 경쟁 · 협력": "兄",
            }
            ys_label = st.selectbox(
                "용신 선택",
                list(yongshin_map.keys()),
                label_visibility="collapsed",
            )
            yongshin = yongshin_map[ys_label]
            if yongshin != "auto":
                st.info(f"선택된 용신: **{yongshin}** — AI가 이 육친을 용신으로 해석합니다.")

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

        if not uploaded:
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
    _, mid, _ = st.columns([2, 1, 2])
    with mid:
        if st.button("📚 육효의 모든 것", use_container_width=True, key="go_lecture"):
            st.session_state.page = "lecture"
            st.rerun()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    _init()

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

    inject_css()

    api_key = _get_api_key()

    if st.session_state.page == "main":
        st.markdown(HERO_HTML, unsafe_allow_html=True)
        page_main(api_key, AUTH_ENABLED, email, is_owner, remaining)
    else:
        page_lecture()


if __name__ == "__main__":
    main()
