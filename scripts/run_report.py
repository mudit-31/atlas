import sys
import argparse
from src.agent import run_research


def main() -> None:
    """CLI entry point for running the research agent to generate reports."""
    parser = argparse.ArgumentParser(
        description="Run the ATLAS V1 Research Agent to generate an evidence-backed report."
    )
    parser.add_argument(
        "--question",
        type=str,
        required=True,
        help="The research question or topic to analyze."
    )
    
    args = parser.parse_args()
    
    try:
        output_path = run_research(args.question)
        print(f"\nResearch report generation complete.")
        print(f"Report Output Path: {output_path}")
    except Exception as e:
        print(f"\nError executing research: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
