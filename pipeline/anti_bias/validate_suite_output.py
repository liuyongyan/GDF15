#!/usr/bin/env python3
"""Validate anti-bias suite output against TARGET-AGNOSTIC thresholds.

Reads thresholds.json and each _results_*.json, computes per-mechanism PASS/FAIL/SKIP,
and emits a summary. Returns non-zero if any HARD threshold fails (severity != "soft").
Soft failures are reported but do not block.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent

MECH_FILE_MAP = {
    "loo_ablation": "_results_loo.json",
    "negative_controls": "_results_nc.json",
    "literature_blinded": "_results_lit_blind.json",
    "cross_biobank_mr": "_results_mr.json",
    "permutation_test": "_results_perm.json",
}


def evaluate(thresholds: dict, results: dict[str, dict]) -> tuple[list[dict], int, int]:
    """Returns (per_mechanism_status, n_failed_hard, n_failed_soft)."""
    statuses: list[dict] = []
    failed_hard = 0
    failed_soft = 0

    # LOO ablation: avg rank change <= max_avg_rank_change_in_top5
    loo = results.get("loo_ablation") or {}
    th = thresholds.get("loo_ablation", {})
    actual = loo.get("aggregate_mean_rank_change")
    threshold_val = th.get("max_avg_rank_change_in_top5")
    severity = th.get("severity", "soft")
    if actual is None or threshold_val is None:
        statuses.append({"mechanism": "loo_ablation", "status": "MISSING", "severity": severity})
        if severity != "soft": failed_hard += 1
        else: failed_soft += 1
    elif actual <= threshold_val:
        statuses.append({"mechanism": "loo_ablation", "status": "PASS",
                          "actual": actual, "threshold": threshold_val, "severity": severity})
    else:
        statuses.append({"mechanism": "loo_ablation", "status": "FAIL",
                          "actual": actual, "threshold": threshold_val, "severity": severity})
        if severity != "soft": failed_hard += 1
        else: failed_soft += 1

    # Negative controls: mean percentile >= min_percentile
    nc = results.get("negative_controls") or {}
    th = thresholds.get("negative_controls", {})
    actual = nc.get("mean_percentile_of_controls")
    threshold_val = th.get("min_percentile")
    severity = th.get("severity", "soft")
    if actual is None or threshold_val is None:
        statuses.append({"mechanism": "negative_controls", "status": "MISSING", "severity": severity})
        if severity != "soft": failed_hard += 1
        else: failed_soft += 1
    elif actual >= threshold_val:
        statuses.append({"mechanism": "negative_controls", "status": "PASS",
                          "actual": actual, "threshold": threshold_val, "severity": severity})
    else:
        statuses.append({"mechanism": "negative_controls", "status": "FAIL",
                          "actual": actual, "threshold": threshold_val, "severity": severity})
        if severity != "soft": failed_hard += 1
        else: failed_soft += 1

    # Literature-blinded: top5 overlap count >= min_top5_overlap
    lb = results.get("literature_blinded") or {}
    th = thresholds.get("literature_blinded", {})
    actual = lb.get("top5_overlap_count")
    threshold_val = th.get("min_top5_overlap")
    severity = th.get("severity", "soft")
    if actual is None or threshold_val is None:
        statuses.append({"mechanism": "literature_blinded", "status": "MISSING", "severity": severity})
        if severity != "soft": failed_hard += 1
        else: failed_soft += 1
    elif actual >= threshold_val:
        statuses.append({"mechanism": "literature_blinded", "status": "PASS",
                          "actual": actual, "threshold": threshold_val, "severity": severity})
    else:
        statuses.append({"mechanism": "literature_blinded", "status": "FAIL",
                          "actual": actual, "threshold": threshold_val, "severity": severity})
        if severity != "soft": failed_hard += 1
        else: failed_soft += 1

    # Cross-biobank MR: OPTIONAL_SKIPPED accepted, else needs agreement >= min_biobank_agreement
    mr = results.get("cross_biobank_mr") or {}
    th = thresholds.get("cross_biobank_mr", {})
    severity = th.get("severity", "soft")
    if mr.get("status") == "OPTIONAL_SKIPPED" and th.get("optional_skip_allowed", True):
        statuses.append({"mechanism": "cross_biobank_mr", "status": "OPTIONAL_SKIPPED",
                          "reason": mr.get("reason"), "severity": severity})
    else:
        actual = mr.get("biobank_agreement")
        threshold_val = th.get("min_biobank_agreement")
        if actual is None or threshold_val is None:
            statuses.append({"mechanism": "cross_biobank_mr", "status": "MISSING", "severity": severity})
            if severity != "soft": failed_hard += 1
            else: failed_soft += 1
        elif actual >= threshold_val:
            statuses.append({"mechanism": "cross_biobank_mr", "status": "PASS",
                              "actual": actual, "threshold": threshold_val, "severity": severity})
        else:
            statuses.append({"mechanism": "cross_biobank_mr", "status": "FAIL",
                              "actual": actual, "threshold": threshold_val, "severity": severity})
            if severity != "soft": failed_hard += 1
            else: failed_soft += 1

    # Permutation: empirical p < max_p_value
    perm = results.get("permutation_test") or {}
    th = thresholds.get("permutation_test", {})
    actual = perm.get("empirical_p_value")
    threshold_val = th.get("max_p_value")
    severity = th.get("severity", "soft")
    if actual is None or threshold_val is None:
        statuses.append({"mechanism": "permutation_test", "status": "MISSING", "severity": severity})
        if severity != "soft": failed_hard += 1
        else: failed_soft += 1
    elif actual < threshold_val:
        statuses.append({"mechanism": "permutation_test", "status": "PASS",
                          "actual": actual, "threshold": threshold_val, "severity": severity})
    else:
        statuses.append({"mechanism": "permutation_test", "status": "FAIL",
                          "actual": actual, "threshold": threshold_val, "severity": severity})
        if severity != "soft": failed_hard += 1
        else: failed_soft += 1

    return statuses, failed_hard, failed_soft


def main() -> int:
    thresholds = json.loads((HERE / "thresholds.json").read_text())

    # Load each mechanism's result file
    results: dict[str, dict] = {}
    missing_files = []
    for mech, fn in MECH_FILE_MAP.items():
        p = HERE / fn
        if not p.exists():
            missing_files.append(fn)
            continue
        try:
            results[mech] = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            print(f"validate_suite_output: malformed JSON in {fn}: {e}", file=sys.stderr)
            return 1

    if missing_files:
        print(f"validate_suite_output: FAIL - missing result files: {missing_files}", file=sys.stderr)
        return 1

    statuses, failed_hard, failed_soft = evaluate(thresholds, results)

    # Print human-readable report
    print("validate_suite_output: per-mechanism threshold status")
    for s in statuses:
        marker = {"PASS": "✓", "FAIL": "✗", "OPTIONAL_SKIPPED": "○", "MISSING": "?"}.get(s.get("status"), "·")
        print(f"  [{marker}] {s['mechanism']:25s} {s['status']:18s} severity={s.get('severity', 'n/a')}", end="")
        if "actual" in s and "threshold" in s:
            print(f"  actual={s['actual']:.4f}  threshold={s['threshold']}")
        else:
            print()

    # Write summary JSON for downstream consumption (assemble_output, FINAL_RESULT)
    summary_path = HERE / "_validation_summary.json"
    summary_path.write_text(json.dumps({
        "statuses": statuses,
        "failed_hard_count": failed_hard,
        "failed_soft_count": failed_soft,
        "overall_status": "PASS" if failed_hard == 0 else "FAIL",
    }, indent=2, sort_keys=True))

    if failed_hard > 0:
        print(f"validate_suite_output: FAIL - {failed_hard} HARD threshold(s) violated", file=sys.stderr)
        return 1
    if failed_soft > 0:
        print(f"validate_suite_output: PASS-WITH-SOFT-FAILURES - {failed_soft} soft threshold(s) violated (non-blocking; reported)")
        return 0
    print("validate_suite_output: PASS - all thresholds satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
