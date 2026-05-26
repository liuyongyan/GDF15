#!/usr/bin/env python3
"""Post-hoc platform compatibility check.

Reads the top-N candidates from the Pipeline's composite ranking and evaluates each
against the saRNA + sublingual microneedle delivery platform's hard constraints:
  - is_secreted == True
  - 100 <= orf_length_bp <= 15000
  - signal_peptide present (preferred but not required)

Produces a TSV of top-N x platform-criteria + an overall verdict per candidate.
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path


PIPELINE_ROOT = Path(__file__).resolve().parent.parent
UNIVERSE_TSV = PIPELINE_ROOT / "universe" / "candidate_universe.tsv"
UP_SNAPSHOT = PIPELINE_ROOT / "data_sources" / "snapshots" / "uniprot_protein_classes.tsv"


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: platform_compatibility.py <pipeline_output.json> <output_tsv>", file=sys.stderr)
        return 2
    output_json_path = Path(sys.argv[1])
    output_tsv_path = Path(sys.argv[2])

    output_json = json.loads(output_json_path.read_text())
    ranked = output_json.get("ranked_targets", [])[:25]  # top 25

    # Load UniProt index
    up_idx: dict[str, dict] = {}
    with UP_SNAPSHOT.open() as f:
        for ln in f:
            if ln.startswith("#") or not ln.strip():
                continue
        # Reset and re-read with DictReader
    with UP_SNAPSHOT.open() as f:
        non_comment = [ln for ln in f if not ln.startswith("#") and ln.strip()]
        reader = csv.DictReader(non_comment, delimiter="\t")
        for r in reader:
            up_idx[r["ensembl_gene_id"]] = r

    output_tsv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_tsv_path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow([
            "rank", "ensembl_gene_id", "gene_symbol",
            "is_secreted", "orf_length_bp", "signal_peptide",
            "passes_secretion", "passes_orf_size", "passes_signal", "platform_compatible_overall",
        ])
        for entry in ranked:
            eg = entry.get("ensembl_gene_id")
            sym = entry.get("gene_symbol", "")
            rank = entry.get("rank", "")
            meta = up_idx.get(eg, {})
            is_sec = meta.get("is_secreted", "False") == "True"
            try:
                orf = int(meta.get("orf_length_bp", "0"))
            except ValueError:
                orf = 0
            has_sig = meta.get("signal_peptide", "False") == "True"
            passes_sec = is_sec
            passes_orf = 100 <= orf <= 15000
            passes_sig = has_sig
            overall = passes_sec and passes_orf
            writer.writerow([
                rank, eg, sym,
                "True" if is_sec else "False",
                orf,
                "True" if has_sig else "False",
                "PASS" if passes_sec else "FAIL",
                "PASS" if passes_orf else "FAIL",
                "PASS" if passes_sig else "FAIL",
                "PASS" if overall else "FAIL",
            ])

    print(f"platform_compatibility: wrote {output_tsv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
