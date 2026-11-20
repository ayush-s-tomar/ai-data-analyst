import os

import pandas as pd
import streamlit as st
from groq import Groq

from analyst import (clean_markdown, MAX_HISTORY_MESSAGES, LLMError, analyze_dataframe,
                     answer_question)
from file_readers import MAX_FILE_MB, SUPPORTED_EXTENSIONS, data_quality, clean_numeric_text, list_sources, read_file_to_df, sensitive_columns
from report import build_report
from scriptexport import build_script
from limits import FREE_QUESTIONS_PER_SESSION, allowed

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Data Analyst", page_icon="📊", layout="wide")


def get_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:  # no secrets file configured
        key = None
    return key or os.environ.get("GROQ_API_KEY")


USER_KEY = st.sidebar.text_input(
    "Your own Groq API key (optional)", type="password",
    help="Leave empty to use the shared demo key, which is limited per session.").strip()
GROQ_API_KEY = USER_KEY or get_api_key()
USING_OWN_KEY = bool(USER_KEY)
if "questions_asked" not in st.session_state:
    st.session_state.questions_asked = 0
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is not set. Add it in Streamlit Cloud → App settings → Secrets, "
             "or in .streamlit/secrets.toml when running locally.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def suggest_questions(df: pd.DataFrame) -> list:
    """Build starter questions from the uploaded file's own columns."""
    numeric = list(df.select_dtypes("number").columns)
    categorical = [c for c in df.columns
                   if c not in numeric and 1 < df[c].nunique() <= 20 and "date" not in str(c).lower()]
    date_cols = [c for c in df.columns
                 if "date" in str(c).lower() or str(df[c].dtype).startswith("datetime")]
    ideas = []
    if numeric and categorical:
        ideas.append(f"Show a bar chart of total {numeric[0]} by {categorical[0]}")
    if numeric and date_cols:
        ideas.append(f"Show the monthly trend of {numeric[0]} as a line chart")
    if numeric:
        ideas.append(f"Show the top 5 rows by {numeric[0]}")
    if len(numeric) >= 2:
        ideas.append(f"Is there a relationship between {numeric[0]} and {numeric[1]}?")
    ideas.append("Summarise this dataset and flag anything unusual")
    return ideas[:5]


def reset_session():
    st.session_state.df = None
    st.session_state.filename = None
    st.session_state.filetype = None
    st.session_state.messages = []


for key, default in (("df", None), ("filename", None), ("filetype", None), ("messages", [])):
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
col_title, col_reset = st.columns([5, 1])
with col_title:
    st.title("📊 AI Data Analyst")
    st.caption("Upload any file. Ask questions in plain English. Get instant charts & insights.")
with col_reset:
    if st.session_state.df is not None:
        st.write("")
        if st.button("+ New File"):
            reset_session()
            st.rerun()

# ─────────────────────────────────────────────────────────────
# Upload step
# ─────────────────────────────────────────────────────────────
if st.session_state.df is None:  # noqa: C901
    uploaded = st.file_uploader(
        "Drop your file here or click to browse",
        type=[e.lstrip(".") for e in SUPPORTED_EXTENSIONS],
        help=f"CSV · Excel · TSV · JSON · PDF · Parquet · XML · SQLite · ODS · Feather (max {MAX_FILE_MB} MB)",
    )
    st.caption("🔒 Privacy: column names, data types, summary statistics and the first rows of your file are "
               "sent to Groq's API to answer your questions. Don't upload sensitive data to the public demo.")

    if uploaded is not None:
        ext = os.path.splitext(uploaded.name)[1].lower()
        data = uploaded.getvalue()
        try:
            sources = list_sources(data, uploaded.name)
        except Exception:  # noqa: BLE001 - fall back to the default reader
            sources = []
        chosen = None
        if len(sources) > 1:
            chosen = st.selectbox("This file has several sheets or tables. Choose one:", sources)
            if not st.button("Load selected"):
                st.stop()
        with st.spinner("Reading your file..."):
            try:
                df = read_file_to_df(data, uploaded.name, source=chosen)
            except Exception as exc:  # noqa: BLE001 - show any parse problem to the user
                st.error(f"Could not read this file: {exc}")
                st.stop()

        with st.spinner("Analyzing your data..."):
            try:
                analysis = analyze_dataframe(client, df, hidden=sensitive_columns(df))
            except LLMError as exc:
                analysis = f"Your file loaded, but the automatic summary is unavailable: {exc}"

        st.session_state.df = df
        st.session_state.filename = uploaded.name
        st.session_state.filetype = ext.lstrip(".").upper()
        st.session_state.messages = [{
            "role": "assistant", "content": analysis, "is_initial": True,
            "charts": [], "code_output": "", "code_error": None, "has_code": False,
        }]
        st.rerun()

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("🤖 **AI-powered analysis**")
    c2.markdown("📈 **Auto-generated charts**")
    c3.markdown("🧠 **Conversation memory**")
    c4.markdown("🛡️ **Restricted code execution**")

