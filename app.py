"""ATLAS web UI. Run with:  streamlit run app.py"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from atlas.config import ConfigError, Settings
from atlas.pipeline import Atlas, save_result
from atlas.render import render_html
from atlas.schemas import LABEL_ORDER

st.set_page_config(page_title="ATLAS", page_icon="🧭", layout="wide")


@st.cache_resource
def get_settings() -> Settings:
    return Settings.from_env()


def show_result(result) -> None:
    s = result.summary
    cols = st.columns(5)
    cols[0].metric("Trust score", f"{s.trust_score:.0f}/100")
    for col, label in zip(cols[1:], LABEL_ORDER):
        col.metric(label.display, s.counts[label.value])
    acc = "n/a" if s.citation_accuracy is None else f"{s.citation_accuracy:.0%}"
    u = result.usage
    st.caption(
        f"Citation coverage {s.citation_coverage:.0%} · citation accuracy {acc} · "
        f"Gemini calls {u.llm_calls} (cache hits {u.llm_cache_hits}) · "
        f"Tavily credits {u.search_credits} · {result.elapsed_seconds:.1f}s"
    )
    components.html(render_html(result), height=900, scrolling=True)
    st.download_button(
        "Download result JSON",
        json.dumps(result.model_dump(mode="json"), indent=2),
        file_name="atlas_result.json",
        mime="application/json",
    )


def run(fn, *args) -> None:
    status = st.status("Working...", expanded=True)
    try:
        result = fn(*args, progress=lambda stage: status.write(stage))
    except ConfigError as exc:
        status.update(label="Configuration error", state="error")
        st.error(str(exc))
        return
    except Exception as exc:
        status.update(label="Failed", state="error")
        st.exception(exc)
        return
    run_dir = save_result(result, get_settings().output_dir)
    status.update(label=f"Done · saved to {run_dir}", state="complete", expanded=False)
    st.session_state["result"] = result


st.title("🧭 ATLAS")
st.write("Research a question, then check every claim in the answer against the sources.")

tab_research, tab_verify, tab_eval = st.tabs(["Research", "Verify text", "Evaluation"])

with tab_research:
    question = st.text_input("Research question", placeholder="e.g. What is NVIDIA's AI strategy?")
    if st.button("Research", type="primary", disabled=not question.strip()):
        run(lambda q, progress: Atlas(get_settings()).research(q, progress), question)

with tab_verify:
    topic = st.text_input("Topic to search for evidence", key="verify_topic")
    text = st.text_area("Text to fact-check", height=220)
    if st.button("Verify", type="primary", disabled=not (topic.strip() and text.strip())):
        run(lambda t, q, progress: Atlas(get_settings()).verify_text(t, q, progress), text, topic)

with tab_eval:
    eval_dir = Path(get_settings().eval_dir)
    runs = sorted((p for p in eval_dir.glob("*/report.md")), reverse=True) if eval_dir.exists() else []
    if not runs:
        st.info("No evaluation runs yet. Run `python -m atlas evaluate` to score the verifier.")
    else:
        choice = st.selectbox("Evaluation run", runs, format_func=lambda p: p.parent.name)
        st.markdown(choice.read_text(encoding="utf-8"))

if "result" in st.session_state:
    st.divider()
    show_result(st.session_state["result"])
