import streamlit as st
import pandas as pd
import io
import json
import os
import traceback
import sqlite3
import tempfile
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from groq import Groq

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Data Analyst", page_icon="📊", layout="wide")

GROQ_MODEL = "openai/gpt-oss-120b"
SUPPORTED_EXTENSIONS = [
    '.csv', '.xlsx', '.xls', '.tsv', '.json',
    '.parquet', '.xml', '.db', '.sqlite', '.sqlite3',
    '.pdf', '.ods', '.feather', '.pkl', '.pickle'
]

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is not set. Add it in Streamlit Cloud → App settings → Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────────────────────
# File parsing (ported from backend/main.py::read_file_to_df)
# ─────────────────────────────────────────────────────────────
def read_file_to_df(contents: bytes, filename: str) -> pd.DataFrame:
    ext = os.path.splitext(filename)[1].lower()

    if ext == '.csv':
        return pd.read_csv(io.BytesIO(contents))
    elif ext in ['.xlsx', '.xls']:
        return pd.read_excel(io.BytesIO(contents))
    elif ext == '.ods':
        return pd.read_excel(io.BytesIO(contents), engine='odf')
    elif ext == '.tsv':
        return pd.read_csv(io.BytesIO(contents), sep='\t')
    elif ext == '.json':
        try:
            return pd.read_json(io.BytesIO(contents))
        except Exception:
            data = json.loads(contents)
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                return pd.DataFrame([data]) if not any(isinstance(v, list) for v in data.values()) else pd.DataFrame(data)
            raise ValueError("Cannot convert JSON structure to table")
    elif ext == '.parquet':
        return pd.read_parquet(io.BytesIO(contents))
    elif ext == '.feather':
        return pd.read_feather(io.BytesIO(contents))
    elif ext in ['.pkl', '.pickle']:
        return pd.read_pickle(io.BytesIO(contents))
    elif ext == '.xml':
        try:
            return pd.read_xml(io.BytesIO(contents))
        except Exception:
            root = ET.fromstring(contents)
            records = []
            for child in root:
                records.append({subchild.tag: subchild.text for subchild in child})
            if not records:
                records = [{child.tag: child.text for child in root}]
            return pd.DataFrame(records)
    elif ext in ['.db', '.sqlite', '.sqlite3']:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        conn = sqlite3.connect(tmp_path)
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        if tables.empty:
            raise ValueError("No tables found in SQLite database")
        table_name = tables['name'].iloc[0]
        df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
        conn.close()
        os.unlink(tmp_path)
        return df
    elif ext == '.pdf':
        try:
            import pdfplumber
            text_data = []
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            text_data.extend(table)
            if text_data and len(text_data) > 1:
                headers = text_data[0]
                rows = text_data[1:]
                return pd.DataFrame(rows, columns=headers)
            else:
                with pdfplumber.open(io.BytesIO(contents)) as pdf:
                    lines = []
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            lines.extend(text.split('\n'))
                return pd.DataFrame({'text': [l for l in lines if l.strip()]})
        except ImportError:
            raise ValueError("PDF support requires pdfplumber. Add it to requirements.txt")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def df_to_string(df: pd.DataFrame, max_rows: int = 50) -> str:
    info = []
    info.append(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    info.append(f"\nColumns: {list(df.columns)}")
    info.append(f"\nDtypes:\n{df.dtypes.to_string()}")
    info.append(f"\nFirst {min(max_rows, len(df))} rows:\n{df.head(max_rows).to_string()}")
    info.append(f"\nBasic Statistics:\n{df.describe(include='all').to_string()}")
    null_counts = df.isnull().sum()
    if null_counts.any():
        info.append(f"\nNull counts:\n{null_counts[null_counts > 0].to_string()}")
    return "\n".join(info)


def chat(system: str, messages: list, max_tokens: int = 2000) -> str:
    groq_messages = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=groq_messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content


def execute_python_code(code: str, df: pd.DataFrame) -> dict:
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    charts = []
    output_text = ""
    error = None
    try:
        plt.close('all')
        local_vars = {
            'df': df.copy(), 'pd': pd, 'plt': plt,
            'json': json, '__builtins__': __builtins__,
        }
        exec(code, local_vars)
        output_text = mystdout.getvalue()
        for fig in [plt.figure(i) for i in plt.get_fignums()]:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
            buf.seek(0)
            charts.append(buf.getvalue())
            plt.close(fig)
    except Exception as e:
        error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout
        plt.close('all')
    return {"output": output_text, "charts": charts, "error": error}


def analyze_dataframe(df: pd.DataFrame) -> str:
    df_summary = df_to_string(df)
    system = "You are an expert data analyst. Be concise, insightful, and use clear markdown formatting."
    user_msg = f"""Analyze this dataset and provide:
1. A brief summary of what the data contains
2. Key observations and patterns
3. 3-5 specific questions this data can answer
4. Suggested analyses to run

Dataset info:
{df_summary}"""
    return chat(system, [{"role": "user", "content": user_msg}], max_tokens=1200)


def answer_question(question: str, df: pd.DataFrame, history: list) -> dict:
    df_summary = df_to_string(df, max_rows=20)
    system_prompt = f"""You are an expert data analyst with Python expertise.
You have access to a pandas DataFrame called 'df' and matplotlib as 'plt'.

Dataset info:
{df_summary}

When answering questions:
1. Write Python code to analyze and visualize the data
2. Use print() to output key findings/numbers
3. Create clear matplotlib charts when visualization helps
4. After the code block, provide a brief interpretation

Format your response as:
ANALYSIS: [Brief explanation of your approach]

```python
[Your Python code here]
```

INTERPRETATION: [Key insights from the results]"""
    messages = history.copy()
    messages.append({"role": "user", "content": question})
    ai_response = chat(system_prompt, messages, max_tokens=2000)

    code_results = {"output": "", "charts": [], "error": None}
    if "```python" in ai_response:
        code_start = ai_response.find("```python") + 9
        code_end = ai_response.find("```", code_start)
        if code_end > code_start:
            code = ai_response[code_start:code_end].strip()
            code_results = execute_python_code(code, df)

    return {
        "ai_response": ai_response,
        "code_output": code_results["output"],
        "charts": code_results["charts"],
        "code_error": code_results["error"],
    }


# ─────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "filename" not in st.session_state:
    st.session_state.filename = None
if "filetype" not in st.session_state:
    st.session_state.filetype = None
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts: role, content, charts, code_output, code_error, is_initial


def reset_session():
    st.session_state.df = None
    st.session_state.filename = None
    st.session_state.filetype = None
    st.session_state.messages = []


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
        if st.button("+ New File", use_container_width=True):
            reset_session()
            st.rerun()

# ─────────────────────────────────────────────────────────────
# Upload step
# ─────────────────────────────────────────────────────────────
if st.session_state.df is None:
    uploaded = st.file_uploader(
        "Drop your file here or click to browse",
        type=[e.lstrip('.') for e in SUPPORTED_EXTENSIONS],
        help="CSV · Excel · TSV · JSON · PDF · Parquet · XML · SQLite · ODS · Feather"
    )
    if uploaded is not None:
        ext = os.path.splitext(uploaded.name)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            st.error(f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")
        else:
            with st.spinner("Analyzing your data..."):
                try:
                    contents = uploaded.read()
                    df = read_file_to_df(contents, uploaded.name)
                    df.columns = [str(c).strip() for c in df.columns]
                    analysis = analyze_dataframe(df)
                except Exception as e:
                    st.error(f"Could not parse file: {e}")
                    st.stop()

            st.session_state.df = df
            st.session_state.filename = uploaded.name
            st.session_state.filetype = ext.lstrip('.').upper()
            st.session_state.messages = [{
                "role": "assistant",
                "content": analysis,
                "is_initial": True,
                "charts": [],
                "code_output": "",
                "code_error": None,
            }]
            st.rerun()

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("🤖 **AI-powered analysis**")
    c2.markdown("📈 **Auto-generated charts**")
    c3.markdown("🧠 **Conversation memory**")
    c4.markdown("🐍 **Python code execution**")

# ─────────────────────────────────────────────────────────────
# Chat step
# ─────────────────────────────────────────────────────────────
else:
    df = st.session_state.df
    conversation_count = len([m for m in st.session_state.messages if not m.get("is_initial")])

    st.info(f"📄 **{st.session_state.filename}** · {st.session_state.filetype} · "
            f"{len(df):,} rows · {len(df.columns)} cols")

    sidebar_col, chat_col = st.columns([1, 3])

    with sidebar_col:
        st.subheader("Dataset Columns")
        for col in df.columns:
            st.markdown(f"**{col}**")
            st.caption(f"{df[col].dtype} · {df[col].nunique()} unique")

        st.subheader("Session Memory")
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        if not user_msgs:
            st.caption("Ask your first question to start building memory")
        else:
            for i, m in enumerate(user_msgs, 1):
                text = m["content"]
                text = text[:45] + "..." if len(text) > 45 else text
                st.caption(f"{i}. {text}")

    with chat_col:
        for msg in st.session_state.messages:
            avatar = "🤖" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                if msg.get("is_initial"):
                    st.caption("📊 Initial Analysis")
                st.markdown(msg["content"])
                if msg.get("code_output"):
                    with st.expander("⚡ Output"):
                        st.text(msg["code_output"])
                if msg.get("code_error"):
                    with st.expander("⚠️ Code Error"):
                        st.text(msg["code_error"])
                for i, chart_bytes in enumerate(msg.get("charts", [])):
                    st.image(chart_bytes)
                    st.download_button(
                        "⬇ Download chart", chart_bytes,
                        file_name=f"chart-{i+1}.png", mime="image/png",
                        key=f"dl-{id(msg)}-{i}"
                    )

        if conversation_count == 0:
            st.caption("Try asking:")
            suggestions = [
                "Show me a bar chart of sales by region",
                "What's the trend in profit over time?",
                "Which product performs best?",
                "Compare sales across customer segments",
                "Show me the top 5 performing days",
            ]
            cols = st.columns(len(suggestions))
            for c, s in zip(cols, suggestions):
                if c.button(s, key=f"sugg-{s}"):
                    st.session_state.pending_question = s
                    st.rerun()

        if conversation_count > 0:
            warn = " · Memory near limit, consider starting a new session" if conversation_count >= 8 else ""
            st.caption(f"🧠 AI remembers your last {conversation_count} message(s) — ask follow-up questions naturally{warn}")

        question = st.chat_input("Ask a follow-up or a new question...")
        pending = st.session_state.pop("pending_question", None)
        final_question = question or pending

        if final_question:
            st.session_state.messages.append({
                "role": "user", "content": final_question, "charts": [],
                "code_output": "", "code_error": None,
            })

            history_for_api = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
                if not m.get("is_initial") and m["role"] in ("user", "assistant")
            ][:-1]  # exclude the question we just appended

            with st.spinner("Analyzing with memory context..."):
                try:
                    result = answer_question(final_question, df, history_for_api)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["ai_response"],
                        "charts": result["charts"],
                        "code_output": result["code_output"],
                        "code_error": result["code_error"],
                        "is_initial": False,
                    })
                except Exception as e:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"⚠️ Request failed: {e}",
                        "charts": [], "code_output": "", "code_error": None,
                    })
            st.rerun()