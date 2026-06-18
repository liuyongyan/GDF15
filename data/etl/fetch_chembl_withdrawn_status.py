#!/usr/bin/env python3
"""Fetch ChEMBL withdrawn_flag / withdrawn_year / withdrawn_reason for compounds
with max_phase >= 2 in our metabolic ChEMBL subset.

Background: ChEMBL `max_phase` records the highest clinical phase a compound
reached. It does NOT indicate whether the program subsequently failed or the
drug was withdrawn from the market. For our Layer 6 opportunity penalty to
distinguish "active clinical program" (correctly penalized as crowded) from
"approved-then-withdrawn" (should NOT be treated as crowded), we need the
`withdrawn_flag` field, which the original ChEMBL-by-indication REST query
did not pull.

This script reads the existing chembl_metabolic_api_subset.tsv, extracts
unique compound IDs with max_phase >= 2, and queries via the molecule endpoint
in batches (molecule_chembl_id__in=...) to avoid one-at-a-time API latency.

Output: data/snapshots_real/chembl_withdrawn_status.tsv with columns
compound_chembl_id, withdrawn_flag (True/False), withdrawn_year, withdrawn_reason.
"""
from __future__ import annotations
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
INPUT = REPO / "data" / "raw_dumps" / "chembl" / "chembl_metabolic_api_subset.tsv"
OUTPUT = REPO / "data" / "snapshots_real" / "chembl_withdrawn_status.tsv"

API_BASE = "https://www.ebi.ac.uk/chembl/api/data/molecule.json"
BATCH_SIZE = 50         # ChEMBL allows large in-lists; 50 keeps URL under most limits
BATCH_INTERVAL = 0.5    # seconds between batches (polite)


def fetch_batch(chembl_ids: list[str]) -> dict[str, dict] | None:
    """Fetch a batch of molecules; returns dict keyed by chembl_id, or None on error."""
    params = {
        'molecule_chembl_id__in': ','.join(chembl_ids),
        'limit': str(len(chembl_ids)),
        'only': 'molecule_chembl_id,withdrawn_flag,withdrawn_year,withdrawn_reason',
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  batch error: {e}", file=sys.stderr)
        return None
    out = {}
    for mol in data.get('molecules', []):
        cid = mol.get('molecule_chembl_id')
        if cid:
            out[cid] = mol
    return out


def main():
    if not INPUT.exists():
        sys.exit(f"ERROR: input not found at {INPUT}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open() as f:
        rows = [r for r in csv.DictReader(
            [ln for ln in f if not ln.startswith("#") and ln.strip()],
            delimiter="\t")]

    unique_compounds = sorted({
        r["compound_chembl_id"] for r in rows
        if r.get("compound_chembl_id")
        and r.get("max_phase")
        and float(r["max_phase"]) >= 2
    })
    print(f"Compounds to fetch: {len(unique_compounds)}")

    # Resume support: load any already-fetched IDs
    done: set[str] = set()
    if OUTPUT.exists():
        with OUTPUT.open() as f:
            for r in csv.DictReader(f, delimiter="\t"):
                done.add(r["compound_chembl_id"])
        print(f"Resuming: {len(done)} already fetched")

    pending = [c for c in unique_compounds if c not in done]
    print(f"Pending: {len(pending)}; {-(-len(pending)//BATCH_SIZE)} batches of {BATCH_SIZE}")

    fout_first = not OUTPUT.exists()
    fout = OUTPUT.open("a", encoding="utf-8", newline="")
    writer = csv.writer(fout, delimiter="\t")
    if fout_first:
        writer.writerow(["compound_chembl_id", "withdrawn_flag",
                         "withdrawn_year", "withdrawn_reason"])
        fout.flush()

    n_fetched = 0
    n_withdrawn = 0
    n_missing = 0
    t_start = time.time()

    for i in range(0, len(pending), BATCH_SIZE):
        batch = pending[i:i + BATCH_SIZE]
        result = fetch_batch(batch)
        if result is None:
            # Backoff and retry once
            time.sleep(5.0)
            result = fetch_batch(batch)
        if result is None:
            print(f"  batch {i//BATCH_SIZE} failed twice, skipping")
            for cid in batch:
                writer.writerow([cid, "False", "", "fetch_failed"])
            fout.flush()
            continue
        for cid in batch:
            mol = result.get(cid)
            if mol is None:
                writer.writerow([cid, "False", "", "not_found"])
                n_missing += 1
            else:
                wf = bool(mol.get("withdrawn_flag"))
                wy = mol.get("withdrawn_year") or ""
                wr = mol.get("withdrawn_reason") or ""
                writer.writerow([cid, str(wf), wy, wr])
                if wf:
                    n_withdrawn += 1
                    print(f"  WITHDRAWN: {cid}  year={wy}  reason={wr}")
            n_fetched += 1
        fout.flush()
        elapsed = time.time() - t_start
        rate = n_fetched / elapsed if elapsed > 0 else 0
        remaining = (len(pending) - (i + len(batch))) / rate if rate > 0 else 0
        print(f"  batch {i//BATCH_SIZE + 1}: fetched {n_fetched}/{len(pending)} "
              f"({rate*60:.0f}/min, eta {remaining/60:.1f} min)")
        time.sleep(BATCH_INTERVAL)

    fout.close()
    print(f"\nDONE: {n_fetched} fetched, {n_withdrawn} withdrawn, {n_missing} not_found")
    print(f"Output: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
