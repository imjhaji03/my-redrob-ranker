import json
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from src.ranker import (
    rank_candidates,
    submission_csv_text,
    submission_xlsx_bytes,
)


st.set_page_config(page_title="Redrob Candidate Ranker", layout="wide")
st.title("Redrob Candidate Ranker")
st.caption("Upload a small candidate file and generate ranking downloads in CSV or XLSX using the same pipeline as the submission ranker.")


def load_uploaded_candidates(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".json":
        return json.load(uploaded_file)

    if suffix == ".jsonl":
        content = uploaded_file.getvalue().decode("utf-8").splitlines()
        candidates = []
        for line in content:
            line = line.strip()
            if line:
                candidates.append(json.loads(line))
        return candidates

    raise ValueError("Unsupported file type. Upload .json or .jsonl")


uploaded_file = st.file_uploader(
    "Upload candidates (.json or .jsonl)",
    type=["json", "jsonl"],
    help="Use small candidate samples for the sandbox demo.",
)

default_top_n = 20
max_top_n = 100

top_n = st.slider("Top N results to display/export", min_value=5, max_value=max_top_n, value=default_top_n, step=5)

if uploaded_file is not None:
    try:
        candidates = load_uploaded_candidates(uploaded_file)
        st.success(f"Loaded {len(candidates)} candidates from {uploaded_file.name}")

        if len(candidates) == 0:
            st.warning("The uploaded file contains no candidate records.")
        else:
            with st.spinner("Ranking candidates..."):
                results = rank_candidates(candidates, top_n=min(top_n, len(candidates)), verbose=False)

            st.subheader("Top ranked candidates")
            table_rows = [
                {
                    "rank": r["rank"],
                    "candidate_id": r["candidate_id"],
                    "score": f"{r['final_score']:.4f}",
                    "reasoning": r["reasoning"],
                    "honeypot": r["honeypot_result"]["is_honeypot"],
                }
                for r in results
            ]
            st.dataframe(table_rows, use_container_width=True)

            honeypots = sum(1 for r in results if r["honeypot_result"]["is_honeypot"])
            st.metric("Flagged honeypots in exported set", f"{honeypots}/{len(results)}")

            csv_data = submission_csv_text(results)
            xlsx_data = submission_xlsx_bytes(results)

            download_col1, download_col2 = st.columns(2)
            with download_col1:
                st.download_button(
                    label="Download ranking CSV",
                    data=csv_data,
                    file_name="submission.csv",
                    mime="text/csv",
                )
            with download_col2:
                st.download_button(
                    label="Download ranking XLSX",
                    data=xlsx_data,
                    file_name="submission.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            with st.expander("Preview CSV"):
                st.code(csv_data, language="csv")

    except Exception as exc:
        st.error(f"Failed to process file: {exc}")
else:
    st.info("Upload a sample candidate file to run the demo.")
