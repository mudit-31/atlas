"""Render a ResearchResult as an annotated Markdown file or a standalone HTML page."""

from __future__ import annotations

import html
import re

from .schemas import LABEL_ORDER, ClaimVerdict, Label, ResearchResult

ICONS = {
    Label.SUPPORTED: "✅",
    Label.PARTIALLY_SUPPORTED: "🟡",
    Label.UNSUPPORTED: "⚪",
    Label.CONTRADICTED: "❌",
}


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"


def _md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(result: ResearchResult) -> str:
    s = result.summary
    lines = [result.report_markdown.rstrip(), "", "---", "", "## ATLAS Verification", ""]
    lines.append(f"**Trust score: {s.trust_score:.0f}/100** across {s.total_claims} claims.")
    lines.append("")
    lines.append(
        " · ".join(f"{ICONS[label]} {label.display}: {s.counts[label.value]}" for label in LABEL_ORDER)
    )
    lines.append("")
    lines.append(
        f"Citation coverage: {_pct(s.citation_coverage)} · "
        f"Citation accuracy: {_pct(s.citation_accuracy)} · "
        f"Mean confidence: {_pct(s.mean_confidence)}"
    )
    lines += ["", "| # | Claim | Verdict | Confidence | Why |", "|---|---|---|---|---|"]
    for v in result.verdicts:
        cites = "".join(f"[{c}]" for c in v.claim.cited_sources)
        lines.append(
            f"| {v.claim.id} | {_md_cell(v.claim.text)} {cites} | {ICONS[v.label]} {v.label.display} "
            f"| {v.confidence:.2f} | {_md_cell(v.rationale)} |"
        )
    u = result.usage
    lines += [
        "",
        f"<sub>Gemini calls: {u.llm_calls} (cache hits {u.llm_cache_hits}) · "
        f"tokens in/out: {u.prompt_tokens}/{u.output_tokens} · "
        f"Tavily credits: {u.search_credits} · {result.elapsed_seconds:.1f}s</sub>",
        "",
    ]
    return "\n".join(lines)


def _inline_md(text: str) -> str:
    """Minimal, safe Markdown -> HTML for report bodies (escape first)."""
    out = html.escape(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", out)
    out = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>',
        out,
    )
    out = re.sub(r"\[(\d+)\]", r'<a class="cite" href="#src-\1">[\1]</a>', out)
    return out


def markdown_to_html(markdown: str) -> str:
    parts: list[str] = []
    list_tag: str | None = None
    for line in markdown.splitlines():
        stripped = line.strip()
        bullet = re.match(r"^[-*+]\s+(.*)", stripped)
        number = re.match(r"^\d+\.\s+(.*)", stripped)
        wanted = "ul" if bullet else "ol" if number else None
        if list_tag and wanted != list_tag:
            parts.append(f"</{list_tag}>")
            list_tag = None
        if wanted and not list_tag:
            parts.append(f"<{wanted}>")
            list_tag = wanted
        if bullet or number:
            parts.append(f"<li>{_inline_md((bullet or number).group(1))}</li>")
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)", stripped)
        if heading:
            level = min(len(heading.group(1)) + 1, 6)  # page title is <h1>
            parts.append(f"<h{level}>{_inline_md(heading.group(2))}</h{level}>")
        elif stripped:
            parts.append(f"<p>{_inline_md(stripped)}</p>")
    if list_tag:
        parts.append(f"</{list_tag}>")
    return "\n".join(parts)


def _verdict_card(v: ClaimVerdict) -> str:
    evidence = "".join(
        f'<blockquote class="{"used" if e.chunk_id in v.cited_evidence_ids else ""}">'
        f'<span class="eid">{html.escape(e.chunk_id)}</span> {html.escape(e.text)}</blockquote>'
        for e in v.evidence
    )
    cites = " ".join(f'<a class="cite" href="#src-{c}">[{c}]</a>' for c in v.claim.cited_sources)
    return f"""
<details class="claim {v.label.value}">
  <summary>
    <span class="badge {v.label.value}">{ICONS[v.label]} {v.label.display}</span>
    <span class="ctext">{html.escape(v.claim.text)} {cites}</span>
    <span class="conf">{v.confidence:.0%}</span>
  </summary>
  <p class="why">{html.escape(v.rationale)}</p>
  {evidence or '<p class="muted">No matching evidence passages were found.</p>'}
</details>"""


