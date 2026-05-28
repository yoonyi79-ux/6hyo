import streamlit as st
from google import genai
from google.genai import types
import os
import io
from PIL import Image
from dotenv import load_dotenv
from lectures import LECTURES, LECTURE_TITLES, QUIZZES
from style import inject_css, HERO_HTML

load_dotenv()

st.set_page_config(
    page_title="육효의 세계",
    page_icon="☯",
    layout="centered",
)

# ──────────────────────────────────────────────
# Session State 초기화
# ──────────────────────────────────────────────
def _init():
    defaults = {
        "page":          "main",   # "main" | "lecture"
        "cur_lec":       1,        # 1 ~ 7
        "content_done":  set(),    # 강의 본문 완료한 강 번호들
        "quiz_done":     set(),    # 퀴즈까지 완료한 강 번호들
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


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

상생: 木→火→土→金→水→木
상극: 木극土 / 土극水 / 水극火 / 火극金 / 金극木

오행-지지 대응:
- 木: 寅·卯  /  火: 巳·午  /  土: 辰·戌·丑·未  /  金: 申·酉  /  水: 子·亥

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
# 사이드바
# ──────────────────────────────────────────────
def sidebar() -> str:
    with st.sidebar:
        st.markdown("### ⚙️ 설정")

        secret_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
        env_key = os.getenv("GEMINI_API_KEY", "")
        preset_key = secret_key or env_key

        if preset_key:
            st.success("✅ API 키 자동 감지됨")
            api_key = preset_key
        else:
            st.markdown(
                "**무료** Google Gemini API 키가 필요합니다.\n\n"
                "👉 **[Google AI Studio → API 키 발급](https://aistudio.google.com/apikey)**"
            )
            api_key = st.text_input(
                "Gemini API Key",
                type="password",
                placeholder="AIzaSy...",
            )
            if api_key:
                st.success("✅ API 키 입력됨")

        st.divider()
        st.markdown("""
### 📖 사용 방법
1. 육효 앱에서 괘를 뽑으세요.
2. 화면을 캡처해서 업로드하세요.
3. 질문을 입력하세요.
4. **해석하기** 버튼을 누르세요.

### 💡 질문 예시
- 이번 달 안에 취업이 될까요?
- 남자친구와 재회할 수 있을까요?
- 사업 투자를 해도 괜찮을까요?
- 소송에서 내가 이길 수 있을까요?

### 🆓 Gemini 무료 한도
- 하루 1,500회 / 분당 15회
- 카드 등록 불필요
        """)
        st.caption("powered by Google Gemini 3.5 Flash")

    return api_key


# ──────────────────────────────────────────────
# 퀴즈
# ──────────────────────────────────────────────
def _lec_quiz_key(lec_num: int, q_idx: int) -> str:
    return f"q_{lec_num}_{q_idx}"

def _saved_answer_key(lec_num: int, q_idx: int) -> str:
    return f"saved_q_{lec_num}_{q_idx}"

def show_quiz(lec_num: int) -> bool:
    """
    퀴즈를 렌더링합니다.
    Returns True if the quiz has been submitted (quiz_done).
    """
    lec_key = f"{lec_num}강"
    quizzes = QUIZZES.get(lec_key, [])
    if not quizzes:
        return True

    st.divider()
    st.markdown(
        "<div style='background:#e3f6f5;border:2px solid #272343;border-radius:16px;"
        "padding:18px 24px;margin-bottom:16px;box-shadow:4px 4px 0 #bae8e8;'>"
        "<span style='font-family:Montserrat,sans-serif;font-weight:800;font-size:1.05rem;"
        "color:#272343;'>📝 확인 퀴즈</span>"
        "<span style='font-size:0.85rem;color:#2d334a;margin-left:10px;'>"
        "강의 내용을 잘 이해했는지 확인해보세요</span></div>",
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
                        f"<div style='color:#059669;font-weight:600;padding:4px 0;'>✅ {opt}</div>",
                        unsafe_allow_html=True,
                    )
                elif opt == saved:
                    st.markdown(
                        f"<div style='color:#dc2626;font-weight:600;padding:4px 0;'>❌ {opt}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='color:#6b7280;padding:4px 0;'>&nbsp;&nbsp;&nbsp;{opt}</div>",
                        unsafe_allow_html=True,
                    )
            st.caption(f"💡 {quiz['explanation']}")
        else:
            sel = st.radio(
                label=f"q{lec_num}_{i}",
                options=quiz["options"],
                index=None,
                key=q_key,
                label_visibility="collapsed",
            )
            if sel is None:
                all_answered = False

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

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
                # 답 저장 + 점수 계산
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

    # 결과 표시
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
# 진도 계산 헬퍼
# ──────────────────────────────────────────────
def _max_unlocked() -> int:
    """접근 가능한 최대 강 번호."""
    unlocked = 1
    for i in range(1, 8):
        if i in st.session_state.quiz_done:
            unlocked = min(i + 1, 7)
        else:
            break
    return unlocked


# ──────────────────────────────────────────────
# 강의 페이지
# ──────────────────────────────────────────────
def page_lecture():
    # ── 뒤로가기 ──────────────────────────────
    if st.button("← 홈으로", key="back_home"):
        st.session_state.page = "main"
        st.rerun()

    # ── 헤더 ──────────────────────────────────
    st.markdown(
        "<div style='background:#e3f6f5;border:2px solid #272343;border-radius:20px;"
        "padding:20px 24px;margin:12px 0 16px;box-shadow:5px 5px 0 #bae8e8;"
        "display:flex;align-items:center;gap:14px;'>"
        "<div style='width:46px;height:46px;background:#272343;border-radius:12px;"
        "display:flex;align-items:center;justify-content:center;"
        "color:#ffd803;font-size:1.3rem;flex-shrink:0;'>"
        "<i class='fa-solid fa-book-open'></i></div>"
        "<div><div style='font-family:Montserrat,sans-serif;font-weight:800;"
        "font-size:1.15rem;color:#272343;'>육효의 모든 것</div>"
        "<div style='font-size:0.85rem;color:#2d334a;margin-top:2px;'>"
        "기초부터 실전까지 — 7강으로 완성하는 육효 입문</div></div></div>",
        unsafe_allow_html=True,
    )

    # ── 진도 표시 ──────────────────────────────
    cur = st.session_state.cur_lec
    max_ok = _max_unlocked()

    dots_html = "<div style='display:flex;align-items:center;gap:6px;margin:4px 0 16px;'>"
    for i in range(1, 8):
        if i in st.session_state.quiz_done:
            bg, fg, symbol = "#ffd803", "#272343", "✓"
            bdr = "#272343"
        elif i == cur:
            bg, fg, symbol = "#272343", "#ffd803", str(i)
            bdr = "#272343"
        elif i <= max_ok:
            bg, fg, symbol = "#e3f6f5", "#272343", str(i)
            bdr = "#272343"
        else:
            bg, fg, symbol = "#fffffe", "#9ca3af", str(i)
            bdr = "#d1d5db"

        dots_html += (
            f"<div style='width:36px;height:36px;background:{bg};"
            f"border:2px solid {bdr};border-radius:50%;"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-weight:700;font-size:0.82rem;color:{fg};flex-shrink:0;'>{symbol}</div>"
        )
        if i < 7:
            dots_html += (
                "<div style='flex:1;max-width:28px;height:2px;"
                f"background:{'#272343' if i < max_ok else '#e5e7eb'};'></div>"
            )
    dots_html += "</div>"
    st.markdown(dots_html, unsafe_allow_html=True)

    # ── 상단 이전/다음 이동 ────────────────────
    nav_prev, nav_title, nav_next = st.columns([1, 4, 1])
    with nav_prev:
        if cur > 1:
            if st.button("← 이전", key="nav_prev", use_container_width=True):
                st.session_state.cur_lec = cur - 1
                st.rerun()
    with nav_title:
        lec_key = f"{cur}강"
        st.markdown(
            f"<div style='text-align:center;font-weight:700;color:#272343;"
            f"font-size:0.92rem;padding:8px 0;'>{lec_key} · {LECTURE_TITLES[lec_key]}</div>",
            unsafe_allow_html=True,
        )
    with nav_next:
        if cur < max_ok:
            if st.button("다음 →", key="nav_next", use_container_width=True):
                st.session_state.cur_lec = cur + 1
                st.rerun()

    st.divider()

    # ── 강의 본문 ─────────────────────────────
    st.markdown(LECTURES[lec_key], unsafe_allow_html=False)

    # ── 학습 완료 버튼 ─────────────────────────
    if cur not in st.session_state.content_done:
        st.divider()
        _, mid, _ = st.columns([2, 1, 2])
        with mid:
            if st.button("✅ 학습 완료", use_container_width=True, key=f"done_{cur}"):
                st.session_state.content_done.add(cur)
                st.rerun()
        st.caption(
            "<div style='text-align:center;'>강의를 다 읽으셨나요? 학습 완료를 누르면 확인 퀴즈가 시작됩니다.</div>",
            # workaround: use markdown
        )
    else:
        # ── 퀴즈 ──────────────────────────────
        quiz_passed = show_quiz(cur)

        # ── 다음 강으로 ────────────────────────
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
                        st.rerun()
                else:
                    st.success(
                        "🎉 모든 강의를 완료했습니다! "
                        "이제 직접 육효 이미지를 업로드해서 해석해보세요."
                    )
                    if st.button("홈으로 돌아가기", use_container_width=True, key="go_home_final"):
                        st.session_state.page = "main"
                        st.rerun()


# ──────────────────────────────────────────────
# 메인 페이지 (육효 해석)
# ──────────────────────────────────────────────
def page_main(api_key: str):
    # ── 입력 영역 ─────────────────────────────
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("#### 육효 화면 이미지")
        uploaded = st.file_uploader(
            "이미지 업로드",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )
        if uploaded:
            st.image(uploaded, use_container_width=True)

    yongshin = "auto"  # 기본값

    with right:
        st.markdown("#### 질문")
        question = st.text_area(
            "질문",
            placeholder=(
                "예시:\n"
                "• 이번 달 안에 취업이 될까요?\n"
                "• 남자친구와 재회할 수 있을까요?\n"
                "• 이 사업 투자를 해도 괜찮을까요?\n"
                "• 소송에서 내가 이길 수 있을까요?"
            ),
            height=158,
            label_visibility="collapsed",
        )

        # 용신 직접 지정 (optional)
        with st.expander("⚙️ 용신 직접 지정 (선택사항)"):
            st.caption("AI가 자동으로 선택합니다. 직접 지정하면 해당 육친을 용신으로 해석합니다.")
            yongshin_map = {
                "AI가 자동 선택 (권장)": "auto",
                "財 — 재물 · 사업 · 연애(남성)": "財",
                "官 — 직장 · 승진 · 남편(여성) · 건강": "官",
                "父 — 문서 · 시험 · 계약 · 부동산": "父",
                "孫 — 자녀 · 건강 · 해결 · 복": "孫",
                "兄 — 동료 · 경쟁 · 협력": "兄",
            }
            ys_label = st.selectbox(
                "용신 선택",
                list(yongshin_map.keys()),
                label_visibility="collapsed",
            )
            yongshin = yongshin_map[ys_label]
            if yongshin != "auto":
                st.info(f"선택된 용신: **{yongshin}** — AI가 이 육친을 용신으로 해석합니다.")

        ready = bool(api_key and uploaded and question.strip())
        clicked = st.button(
            "🔮 해석하기",
            type="primary",
            use_container_width=True,
            disabled=not ready,
        )

        if not api_key:
            st.caption("⬅️ 사이드바에서 API 키를 입력해주세요.")
        elif not uploaded:
            st.caption("왼쪽에 이미지를 업로드해주세요.")
        elif not question.strip():
            st.caption("질문을 입력해주세요.")

    # ── 해석 결과 ─────────────────────────────
    if clicked and ready:
        st.divider()
        with st.spinner("🔮 육효를 해석하고 있습니다... (20~40초 소요)"):
            try:
                result = call_gemini(uploaded, question.strip(), api_key, yongshin)
                with st.container(border=True):
                    st.subheader("🌟 해석 결과")
                    st.markdown(result)
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

    # ── 강의 페이지 이동 버튼 ─────────────────
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

    st.markdown(
        "<div style='text-align:center;color:#6b7280;font-size:0.9rem;margin-bottom:10px;'>"
        "육효가 처음이신가요? 7강 강의로 기초부터 배워보세요.</div>",
        unsafe_allow_html=True,
    )

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
    inject_css()

    api_key = sidebar()

    if st.session_state.page == "main":
        st.markdown(HERO_HTML, unsafe_allow_html=True)
        page_main(api_key)
    else:
        page_lecture()


if __name__ == "__main__":
    main()
