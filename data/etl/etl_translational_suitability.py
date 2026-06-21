#!/usr/bin/env python3
"""ETL: data-driven 'Translational cargo suitability' snapshot.

Produces data/snapshots_real/translational_cargo_suitability.tsv — one row per
L1-pass secreted-signaling ligand, with the four pass/fail flags derived ENTIRELY
from public data plus one small citable constant (the CVO structure list).

Data sources
------------
  ligand -> cognate receptor : OmniPath interactions (curated ligand-receptor
      edges; cognate receptor = single-gene target with the most curated sources,
      e.g. GDF15->GFRAL [6 sources] over GDF15->TGFBR2 [1]).
  HPA proteinatlas.tsv :
      Secretome location           -> C1a (ligand secreted to blood = endocrine)
      RNA tissue specificity       -> C2ii (receptor restricted)
      RNA tissue distribution / specific nTPM -> C1b peripheral test (receptor
                                      expressed outside brain = blood-accessible)
  Allen Mouse Brain ISH (api.brain-map.org) :
      Only queried for the few receptors that HPA shows as brain-restricted /
      below bulk detection. Structure-unionize expression_energy is used to test
      whether the receptor is enriched in a circumventricular organ (AP/NTS,
      blood-accessible) versus a behind-BBB region. This is what rescues GFRAL,
      which is below HPA bulk detection (area postrema is a tiny cell population).

The one non-data constant: the CVO keyword list (which brain structures are
circumventricular / blood-accessible). Standard neuroanatomy; cited below.
  CVOs: Gross PM, Weindl A. "Peering through the windows of the brain."
        J Cereb Blood Flow Metab. 1987;7:663-672.  (area postrema, NTS-adjacent,
        median eminence, subfornical organ, OVLT, subcommissural organ)
GFRAL localization to area postrema / NTS:
  Mullican SE et al. Nat Med 2017; Emmerson PJ et al. Nat Med 2017;
  Yang L et al. Nat Med 2017; Hsu JY et al. Nature 2017.
"""
from __future__ import annotations
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HPA = REPO / "data/raw_dumps/hpa/proteinatlas.tsv"
OMNI = REPO / "data/raw_dumps/omnipath/ligand_receptor_edges.tsv"
ALLEN_CACHE = REPO / "data/raw_dumps/allen"
OUT = REPO / "data/snapshots_real/translational_cargo_suitability.tsv"

ALLEN_CACHE.mkdir(parents=True, exist_ok=True)

# --- the one citable constant: CVO (blood-accessible) vs behind-BBB structures
CVO_KEYWORDS = ("area postrema", "solitary", "subfornical", "lamina terminalis",
                "vascular organ", "median eminence", "subcommissural")
BBB_REF_KEYWORDS = ("hypothalamus", "isocortex", "cerebral cortex", "thalamus",
                    "hippocamp", "amygdal", "olfactory")
CVO_RATIO = 2.0          # brain-restricted receptor is blood-accessible if
                         # max CVO energy >= CVO_RATIO * max behind-BBB energy
RESTRICTED_SPEC = {"Tissue enriched", "Group enriched"}   # strict C2ii


def log(m): print(f"[etl_tcs] {m}", file=sys.stderr, flush=True)


def allen_get(url):
    return json.load(urllib.request.urlopen(url, timeout=90))["msg"]


def allen_cvo_verdict(gene):
    """Return (cvo_max, cvo_struct, bbb_max, datasets) for a mouse gene, cached."""
    cache = ALLEN_CACHE / f"{gene}_unionize.json"
    if cache.exists():
        rows = json.loads(cache.read_text())
    else:
        mouse = gene.capitalize()          # Allen mouse symbols are title-case (GFRAL->Gfral)
        q = ("http://api.brain-map.org/api/v2/data/query.json?criteria=model::"
             "SectionDataSet,rma::criteria,genes[acronym$eq'%s'],products[id$eq1]"
             "&only=data_sets.id" % mouse)
        dsets = [r["id"] for r in allen_get(q)]
        rows = []
        for ds in dsets:
            q2 = ("http://api.brain-map.org/api/v2/data/query.json?criteria=model::"
                  "StructureUnionize,rma::criteria,[section_data_set_id$eq%d],"
                  "rma::include,structure,rma::options[order$eq'structure_unionizes."
                  "expression_energy$desc'][num_rows$eq60]"
                  "&only=structure_unionizes.expression_energy,structures.name" % ds)
            for r in allen_get(q2):
                rows.append({"e": r.get("expression_energy", 0) or 0,
                             "name": (r.get("structure") or {}).get("name", "")})
            time.sleep(0.2)
        cache.write_text(json.dumps(rows))
    cvo_max, cvo_struct, bbb_max = 0.0, "", 0.0
    for r in rows:
        n = r["name"].lower()
        if any(k in n for k in CVO_KEYWORDS) and r["e"] > cvo_max:
            cvo_max, cvo_struct = r["e"], r["name"]
        if any(k in n for k in BBB_REF_KEYWORDS) and r["e"] > bbb_max:
            bbb_max = r["e"]
    return cvo_max, cvo_struct, bbb_max


