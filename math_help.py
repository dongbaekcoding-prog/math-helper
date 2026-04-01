import streamlit as st
import google.generativeai as genai
import random

# ════════════════════════════════════════════════════════════
# 🔑 Gemini API 키
# ════════════════════════════════════════════════════════════
GEMINI_API_KEY = st.secrests["GEMINI_API_KEY"]  # ← 본인의 Gemini API 키로 교체


st.set_page_config(page_title="수학 도우미", page_icon="🧮",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&family=Nanum+Gothic+Coding&display=swap');

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #f7f3eb !important;
    font-family: 'Gowun Dodum', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fffbf0 0%, #ffefc0 100%) !important;
    border-right: 3px solid #e8c87a;
}
[data-testid="stSidebar"] * { font-family: 'Jua', sans-serif !important; }

.sb-logo {
    font-family: 'Jua', sans-serif; font-size: 2rem; text-align: center;
    background: linear-gradient(90deg, #f4c430, #ff9800);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    padding: 6px 0 2px 0; letter-spacing: 2px;
}
.divider-label {
    text-align: center; font-family: 'Jua', sans-serif;
    font-size: 0.82rem; color: #c8a040; margin: 4px 0; letter-spacing: 2px;
}
.chat-wrap {
    display: flex; flex-direction: column; gap: 12px;
    max-height: 480px; overflow-y: auto; padding: 8px 4px;
}
.bubble-ai { display: flex; align-items: flex-start; gap: 10px; }
.char-icon {
    font-size: 2.2rem; flex-shrink: 0;
    animation: bob 2.2s ease-in-out infinite;
}
@keyframes bob {
    0%,100% { transform: translateY(0); }
    50%      { transform: translateY(-6px); }
}
.speech-ai {
    background: white; border: 2.5px solid #d4b483;
    border-radius: 6px 20px 20px 20px;
    padding: 14px 18px; font-size: 0.95rem; color: #3e2800;
    line-height: 1.75; box-shadow: 3px 4px 12px rgba(180,140,60,0.12);
    word-break: break-word; max-width: 98%;
}
.bubble-user { display: flex; justify-content: flex-end; }
.speech-user {
    background: linear-gradient(135deg, #fff8e1, #ffefc0);
    border: 2px solid #e8c87a; border-radius: 20px 6px 20px 20px;
    padding: 12px 16px; font-size: 0.95rem; color: #3e2800;
    line-height: 1.7; word-break: break-word; max-width: 98%;
}
.bubble-label {
    font-size: 0.72rem; color: #bbb; margin: 2px 6px;
    font-family: 'Nanum Gothic Coding', monospace;
}
/* 정답/오답 피드백 */
.feedback-correct {
    background: #d4edda; border: 2px solid #28a745; border-radius: 14px;
    padding: 10px 16px; color: #155724; font-family: 'Jua', sans-serif;
    font-size: 1rem; text-align: center; margin: 6px 0;
}
.feedback-wrong {
    background: #f8d7da; border: 2px solid #dc3545; border-radius: 14px;
    padding: 10px 16px; color: #721c24; font-family: 'Jua', sans-serif;
    font-size: 1rem; text-align: center; margin: 6px 0;
}
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    border-radius: 20px !important; border: 2.5px solid #e8c87a !important;
    background: #fffdf5 !important; font-family: 'Gowun Dodum', sans-serif !important;
    font-size: 1rem !important; padding: 10px 18px !important; resize: none !important;
}
.stButton > button {
    border-radius: 25px !important; border: 2px solid #e8c87a !important;
    background: white !important; color: #5a3e00 !important;
    font-family: 'Jua', sans-serif !important; font-size: 0.88rem !important;
    transition: all 0.18s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #f4c430, #ff9800) !important;
    color: white !important; border-color: #ff9800 !important;
}
.mode-now {
    display: inline-block; background: linear-gradient(90deg, #f4c430, #ff9800);
    color: white; border-radius: 20px; padding: 3px 16px;
    font-family: 'Jua', sans-serif; font-size: 0.85rem;
    box-shadow: 2px 2px 6px rgba(255,152,0,0.3); margin-bottom: 10px;
}
hr { border-color: #e8c87a !important; opacity: 0.4; }
[data-testid="stSelectbox"] > div {
    border-radius: 25px !important; border: 2px solid #e8c87a !important;
    font-family: 'Jua', sans-serif !important;
}
/* selectbox 타이핑 방지 */
[data-testid="stSelectbox"] input {
    pointer-events: none !important;
    caret-color: transparent !important;
    user-select: none !important;
}
</style>
""", unsafe_allow_html=True)


# ── 세션 초기화 ──────────────────────────────────────────────
defaults = {
    "messages":        [],     # {"role":..., "content":..., "mode":...}
    "history":         [],     # {"label":..., "mode":..., "messages":[전체 대화]}
    "mode":            "문장을 식으로",
    "pending":         "",
    "input_key":       0,
    "is_replay":       False,
    "session_saved":   False,  # 현재 세션이 이미 히스토리에 저장됐는지
    # 랜덤 문제 전용 상태
    "rand_problem":    "",     # 현재 출제된 문제 텍스트
    "rand_answer":     "",     # 정답 (Gemini가 내부적으로 알고 있는 값)
    "rand_waiting":    False,  # 문제 출제 후 학생 답 대기 중 여부
    "rand_feedback":   "",     # "correct" / "wrong" / ""
    "rand_correct_ans":"",     # 틀렸을 때 보여줄 정답
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── 상수 ─────────────────────────────────────────────────────
MODES = ["문장을 식으로", "답 도출", "랜덤 문제", "오답 풀이"]
MODE_EMOJI = {"문장을 식으로":"📝","답 도출":"🔢","랜덤 문제":"🎲","오답 풀이":"❌"}
MODE_BADGE = {"문장을 식으로":"badge-문장","답 도출":"badge-답","랜덤 문제":"badge-랜덤","오답 풀이":"badge-오답"}
MODE_SYSTEM = {
    "문장을 식으로": "수학 문장제를 수식으로 간결하게 변환해 주세요. 핵심 단계만 짧게, 3줄 이내로. 한국어로.",
    "답 도출":       "수학 문제의 답을 구해 주세요. 핵심 단계만 간단히 보여주고 최종 답을 명확히. 한국어로.",
    "랜덤 문제":     "",  # 별도 처리
    "오답 풀이":     "학생의 오답에서 틀린 부분을 한 줄로 짚고 올바른 풀이를 간단히 보여주세요. 한국어로.",
}
RAND_PROBLEMS = [
    ("2x - 3y = 7, y = 2일 때 x의 값은?",          "x = 13/2"),
    ("5의 배수 중 가장 작은 두 자리 수는?",          "10"),
    ("삼각형의 세 각의 합은 몇 도인가요?",            "180"),
    ("1부터 10까지 자연수의 합은?",                  "55"),
    ("x² - 5x + 6 = 0에서 x의 값 두 개는? (쉼표로)", "2, 3"),
    ("반지름 5cm인 원의 넓이는? (π=3.14, 소수점 버림)","78"),
    ("3/4 + 1/4 를 계산하세요.",                     "1"),
    ("소수(Prime) 중 10 이하인 수의 개수는?",         "4"),
    ("가로3 세로4 높이5인 직육면체의 부피는?",         "60"),
    ("2의 10제곱은?",                                "1024"),
]


# ── Gemini 호출 ───────────────────────────────────────────────
def call_gemini(prompt: str) -> str:
    import time, re
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    for attempt in range(3):
        try:
            return model.generate_content(prompt).text
        except Exception as e:
            err = str(e)
            if "429" in err:
                match = re.search(r"retry[^\d]*(\d+)", err)
                wait  = min(int(match.group(1)) if match else 60, 65)
                if attempt < 2:
                    st.warning(f"⏳ 잠시 후 재시도합니다... ({wait}초 대기 중)")
                    time.sleep(wait)
                else:
                    return "❌ 요청 한도 초과. 1~2분 후 다시 시도해 주세요."
            else:
                return f"❌ 오류: {e}"
    return "❌ 재시도 실패."


def ask_gemini(question: str) -> str:
    """일반 모드 질문"""
    mode = st.session_state.mode
    system = (
        "당신은 초등학생과 중학생을 위한 수학 선생님 AI입니다.\n"
        f"현재 모드: [{mode}]\n지시: {MODE_SYSTEM[mode]}\n"
        "답변은 짧고 간결하게 핵심만. 인사말 없이. 이모지 최소. 한국어로."
    )
    ctx = "\n".join(
        f"{'학생' if m['role']=='user' else '선생님'}: {m['content']}"
        for m in st.session_state.messages[-6:]
    )
    return call_gemini(f"{system}\n\n대화:\n{ctx}\n\n학생: {question}\n선생님:")


def generate_rand_problem() -> str:
    """랜덤 문제 출제 — 문제 텍스트만 반환, 정답은 세션에 저장"""
    prob, ans = random.choice(RAND_PROBLEMS)
    st.session_state.rand_problem    = prob
    st.session_state.rand_answer     = ans
    st.session_state.rand_waiting    = True
    st.session_state.rand_feedback   = ""
    st.session_state.rand_correct_ans= ""
    return f"🎲 문제: {prob}"


def check_rand_answer(student_ans: str) -> tuple[bool, str]:
    """학생 답을 Gemini에게 채점 요청"""
    prob       = st.session_state.rand_problem
    correct    = st.session_state.rand_answer
    prompt = (
        f"수학 문제: {prob}\n"
        f"정답: {correct}\n"
        f"학생 답: {student_ans}\n\n"
        "학생의 답이 정답과 같은지 판단하세요. "
        "숫자 표현이 달라도 값이 같으면 정답입니다. "
        "첫 줄에 반드시 '정답' 또는 '오답' 중 하나만 쓰고, "
        "둘째 줄에 한 줄 이내로 간단한 이유를 한국어로 쓰세요."
    )
    result = call_gemini(prompt)
    is_correct = result.strip().startswith("정답")
    return is_correct, result


# ════════════════════════════════════════════════════════════
# 사이드바
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sb-logo">🧮 수학 도우미</div>', unsafe_allow_html=True)
    st.markdown("---")

    if st.button("✏️ 새 풀이", use_container_width=True):
        st.session_state.messages        = []
        st.session_state.input_key      += 1
        st.session_state.rand_problem    = ""
        st.session_state.rand_waiting    = False
        st.session_state.rand_feedback   = ""
        st.session_state.session_saved   = False
        st.rerun()

    if st.button("🗑️ 이전 기록 삭제", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    st.markdown('<div class="divider-label">────  이전  ────</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown(
            '<div style="font-family:Jua,sans-serif;font-size:0.8rem;color:#c8a040;'
            'text-align:center;padding:10px 0;">아직 풀이 기록이 없어요</div>',
            unsafe_allow_html=True
        )
    else:
        for i, h in enumerate(reversed(st.session_state.history)):
            emoji = MODE_EMOJI.get(h["mode"], "📝")
            label = h.get("label", "")
            if st.button(f"{emoji} [{h['mode']}]  {label}", key=f"hist_{i}", use_container_width=True):
                # 다시보기: 전체 대화 복원, 히스토리에 추가 안 함
                st.session_state.messages      = list(h["messages"])
                st.session_state.mode          = h["mode"]
                st.session_state.is_replay     = True
                st.session_state.session_saved = True   # 복원된 세션은 다시 저장 안 함
                st.session_state.rand_waiting  = False
                st.session_state.rand_feedback = ""
                st.session_state.rand_problem  = ""
                st.session_state.input_key    += 1
                st.rerun()


# ════════════════════════════════════════════════════════════
# 메인 영역
# ════════════════════════════════════════════════════════════
main_left, main_right = st.columns([3, 2])

# ── 왼쪽: 채팅 ───────────────────────────────────────────────
with main_left:
    st.markdown(
        f'<div class="mode-now">{MODE_EMOJI[st.session_state.mode]} 현재 모드: {st.session_state.mode}</div>',
        unsafe_allow_html=True
    )

    chat_html = '<div class="chat-wrap">'
    if not st.session_state.messages:
        chat_html += (
            '<div class="bubble-ai"><span class="char-icon">🤖</span><div>'
            '<div class="bubble-label">수학봇</div>'
            '<div class="speech-ai">안녕하세요! 저는 수학 도우미예요 😊<br>'
            '오른쪽 아래 <b>mode</b>로 모드를 선택하고 질문해 보세요!</div>'
            '</div></div>'
        )
    else:
        for msg in st.session_state.messages:
            content = msg["content"].replace("\n", "<br>")
            if msg["role"] == "assistant":
                chat_html += (
                    f'<div class="bubble-ai"><span class="char-icon">🤖</span><div>'
                    f'<div class="bubble-label">수학봇</div>'
                    f'<div class="speech-ai">{content}</div></div></div>'
                )
            else:
                chat_html += (
                    f'<div class="bubble-user"><div>'
                    f'<div class="bubble-label" style="text-align:right;">나 ✏️</div>'
                    f'<div class="speech-user">{content}</div>'
                    f'</div></div>'
                )

    # 정답/오답 피드백 표시
    if st.session_state.rand_feedback == "correct":
        chat_html += '<div class="feedback-correct">🎉 정답이에요! 다음 문제로 넘어갑니다...</div>'
    elif st.session_state.rand_feedback == "wrong":
        chat_html += (
            f'<div class="feedback-wrong">❌ 오답이에요!<br>'
            f'정답: <b>{st.session_state.rand_correct_ans}</b></div>'
        )

    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)


# ── 오른쪽: 입력 + mode ──────────────────────────────────────
with main_right:
    is_rand = st.session_state.mode == "랜덤 문제"

    # ── 랜덤 모드: 문제 출제 버튼 (문제 대기 중이 아닐 때)
    if is_rand and not st.session_state.rand_waiting:
        if st.button("🎲 문제 출제", use_container_width=True):
            problem_text = generate_rand_problem()
            st.session_state.messages.append(
                {"role": "assistant", "content": problem_text, "mode": "랜덤 문제"}
            )
            st.rerun()

    # ── 일반 모드 or 랜덤 대기 중: 입력창 표시
    show_input = (not is_rand) or st.session_state.rand_waiting

    if show_input:
        placeholder_text = "답 입력" if (is_rand and st.session_state.rand_waiting) else "수학 문제를 입력하세요..."
        st.markdown('<p style="font-family:Jua,sans-serif;font-size:0.82rem;color:#9a7200;margin-bottom:4px;">✏️ 입력</p>', unsafe_allow_html=True)
        user_input = st.text_area(
            "입력",
            placeholder=placeholder_text,
            label_visibility="collapsed",
            height=90,
            key=f"main_input_{st.session_state.input_key}",
        )

        send_col, mode_col = st.columns([2, 3])
        with send_col:
            send_btn = st.button("전송 ➤", use_container_width=True)
        with mode_col:
            mode_options = [f"{MODE_EMOJI[m]} {m}" for m in MODES]
            sel_raw = st.selectbox(
                "mode", mode_options,
                index=MODES.index(st.session_state.mode),
                label_visibility="collapsed",
                key="mode_select",
            )
            sel_mode = sel_raw.split(" ", 1)[1]
            if sel_mode != st.session_state.mode:
                st.session_state.mode          = sel_mode
                st.session_state.messages      = []
                st.session_state.rand_waiting  = False
                st.session_state.rand_feedback = ""
                st.session_state.rand_problem  = ""
                st.session_state.rand_answer   = ""
                st.session_state.rand_correct_ans = ""
                st.session_state.session_saved = False
                st.session_state.input_key    += 1
                st.rerun()
    else:
        # 랜덤 모드인데 아직 문제 안 출제된 상태 → mode selectbox만 표시
        user_input = ""
        send_btn   = False
        mode_options = [f"{MODE_EMOJI[m]} {m}" for m in MODES]
        sel_raw = st.selectbox(
            "mode", mode_options,
            index=MODES.index(st.session_state.mode),
            label_visibility="collapsed",
            key="mode_select",
        )
        sel_mode = sel_raw.split(" ", 1)[1]
        if sel_mode != st.session_state.mode:
            st.session_state.mode          = sel_mode
            st.session_state.messages      = []
            st.session_state.rand_waiting  = False
            st.session_state.rand_feedback = ""
            st.session_state.rand_problem  = ""
            st.session_state.rand_answer   = ""
            st.session_state.rand_correct_ans = ""
            st.session_state.session_saved = False
            st.session_state.input_key    += 1
            st.rerun()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages     = []
        st.session_state.rand_waiting = False
        st.session_state.rand_feedback= ""
        st.session_state.input_key   += 1
        st.rerun()


# ════════════════════════════════════════════════════════════
# 전송 처리
# ════════════════════════════════════════════════════════════
final_q = st.session_state.pending or (user_input.strip() if send_btn else "")

if final_q:
    st.session_state.pending    = ""
    st.session_state.input_key += 1

    # ── 랜덤 문제 답 채점 ──────────────────────────────────
    if st.session_state.mode == "랜덤 문제" and st.session_state.rand_waiting:
        st.session_state.messages.append(
            {"role": "user", "content": final_q, "mode": "랜덤 문제"}
        )
        with st.spinner("🤔 채점 중..."):
            is_correct, feedback_text = check_rand_answer(final_q)

        if is_correct:
            st.session_state.rand_feedback = "correct"
            st.session_state.messages.append(
                {"role": "assistant", "content": "🎉 정답이에요! 잘했어요!", "mode": "랜덤 문제"}
            )
            # 히스토리 저장 (랜덤 문제 정답 기록 — messages 스냅샷)
            if not st.session_state.is_replay:
                first_q = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), st.session_state.rand_problem)
                label   = first_q[:18] + ("…" if len(first_q) > 18 else "")
                if not st.session_state.session_saved:
                    st.session_state.history.append({
                        "label":    label,
                        "mode":     "랜덤 문제",
                        "messages": list(st.session_state.messages),
                    })
                    st.session_state.session_saved = True
                else:
                    if st.session_state.history:
                        st.session_state.history[-1]["messages"] = list(st.session_state.messages)
            # 다음 문제 자동 출제
            st.session_state.rand_waiting  = False
            st.session_state.rand_feedback = ""
            new_prob = generate_rand_problem()
            st.session_state.messages.append(
                {"role": "assistant", "content": new_prob, "mode": "랜덤 문제"}
            )
        else:
            correct_ans = st.session_state.rand_answer
            st.session_state.rand_feedback    = "wrong"
            st.session_state.rand_correct_ans = correct_ans
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ 오답이에요!\n정답은 **{correct_ans}** 입니다.\n다시 도전해 보세요!",
                "mode": "랜덤 문제",
            })
            # 오답: 입력창 유지 (rand_waiting = True 유지)

        st.rerun()

    # ── 일반 모드 질문 ──────────────────────────────────────
    else:
        st.session_state.messages.append(
            {"role": "user", "content": final_q, "mode": st.session_state.mode}
        )
        with st.spinner("🤔 수학봇이 생각 중이에요..."):
            answer = ask_gemini(final_q)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "mode": st.session_state.mode}
        )

        # 히스토리 저장: 세션 첫 질문 시 새 항목 추가, 이후엔 messages 스냅샷 갱신
        if not st.session_state.is_replay:
            first_q = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), final_q)
            label   = first_q[:18] + ("…" if len(first_q) > 18 else "")
            if not st.session_state.session_saved:
                # 첫 질문 → 새 히스토리 항목 생성
                st.session_state.history.append({
                    "label":    label,
                    "mode":     st.session_state.mode,
                    "messages": list(st.session_state.messages),
                })
                st.session_state.session_saved = True
            else:
                # 이후 대화 → 마지막 항목의 messages 스냅샷 갱신
                if st.session_state.history:
                    st.session_state.history[-1]["messages"] = list(st.session_state.messages)
        st.session_state.is_replay = False

        st.rerun()