def render_html(result: ResearchResult) -> str:
    s = result.summary
    body = result.report_markdown
    # Drop the generated "# question" title and Sources list; the page has its own.
    body = re.sub(r"^#\s+.*\n", "", body, count=1)
    body = re.split(r"^##\s*Sources\s*$", body, flags=re.MULTILINE)[0]

    counts = "".join(
        f'<div class="stat {label.value}"><b>{s.counts[label.value]}</b><span>{label.display}</span></div>'
        for label in LABEL_ORDER
    )
    sources = "".join(
        f'<li id="src-{src.id}"><a href="{html.escape(src.url)}" target="_blank" rel="noopener">'
        f"{html.escape(src.title or src.url)}</a></li>"
        for src in result.sources
    )
    claims = "".join(_verdict_card(v) for v in result.verdicts)
    u = result.usage
    score_class = "good" if s.trust_score >= 75 else "warn" if s.trust_score >= 50 else "bad"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ATLAS Report</title>
<style>
:root {{
  --bg:#f7f7f5; --card:#ffffff; --text:#1d1d1f; --muted:#6b6b70; --border:#e3e3e0;
  --ok:#1f8a4c; --part:#b7791f; --none:#6b6b70; --bad:#c0392b; --accent:#2f5bd3;
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#141416; --card:#1d1d20; --text:#ececee; --muted:#9a9aa1; --border:#2e2e33;
    --ok:#4cc38a; --part:#e0b04f; --none:#9a9aa1; --bad:#ef6f61; --accent:#7c9cff; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
main {{ max-width:880px; margin:0 auto; padding:32px 16px 64px; }}
h1 {{ font-size:1.7rem; line-height:1.3; margin:0 0 4px; }}
.meta {{ color:var(--muted); font-size:.85rem; margin-bottom:24px; }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:20px 22px; margin-bottom:20px; }}
.scorebar {{ display:flex; flex-wrap:wrap; gap:16px; align-items:center; }}
.score {{ font-size:2.6rem; font-weight:700; line-height:1; }}
.score.good {{ color:var(--ok); }} .score.warn {{ color:var(--part); }} .score.bad {{ color:var(--bad); }}
.score small {{ font-size:1rem; color:var(--muted); font-weight:400; }}
.stats {{ display:flex; flex-wrap:wrap; gap:10px; }}
.stat {{ border:1px solid var(--border); border-radius:8px; padding:6px 12px; min-width:92px; }}
.stat b {{ display:block; font-size:1.3rem; }} .stat span {{ font-size:.75rem; color:var(--muted); }}
.stat.supported b {{ color:var(--ok); }} .stat.partially_supported b {{ color:var(--part); }}
.stat.unsupported b {{ color:var(--none); }} .stat.contradicted b {{ color:var(--bad); }}
.sub {{ color:var(--muted); font-size:.85rem; margin-top:12px; }}
a {{ color:var(--accent); }} a.cite {{ text-decoration:none; font-size:.85em; }}
details.claim {{ border-left:4px solid var(--none); padding:8px 12px; margin:8px 0; background:var(--bg); border-radius:6px; }}
details.claim.supported {{ border-color:var(--ok); }} details.claim.partially_supported {{ border-color:var(--part); }}
details.claim.contradicted {{ border-color:var(--bad); }}
summary {{ cursor:pointer; display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; }}
.badge {{ font-size:.75rem; font-weight:600; white-space:nowrap; }}
.ctext {{ flex:1; min-width:200px; }} .conf {{ color:var(--muted); font-size:.8rem; }}
.why {{ margin:8px 0; }}
blockquote {{ margin:6px 0; padding:6px 10px; border-left:3px solid var(--border); color:var(--muted); font-size:.9rem; }}
blockquote.used {{ border-color:var(--accent); color:var(--text); }}
.eid {{ font-family:ui-monospace,monospace; font-size:.75rem; color:var(--accent); }}
.muted {{ color:var(--muted); }}
</style>
</head>
<body><main>
<h1>{html.escape(result.question)}</h1>
<div class="meta">Generated {html.escape(result.created_at)} · writer {html.escape(result.models.get("writer", ""))} · verifier {html.escape(result.models.get("verifier", ""))}</div>

<section class="card">
  <div class="scorebar">
    <div class="score {score_class}">{s.trust_score:.0f}<small>/100 trust</small></div>
    <div class="stats">{counts}</div>
  </div>
  <div class="sub">Citation coverage {_pct(s.citation_coverage)} · citation accuracy {_pct(s.citation_accuracy)} ·
  mean confidence {_pct(s.mean_confidence)} · {s.total_claims} claims</div>
</section>

<section class="card">{markdown_to_html(body)}</section>

<section class="card"><h2>Claim verification</h2>{claims or '<p class="muted">No claims were extracted.</p>'}</section>

<section class="card"><h2>Sources</h2><ol>{sources}</ol></section>

<p class="sub">Gemini calls {u.llm_calls} (cache hits {u.llm_cache_hits}) · tokens {u.prompt_tokens} in / {u.output_tokens} out ·
Tavily credits {u.search_credits} · {result.elapsed_seconds:.1f}s</p>
</main></body></html>
"""
