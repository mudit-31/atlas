"""Command-line interface: `python -m atlas <command>` (or `atlas <command>`)."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import ConfigError, Settings
from .schemas import LABEL_ORDER


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _print_summary(result, run_dir: Path) -> None:
    s = result.summary
    u = result.usage
    print()
    print(f"Trust score: {s.trust_score:.0f}/100  ({s.total_claims} claims)")
    print("  " + " | ".join(f"{label.display}: {s.counts[label.value]}" for label in LABEL_ORDER))
    acc = "n/a" if s.citation_accuracy is None else f"{s.citation_accuracy:.0%}"
    print(f"  Citation coverage: {s.citation_coverage:.0%} | Citation accuracy: {acc}")
    print(
        f"  Gemini calls: {u.llm_calls} (cache hits {u.llm_cache_hits}) | "
        f"Tavily credits: {u.search_credits} | {result.elapsed_seconds:.1f}s"
    )
    print()
    print(f"Saved to: {run_dir}")
    print(f"  Open {run_dir / 'report.html'} in a browser for the annotated report.")


def _apply_overrides(settings: Settings, args: argparse.Namespace) -> Settings:
    if getattr(args, "no_cache", False):
        settings.cache_enabled = False
    if getattr(args, "max_sources", None):
        settings.max_sources = args.max_sources
    if getattr(args, "max_claims", None):
        settings.max_claims = args.max_claims
    if getattr(args, "model", None):
        settings.verifier_model = args.model
    if getattr(args, "batch_size", None):
        settings.verify_batch_size = args.batch_size
    return settings


def cmd_research(args: argparse.Namespace, settings: Settings) -> int:
    from .pipeline import Atlas, save_result

    atlas = Atlas(settings)
    result = atlas.research(args.question, progress=lambda stage: print(f"- {stage}..."))
    run_dir = save_result(result, settings.output_dir)
    _print_summary(result, run_dir)
    return 0


def cmd_verify(args: argparse.Namespace, settings: Settings) -> int:
    from .pipeline import Atlas, save_result

    text = Path(args.file).read_text(encoding="utf-8")
    atlas = Atlas(settings)
    result = atlas.verify_text(text, args.question, progress=lambda stage: print(f"- {stage}..."))
    run_dir = save_result(result, settings.output_dir)
    _print_summary(result, run_dir)
    return 0


def cmd_evaluate(args: argparse.Namespace, settings: Settings) -> int:
    from .evaluation.runner import DEFAULT_DATASET, run_evaluation

    dataset = Path(args.dataset) if args.dataset else DEFAULT_DATASET
    result = run_evaluation(settings, dataset=dataset, limit=args.limit)
    m = result["metrics"]
    pd = m["problem_detection"]
    print()
    print(f"Examples: {m['n']} | model: {result['model']}")
    print(f"Accuracy: {m['accuracy']:.3f} | Macro F1: {m['macro_f1']:.3f} | Weighted F1: {m['weighted_f1']:.3f}")
    print(f"Problem-claim detection: precision {pd['precision']:.3f}, recall {pd['recall']:.3f}, F1 {pd['f1']:.3f}")
    for label in LABEL_ORDER:
        c = m["per_class"][label.value]
        print(f"  {label.display:<20} P {c['precision']:.2f}  R {c['recall']:.2f}  F1 {c['f1']:.2f}  (n={c['support']})")
    print(f"Gemini calls: {result['usage']['llm_calls']} | {result['elapsed_seconds']}s")
    print(f"\nSaved to: {result['output_dir']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atlas",
        description="ATLAS: research a question and verify every claim in the report.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="show progress logs")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--no-cache", action="store_true", help="ignore cached API responses")

    p = sub.add_parser("research", parents=[common], help="research a question and verify the report")
    p.add_argument("question", help="the research question")
    p.add_argument("--max-sources", type=int, help="number of web sources (default 6)")
    p.add_argument("--max-claims", type=int, help="maximum claims to verify (default 25)")
    p.set_defaults(func=cmd_research)

    p = sub.add_parser("verify", parents=[common], help="fact-check an existing text file")
    p.add_argument("file", help="path to a Markdown or text file to check")
    p.add_argument("--question", "-q", required=True, help="topic used to search for evidence")
    p.add_argument("--max-sources", type=int)
    p.add_argument("--max-claims", type=int)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("evaluate", parents=[common], help="score the verifier on a labelled dataset")
    p.add_argument("--dataset", help="JSONL dataset (default: data/benchmark/atlas_seed_v1.jsonl)")
    p.add_argument("--limit", type=int, help="only use the first N examples")
    p.add_argument("--model", help="verifier model to evaluate (overrides ATLAS_VERIFIER_MODEL)")
    p.add_argument("--batch-size", type=int, help="claims per Gemini call")
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("experiment", help="run a measurement experiment (results in data/experiments/)")
    p.add_argument(
        "name", choices=["scifact-build", "retrieval", "verifier", "planted", "injection"],
        help="which experiment to run",
    )
    p.add_argument("--dataset", help="verifier: JSONL dataset (default: SciFact 150)")
    p.add_argument("--model", default="gemini-3.5-flash-lite", help="model under test")
    p.add_argument("--runs", type=int, default=3, help="verifier: repeated runs")
    p.add_argument("--batch-size", type=int, help="verifier: claims per call")
    p.add_argument("--limit", type=int, help="verifier: only the first N examples")
    p.set_defaults(func=cmd_experiment)
    return parser


def cmd_experiment(args: argparse.Namespace, settings: Settings) -> int:
    name = args.name
    if name == "scifact-build":
        from .experiments.scifact import build_benchmark

        print(f"Wrote {build_benchmark()}")
        return 0
    if name == "retrieval":
        from .experiments.scifact import retrieval_recall

        r = retrieval_recall()
        print(f"Doc recall: {r['doc_recall']}\nRationale recall: {r['rationale_recall']}\nSaved to {r['output_dir']}")
        return 0
    if name == "verifier":
        from .experiments.scifact import DEFAULT_OUT
        from .experiments.verifier import verifier_runs

        dataset = Path(args.dataset) if args.dataset else DEFAULT_OUT
        tag = f"verifier_{dataset.stem}_{args.model}".replace(".", "-")
        r = verifier_runs(dataset, tag, model=args.model, runs=args.runs,
                          batch_size=args.batch_size, limit=args.limit)
        a = r["aggregate"]
        print(f"Accuracy {a['accuracy']['mean']:.3f} ± {a['accuracy']['sd']:.3f} | "
              f"macro F1 {a['macro_f1']['mean']:.3f} ± {a['macro_f1']['sd']:.3f} | served by {r['served_by']}")
        print(f"Saved to {r['output_dir']}")
        return 0
    if name == "planted":
        from .experiments.planted import run_planted

        r = run_planted(model=args.model)
        s = r["summary"]
        print(f"Content errors detected {s['content_detection_rate']:.1%} | "
              f"false alarms {s['false_alarm_rate']:.1%}\nSaved to {r['output_dir']}")
        return 0
    from .experiments.injection import run_injection

    r = run_injection(model=args.model)
    for attack, d in r["per_attack"].items():
        print(f"{attack:<14} success {d['success_rate']:.1%}")
    print(f"Saved to {r['output_dir']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _setup_logging(args.verbose)
    try:
        settings = _apply_overrides(Settings.from_env(), args)
        return args.func(args, settings)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # report cleanly instead of a traceback
        logging.getLogger("atlas").debug("Unhandled error", exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
