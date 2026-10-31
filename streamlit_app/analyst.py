"""LLM orchestration for AI Data Analyst (no Streamlit imports, so it is unit-testable).

Flow for each question:
  1. The model writes pandas/seaborn code (or says it cannot answer).
  2. The code is validated and executed in an isolated subprocess (sandbox.py).
  3. If it fails, the model gets the error once and returns corrected code.
  4. A second model call explains the ACTUAL printed output, so the explanation
     never has to guess numbers that the code has not produced yet.
"""
from __future__ import annotations

import re

import groq

from file_readers import df_to_string
from sandbox import run_user_code

GROQ_MODEL = "openai/gpt-oss-120b"
MAX_HISTORY_MESSAGES = 12
MAX_OUTPUT_FOR_EXPLANATION = 6000

CODE_SYSTEM_PROMPT = """You are an expert data analyst. A pandas DataFrame named `df` is already loaded.

Names available to your code: df, pd (pandas), np (numpy), plt (matplotlib.pyplot), sns (seaborn).

Reply in exactly this format:
ANALYSIS: one or two sentences describing your approach

```python
# your code
```

Rules:
- Use print() for every number or table you want to report. Never call plt.show() or plt.savefig().
- For charts use matplotlib/seaborn. Give every chart a title and labelled axes.
- Read data only from `df`. There is no file, network or system access. Imports are limited to pandas, numpy, matplotlib, seaborn, math, statistics, datetime and collections.
- Do not modify `df` in place; work on copies.
- Never invent numbers. Compute them.
- If the question cannot be answered from the available columns (for example it names a column that does not exist), reply with exactly one line and no code:
  CANNOT_ANSWER: short reason that names the available columns

Dataset information:
{summary}"""

INTERPRET_PROMPT = """You are a careful data analyst explaining a result to a non-technical user.

Rules:
- Use ONLY numbers that appear in the printed output below. Never invent, estimate or guess a number.
- If the printed output is empty and only charts were produced, describe in general terms what the chart shows and say the exact values are on the chart.
- If an error remains, say plainly that the analysis failed and why.
- Write 2 to 5 short sentences or bullets in markdown. Do not repeat the code.

Question: {question}

Code that was run:
{code}

Printed output:
{output}

Charts produced: {charts}
Error (if any): {error}"""


class LLMError(Exception):
    """A user-presentable problem talking to the model service."""


def chat(client, system: str, messages: list, max_tokens: int = 2000, temperature: float = 0.2) -> str:
    payload = [{"role": "system", "content": system}] + messages
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL, messages=payload,
            max_tokens=max_tokens, temperature=temperature,
        )
    except groq.RateLimitError as exc:
        raise LLMError("The free AI service is rate-limited right now. Please wait a minute and try again.") from exc
    except groq.APIConnectionError as exc:
        raise LLMError("Could not reach the AI service. Please check your connection and try again.") from exc
    except groq.APIStatusError as exc:
        raise LLMError(f"The AI service returned an error (HTTP {exc.status_code}). Please try again.") from exc
    return (response.choices[0].message.content or "").strip()


def extract_code(text: str) -> str | None:
    match = re.search(r"```(?:python|py)?[ \t]*\r?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_analysis(text: str) -> str:
    head = text.split("```", 1)[0].strip()
    head = re.sub(r"^\**ANALYSIS:?\**:?\s*", "", head, flags=re.IGNORECASE).strip()
    return head or "Computed the answer from your data."


def analyze_dataframe(client, df) -> str:
    system = "You are an expert data analyst. Be concise, insightful, and use clear markdown formatting."
    user = f"""Analyze this dataset and provide:
1. A brief summary of what the data contains
2. Key observations and patterns (only what the data shows)
3. 3-5 specific questions this data can answer
4. Suggested analyses to run

Dataset info:
{df_to_string(df)}"""
    return chat(client, system, [{"role": "user", "content": user}], max_tokens=1200)


def interpret(client, question: str, code: str, run: dict) -> str:
    prompt = INTERPRET_PROMPT.format(
        question=question,
        code=code,
        output=(run["output"] or "(nothing was printed)")[:MAX_OUTPUT_FOR_EXPLANATION],
        charts=len(run["charts"]),
        error=run["error"] or "none",
    )
    return chat(client, "You explain data analysis results accurately and concisely.",
                [{"role": "user", "content": prompt}], max_tokens=700, temperature=0.1)


def answer_question(client, question: str, df, history: list) -> dict:
    """Return {"content", "charts", "code_output", "code_error", "has_code"}."""
    system = CODE_SYSTEM_PROMPT.format(summary=df_to_string(df, max_rows=20))
    messages = history[-MAX_HISTORY_MESSAGES:] + [{"role": "user", "content": question}]

    reply = chat(client, system, messages)

    refusal = re.match(r"\s*CANNOT_ANSWER:\s*(.*)", reply, re.DOTALL)
    if refusal:
        detail = refusal.group(1).strip()
        reason = detail.splitlines()[0] if detail else "the data does not contain what is needed."
        return {"content": f"I can't answer that from this dataset: {reason}",
                "charts": [], "code_output": "", "code_error": None, "has_code": False}

    code = extract_code(reply)
    if not code:
        return {"content": reply or "I could not produce an answer. Please rephrase the question.",
                "charts": [], "code_output": "", "code_error": None, "has_code": False}

    run = run_user_code(code, df)

    if run["error"]:  # one automatic repair attempt
        repair = messages + [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": "That code failed:\n" + run["error"][:1500]
             + "\nReturn corrected code in the same format."},
        ]
        fixed_reply = chat(client, system, repair)
        fixed_code = extract_code(fixed_reply)
        if fixed_code:
            reply, code = fixed_reply, fixed_code
            run = run_user_code(code, df)

    explanation = interpret(client, question, code, run)
    content = (f"**Analysis:** {extract_analysis(reply)}\n\n"
               f"```python\n{code}\n```\n\n"
               f"**Interpretation:**\n{explanation}")
    return {"content": content, "charts": run["charts"], "code_output": run["output"],
            "code_error": run["error"], "has_code": True}
