# style.py — Happy Hues Palette #14 + Neo-Brutalist Design System
# Colors: bg #fffffe · headline #272343 · paragraph #2d334a
#         button #ffd803 · secondary #e3f6f5 · tertiary #bae8e8

import streamlit as st

CUSTOM_CSS = """
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;900&display=swap"
  rel="stylesheet">

<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

/* ══════════════════════════════════════
   CSS Variables — Happy Hues #14
══════════════════════════════════════ */
:root {
  --bg:        #fffffe;
  --bg-card:   #fffffe;
  --bg-sec:    #e3f6f5;
  --bg-ter:    #bae8e8;
  --head:      #272343;
  --body:      #2d334a;
  --muted:     #6b7280;
  --accent:    #ffd803;
  --stroke:    #272343;
  --border:    rgba(39,35,67,0.14);

  --shadow-flat-sm:  3px 3px 0 var(--bg-ter);
  --shadow-flat-md:  5px 5px 0 var(--bg-ter);
  --shadow-flat-lg:  6px 6px 0 var(--stroke);

  --r-sm: 8px;
  --r-md: 14px;
  --r-lg: 20px;
  --r-xl: 24px;

  --font-ko: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-en: 'Montserrat', sans-serif;
}

/* ══════════════════════════════════════
   Global
══════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
  background-color: var(--bg) !important;
  font-family: var(--font-ko) !important;
  color: var(--body) !important;
}

/* ══════════════════════════════════════
   Header
══════════════════════════════════════ */
header[data-testid="stHeader"] {
  background: rgba(255,255,254,0.92) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border-bottom: 2px solid var(--border) !important;
}

/* ══════════════════════════════════════
   Sidebar
══════════════════════════════════════ */
[data-testid="stSidebar"] {
  background-color: var(--bg-sec) !important;
  border-right: 2px solid var(--border) !important;
}
[data-testid="stSidebar"] h3 {
  font-family: var(--font-en) !important;
  font-weight: 700 !important;
  font-size: 0.78rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
  color: var(--head) !important;
  margin-top: 1.4rem !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li {
  font-size: 0.87rem !important;
  color: var(--body) !important;
  line-height: 1.65 !important;
}
[data-testid="stSidebar"] .stTextInput input {
  background: var(--bg) !important;
  border: 2px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--head) !important;
}
[data-testid="stSidebar"] .stTextInput input:focus {
  border-color: var(--stroke) !important;
  box-shadow: var(--shadow-flat-sm) !important;
  outline: none !important;
}

/* ══════════════════════════════════════
   Typography
══════════════════════════════════════ */
h1 {
  font-family: var(--font-en) !important;
  font-weight: 900 !important;
  color: var(--head) !important;
  letter-spacing: -0.04em !important;
  line-height: 1.1 !important;
}
h2 {
  font-family: var(--font-en) !important;
  font-weight: 700 !important;
  color: var(--head) !important;
  letter-spacing: -0.02em !important;
}
h3, h4 {
  font-family: var(--font-ko) !important;
  font-weight: 700 !important;
  color: var(--head) !important;
}
p, li {
  font-family: var(--font-ko) !important;
  color: var(--body) !important;
  line-height: 1.78 !important;
}

/* ══════════════════════════════════════
   Buttons — Yellow Neo-Brutalist
══════════════════════════════════════ */
.stButton > button {
  background: var(--accent) !important;
  color: var(--head) !important;
  border: 2px solid var(--stroke) !important;
  border-radius: var(--r-md) !important;
  font-family: var(--font-ko) !important;
  font-weight: 700 !important;
  font-size: 0.97rem !important;
  padding: 12px 24px !important;
  letter-spacing: 0.01em !important;
  cursor: pointer !important;
  box-shadow: var(--shadow-flat-md) !important;
  transition: transform 0.12s ease, box-shadow 0.12s ease !important;
  position: relative !important;
}
.stButton > button:hover:not(:disabled) {
  transform: translate(-2px, -2px) !important;
  box-shadow: 7px 7px 0 var(--stroke) !important;
}
.stButton > button:active:not(:disabled) {
  transform: translate(2px, 2px) !important;
  box-shadow: 2px 2px 0 var(--stroke) !important;
}
.stButton > button:disabled {
  background: #e5e7eb !important;
  color: #9ca3af !important;
  border-color: #d1d5db !important;
  box-shadow: none !important;
  cursor: not-allowed !important;
  transform: none !important;
}

/* ══════════════════════════════════════
   File Uploader
══════════════════════════════════════ */
[data-testid="stFileUploader"] {
  background: var(--bg-sec) !important;
  border: 2px dashed var(--border) !important;
  border-radius: var(--r-lg) !important;
  transition: border-color 0.2s, background 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--stroke) !important;
  background: var(--bg-ter) !important;
}

/* ══════════════════════════════════════
   Textarea
══════════════════════════════════════ */
.stTextArea textarea {
  background: var(--bg-sec) !important;
  border: 2px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--head) !important;
  font-family: var(--font-ko) !important;
  font-size: 0.94rem !important;
  line-height: 1.72 !important;
  resize: vertical !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextArea textarea:focus {
  border-color: var(--stroke) !important;
  box-shadow: var(--shadow-flat-sm) !important;
  outline: none !important;
}
.stTextArea textarea::placeholder {
  color: var(--muted) !important;
  font-size: 0.87rem !important;
}

/* ══════════════════════════════════════
   Selectbox
══════════════════════════════════════ */
.stSelectbox [data-baseweb="select"] > div {
  background: var(--bg-sec) !important;
  border: 2px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--head) !important;
}
.stSelectbox [data-baseweb="select"] > div:focus-within {
  border-color: var(--stroke) !important;
  box-shadow: var(--shadow-flat-sm) !important;
}

/* ══════════════════════════════════════
   Expander
══════════════════════════════════════ */
.stExpander {
  border: 2px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  background: var(--bg-sec) !important;
}
.stExpander summary {
  font-weight: 600 !important;
  color: var(--head) !important;
}

/* ══════════════════════════════════════
   Image
══════════════════════════════════════ */
.stImage img {
  border-radius: var(--r-lg) !important;
  border: 2px solid var(--border) !important;
  box-shadow: var(--shadow-flat-md) !important;
}

/* ══════════════════════════════════════
   Markdown — Tables
══════════════════════════════════════ */
.stMarkdown table {
  width: 100% !important;
  border-collapse: separate !important;
  border-spacing: 0 !important;
  border: 2px solid var(--stroke) !important;
  border-radius: var(--r-md) !important;
  overflow: hidden !important;
  font-size: 0.89rem !important;
  margin: 1rem 0 !important;
  box-shadow: var(--shadow-flat-sm) !important;
}
.stMarkdown th {
  background: var(--head) !important;
  color: var(--accent) !important;
  font-weight: 700 !important;
  padding: 12px 16px !important;
  text-align: left !important;
  font-family: var(--font-ko) !important;
  letter-spacing: 0.03em !important;
}
.stMarkdown td {
  padding: 10px 16px !important;
  border-bottom: 1px solid var(--border) !important;
  background: var(--bg) !important;
  color: var(--body) !important;
}
.stMarkdown tr:last-child td { border-bottom: none !important; }
.stMarkdown tr:nth-child(even) td { background: var(--bg-sec) !important; }

/* ══════════════════════════════════════
   Markdown — Blockquote
══════════════════════════════════════ */
.stMarkdown blockquote {
  border-left: 4px solid var(--accent) !important;
  background: #fffde7 !important;
  border-radius: 0 var(--r-md) var(--r-md) 0 !important;
  padding: 14px 20px !important;
  margin: 1.2rem 0 !important;
  color: var(--head) !important;
  font-weight: 600 !important;
  border: 2px solid var(--border) !important;
  border-left: 4px solid var(--accent) !important;
}

/* ══════════════════════════════════════
   Markdown — Code
══════════════════════════════════════ */
.stMarkdown code {
  background: var(--bg-sec) !important;
  border: 1px solid var(--border) !important;
  border-radius: 5px !important;
  padding: 2px 6px !important;
  font-size: 0.87em !important;
  color: var(--head) !important;
}

/* ══════════════════════════════════════
   Radio — 퀴즈용 (clean, no card style)
══════════════════════════════════════ */
.stRadio [role="radiogroup"] label {
  cursor: pointer !important;
  padding: 6px 4px !important;
  transition: color 0.15s !important;
}
.stRadio [role="radiogroup"] label:hover {
  color: var(--head) !important;
}

/* ══════════════════════════════════════
   Container (border=True) — Result Card
══════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--bg-sec) !important;
  border: 2px solid var(--stroke) !important;
  border-radius: var(--r-xl) !important;
  box-shadow: var(--shadow-flat-lg) !important;
  padding: 8px !important;
}

/* ══════════════════════════════════════
   HR
══════════════════════════════════════ */
hr {
  border: none !important;
  border-top: 2px solid var(--border) !important;
  margin: 1.6rem 0 !important;
}

/* ══════════════════════════════════════
   Alerts
══════════════════════════════════════ */
.stAlert {
  border-radius: var(--r-md) !important;
  border: 2px solid var(--border) !important;
  font-family: var(--font-ko) !important;
}

/* ══════════════════════════════════════
   Success / Info / Warning
══════════════════════════════════════ */
div[data-testid="stNotification"] {
  border-radius: var(--r-md) !important;
  border: 2px solid var(--border) !important;
}

/* ══════════════════════════════════════
   Spinner
══════════════════════════════════════ */
.stSpinner > div {
  border-top-color: var(--head) !important;
}

/* ══════════════════════════════════════
   Caption
══════════════════════════════════════ */
.stCaption, [data-testid="stCaptionContainer"] {
  color: var(--muted) !important;
  font-size: 0.82rem !important;
}

/* ══════════════════════════════════════
   Fade-up animation
══════════════════════════════════════ */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
.stMarkdown, .stButton, .stFileUploader, .stTextArea, .stImage {
  animation: fadeUp 0.38s ease-out both;
}

/* ══════════════════════════════════════
   Focus ring
══════════════════════════════════════ */
*:focus-visible {
  outline: 2px solid var(--head) !important;
  outline-offset: 3px !important;
}

/* ══════════════════════════════════════
   Mobile
══════════════════════════════════════ */
@media (max-width: 768px) {
  .stButton > button { padding: 11px 18px !important; font-size: 0.9rem !important; }
}
</style>
"""


HERO_HTML = """
<div style="
  background: #e3f6f5;
  border: 2px solid #272343;
  border-radius: 24px;
  padding: 32px 36px 28px;
  margin-bottom: 20px;
  box-shadow: 6px 6px 0 #bae8e8;
  position: relative;
  overflow: hidden;
">
  <div style="
    font-family: 'Montserrat', sans-serif;
    font-weight: 900;
    font-size: 2.2rem;
    letter-spacing: -0.04em;
    color: #272343;
    margin: 0 0 6px;
    line-height: 1.1;
  ">☯ 육효의 세계</div>
  <div style="
    font-size: 0.98rem;
    color: #2d334a;
    font-style: italic;
    margin: 0 0 20px;
    line-height: 1.6;
    font-family: 'Pretendard', sans-serif;
  ">하늘이 흔들리는 순간을 여섯 개의 획으로 읽는 오래된 지혜</div>
</div>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
