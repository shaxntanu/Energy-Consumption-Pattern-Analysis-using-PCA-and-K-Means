"""
Real-world validation run (Improvement 3, orchestrator).

Run the separate real-world pathway end to end:

    raw dataset
        -> dataset_adapter (map columns, convert to kWh)
        -> validate_panel_shape (contract guard)
        -> ingest (window / meter cap, ingestion facts)
        -> preprocess_pipeline (within-meter imputation, shared with synthetic)
        -> engineer_all_features / select_features (behavioural shape features)
        -> run_pca_pipeline (scale + PCA, shared with synthetic)
        -> find_optimal_k / select_optimal_k / perform_kmeans (shared rule)
        -> realworld_validate (internal + restart + temporal stability, NO ARI/NMI)
        -> report (markdown + JSON summary)

The validation is deliberately kept separate from the synthetic branch's
ARI/NMI marking: real data has no ground-truth archetype, so the real branch
speaks only in internal quality and stability. The synthetic branch still owns
the archetype marking; the two never mix.

Run (from the project root):

    py src/run_realworld.py --source data/real/sample.csv --adapter generic_csv
    py src/run_realworld.py --demo            # synthetic plumbing smoke test

By default (no --source and no --demo) it exercises the pipeline on the small
in-repo demo panel so the pathway is runnable without a download.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _anchor():
    """Make top-level src imports resolve when run as `py src/run_realworld.py`."""
    import project_paths
    project_paths.anchor_to_project_root()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    data = p.add_mutually_exclusive_group()
    data.add_argument("--demo", action="store_true",
                      help="Run on the small in-repo demo panel (synthetic plumbing only).")
    data.add_argument("--source", type=str, default=None,
                      help="Path to a real-world CSV file to ingest via the adapter.")
    p.add_argument("--adapter", type=str, default="generic_csv",
                   choices=["generic_csv", "uci_power"],
                   help="Adapter mapping the source file onto the pipeline panel.")
    p.add_argument("--meter-cap", type=int, default=None,
                   help="Keep only the first N meters (window the load).")
    p.add_argument("--start", type=str, default=None,
                   help="Inclusive date floor, e.g. 2008-01-01.")
    p.add_argument("--end", type=str, default=None, help="Inclusive date ceiling.")
    p.add_argument("--k-min", type=int, default=2)
    p.add_argument("--k-max", type=int, default=8)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", type=str, default=None,
                   help="Output markdown path (default outputs/reports/real_world_<source>.md).")
    p.add_argument("--json", type=str, default=None,
                   help="Optional path to also write a compact JSON summary.")
    return p


def main(argv=None) -> int:
    _anchor()
    args = _build_parser().parse_args(argv)

    from realworld_ingest import RealWorldConfig, ingest, make_demo_panel
    from realworld_validate import RealWorldReport, run_real_world_study, write_report

    route = "demo" if args.demo else ("source:" + str(args.source) if args.source else "demo")
    logger.info("Real-world pathway route: %s", route)

    if args.source:
        if not Path(args.source).exists():
            logger.error("Source file not found: %s", args.source)
            return 2
        config = RealWorldConfig(
            source_path=args.source,
            adapter=args.adapter,
            meter_cap=args.meter_cap,
            date_start=args.start,
            date_end=args.end,
        )
        panel, facts = ingest(config)
    else:
        # No --source and no --demo: exercise the pathway on the in-repo demo panel.
        panel = make_demo_panel(seed=args.seed)
        facts = {
            "source": "demo:generic_csv",
            "source_name": "demo_panel",
            "description": ("Tiny in-repo multi-meter daily-load panel. This exercises "
                            "the real-world plumbing ONLY and is not study evidence."),
            "citation": "N/A - synthetic provenance for a pipeline smoke test.",
            "url": "",
            "license": "N/A",
            "meters": int(panel["meter_id"].nunique()),
            "date_start": str(panel["timestamp"].min()),
            "date_end": str(panel["timestamp"].max()),
            "config": {"adapter": "generic_csv", "route": "demo_smoke_test"},
        }

    study = run_real_world_study(
        panel,
        facts,
        k_range=(args.k_min, args.k_max),
        random_state=args.seed,
    )

    out_md = args.out or f"outputs/reports/real_world_{study.source_name}.md"
    text = write_report(study, out_md)
    print(text)

    if args.json:
        summary = {
            "source_name": study.source_name,
            "meters": study.n_meters,
            "records": study.n_records,
            "features": len(study.feature_names),
            "pca_components": study.n_pca_components,
            "pca_cumulative_variance": round(study.pca_cumulative_variance, 4),
            "k": study.optimal_k,
            "internal": study.internal_scores(),
            "temporal_stability": study.temporal_stability_at_k.get(study.optimal_k, {}),
            "warnings": study.warnings,
            "report_md": out_md,
        }
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nJSON summary written to {args.json}")

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())