def load_receptors():
    by = {}
    for r in csv.DictReader(OMNI.open(), delimiter="\t"):
        t = r["target_genesymbol"]
        if "_" in t:
            continue
        n = (r["sources"].count(";") + 1) if r["sources"] else 1
        by.setdefault(r["source_genesymbol"], []).append((t, n))
    return {l: sorted(v, key=lambda x: -x[1])[0][0] for l, v in by.items()}


def load_hpa():
    h = {}
    for row in csv.DictReader(HPA.open(), delimiter="\t"):
        h[row["Gene"]] = {"sec": row.get("Secretome location", ""),
                          "spec": row.get("RNA tissue specificity", ""),
                          "dist": row.get("RNA tissue distribution", ""),
                          "ntpm": row.get("RNA tissue specific nTPM", "")}
    return h


def receptor_peripheral(h):
    """C1b peripheral branch: receptor expressed in >=1 non-brain tissue?"""
    spec, dist, ntpm = h["spec"], h["dist"], h["ntpm"]
    if spec in ("Not detected", "") or dist == "Not detected":
        return False
    if dist in ("Detected in all", "Detected in many"):
        return True
    ts = [t.split(":")[0].strip() for t in ntpm.split(";") if t.strip()]
    if ts:
        return any(t != "brain" for t in ts)
    return False


def main():
    recep = load_receptors()
    hpa = load_hpa()
    # universe = ligands we have a secretome row for and that map to a receptor
    ligands = sorted(g for g in hpa if g in recep)

    fields = ["gene_symbol", "cognate_receptor", "ligand_secretome",
              "receptor_tissue_specificity", "receptor_peripheral",
              "receptor_brain_restricted", "allen_cvo_struct", "allen_cvo_energy",
              "allen_bbb_energy", "c1a_secreted_blood", "c1b_blood_accessible",
              "c2i_has_receptor", "c2ii_restricted"]
    out_rows = []
    for g in ligands:
        rg = recep.get(g)
        lh = hpa.get(g, {})
        rh = hpa.get(rg, {})
        c1a = lh.get("sec", "") == "Secreted to blood"
        c2i = bool(rg)
        periph = receptor_peripheral(rh) if rh else False
        brain_restricted = bool(rg) and not periph
        cvo_struct, cvo_e, bbb_e = "", "", ""
        c1b = periph
        c2ii = rh.get("spec", "") in RESTRICTED_SPEC
        if brain_restricted and rg:
            log(f"Allen CVO check for {g}->{rg} ...")
            cmax, cstruct, bmax = allen_cvo_verdict(rg)
            cvo_struct, cvo_e, bbb_e = cstruct, f"{cmax:.3f}", f"{bmax:.3f}"
            cvo_access = (cmax >= 1.0) and (cmax >= CVO_RATIO * max(bmax, 1e-9))
            c1b = cvo_access
            # a receptor confined to a tiny CVO is, by construction, restricted
            if cvo_access:
                c2ii = True
        out_rows.append({
            "gene_symbol": g, "cognate_receptor": rg or "",
            "ligand_secretome": lh.get("sec", ""),
            "receptor_tissue_specificity": rh.get("spec", ""),
            "receptor_peripheral": periph, "receptor_brain_restricted": brain_restricted,
            "allen_cvo_struct": cvo_struct, "allen_cvo_energy": cvo_e,
            "allen_bbb_energy": bbb_e,
            "c1a_secreted_blood": c1a, "c1b_blood_accessible": c1b,
            "c2i_has_receptor": c2i, "c2ii_restricted": c2ii,
        })

    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(out_rows)
    log(f"wrote {len(out_rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
