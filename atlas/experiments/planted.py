"""Planted-error test: insert known mistakes into real ATLAS reports.

For each research question:

1. Run the full pipeline (search -> write -> extract -> retrieve -> verify).
   Pass-1 verdicts measure how faithful the writer is.
2. From claims the verifier judged *supported*, make controlled corruptions:
   number, date, entity, negation (rewritten by an LLM), a fabricated claim,
   and a wrong citation (code swaps the [n] to another source).
3. Re-verify the corrupted claims mixed with the untouched originals
   (controls), shuffled, so the verifier cannot tell which are planted.

Detection = a corrupted claim is labelled unsupported or contradicted.
False alarm = an untouched control is labelled unsupported or contradicted.
A wrong citation counts as detected when the claim is not backed by
evidence from the source it cites (the same rule as citation accuracy).
"""

from __future__ import annotations

import random
import re
import time
from collections import Counter, defaultdict

from pydantic import BaseModel

from ..pipeline import Atlas
from ..retrieval import BM25Index, build_chunks
from ..schemas import Claim, ClaimVerdict, Label, Usage
from ..verify import judge_claims
from .common import experiment_settings, pct, save_experiment

QUESTIONS = [
    "How much did global electric vehicle sales grow in 2024?",
    "What has the James Webb Space Telescope discovered so far?",
    "How does the EU AI Act regulate high-risk AI systems?",
    "What caused the 2008 global financial crisis?",
    "Which CRISPR-based therapies have been approved and when?",
    "How fast has India's UPI digital payments system grown?",
    "What does research say about the health effects of intermittent fasting?",
    "What were the key outcomes of the COP28 climate conference?",
    "How did the Chandrayaan-3 mission land on the Moon?",
    "What is the current state of nuclear fusion energy research?",
]

LLM_TYPES = ["number", "date", "entity", "negation"]
FLAGGED = {Label.UNSUPPORTED, Label.CONTRADICTED}
_YEAR_RE = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")
# A standalone quantity: not part of a name such as "Chandrayaan-3" or "COP28".
_NUM_RE = re.compile(r"(?<![\w-])\d[\d,.]*(?![\w-])")

PERTURB_SYSTEM = "You create realistic factual errors for testing a fact-checking system."
PERTURB_PROMPT = """Rewrite each claim below so that it becomes FALSE, using the requested error type.
Change exactly one detail and keep everything else identical, so the error looks like a
plausible mistake rather than an obvious one.

Error types:
- number: change one quantity or percentage to a different, plausible value (not a year).
- date: change one year or date to a different, plausible one.
- entity: replace one named person, organisation, place or product with a different, plausible one.
- negation: reverse the meaning (e.g. increased -> decreased, approved -> rejected, did -> did not).

Also write one "fabricated" claim: a specific, plausible-sounding factual statement about the
topic "{question}" that includes a concrete number or name, and that is NOT stated in any of the
claims below.

Claims:
{claims}"""


class _Rewrite(BaseModel):
    claim_id: str
    rewritten: str


class _Perturbations(BaseModel):
    rewrites: list[_Rewrite]
    fabricated: str


def _eligible(text: str) -> list[str]:
    types = ["entity", "negation"]
    if _YEAR_RE.search(text):
        types.append("date")
    if _NUM_RE.search(_YEAR_RE.sub("", text)):
        types.append("number")
    return types


def _assign_types(claims: list[Claim], used: Counter) -> dict[str, str]:
    """Give each claim the eligible error type used least so far (balances types)."""
    assignment = {}
    for c in claims:
        options = _eligible(c.text)
        choice = min(options, key=lambda t: (used[t], LLM_TYPES.index(t)))
        assignment[c.id] = choice
        used[choice] += 1
    return assignment


def _citation_backed(v: ClaimVerdict) -> bool:
    if v.label not in (Label.SUPPORTED, Label.PARTIALLY_SUPPORTED):
        return False
    used = {e.source_id for e in v.evidence if e.chunk_id in v.cited_evidence_ids}
    return bool(used & set(v.claim.cited_sources))