# ─────────────────────────────────────────────────────────────
# Chat step
# ─────────────────────────────────────────────────────────────
else:
    df = st.session_state.df
    conversation_count = len([m for m in st.session_state.messages if not m.get("is_initial")])

    st.info(f"📄 **{st.session_state.filename}** · {st.session_state.filetype} · "
            f"{len(df):,} rows · {len(df.columns)} cols")

    quality = data_quality(df)
    with st.expander("Data quality check"):
        q1, q2, q3 = st.columns(3)
        q1.metric("Duplicate rows", quality["duplicate_rows"])
        q2.metric("Missing cells", quality["missing_cells"])
        q3.metric("Numbers stored as text", len(quality["numbers_stored_as_text"]))
        if quality["columns_with_missing"]:
            st.caption("Missing values by column: " + ", ".join(f"{k} ({v})" for k, v in quality["columns_with_missing"].items()))
        if quality["numbers_stored_as_text"]:
            st.caption("Columns that look numeric but are text: " + ", ".join(quality["numbers_stored_as_text"]))
            if st.button("Convert them to numbers"):
                st.session_state.df = clean_numeric_text(df, quality["numbers_stored_as_text"])
                st.rerun()

    sidebar_col, chat_col = st.columns([1, 3])

    with sidebar_col:
        st.subheader("Dataset Columns")
        for col in df.columns:
            st.markdown(f"**{col}**")
            st.caption(f"{df[col].dtype} · {df[col].nunique()} unique")

        hidden = st.multiselect(
            "Hide values from the AI", list(df.columns), default=sensitive_columns(df),
            key=f"hidden_{st.session_state.filename}",
            help="Selected columns keep their names and types in the prompt, but their values are replaced by <hidden>.")
        if any(m["role"] == "user" for m in st.session_state.messages):
            st.download_button("Download report (.md)", build_report(st.session_state.filename, st.session_state.messages),
                               file_name="analysis-report.md", mime="text/markdown")
        if any(m["role"] == "user" for m in st.session_state.messages):
            st.download_button("Download code (.py)", build_script(st.session_state.filename, st.session_state.messages),
                               file_name="analysis.py", mime="text/x-python")
        st.subheader("Session Memory")
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        if not user_msgs:
            st.caption("Ask your first question to start building memory")
        else:
            for i, m in enumerate(user_msgs, 1):
                text = m["content"]
                st.caption(f"{i}. {text[:45] + '...' if len(text) > 45 else text}")

    with chat_col:
        with st.expander("Preview data (first 10 rows)"):
            st.dataframe(df.head(10))

        for index, msg in enumerate(st.session_state.messages):
            avatar = "🤖" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                if msg.get("is_initial"):
                    st.caption("📊 Initial Analysis")
                st.markdown(clean_markdown(msg["content"]))
                if msg.get("code_output"):
                    with st.expander("⚡ Output"):
                        st.text(msg["code_output"])
                if msg.get("code_error"):
                    with st.expander("⚠️ Code Error"):
                        st.text(msg["code_error"])
                for i, chart_bytes in enumerate(msg.get("charts", [])):
                    st.image(chart_bytes)
                    st.download_button("⬇ Download chart", chart_bytes,
                                       file_name=f"chart-{index}-{i + 1}.png", mime="image/png",
                                       key=f"dl-{index}-{i}")
                if msg.get("has_code"):
                    st.caption("🛡️ Code ran in an isolated, time-limited process with restricted imports.")

        if conversation_count == 0:
            st.caption("Try asking:")
            ideas = suggest_questions(df)
            for c, s in zip(st.columns(len(ideas)), ideas):
                if c.button(s, key=f"sugg-{s}"):
                    st.session_state.pending_question = s
                    st.rerun()

        if conversation_count > 0:
            remembered = min(len(st.session_state.messages), MAX_HISTORY_MESSAGES)
            note = " · Long chat: older messages are dropped, consider starting a new session" \
                if len(st.session_state.messages) > MAX_HISTORY_MESSAGES else ""
            st.caption(f"🧠 The AI sees your last {remembered} message(s) — ask follow-up questions naturally{note}")

        question = st.chat_input("Ask a follow-up or a new question...")
        pending = st.session_state.pop("pending_question", None)
        final_question = question or pending

        if final_question and not allowed(st.session_state.questions_asked, USING_OWN_KEY):
            st.warning(f"The shared demo key is limited to {FREE_QUESTIONS_PER_SESSION} questions per session. "
                       "Paste your own free Groq key in the sidebar to continue.")
            final_question = None
        if final_question:
            st.session_state.questions_asked += 1
            history_for_api = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
                if not m.get("is_initial") and m["role"] in ("user", "assistant")
                and not m["content"].startswith("⚠️")
            ]
            st.session_state.messages.append({
                "role": "user", "content": final_question, "charts": [],
                "code_output": "", "code_error": None, "has_code": False,
            })

            with st.spinner("Analyzing with memory context..."):
                try:
                    result = answer_question(client, final_question, df, history_for_api, hidden=hidden)
                    st.session_state.messages.append({
                        "role": "assistant", "content": result["content"],
                        "charts": result["charts"], "code_output": result["code_output"],
                        "code_error": result["code_error"], "has_code": result["has_code"],
                        "is_initial": False,
                    })
                except LLMError as exc:
                    st.session_state.messages.append({
                        "role": "assistant", "content": f"⚠️ {exc}", "charts": [],
                        "code_output": "", "code_error": None, "has_code": False,
                    })
            st.rerun()
