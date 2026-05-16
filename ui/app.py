import streamlit as st
import httpx
import os
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Criterion", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

* { font-family: 'Inter', sans-serif; }

[data-testid="stSidebar"] {
    background-color: #4A1528;
}
[data-testid="stSidebar"] * {
    color: #F5F0E8 !important;
}
[data-testid="stSidebar"] .stRadio > div {
    gap: 0.5rem;
}

.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: #2c3e50;
    margin-bottom: 1.5rem;
    letter-spacing: -0.5px;
}
.racing-stripe {
    height: 4px;
    background: linear-gradient(90deg, #9b2c2c 0%, #c0392b 60%, #4A1528 100%);
    border-radius: 2px;
    margin-bottom: 2rem;
}
.result-pass {
    background: linear-gradient(135deg, rgba(155,44,44,0.07), rgba(192,57,43,0.02));
    border-left: 4px solid #9b2c2c;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-top: 1.5rem;
}
.result-fail {
    background: linear-gradient(135deg, rgba(44,62,80,0.07), rgba(44,62,80,0.02));
    border-left: 4px solid #64748b;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-top: 1.5rem;
}
.score-big {
    font-size: 3rem;
    font-weight: 900;
    color: #9b2c2c;
    line-height: 1;
}
.result-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.25rem;
}
.history-card {
    background: white;
    border-radius: 16px;
    padding: 1.25rem 1.75rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #f1f5f9;
    margin-bottom: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: box-shadow 0.2s ease;
}
.history-card:hover {
    box-shadow: 0 6px 20px rgba(155,44,44,0.12);
}
.rank-card {
    background: white;
    border-radius: 20px;
    padding: 1.5rem 2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid #f1f5f9;
    margin-bottom: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.rank-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(155,44,44,0.12);
}
.rank-model {
    font-size: 1.1rem;
    font-weight: 700;
    color: #2c3e50;
}
.rank-stat {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 2px;
}
.rank-score {
    font-size: 2rem;
    font-weight: 900;
    color: #9b2c2c;
}
.stTextInput input, .stTextArea textarea {
    border-radius: 12px !important;
    border: 1.5px solid #e2e8f0 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #9b2c2c !important;
    box-shadow: 0 0 0 3px rgba(155,44,44,0.1) !important;
}
.stSelectbox label, .stTextInput label, .stTextArea label {
    color: #7B2D3E !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
.stButton > button {
    background: #9b2c2c !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 0.55rem 2rem !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 1px !important;
    box-shadow: 0 4px 12px rgba(155,44,44,0.25) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: #c0392b !important;
    box-shadow: 0 8px 20px rgba(155,44,44,0.4) !important;
}
</style>
""", unsafe_allow_html=True)

page = st.sidebar.radio("Navigate", ["Submit Evaluation", "History", "Leaderboard"])

st.markdown("""
<div style='font-size:2.8rem; font-weight:900; color:#9b2c2c; letter-spacing:5px; margin-bottom:0.75rem;'>
    CRITERION
</div>
<div class="racing-stripe"></div>
""", unsafe_allow_html=True)

if page == "Submit Evaluation":
    st.markdown('<div class="page-title">Submit Evaluation</div>', unsafe_allow_html=True)
    input_text = st.text_input("Input")
    prediction = st.text_area("Prediction", height=100)
    reference = st.text_area("Reference", height=100)
    grader = st.selectbox("Grader", ["exact_match", "contains_match", "regex_match", "llm_judge"])
    model_name = st.text_input("Model name (optional)")

    if st.button("RUN EVALUATION"):
        if not prediction or not reference:
            st.warning("Prediction and Reference are required.")
        else:
            payload = {
                "input": input_text,
                "prediction": prediction,
                "reference": reference,
                "grader_name": grader,
                "model_name": model_name or "unknown"
            }
            res = httpx.post(f"{API_URL}/jobs", json=payload)
            data = res.json()
            score = data.get("score", 0)
            passed = data.get("passed", False)
            reasoning = data.get("reasoning", "")
            verdict = "PASSED" if passed else "FAILED"
            result_class = "result-pass" if passed else "result-fail"
            reasoning_html = f"<div style='margin-top:0.75rem; font-size:0.85rem; color:#2c3e50;'>{reasoning}</div>" if reasoning else ""
            st.markdown(f"""
            <div class="{result_class}">
                <div class="result-label">{verdict}</div>
                <div class="score-big">{score}</div>
                <div style="font-size:0.82rem; color:#94a3b8; margin-top:0.4rem;">
                    {grader} &nbsp;·&nbsp; {model_name or 'unnamed'}
                </div>
                {reasoning_html}
            </div>
            """, unsafe_allow_html=True)

elif page == "History":
    st.markdown('<div class="page-title">History</div>', unsafe_allow_html=True)
    res = httpx.get(f"{API_URL}/history")
    history = res.json()
    if not history:
        st.info("No evaluations yet.")
    else:
        for entry in history:
            score = entry.get("score", 0)
            passed = entry.get("passed", 0)
            color = "#9b2c2c" if passed else "#64748b"
            verdict = "PASS" if passed else "FAIL"
            preview = str(entry.get("prediction", ""))[:60]
            st.markdown(f"""
            <div class="history-card">
                <div>
                    <div style="font-weight:700; color:#2c3e50; font-size:0.95rem;">
                        {entry.get('model_name') or 'unnamed'}
                        <span style="font-weight:400; color:#94a3b8; font-size:0.8rem;">
                            &nbsp;·&nbsp; {entry.get('grader_name', '')}
                        </span>
                    </div>
                    <div style="font-size:0.75rem; color:#cbd5e1; margin-top:2px;">
                        {entry.get('created_at', '')}
                    </div>
                    <div style="font-size:0.82rem; color:#94a3b8; margin-top:6px;">
                        {preview}...
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.6rem; font-weight:900; color:{color};">{score}</div>
                    <div style="font-size:0.68rem; font-weight:700; letter-spacing:1px; color:{color};">{verdict}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

elif page == "Leaderboard":
    st.markdown('<div class="page-title">Leaderboard</div>', unsafe_allow_html=True)
    res = httpx.get(f"{API_URL}/jobs/leaderboard")
    board = res.json()
    if not board:
        st.info("No models on the leaderboard yet.")
    else:
        for i, model in enumerate(board):
            rank = i + 1
            rank_display = f"0{rank}" if rank < 10 else str(rank)
            st.markdown(f"""
            <div class="rank-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:2.2rem; font-weight:900; color:#9b2c2c; opacity:0.15; line-height:1;">
                            {rank_display}
                        </div>
                        <div class="rank-model">{model.get('model_name', 'unknown')}</div>
                        <div class="rank-stat">
                            {model.get('total_runs', 0)} runs &nbsp;·&nbsp; {model.get('pass_rate', 0)}% pass rate
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div class="rank-score">{model.get('avg_score', 0)}</div>
                        <div class="rank-stat">avg score</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("Full table"):
            st.dataframe(board, use_container_width=True)