def run_planted(
    questions: list[str] | None = None,
    model: str = "gemini-3.5-flash-lite",
    per_report: int = 6,
    seed: int = 7,
) -> dict:
    questions = questions or QUESTIONS
    rng = random.Random(seed)
    settings = experiment_settings(cache=True)
    settings.writer_model = settings.extractor_model = settings.verifier_model = model

    type_counts: Counter = Counter()
    planted_rows: list[dict] = []
    control_rows: list[dict] = []
    reports: list[dict] = []
    pass1_labels: Counter = Counter()
    total_usage = Usage()

    for q in questions:
        usage = Usage()
        atlas = Atlas(settings, usage=usage)
        t0 = time.perf_counter()
        result = atlas.research(q)
        pipeline_s = time.perf_counter() - t0
        pipeline_calls = usage.llm_calls + usage.llm_cache_hits
        for v in result.verdicts:
            pass1_labels[v.label.value] += 1

        supported = [v.claim for v in result.verdicts if v.label == Label.SUPPORTED]
        rng.shuffle(supported)
        to_rewrite = supported[:per_report]
        miscite_pool = [c for c in supported[per_report:] if c.cited_sources]
        if not miscite_pool:
            miscite_pool = [c for c in to_rewrite if c.cited_sources]

        assignment = _assign_types(to_rewrite, type_counts)
        listing = "\n".join(f"- id {c.id} | type {assignment[c.id]} | {c.text}" for c in to_rewrite)
        pert = atlas.llm.generate_json(
            PERTURB_PROMPT.format(question=q, claims=listing),
            _Perturbations,
            model=model,
            system=PERTURB_SYSTEM,
        )
        rewrites = {r.claim_id.strip(): r.rewritten.strip() for r in pert.rewrites}

        # Build the mixed verification set.
        items: list[tuple[str, str, Claim, Claim | None]] = []  # (kind, type, claim, original)
        for c in to_rewrite:
            new = rewrites.get(c.id)
            if new and new.lower() != c.text.lower():
                items.append(("planted", assignment[c.id], c.model_copy(update={"text": new}), c))
            items.append(("control", "control", c, None))
        if pert.fabricated.strip():
            cite = [1] if result.sources else []
            items.append(("planted", "fabricated", Claim(id="F", text=pert.fabricated.strip(), cited_sources=cite), None))
        for c in miscite_pool:
            others = [s.id for s in result.sources if s.id not in c.cited_sources]
            if others:  # skip claims that already cite every source
                wrong = rng.choice(others)
                items.append(("planted", "wrong_citation", c.model_copy(update={"cited_sources": [wrong]}), c))
                break

        rng.shuffle(items)
        index = BM25Index(build_chunks(result.sources, settings.chunk_chars, settings.chunk_overlap))
        verify_items = []
        for i, (_, _, claim, _) in enumerate(items, 1):
            claim = claim.model_copy(update={"id": f"P{i}"})
            verify_items.append((claim, index.evidence_for(claim, settings.evidence_per_claim)))
        verdicts = judge_claims(atlas.llm, model, verify_items, settings.verify_batch_size)
        failed = [v for v in verdicts if v.error]
        if failed:
            raise RuntimeError(f"{len(failed)} verdicts missing for '{q}' (quota/API failure); aborting.")

        for (kind, etype, claim, original), v in zip(items, verdicts):
            row = {
                "question": q,
                "type": etype,
                "claim": claim.text,
                "original": original.text if original else None,
                "cited": claim.cited_sources,
                "label": v.label.value,
                "confidence": v.confidence,
                "rationale": v.rationale,
            }
            if etype == "wrong_citation":
                row["detected"] = not _citation_backed(v)
            elif kind == "planted":
                row["detected"] = v.label in FLAGGED
            else:
                row["false_alarm"] = v.label in FLAGGED
            (planted_rows if kind == "planted" else control_rows).append(row)

        reports.append(
            {
                "question": q,
                "sources": len(result.sources),
                "claims": result.summary.total_claims,
                "trust_score": result.summary.trust_score,
                "citation_coverage": result.summary.citation_coverage,
                "citation_accuracy": result.summary.citation_accuracy,
                "counts": result.summary.counts,
                "pipeline_seconds": round(pipeline_s, 2),
                "pipeline_llm_requests": pipeline_calls,
                "total_llm_calls_incl_experiment": usage.llm_calls,
            }
        )
        for field in ("llm_calls", "llm_cache_hits", "prompt_tokens", "output_tokens", "search_calls", "search_credits"):
            setattr(total_usage, field, getattr(total_usage, field) + getattr(usage, field))
        for m_, n_ in usage.calls_by_model.items():
            total_usage.calls_by_model[m_] = total_usage.calls_by_model.get(m_, 0) + n_

    # ---- aggregate
    by_type: dict[str, list[dict]] = defaultdict(list)
    for r in planted_rows:
        by_type[r["type"]].append(r)
    per_type = {
        t: {
            "n": len(rows),
            "detected": sum(r["detected"] for r in rows),
            "detection_rate": round(sum(r["detected"] for r in rows) / len(rows), 4),
            "labels": dict(Counter(r["label"] for r in rows)),
        }
        for t, rows in sorted(by_type.items())
    }
    content = [r for r in planted_rows if r["type"] != "wrong_citation"]
    n_ctrl = len(control_rows)
    n_fa = sum(r["false_alarm"] for r in control_rows)
    total_p1 = sum(pass1_labels.values())
    summary = {
        "model": model,
        "reports": len(reports),
        "planted_total": len(planted_rows),
        "content_errors": len(content),
        "content_detection_rate": round(sum(r["detected"] for r in content) / len(content), 4) if content else None,
        "content_contradicted_rate": round(sum(r["label"] == "contradicted" for r in content) / len(content), 4) if content else None,
        "overall_detection_rate": round(sum(r["detected"] for r in planted_rows) / len(planted_rows), 4),
        "controls": n_ctrl,
        "false_alarm_rate": round(n_fa / n_ctrl, 4) if n_ctrl else None,
        "per_type": per_type,
        "pass1_claims": total_p1,
        "pass1_label_share": {k: round(v / total_p1, 4) for k, v in pass1_labels.items()} if total_p1 else {},
        "mean_trust_score": round(sum(r["trust_score"] for r in reports) / len(reports), 1),
        "mean_claims_per_report": round(total_p1 / len(reports), 1),
        "mean_pipeline_seconds": round(sum(r["pipeline_seconds"] for r in reports) / len(reports), 1),
    }
    result = {"summary": summary, "reports": reports, "planted": planted_rows, "controls": control_rows,
              "usage": total_usage.model_dump()}

    s = summary
    lines = [
        "# Planted-error test",
        "",
        f"- {s['reports']} real reports (Tavily + `{model}` for writing, extraction and verification)",
        f"- {s['planted_total']} planted errors, {s['controls']} untouched controls, shuffled together",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Content errors detected (unsupported or contradicted) | {pct(s['content_detection_rate'])} ({sum(r['detected'] for r in content)}/{len(content)}) |",
        f"| ...of which labelled contradicted | {pct(s['content_contradicted_rate'])} |",
        f"| All planted errors detected (incl. wrong citations) | {pct(s['overall_detection_rate'])} |",
        f"| False alarms on untouched claims | {pct(s['false_alarm_rate'])} ({n_fa}/{n_ctrl}) |",
        "",
        "| Error type | Planted | Detected | Rate | Verdicts |",
        "|---|---|---|---|---|",
    ]
    for t, d in per_type.items():
        lines.append(f"| {t} | {d['n']} | {d['detected']} | {pct(d['detection_rate'])} | {d['labels']} |")
    lines += [
        "",
        "## Writer faithfulness (pass 1, before planting)",
        "",
        f"- {s['pass1_claims']} claims across {s['reports']} reports ({s['mean_claims_per_report']} per report)",
        f"- Verdict share: {', '.join(f'{k} {pct(v)}' for k, v in s['pass1_label_share'].items())}",
        f"- Mean trust score {s['mean_trust_score']}/100 · mean pipeline time {s['mean_pipeline_seconds']}s per report",
        "",
        "## Missed errors",
        "",
        "| Type | Original | Planted | Verdict |",
        "|---|---|---|---|",
    ]
    for r in planted_rows:
        if not r["detected"]:
            orig = (r["original"] or "-").replace("|", "\\|")
            lines.append(f"| {r['type']} | {orig} | {r['claim'].replace('|', chr(92) + '|')} | {r['label']} |")
    result["output_dir"] = str(save_experiment("planted_errors", result, "\n".join(lines) + "\n"))
    return result
