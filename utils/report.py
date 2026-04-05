"""
AutoASO Report Generator

Reads all results TSV files and prints a summary of experiment progress.

Usage:
    python utils/report.py                           # all apps
    python utils/report.py --app kids_focus_ios_us   # specific app
"""

import argparse
import os
import sys


def parse_tsv(filepath: str) -> list[dict]:
    rows = []
    try:
        with open(filepath) as f:
            lines = f.readlines()
        if len(lines) < 2:
            return rows
        # skip header
        for line in lines[1:]:
            parts = line.strip().split("\t")
            if len(parts) < 4:
                continue
            rows.append({
                "commit":      parts[0],
                "total_score": float(parts[1]),
                "status":      parts[2],
                "description": parts[3],
            })
    except Exception as e:
        print(f"  Warning: could not parse {filepath}: {e}", file=sys.stderr)
    return rows


def report_app(name: str, rows: list[dict]):
    if not rows:
        print(f"\n  {name}: no experiments yet.\n")
        return

    kept     = [r for r in rows if r["status"] == "keep"]
    discarded = [r for r in rows if r["status"] == "discard"]
    crashed  = [r for r in rows if r["status"] == "crash"]

    baseline_score = rows[0]["total_score"] if rows else 0.0
    best_score     = max(r["total_score"] for r in kept) if kept else baseline_score
    improvement    = best_score - baseline_score

    print(f"\n{'─'*55}")
    print(f"  App:         {name}")
    print(f"  Experiments: {len(rows)} total | {len(kept)} kept | {len(discarded)} discarded | {len(crashed)} crashed")
    print(f"  Baseline:    {baseline_score:.2f}")
    print(f"  Best score:  {best_score:.2f}  (+{improvement:.2f})")
    print(f"{'─'*55}")

    print("  Last 5 experiments:")
    for r in rows[-5:]:
        mark = "✓" if r["status"] == "keep" else "✗" if r["status"] == "discard" else "!"
        print(f"  {mark}  [{r['commit'][:7]}] {r['total_score']:.2f}  {r['description'][:45]}")
    print()


def main():
    parser = argparse.ArgumentParser(description="AutoASO Report")
    parser.add_argument("--app", default=None, help="Specific app name (filename without .tsv)")
    args = parser.parse_args()

    results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    results_dir = os.path.normpath(results_dir)

    if not os.path.isdir(results_dir):
        print(f"Results directory not found: {results_dir}")
        sys.exit(1)

    tsv_files = sorted(f for f in os.listdir(results_dir) if f.endswith(".tsv"))

    if args.app:
        tsv_files = [f for f in tsv_files if f == f"{args.app}.tsv"]

    if not tsv_files:
        print("No results files found.")
        sys.exit(0)

    print("\n" + "═" * 55)
    print("  AutoASO — Experiment Report")
    print("═" * 55)

    for tsv_file in tsv_files:
        name = tsv_file.replace(".tsv", "")
        rows = parse_tsv(os.path.join(results_dir, tsv_file))
        report_app(name, rows)


if __name__ == "__main__":
    main()
