from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import json
import os
import traceback
import threading
import requests
import time
import sqlite3
import xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from groq import Groq

app = FastAPI(title="AI Data Analyst Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"

SUPPORTED_EXTENSIONS = [
    '.csv', '.xlsx', '.xls', '.tsv', '.json',
    '.parquet', '.xml', '.db', '.sqlite', '.sqlite3',
    '.pdf', '.ods', '.feather', '.pkl', '.pickle'
]

# Keep-alive: pings this server every 10 min so Render free tier never sleeps
def _keep_alive():
    url = "https://ai-data-analyst-fdcx.onrender.com/"
    time.sleep(60)
    while True:
        try:
            requests.get(url, timeout=10)
        except Exception:
            pass
        time.sleep(600)

threading.Thread(target=_keep_alive, daemon=True).start()


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
        import tempfile
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


def chat(system: str, messages: list, max_tokens: int = 2000) -> str:
    groq_messages = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=groq_messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content


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
            charts.append(f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}")
            plt.close(fig)
    except Exception as e:
        error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout
        plt.close('all')
    return {"output": output_text, "charts": charts, "error": error}


@app.get("/")
def root():
    return {"message": "AI Data Analyst Agent API", "status": "running", "model": GROQ_MODEL}


@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    contents = await file.read()
    try:
        df = read_file_to_df(contents, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {str(e)}")

    df.columns = [str(c).strip() for c in df.columns]

    df_summary = df_to_string(df)
    system = "You are an expert data analyst. Be concise, insightful, and use clear markdown formatting."
    user_msg = f"""Analyze this dataset and provide:
1. A brief summary of what the data contains
2. Key observations and patterns
3. 3-5 specific questions this data can answer
4. Suggested analyses to run

Dataset info:
{df_summary}"""
    analysis = chat(system, [{"role": "user", "content": user_msg}], max_tokens=1200)
    columns_info = [
        {"name": col, "dtype": str(df[col].dtype),
         "non_null": int(df[col].count()), "unique": int(df[col].nunique())}
        for col in df.columns
    ]
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return {
        "filename": file.filename,
        "filetype": ext.lstrip('.').upper(),
        "rows": len(df),
        "columns": len(df.columns),
        "columns_info": columns_info,
        "initial_analysis": analysis,
        "data_preview": df.head(10).to_dict(orient='records'),
        "csv_data": csv_buffer.getvalue()
    }


@app.post("/query")
async def query_data(request: dict):
    question = request.get("question", "")
    csv_data = request.get("csv_data", "")
    conversation_history = request.get("history", [])
    if not question or not csv_data:
        raise HTTPException(status_code=400, detail="Question and data are required")
    try:
        df = pd.read_csv(io.StringIO(csv_data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse data: {str(e)}")
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
    messages = conversation_history.copy()
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
        "question": question,
        "ai_response": ai_response,
        "code_output": code_results["output"],
        "charts": code_results["charts"],
        "code_error": code_results["error"]
    }