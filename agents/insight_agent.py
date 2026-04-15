"""
Insight Agent — fast business narrative. Minimal prompt, capped tokens.
"""
import pandas as pd


INSIGHT_PROMPT = """Senior analyst. 2-3 sentences max.
State the top finding with a number. Give one actionable recommendation.
No SQL, no jargon.

Question: {question}
Data ({rows} rows): {summary}

Insight:"""


EMPTY_PROMPT = """Analyst. The query returned 0 rows.
Question: {question}
In 2 sentences: say no data was found and suggest one alternative question to try.
Be brief and helpful."""


class InsightAgent:
    def __init__(self, llm):
        self.llm = llm

    def _summarize(self, df: pd.DataFrame) -> str:
        # Only send top 5 rows + numeric stats — keep tokens minimal
        parts = [df.head(5).to_string(index=False)]
        num = df.select_dtypes(include="number").columns.tolist()
        if num:
            parts.append(df[num].agg(["min","max","mean"]).round(2).to_string())
        return "\n".join(parts)

    def narrate(self, question: str, sql: str, df: pd.DataFrame) -> str:
        if df is None or df.empty:
            try:
                return self.llm.invoke(
                    EMPTY_PROMPT.format(question=question),
                    max_tokens=120, temperature=0.3)
            except Exception:
                return ("No data found for this question. "
                        "Try removing year filters or check the Table tab to explore available values.")
        try:
            return self.llm.invoke(
                INSIGHT_PROMPT.format(
                    question=question,
                    rows=len(df),
                    summary=self._summarize(df)
                ),
                max_tokens=180, temperature=0.3)
        except Exception as e:
            return f"Insight error: {e}"
