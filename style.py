# style.py — 디자인 시스템 (The Verge Light Mode + yoondesign 10원칙)
# 색상: 60(웜 베이지) - 30(화이트 서피스) - 10(퍼플·에메랄드 액센트)

import streamlit as st

CUSTOM_CSS = """
<!-- FontAwesome 6 -->
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

<!-- Google Fonts: Montserrat -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;900&display=swap"
  rel="stylesheet">

<style>
/* ══════════════════════════════════════════
   Pretendard 웹폰트 (한글)
══════════════════════════════════════════ */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

/* ══════════════════════════════════════════
   CSS 변수 — 60-30-10 컬러 시스템
══════════════════════════════════════════ */
:root {
  /* 60% — 배경 베이스 (웜 베이지) */
  --bg-base:       #FAF8F5;
  --bg-surface:    #FFFFFF;
  --bg-subtle:     #F3F0EB;

  /* 30% — 서브 컬러 (에메랄드 민트, The Verge acid-mint 라이트 버전) */
  --teal:          #059669;
  --teal-hover:    #047857;
  --teal-light:    #ECFDF5;
  --teal-border:   rgba(5,150,105,0.18);

  /* 10% — 포인트 컬러 (울트라바이올렛, The Verge 시그니처) */
  --purple:        #7C3AED;
  --purple-hover:  #6D28D9;
  --purple-dark:   #5B21B6;
  --purple-light:  #EDE9FE;
  --purple-border: rgba(124,58,237,0.18);

  /* 텍스트 */
  --text-primary:   #1C1C2E;
  --text-secondary: #6B7280;
  --text-muted:     #9CA3AF;

  /* 테두리 · 그림자 */
  --border:       rgba(0,0,0,0.08);
  --shadow-xs:    0 1px 3px  rgba(0,0,0,0.06);
  --shadow-sm:    0 4px 12px rgba(0,0,0,0.07);
  --shadow-md:    0 8px 28px rgba(0,0,0,0.09);
  --shadow-lg:    0 16px 48px rgba(0,0,0,0.11);

  /* 반경 */
  --r-sm: 8px;
  --r-md: 14px;
  --r-lg: 20px;
  --r-xl: 28px;

  /* 폰트 */
  --font-ko: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-en: 'Montserrat', sans-serif;
}

/* ══════════════════════════════════════════
   글로벌 리셋
══════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
  background-color: var(--bg-base) !important;
  font-family: var(--font-ko) !important;
  color: var(--text-primary) !important;
}

/* 그레인 텍스처 */
.stApp::after {
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.78' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
  opacity: 0.028;
  pointer-events: none;
  z-index: 9999;
}

/* ══════════════════════════════════════════
   타이포그래피
══════════════════════════════════════════ */
h1 {
  font-family: var(--font-en) !important;
  font-weight: 900 !important;
  font-size: 2.2rem !important;
  letter-spacing: -0.03em !important;
  color: var(--text-primary) !important;
  line-height: 1.1 !important;
}
h2 {
  font-family: var(--font-en) !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em !important;
  color: var(--text-primary) !important;
}
h3 {
  font-family: var(--font-ko) !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
}
p, li {
  font-family: var(--font-ko) !important;
  color: var(--text-primary) !important;
  line-height: 1.78 !important;
}
.stCaption > div {
  color: var(--text-secondary) !important;
  font-size: 0.83rem !important;
}

/* ══════════════════════════════════════════
   헤더 — Blur 효과
══════════════════════════════════════════ */
header[data-testid="stHeader"] {
  background: rgba(250,248,245,0.82) !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  border-bottom: 1px solid var(--border) !important;
}

/* ══════════════════════════════════════════
   사이드바
══════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background-color: var(--bg-surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
  color: var(--purple) !important;
  font-size: 0.78rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
  margin-top: 1.4rem !important;
  margin-bottom: 0.4rem !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li {
  font-size: 0.87rem !important;
  color: var(--text-secondary) !important;
  line-height: 1.65 !important;
}
[data-testid="stSidebar"] .stTextInput input {
  background: var(--bg-subtle) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ko) !important;
}
[data-testid="stSidebar"] .stTextInput input:focus {
  border-color: var(--purple) !important;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}

/* 성공 배지 */
[data-testid="stSidebar"] .stAlert[data-baseweb="notification"] {
  background: var(--teal-light) !important;
  border: 1px solid var(--teal-border) !important;
  border-radius: var(--r-md) !important;
  color: var(--teal-hover) !important;
  font-weight: 600 !important;
}

/* ══════════════════════════════════════════
   탭 — pill 스타일
══════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-subtle) !important;
  border-radius: 50px !important;
  padding: 5px !important;
  gap: 4px !important;
  border: none !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border: none !important;
  border-radius: 50px !important;
  color: var(--text-secondary) !important;
  font-weight: 600 !important;
  font-size: 0.93rem !important;
  padding: 10px 26px !important;
  transition: all 0.25s ease !important;
}
.stTabs [aria-selected="true"] {
  background: var(--bg-surface) !important;
  color: var(--purple) !important;
  box-shadow: var(--shadow-sm) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
  display: none !important;
}

/* ══════════════════════════════════════════
   버튼 — 그래디언트 + Ripple
══════════════════════════════════════════ */
.stButton > button {
  position: relative !important;
  overflow: hidden !important;
  background: linear-gradient(135deg, var(--purple) 0%, var(--purple-dark) 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--r-md) !important;
  font-family: var(--font-ko) !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  padding: 14px 32px !important;
  letter-spacing: 0.02em !important;
  cursor: pointer !important;
  transition: transform 0.25s cubic-bezier(.4,0,.2,1),
              box-shadow 0.25s cubic-bezier(.4,0,.2,1),
              background 0.25s ease !important;
  box-shadow: 0 4px 18px rgba(124,58,237,0.32) !important;
}
.stButton > button:hover:not(:disabled) {
  transform: translateY(-2px) !important;
  box-shadow: 0 10px 28px rgba(124,58,237,0.42) !important;
}
.stButton > button:active:not(:disabled) {
  transform: translateY(0) scale(0.98) !important;
}
.stButton > button:disabled {
  background: #D1D5DB !important;
  box-shadow: none !important;
  color: #9CA3AF !important;
  cursor: not-allowed !important;
}

/* Ripple 레이어 */
.stButton > button::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255,255,255,0.35);
  width: 0; height: 0;
  top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  transition: width 0.55s ease, height 0.55s ease, opacity 0.55s ease;
  opacity: 1;
}
.stButton > button:active::after {
  width: 360px; height: 360px;
  opacity: 0;
}

/* ══════════════════════════════════════════
   강의 선택 — 라디오 카드 스타일
══════════════════════════════════════════ */
.stRadio label {
  background: var(--bg-surface) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  padding: 13px 18px !important;
  margin-bottom: 6px !important;
  cursor: pointer !important;
  transition: border-color 0.2s, background 0.2s, transform 0.2s !important;
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
}
.stRadio label:hover {
  border-color: var(--purple) !important;
  background: var(--purple-light) !important;
  transform: translateX(5px) !important;
}
.stRadio label[data-checked="true"],
.stRadio input:checked + div {
  border-color: var(--purple) !important;
  background: var(--purple-light) !important;
}
.stRadio [data-testid="stMarkdownContainer"] p {
  font-size: 0.93rem !important;
  font-weight: 500 !important;
  margin: 0 !important;
}

/* ══════════════════════════════════════════
   파일 업로더
══════════════════════════════════════════ */
[data-testid="stFileUploader"] {
  background: var(--bg-surface) !important;
  border: 2px dashed var(--border) !important;
  border-radius: var(--r-lg) !important;
  transition: border-color 0.25s, background 0.25s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--teal) !important;
  background: var(--teal-light) !important;
}

/* ══════════════════════════════════════════
   텍스트에어리어
══════════════════════════════════════════ */
.stTextArea textarea {
  background: var(--bg-surface) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ko) !important;
  font-size: 0.94rem !important;
  line-height: 1.72 !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  resize: vertical !important;
}
.stTextArea textarea:focus {
  border-color: var(--purple) !important;
  box-shadow: 0 0 0 3px rgba(124,58,237,0.11) !important;
  outline: none !important;
}
.stTextArea textarea::placeholder {
  color: var(--text-muted) !important;
  font-size: 0.87rem !important;
}

/* ══════════════════════════════════════════
   이미지
══════════════════════════════════════════ */
.stImage img {
  border-radius: var(--r-lg) !important;
  box-shadow: var(--shadow-md) !important;
}

/* ══════════════════════════════════════════
   마크다운 — 테이블
══════════════════════════════════════════ */
.stMarkdown table {
  width: 100% !important;
  border-collapse: separate !important;
  border-spacing: 0 !important;
  border-radius: var(--r-md) !important;
  overflow: hidden !important;
  box-shadow: var(--shadow-xs) !important;
  font-size: 0.89rem !important;
  margin: 1rem 0 !important;
}
.stMarkdown th {
  background: var(--purple) !important;
  color: #fff !important;
  font-weight: 700 !important;
  padding: 12px 16px !important;
  text-align: left !important;
  font-family: var(--font-ko) !important;
}
.stMarkdown td {
  padding: 10px 16px !important;
  border-bottom: 1px solid var(--border) !important;
  background: var(--bg-surface) !important;
  color: var(--text-primary) !important;
}
.stMarkdown tr:last-child td { border-bottom: none !important; }
.stMarkdown tr:nth-child(even) td { background: var(--bg-subtle) !important; }

/* ══════════════════════════════════════════
   마크다운 — 인용문 (blockquote)
══════════════════════════════════════════ */
.stMarkdown blockquote {
  border-left: 4px solid var(--purple) !important;
  background: var(--purple-light) !important;
  border-radius: 0 var(--r-md) var(--r-md) 0 !important;
  padding: 14px 20px !important;
  margin: 1.2rem 0 !important;
  color: var(--purple-dark) !important;
  font-weight: 600 !important;
}

/* ══════════════════════════════════════════
   마크다운 — 코드
══════════════════════════════════════════ */
.stMarkdown code {
  background: var(--bg-subtle) !important;
  border: 1px solid var(--border) !important;
  border-radius: 5px !important;
  padding: 2px 6px !important;
  font-size: 0.87em !important;
  color: var(--teal-hover) !important;
}
.stMarkdown pre {
  background: var(--text-primary) !important;
  border-radius: var(--r-md) !important;
  padding: 20px !important;
  overflow-x: auto !important;
}
.stMarkdown pre code {
  background: transparent !important;
  border: none !important;
  color: #F0FDF4 !important;
  font-size: 0.9em !important;
}

/* ══════════════════════════════════════════
   구분선
══════════════════════════════════════════ */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.6rem 0 !important;
}

/* ══════════════════════════════════════════
   알림 메시지
══════════════════════════════════════════ */
.stAlert {
  border-radius: var(--r-md) !important;
  border: none !important;
}
.stAlert[kind="error"],   div[data-baseweb="notification"][kind="negative"] {
  background: #FEF2F2 !important;
  border-left: 4px solid #EF4444 !important;
}
.stAlert[kind="success"], div[data-baseweb="notification"][kind="positive"] {
  background: var(--teal-light) !important;
  border-left: 4px solid var(--teal) !important;
}
.stAlert[kind="info"],    div[data-baseweb="notification"][kind="info"] {
  background: var(--purple-light) !important;
  border-left: 4px solid var(--purple) !important;
}

/* ══════════════════════════════════════════
   해석 결과 카드 — .result-card + st.container(border=True)
══════════════════════════════════════════ */
.result-card {
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(124,58,237,0.12);
  border-radius: var(--r-xl);
  padding: 36px 40px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.07);
  margin-top: 0.5rem;
}

/* st.container(border=True) → 글래스모피즘 카드 */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255,255,255,0.84) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(124,58,237,0.15) !important;
  border-radius: var(--r-xl) !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.07) !important;
  padding: 8px !important;
}

/* ══════════════════════════════════════════
   히어로 섹션
══════════════════════════════════════════ */
.hero {
  background: linear-gradient(135deg,
    rgba(124,58,237,0.06) 0%,
    rgba(5,150,105,0.05) 100%);
  border: 1px solid rgba(124,58,237,0.1);
  border-radius: var(--r-xl);
  padding: 36px 40px 32px;
  margin-bottom: 8px;
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute;
  top: -60px; right: -60px;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%);
  border-radius: 50%;
}
.hero h1 {
  font-family: 'Montserrat', sans-serif !important;
  font-weight: 900 !important;
  font-size: 2.3rem !important;
  letter-spacing: -0.04em !important;
  color: var(--text-primary) !important;
  margin: 0 0 8px !important;
  line-height: 1.1 !important;
}
.hero h1 span { color: var(--purple); }
.hero .sub {
  font-size: 0.95rem;
  color: var(--text-secondary);
  font-family: 'Pretendard', sans-serif;
  line-height: 1.6;
  margin: 0;
}
.hero .badge-row {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-top: 20px;
}
.hero .badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 50px;
  padding: 5px 14px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-secondary);
  box-shadow: var(--shadow-xs);
}
.hero .badge i { color: var(--purple); font-size: 0.78rem; }

/* ══════════════════════════════════════════
   강의 섹션 헤더
══════════════════════════════════════════ */
.lecture-header {
  display: flex; align-items: center; gap: 14px;
  background: linear-gradient(135deg, var(--purple-light), var(--teal-light));
  border-radius: var(--r-lg);
  padding: 24px 28px;
  margin-bottom: 20px;
}
.lecture-header .icon {
  width: 52px; height: 52px;
  background: var(--purple);
  border-radius: var(--r-md);
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 1.4rem;
  box-shadow: 0 4px 14px rgba(124,58,237,0.3);
  flex-shrink: 0;
}
.lecture-header h2 {
  font-size: 1.35rem !important;
  margin: 0 0 4px !important;
  color: var(--text-primary) !important;
}
.lecture-header p {
  margin: 0 !important;
  font-size: 0.88rem !important;
  color: var(--text-secondary) !important;
}

/* ══════════════════════════════════════════
   fade-up 애니메이션
══════════════════════════════════════════ */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
.hero, .stTabs, .result-card,
.element-container, .stMarkdown,
.stButton, .stFileUploader, .stTextArea,
.stImage, .stRadio {
  animation: fadeUp 0.45s ease-out both;
}

/* ══════════════════════════════════════════
   모바일 반응형 (Mobile First)
══════════════════════════════════════════ */
@media (max-width: 768px) {
  .hero { padding: 24px 20px 20px; }
  .hero h1 { font-size: 1.7rem !important; }
  .result-card { padding: 24px 20px; }
  .stTabs [data-baseweb="tab"] {
    font-size: 0.8rem !important;
    padding: 8px 14px !important;
  }
  .lecture-header { flex-direction: column; text-align: center; }
}

/* ══════════════════════════════════════════
   접근성 — 포커스 링
══════════════════════════════════════════ */
*:focus-visible {
  outline: 2px solid var(--purple) !important;
  outline-offset: 3px !important;
}

/* skip navigation */
.skip-nav {
  position: absolute; top: -40px; left: 0;
  background: var(--purple); color: white;
  padding: 8px 16px; border-radius: 0 0 8px 0;
  font-weight: 700; text-decoration: none; z-index: 10000;
  transition: top 0.2s;
}
.skip-nav:focus { top: 0; }
</style>
"""


HERO_HTML = """
<a href="#main" class="skip-nav">본문으로 바로가기</a>
<div class="hero" id="top">
  <h1>☯ <span>육효</span>의 세계</h1>
  <p class="sub">
    AI가 읽어주는 육효 해석 &nbsp;·&nbsp; 7강 완성 입문 강의<br>
    이미지 한 장과 질문만 있으면 됩니다
  </p>
  <div class="badge-row">
    <span class="badge"><i class="fa-solid fa-bolt"></i> Gemini 3.5 Flash</span>
    <span class="badge"><i class="fa-solid fa-graduation-cap"></i> 7강 강의 수록</span>
    <span class="badge"><i class="fa-solid fa-lock"></i> API 키 암호화 보관</span>
    <span class="badge"><i class="fa-solid fa-mobile-screen"></i> 모바일 최적화</span>
  </div>
</div>
"""

LECTURE_HEADER_HTML = """
<div class="lecture-header">
  <div class="icon"><i class="fa-solid fa-book-open"></i></div>
  <div>
    <h2>육효의 모든 것</h2>
    <p>기초부터 실전 케이스까지 &mdash; 7강으로 완성하는 육효 입문</p>
  </div>
</div>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
