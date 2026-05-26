#!/usr/bin/env python3
"""Cross-biobank MR (OPTIONAL_SKIPPED for Round 0).

Full 2SMR across UKBB / FinnGen / BBJ requires harmonized GWAS instruments
and access to outcome cohorts. For Round 0, this mechanism is OPTIONAL_SKIPPED
with documented reason. Phase β may enable real MR if cached summary stats are present.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def main() -> int:
    output = {
        "mechanism": "cross_biobank_mr",
        "status": "OPTIONAL_SKIPPED",
        "reason": (
            "Round 0 bootstrap: harmonized multi-biobank GWAS summary statistics for "
            "exposure (cis-pQTL instruments per candidate) and outcomes (BMI, HbA1c, "
            "ALT, liver fat fraction) require ~10-50 GB of cached data per biobank "
            "(UKBB, FinnGen, BBJ). Not feasible to ingest in overnight Round 0. "
            "Pipeline architecture supports drop-in addition in Phase β by populating "
            "pipeline/data_sources/snapshots/mr_*.tsv files. "
            "Recommended: defer to Phase β engineering iteration with cached MR-Base "
            "summary statistics, or accept this as a documented limitation in FINAL_RESULT.md."
        ),
        "phase_beta_drop_in_path": "pipeline/data_sources/snapshots/mr_<biobank>_<phenotype>.tsv",
    }
    out_path = Path(__file__).resolve().parent / "_results_mr.json"
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True))
    print(f"cross_biobank_mr: wrote {out_path} (status=OPTIONAL_SKIPPED)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
