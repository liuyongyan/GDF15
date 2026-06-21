# Why We Chose GDF15

*An accessible explanation of our target selection rationale for the saRNA-sublingual delivery platform.*

**Lab**: Cheng Lab, Columbia University, Department of Biomedical Engineering / Department of Medicine.

**Project**: Self-amplifying RNA + sublingual microneedle delivery of a secreted endocrine factor for obesity, type 2 diabetes, and metabolic-associated steatohepatitis (MASH).

**Document version**: 2026-06-21 (six-layer cascade: five data-driven boolean gates — L1-L4 plus a data-driven L5 "translational cargo suitability" gate — followed by the L6 opportunity ranker. The cascade now ends at a ranked shortlist; the single-cargo selection of GDF15 is an explicit human-synthesis step in §6, which absorbed the deliverability judgments that an earlier revision ran as a hand-curated "expert" gate). All numbers below derive from the cascade applied to fully real public data (Open Targets 26.03, NHGRI-EBI GWAS Catalog latest, UniProt SwissProt human reviewed, ChEMBL via REST API by indication, PubMed E-utilities literature counts, Human Protein Atlas tissue/secretome data, OmniPath ligand-receptor edges, and Allen Mouse Brain ISH), plus one citable constant (the circumventricular-organ structure list used by L5).

---

## 1. The problem we are trying to solve

Obesity, type 2 diabetes (T2D), and metabolic-associated steatohepatitis (MASH) together affect over a billion people globally and account for the largest preventable disease burden in the developed world. Until very recently, the pharmacological options for chronic weight management were limited to a handful of marginally effective drugs with poor tolerability.

That changed dramatically with the GLP-1 receptor agonist class — semaglutide (Ozempic, Wegovy), tirzepatide (Mounjaro, Zepbound, the GLP-1/GIP dual agonist), and the in-development retatrutide (GLP-1/GIP/glucagon triple agonist, ~24% mean weight loss in Phase 2). These drugs produce weight loss results approaching those of bariatric surgery, and the market response has been historic.

But the GLP-1 class has not solved the problem. The remaining limitations are not minor:

| Limitation | Why it matters |
|---|---|
| **Severe GI side effects** | Nausea, vomiting, constipation in 15–44% of patients. The leading cause of treatment discontinuation. |
| **Lean mass loss** | 25–40% of total weight loss is lean tissue (muscle and organ mass), not fat. A growing safety concern in elderly populations and long-term users. |
| **Rebound on discontinuation** | Patients who stop GLP-1 therapy regain nearly all lost weight within a year. The implication is *lifetime* therapy. |
| **β-cell dependency in T2D** | GLP-1 efficacy declines as pancreatic β-cells deteriorate in late-stage T2D. The patients who need the most help respond the least. |
| **Injection administration** | Most GLP-1 drugs require weekly subcutaneous injection. Oral semaglutide (Rybelsus) exists but absorbs at roughly 1% bioavailability and requires fasting plus a permeation enhancer. |
| **Cost and access** | $1000–1500 per month in the US; global supply remains constrained. |
| **Non-responders** | 10–30% of patients respond poorly or not at all. The mechanism of resistance is not well understood. |

The honest framing of our project is not "we are going to beat semaglutide on weight loss." The GLP-1 class is the high bar in that race. Our framing is: **how do we deliver a complementary therapeutic that addresses the limitations above, rather than competing head-on with the existing class?**

---

## 2. A different way to deliver a drug

The Cheng Lab has been developing a delivery platform built on two pieces of technology:

1. **Self-amplifying RNA (saRNA)**: an engineered RNA molecule that, once inside a cell, both encodes the therapeutic protein *and* replicates itself for an extended period. Compared to conventional mRNA (which is translated once and rapidly degraded), saRNA produces sustained protein expression from a single dose — measured in days to weeks rather than hours.

2. **Sublingual microneedles**: a small dissolving patch placed under the tongue. The microneedles painlessly deposit the saRNA payload into the highly vascularized sublingual mucosa, where it is taken up by local cells. The patch dissolves in minutes; there is no injection, no swallowing, and no need for fasting.

Combined, the platform enables a patient to receive a long-acting protein therapeutic by holding a small patch under the tongue for a few minutes, perhaps once a week or once every two weeks. It addresses, in principle, the *administration* and *durability* limitations of the current GLP-1 class.

There is, however, a fundamental constraint built into this modality: **whatever therapeutic protein it delivers must be one that the patient's own cells can produce correctly from an RNA template**. This sounds obvious, but it excludes much of modern pharmacology. Specifically:

- **Semaglutide and tirzepatide cannot be delivered this way.** Both are chemically modified peptides. Semaglutide contains an Aib (α-aminoisobutyric acid) residue at position 8 of its sequence — Aib is not one of the 20 standard amino acids and cannot be inserted by a ribosome. It also carries a C18 fatty acid side chain that extends its half-life from 1–2 minutes to about a week; this chemical modification is added during industrial synthesis and cannot be encoded by RNA. Tirzepatide has analogous modifications.

- **Native GLP-1, while encodable, is useless on its own.** The unmodified peptide is degraded in the bloodstream within 1–2 minutes by the enzyme DPP-4. Continuous RNA-driven expression cannot keep up with this clearance rate.

This is not a limitation we worked around with clever engineering. It is a physics-of-delivery fact. The same fact, however, defines an opportunity: there exists a class of therapeutically interesting proteins that are **natively secreted, intrinsically stable, and pharmacologically active without chemical modification** — and these are exactly the proteins our platform is well-suited to deliver. The GLP-1 drugs cannot enter this space. Our platform's question is therefore not "what beats GLP-1" but "**which natively-deliverable secreted protein addresses an unmet need that GLP-1 cannot reach?**"

---

## 3. The target selection problem

Once we commit to the saRNA-microneedle modality, we still have to choose which protein it should produce. The human body makes roughly 20,000 distinct protein-coding genes, and several thousand of these encode secreted proteins. Of those, some address metabolic disease biology; some are druggable; some are tractable for clinical development. The intersection of these requirements is non-obvious.

Naive answers do not work:

- *"Just pick the most studied metabolic protein."* That would point us at leptin or insulin — both have decades of failed clinical development for chronic weight management and well-understood reasons (leptin resistance, insulin's hypoglycemia risk).
- *"Pick whatever has the strongest genetic association."* Genome-wide association studies highlight hundreds of genes; many are upstream regulators that are not directly druggable or are not secreted.
- *"Pick whatever a clinician thinks is best."* This biases toward what the clinician has personally seen succeed, which is essentially the GLP-1 class again.

The selection has to consider multiple dimensions at once: **what the disease biology actually supports, what the modality can physically deliver, what is technically druggable, what is clinically underdeveloped (rather than already crowded), and what carries acceptable safety risk.** We built an AI-assisted pipeline to make this selection systematic and auditable rather than ad hoc.

---

## 4. The pipeline: a six-layer constraint cascade

We assembled what we call a **target cascade**. Starting from the full set of ~20,000 reviewed human protein-coding genes, the pipeline applies six sequential layers. The first five (L1 through L5) are **boolean gates**: a candidate either passes each filter or it does not. The sixth (L6) is the **ranker**: it does not filter the admissible set, only orders it by an opportunity index. The execution order matches the layer numbering — gates run first, then the surviving candidates are ranked. The cascade ends there, at a ranked shortlist; choosing a single cargo from that shortlist is a separate, explicitly human step (§6).

**Data sources by layer**:

| Layer | Role | Data source |
|---|---|---|
| L1 | gate | UniProt SwissProt human reviewed (subcellular localization, sequence length, signal peptide, post-translational modification annotations) |
| L2 | gate | Open Targets Platform v26.03 (disease association scores) + NHGRI-EBI GWAS Catalog (genome-wide-significant hits) + NCBI PubMed via E-utilities (literature counts; metabolic scope only) |
| L3 | gate | UniProt SwissProt `protein_class` annotation (signaling-class taxonomy) |
| L4 | gate | Hand-curated 4-target list from the public clinical-development record (CETP, CNR1, HTR2C, DGAT1) |
| L5 | gate | **Data-driven**: OmniPath ligand-receptor edges (cognate receptor) + Human Protein Atlas `proteinatlas.tsv` (secretome location, tissue specificity) + Allen Mouse Brain ISH (circumventricular-organ localization of brain-restricted receptors). One citable constant: the CVO structure list (Gross & Weindl 1987). Snapshot at `data/snapshots_real/translational_cargo_suitability.tsv`, built by `data/etl/etl_translational_suitability.py` |
| L6 | rank | ChEMBL REST API queried by MeSH indication (compound-level `max_phase`) augmented with ChEMBL molecule-endpoint `withdrawn_flag` overlay; evidence numerator reuses L2's OT + GWAS + PubMed |

### Layer 1 — Modality compatibility

This layer asks: *can our delivery platform actually produce this protein in functional form?* We require:

- The protein must be **secreted** (so that cells producing it locally can release it into circulation).
- It must be composed entirely of the **20 standard amino acids** (so that ribosomes can synthesize it).
- It must **not require post-translational chemical modifications** (no chemical lipidation, no PEGylation).
- Its **open reading frame must fit within ~4500 base pairs** (the saRNA payload limit after accounting for the replicase machinery).
- It must have an **intrinsic plasma half-life of at least about an hour** (so that continuous expression can sustain therapeutic concentration).

These criteria are evaluated against the UniProt SwissProt database, which provides curated annotations for each human protein's subcellular localization, sequence length, signal peptide, and post-translational modifications.

**Data source**: UniProt SwissProt human reviewed release 2026_03 (one row per gene at `data/snapshots_real/uniprot_protein_classes.tsv`, 19,327 reviewed entries).

**Layer 1 result**: approximately **1,921** secreted human proteins pass.

### Layer 2 — Disease evidence

A modality-compatible protein is not worth pursuing if there is no evidence connecting it to the disease. This layer requires *at least one* of the following:

- An Open Targets Platform association score above a low threshold (≥ 0.05) for the indication(s) in scope. Open Targets aggregates 20+ independent evidence sources, so a non-zero score implies multi-source support.
- At least one genome-wide-significant GWAS hit (p < 5×10⁻⁸) in the NHGRI-EBI GWAS Catalog for a trait in scope.
- (In broad-metabolic scope only:) a substantial body of indexed PubMed literature (≥ 50 publications) connecting the gene to metabolic context.

**Layer 2 is indication-parameterized.** The cascade takes an `--indication` flag that sets the disease/trait scope, and the same flag also controls the L6 opportunity scoring (so the gate and the ranker stay consistent). The supported scopes are:

| Scope | OT diseases | GWAS traits | PubMed |
|---|---|---|---|
| `metabolic` (default) | obesity + T2D + NAFLD + MASH | any metabolic | used (≥50 threshold) |
| `obesity` | obesity | BMI | not used (our PubMed counts are metabolic-aggregated, not obesity-specific) |
| `t2d` | type 2 diabetes | T2D / fasting glucose / HbA1c | not used |
| `mash` | NAFLD + MASH | MASH / liver fat fraction / ALT | not used |

**Data sources**:
- Open Targets Platform v26.03 disease-anchored associations (`data/snapshots_real/opentargets_metabolic_associations.tsv`, 28,578 rows / 13,141 genes across 4 disease terms).
- NHGRI-EBI GWAS Catalog full dump retrieved 2026-06, filtered to 10 metabolic traits (`data/snapshots_real/gwas_catalog_metabolic_loci.tsv`, 36,035 rows / 9,044 genes).
- NCBI PubMed counts via E-utilities `esearch` with an `api_key` (`data/snapshots_real/literature_metabolic_genes.tsv`, 1,918 genes — the L1-pass subset). Metabolic-scope only.

**Layer 2 result depends on scope**: `metabolic` retains **852** candidates from L1's 1,921; `obesity` retains **426**; `t2d` retains **460**; `mash` retains **277**. The metabolic scope serves as the cascade's reusable backbone (one cascade artifact that future T2D-first or MASH-first papers can specialize); per-indication scopes give the project-specific shortlist directly.

### Layer 3 — Druggability

A target with strong disease evidence is still useless if it cannot be acted on pharmacologically. For a saRNA-delivered secreted protein cargo, the relevant druggability question is more specific than "is there any precedent": it is whether the protein acts as a *dose-titratable signaling molecule*. We therefore restrict Layer 3 to five secreted protein classes whose pharmacology is established as receptor-binding signaling rather than enzymatic, structural, transport, or acute-phase function:

- `secreted_hormone` (insulin, leptin-class endocrine signaling)
- `secreted_growth_factor` (FGF21, GDF15, BDNF-class paracrine/endocrine signaling)
- `secreted_cytokine` (immune/inflammatory signaling)
- `secreted_peptide` (short-peptide signaling)
- `secreted_neuropeptide` (CNS signaling)

Excluded at this layer are secreted enzymes (catalytic, requiring functional enzymatic activity to dose), secreted transport proteins (apolipoproteins and lipid carriers, whose pharmacology is rebalancing transport rather than signaling), secreted acute-phase proteins (CRP-family inflammatory markers, biomarkers rather than drug targets), and secreted proteases (proteolytic, complex feedback regulation).

This is a deliberate narrowing relative to a naïve "any secreted protein" druggability test. It reflects the modality's strength: saRNA-encoded local production delivers a *signaling molecule* into circulation; it does not deliver enzymatic activity or rebuild a lipid-transport pathway.

**Data source**: UniProt SwissProt `protein_class` annotation, parsed from the same SwissProt release used by Layer 1.

**Layer 3 result**: **239** candidates retained (filtered from 852, removing 613 mostly-enzyme and transport-protein candidates).

### Layer 4 — Safety baseline (confirmatory audit)

We compile a list of historically failed metabolic-disease drug targets (CETP, cannabinoid receptor 1, 5-HT2C receptor, DGAT1) and verify that no candidate on the shortlist matches it. These four targets have well-documented clinical failures — torcetrapib/evacetrapib/anacetrapib cardiovascular liability, rimonabant psychiatric adverse events leading to withdrawal, lorcaserin cardiovascular and oncologic signal leading to withdrawal, multiple Phase 2 DGAT1 failures.

In our cascade this layer is structurally vacuous: it excludes **zero** candidates, because all four historical failures are non-secreted GPCRs (CNR1, HTR2C) or non-secreted enzymes (DGAT1) that are already excluded by Layer 1's secretion requirement, and the one that *is* secreted (CETP, a lipid transport protein) is already excluded by Layer 3's restriction to direct signaling protein classes.

The vacuity is itself a finding worth recording. The chemistries that produced most historical metabolic clinical failures — small-molecule GPCR ligands and small-molecule enzyme inhibitors — are precisely the modalities the saRNA platform cannot deliver in the first place. The platform's structural constraint inherently routes us away from the most well-trodden failure paths.

**Data source**: Hand-curated 4-target list from the public clinical-development record (FDA/EMA action histories, primary trial publications), written out as `L4_KNOWN_FAILURES` in `cascade.py` with per-gene citation comments.

**Layer 4 result**: **239** candidates retained (0 excluded by audit; 0 excluded by audit *because* L1+L3 already covered all four historical failures).

### Layer 5 — Translational cargo suitability (data-driven)

Layer 1 only checks *structural* modality compatibility (secreted + ORF size). It does not check whether the protein actually works as a **systemically-delivered endocrine drug**: a saRNA-encoded protein is made locally, dumped into the bloodstream, and must then act on a target reachable from the blood. Layer 5 enforces that, and — unlike the expert layer that follows — it is built entirely from public data plus one citable anatomical constant. A candidate passes only if **all four** of the following hold:

- **C1a — secreted into blood (endocrine, not local).** The ligand must be a circulating endocrine signal, not an autocrine/paracrine factor that acts only on its neighbours. *Data*: Human Protein Atlas `Secretome location` = "Secreted to blood".
- **C1b — cognate receptor reachable from the blood.** Either the receptor is expressed in a peripheral tissue (HPA tissue expression), *or* — for a receptor confined to the brain — it sits in a **circumventricular organ** (area postrema, NTS, median eminence, subfornical organ, OVLT), the small brain regions whose capillaries lack a blood-brain barrier. This second branch is what correctly admits GFRAL: it is below the detection limit of bulk RNA atlases, so we use **Allen Mouse Brain ISH**, which localizes it to the area postrema / nucleus of the solitary tract (expression energy ~30–60× higher there than in behind-the-barrier hypothalamus). The list of which structures count as circumventricular is the one hand-entered constant (Gross & Weindl 1987).
- **C2i — a well-characterized cognate receptor exists.** *Data*: the ligand has a curated receptor edge in OmniPath (which aggregates Guide to PHARMACOLOGY, connectomeDB2020, CellTalkDB, and others). Where a ligand maps to several receptors, we take the one with the most curated sources — e.g. GDF15 → GFRAL (6 sources) over the legacy GDF15 → TGFBR2 (1 source).
- **C2ii — the receptor is anatomically restricted.** A receptor expressed all over the body means a systemically-dosed ligand would act everywhere, which is exactly the chronic-exposure liability we want to avoid. *Data*: HPA `RNA tissue specificity` ∈ {tissue enriched, group enriched}. The broader "tissue enhanced" and "low tissue specificity" categories — which by HPA's own definition mean expression spread across many tissues — do **not** count as restricted. This is the threshold that removes the broadly-acting growth-factor and cytokine receptors (e.g. BDNF's NTRK2, NRG1's ERBB3) while retaining the truly focused ones.

Only **2** of the candidate receptors are below HPA bulk detection or otherwise brain-restricted enough to require the Allen step (GFRAL and PROKR2); of those, only GFRAL is enriched in a circumventricular organ, so only GFRAL is rescued. Everything else is decided directly from HPA + OmniPath.

This is a deliberately conservative gate, and it is *not* a clean "obesity-relevant" filter — some surviving receptors are restricted and blood-accessible yet mediate central or reproductive effects (the receptor-location data cannot encode *which* site produces the weight effect). It should be read as "is this a deliverable systemic-endocrine cargo at all," with disease relevance still carried by L2 and the final ranking by L6.

**A note on threshold sensitivity (important).** The C2ii cut is load-bearing. With the strict definition used here (enriched + group enriched), the obesity shortlist is **17** candidates and GDF15 ranks **#3**. If "tissue enhanced" is also counted as restricted, the shortlist balloons to **65** (BDNF, IL34, CALCB, HBEGF re-enter) and GDF15 falls to **#10**. We use the strict cut because it matches HPA's own category semantics — "enhanced" means broadly expressed — not because it favours GDF15; but the dependence is real and stated.

**Data sources**: OmniPath ligand-receptor interactions (REST API); Human Protein Atlas `proteinatlas.tsv` (secretome location + tissue specificity); Allen Mouse Brain Atlas ISH (`api.brain-map.org`, expression energy by structure). Computed into `data/snapshots_real/translational_cargo_suitability.tsv` (one row per candidate, all four flags + the Allen evidence values) by `data/etl/etl_translational_suitability.py`. The cascade reads the snapshot; only the CVO structure list is hand-entered.

**Layer 5 result**: **29** retained in the metabolic scope (210-candidate snapshot universe; obesity scope **17**, t2d **19**, mash **9**). This is the cascade's sharpest narrowing — it is where the higher-evidence-but-undeliverable candidates (BDNF, NRG1) drop out, leaving GDF15 in the top tier of the deliverable set (it ranks #3 of the 17 obesity-scoped survivors; see §5). Note that the deliverability *failure modes* that an earlier revision of this document enforced as a separate hand-curated "expert" gate (short native half-life, prohormone processing, obligate heterodimer, secretome misannotation) are **no longer a cascade layer**; that gate was target-aware and, for the half-life mode, in tension with GDF15's own hours-scale half-life, so its reasoning has been moved into the human-synthesis selection step (§6). With the data-driven L5 in place, most of those hand-curated exclusions are anyway redundant — the proteins are already removed upstream because their receptors are not blood-accessible/restricted or they are not secreted to blood.

### Layer 6 — Opportunity ranking (the final step)

Layers 1-5 are all boolean gates: a candidate either passes or it does not. Layer 6 is qualitatively different — it does not filter, it ranks the admissible set. We compute an **opportunity index** for each surviving candidate:

```
opportunity = evidence_strength / (1 + max_clinical_phase)
```

The numerator captures aggregate biological support (OT scores summed across the indication's diseases, GWAS hit count over the indication's traits, log-scaled literature density where applicable). The denominator penalizes targets that are already heavily invested in industrially — a target with a Phase 3 program is much less of an *opportunity* for academic discovery than a target with equally strong evidence and no Phase 2 program. This deliberately steers the ranking toward **underdeveloped high-evidence opportunities** rather than rediscovering targets that pharma is already actively developing.

Layer 6 is *indication-scoped in lockstep with Layer 2*: when the cascade is run with `--indication obesity`, both the L2 evidence gate and the L6 opportunity ranker restrict to obesity evidence only. This keeps gate and ranker consistent and prevents a candidate from being "boosted" by evidence in indications it was not gated on.

The honest scope of what Layer 6 produces is *a ranking, not a discovery*. The opportunity formula uses hand-set weights (GWAS bonus of 0.5 per hit capped at 10, PubMed log-density coefficient of 0.1) that have not been calibrated against any ground-truth outcome dataset. Rankings near the top should be read as a *tier* rather than a precise ordering: candidates near the top of the obesity-scoped shortlist should all be regarded as defensible cargos, with the choice among them determined by additional information beyond the cascade.

**Two phase-penalty corrections** are applied to make the L6 denominator reflect *crowded active development* rather than just "highest clinical phase ever reached":

1. **Indication-scoped phase**: ChEMBL `max_phase` is recorded per (compound, indication). The original cascade collapsed across all 9 queried indication tags (obesity, T2D, MASH, NAFLD, cardiovascular, heart failure, dyslipidemia, cachexia, muscle wasting) by taking the gene-wise maximum. This wrongly penalized targets whose only clinical advancement was in an off-direction indication — e.g. TNF Phase 3 trials are for *cachexia* (excess weight loss in cancer), the opposite of obesity, yet TNF's obesity-scoped opportunity was being divided by `(1 + 3) = 4`. The corrected logic counts a ChEMBL row only if its indication matches the cascade's `--indication` scope. Under `--indication obesity`, TNF / IL6 / IL1A / IL1B all revert to effective phase 0 (their Phase 2-3 advancement was for cachexia or T2D, not obesity); only MSTN retains its obesity-row Phase 2 (bimagrumab, anti-ActRII), which is genuinely an active obesity competitor.

2. **Withdrawn-flag overlay**: A compound's `max_phase=4` (approved/marketed) flag does not distinguish currently-marketed drugs from drugs that were approved then later withdrawn for safety. We re-queried ChEMBL's molecule endpoint for `withdrawn_flag` across all 389 compounds in our subset with `max_phase >= 2`. Of 17 withdrawn compounds found, 0 affect a cascade-admissible candidate — every withdrawn compound's primary target is a non-secreted GPCR, ion channel, transporter, or nuclear receptor that Layer 1 (secretion requirement) or Layer 3 (signaling-class requirement) already excludes. This is another instance of the same modality-driven finding noted at Layer 4: the historical metabolic clinical failures are concentrated in protein classes our delivery platform cannot address, so they cannot pollute our shortlist by either route.

**Data sources**:
- ChEMBL via REST API queried by MeSH indication ID across 9 metabolic-relevant indications (`data/raw_dumps/chembl/chembl_metabolic_api_subset.tsv`, 1,972 compound-indication rows / 434 unique genes).
- ChEMBL molecule-endpoint `withdrawn_flag` overlay batch-fetched for the 389 compounds with `max_phase >= 2` (`data/snapshots_real/chembl_withdrawn_status.tsv`, 17 carry `withdrawn_flag=True`).
- The evidence numerator reuses Layer 2's OT + GWAS + PubMed snapshots; weights are hand-set (see opportunity formula above).

### Implementation notes

All six layers are implemented in target-blind code — no gene symbol of interest is hard-coded as a filter or as a special case. Layer 5 reads a data-derived snapshot; its only hand-entered input is the circumventricular-organ structure list, which is anatomical, not target-specific. Layer 6 is a formula over public evidence/phase data. The cascade therefore contains no per-gene curation; the one place human judgment enters explicitly is the §6 selection step, which is presented as such. The full implementation has been run against current Open Targets (version 26.03), GWAS Catalog (latest), ChEMBL (via REST API), UniProt (SwissProt human reviewed), PubMed (via NCBI E-utilities for 1,918 modality-compatible candidate genes), Human Protein Atlas, OmniPath, and the Allen Mouse Brain Atlas.

---

## 5. The obesity-scoped shortlist

For this paper's primary indication of chronic weight management, we run the cascade with `--indication obesity`, which restricts Layer 2's disease scope to the obesity term and the BMI GWAS trait, and restricts Layer 6's opportunity scoring to the same. This is the indication-specialized instance of the same six-layer cascade described in §4 — not a separate post-cascade narrowing step.

**Obesity-scoped shortlist**: **17** candidates. Cascade chain: 19,327 → L1=1,921 → L2=426 → L3=128 → L4=128 → L5=17, then L6 ranks those 17. The cascade stops here; selecting one cargo from this ranked list is the human step in §6.

### The obesity-scoped L6 ranking (all 17)

| Rank | Gene | Opp. score | OT obesity | BMI GWAS | Max phase | Protein class |
|---:|---|---:|---:|---:|---:|---|
|  1  | CCK       | 2.33 | 0.33 |  4 | 0 | secreted_hormone |
|  2  | HMGB1     | 1.35 | 0.35 |  2 | 0 | secreted_peptide |
| **3** | **→ GDF15 ←** | **0.62** | **0.12** | **1** | **0** | **secreted_hormone** |
|  4  | PNOC      | 0.53 | 0.03 |  1 | 0 | secreted_neuropeptide |
|  5  | GNRH2     | 0.52 | 0.02 |  1 | 0 | secreted_hormone |
|  6  | IL17B     | 0.50 | 0.00 |  1 | 0 | secreted_cytokine |
|  7  | GHRL      | 0.27 | 0.27 |  0 | 0 | secreted_hormone |
|  8  | FSHB      | 0.19 | 0.19 |  0 | 0 | secreted_hormone |
|  9  | CRH       | 0.16 | 0.16 |  0 | 0 | secreted_hormone |
| 10  | OXT       | 0.11 | 0.11 |  0 | 0 | secreted_hormone |
| 11  | IL33      | 0.10 | 0.10 |  0 | 0 | secreted_cytokine |
| 12  | IL22      | 0.08 | 0.08 |  0 | 0 | secreted_cytokine |
| 13  | PTN       | 0.07 | 0.07 |  0 | 0 | secreted_growth_factor |
| 14  | RETN      | 0.07 | 0.07 |  0 | 0 | secreted_hormone |
| 15  | TNFSF13B  | 0.06 | 0.06 |  0 | 0 | secreted_cytokine |
| 16  | IL25      | 0.06 | 0.06 |  0 | 0 | secreted_cytokine |
| 17  | GNRH1     | 0.06 | 0.06 |  0 | 0 | secreted_hormone |

*(Reproducible via `python3 cascade.py --indication obesity`. Per-gene cascade trace via `--gene <SYMBOL>`.)*

By obesity-scoped opportunity score, GDF15 ranks **#3 of 17**. We are deliberate about what the cascade does and does not establish here:

- **What L5 already achieved.** The candidates that dominated the pre-L5 cascade — BDNF (5.61), NRG1 (3.70), BMP8A, IL34, CALCB, all with strong BMI GWAS support — are *gone*, removed by the data-driven L5 because their receptors are broadly expressed (NRG1's ERBB3, "low tissue specificity") or behind the blood-brain barrier (BDNF's hypothalamic TrkB). Those are legitimate removals: those proteins genuinely cannot be delivered as systemic-endocrine cargos by this platform. GDF15 survives L5 only because Allen Mouse Brain ISH localizes its otherwise-undetectable receptor GFRAL to the area postrema (a blood-accessible circumventricular organ). So L5 lifts GDF15 from mid-pack into the deliverable top tier.
- **What the cascade does *not* do is crown GDF15.** Two candidates outrank it: **CCK** (#1, opp 2.33) and **HMGB1** (#2, 1.35). The cascade is honest about this — it ends at a ranked shortlist, not a winner. Choosing GDF15 over the two above it (and over the rest) is the explicit human-synthesis step in §6, which is where the qualitative deliverability and evidence judgments live.
- **The survivor set is biologically mixed.** Below GDF15 are central neuropeptides (PNOC), reproductive hormones (GNRH1/2, FSHB), stress/neurohypophyseal hormones (CRH, OXT), and immune cytokines (IL17B, IL33, IL22, IL25, TNFSF13B) — several of which pass L5 only because their receptors happen to be restricted and blood-accessible, even though their primary physiology is not anti-obesity. The receptor-location data cannot encode *which* site produces the weight effect; L2 disease evidence and the §6 synthesis carry that.
- **The shortlist size is threshold-sensitive** (see §4 Layer 5): a looser receptor-specificity cut would readmit BDNF/IL34/CALCB and enlarge the list to ~52. We use the stricter, HPA-definition-consistent cut.

Two categories of well-known metabolic hormones are absent relative to a naïve cascade output: the gut/pancreatic peptide hormones (PYY, GIP, GCG/GLP-1, insulin) and the hypothalamic prohormones (POMC, NPY). They are removed by Layer 5 (receptor not restricted/blood-accessible, or ligand not secreted-to-blood). CCK and ghrelin (GHRL) *do* survive the data cascade — they have restricted, blood-accessible receptors — which is exactly why §6 must address them by hand: they fail not on the data criteria but on native-protein-sufficiency grounds discussed there.

---

## 6. Why GDF15 was chosen as the first cargo

The cascade ends at the ranked shortlist; it does not pick a cargo. GDF15 sits at **#3 of 17**. Selecting it is a human judgment with two parts — passing over the two candidates ranked above it, and the positive case for GDF15 — none of which the structured databases capture. This is also where the deliverability judgments that an earlier revision ran as a mechanical "expert gate" now live, applied with the nuance a hard threshold could not.

### Passing over the two higher-ranked candidates

**CCK (#1, opp 2.33)** has strong obesity genetics and a restricted, blood-accessible receptor (CCK1R on vagal afferents), so it clears every data gate. It fails on **native-protein sufficiency**. Cholecystokinin's circulating half-life is on the order of a minute, its satiety effect is acute and prone to rapid tachyphylaxis, and there is no evidence that a sustained elevation of the *unmodified* peptide produces durable weight loss — every clinical CCK-axis program uses an engineered analog. This is the consideration an earlier draft enforced as a mechanical "half-life gate." We removed that gate on purpose: as a hard threshold it is both biophysically weak (continuous saRNA expression reaches steady state regardless of half-life) and internally inconsistent — GDF15's own native half-life is only a few hours and clinical GDF15 agonists are themselves half-life-extended Fc-fusions. The honest discriminator is not a half-life number but whether there is evidence the *native, sustained* protein is therapeutically active. That evidence exists for GDF15 (next section) and not for CCK.

**HMGB1 (#2, opp 1.35)** is an annotation artifact. Because it is detected extracellularly it is labelled "secreted to blood" and clears the L5 endocrine test, but its real biology is a nuclear chromatin protein released only as a damage-associated alarmin — not an endocrine ligand one would agonize for weight loss. The data cannot self-correct this misclassification; we exclude it on that basis.

### The positive case for GDF15

**A human natural experiment — the decisive signal.** In 2024 a multi-institution *Nature* study (Fejzo et al.) established that the severe nausea and weight loss of hyperemesis gravidarum is caused by elevated endogenous GDF15 acting on its hindbrain receptor. This is an unintentional human dose-response study: when a woman's *native, unmodified* GDF15 rises in early pregnancy, she experiences sustained anorexia and significant weight loss — dramatic, documented across thousands of patients, unambiguous on causal direction. No other shortlist candidate has human in-vivo evidence of this strength, and it is exactly the native-protein-sufficiency proof that CCK lacks.

**A restricted, well-characterized receptor.** GFRAL was identified in 2017 by three groups at once and is expressed essentially only in the area postrema and nucleus tractus solitarius. Two consequences: systemic GDF15 acts only through this restricted circuit (limiting off-target effects), and the expected adverse effect is predictable — nausea, since the area postrema is the brain's nausea center (the same endpoint as GLP-1, via a different pathway). That receptor restriction is also what let GDF15 clear L5 where broader-receptor competitors (NRG1/ERBB3, BDNF/TrkB) did not.

**Industry derisking.** Pfizer (via NGM Biopharmaceuticals) took NGM120, a GFRAL *antagonist*, into Phase 1 for cancer cachexia. We want the opposite — a GFRAL *agonist* for weight loss — but the antagonist program shows the axis can be drugged at acceptable human exposures and that a GFRAL-biologic supply chain exists. This signal is invisible to our cascade (the ChEMBL query is metabolic-indication-scoped; a cachexia trial is not indexed), so we add it explicitly.

---

## 7. What we are and are not claiming

Because we are taking pains to frame this honestly, it is worth stating explicitly what this rationale does *not* claim:

- **We are not claiming GDF15 is mechanistically superior to GLP-1 for weight loss.** The semaglutide-tirzepatide-retatrutide trajectory has set a very high efficacy bar. GDF15-pathway agonists have not yet demonstrated comparable Phase 3 outcomes in obesity.
- **We are not claiming GDF15 will have fewer side effects than GLP-1.** Both pathways converge on the same anatomical nausea center. The side effect profile may turn out to be similar.
- **We are not claiming GDF15 is the only worthwhile cargo for our platform.** High-evidence proteins like BDNF and NRG1 are biologically interesting but were screened out by Layer 5 as undeliverable by *this* modality (BBB-restricted or broadly-expressed receptors); they could be revisited if the platform adds blood-brain-barrier transit or multi-cistronic constructs. Among deliverable candidates, the cascade's other admissible cargos and the broader-scope shortlists (t2d, mash) offer further targets to validate.
- **We are not claiming the AI pipeline "discovered" GDF15.** The data cascade ranks GDF15 **#3 of 17** deliverable obesity candidates — it does *not* place it first (CCK and HMGB1 score higher). GDF15 was selected from that shortlist by the human synthesis in §6: passing over CCK (no native-sustained-activity evidence) and HMGB1 (a misannotated damage signal), and weighing three cascade-external derisking signals (hyperemesis gravidarum, the 2017 GFRAL characterization, NGM120). That is a transparent human decision, not an algorithmic output — and it further depends on the Allen-ISH rescue of the otherwise-undetectable GFRAL receptor and on the L5 receptor-specificity threshold (a looser cut would enlarge the shortlist to ~52).

What we *are* claiming is methodological: that the modality-constrained constraint cascade is a systematic, auditable framework for narrowing a high-dimensional target selection problem down to a defensible, deliverable shortlist, and that GDF15 is the best-supported choice from that shortlist for principled, transparently-stated reasons.

---

## 8. What comes next

The cascade and its rationale are inputs to a translational research program, not the program itself. The actual scientific tests are the wet-lab experiments that determine whether the saRNA-microneedle-GDF15 combination produces durable, well-tolerated body composition improvement in mouse models — and eventually in humans.

The immediate next steps are:

1. **Complete the cargo characterization in mouse models**: full pharmacokinetics of GDF15 expression after sublingual dosing; weight loss kinetics; body composition (DXA or NMR) to distinguish fat-mass from lean-mass change; glycemic control (oral glucose tolerance); hepatic steatosis improvement (histology and magnetic resonance spectroscopy); behavioral and tissue-level safety assessment.
2. **Comparator studies**: head-to-head comparison with semaglutide and (where feasible) with a GLP-1-Fc fusion delivered by the same saRNA-microneedle platform, to separate the contribution of the cargo from the contribution of the delivery modality.
3. **Platform expansion**: applying the same cascade and the same delivery platform to a second cargo. Two distinct expansion routes exist. (i) *Within the deliverable shortlist* — validate the platform with another L5-admissible cargo to convert the project from a single-target study into a delivery-platform study. (ii) *By extending the modality* — proteins like BDNF (the former top-cascade candidate, removed by L5 because its weight-relevant TrkB signaling is behind the blood-brain barrier) and NRG1 (removed because ERBB3 is broadly expressed) are high-evidence but require the platform to first solve BBB transit or restricted targeting; they are explicitly *not* deliverable today. The well-known appetite-regulating gut peptides are likewise unsuitable: PYY and GIP are removed by Layer 5, while CCK and ghrelin survive the data cascade but are passed over in §6 on native-protein-sufficiency grounds (minutes-scale half-life, no evidence the unmodified peptide works sustained).

4. **Indication expansion**: re-running the same cascade with `--indication t2d` (17 candidates) or `--indication mash` (7 candidates) to identify saRNA-deliverable cargos for type 2 diabetes or metabolic-associated steatohepatitis. The cascade architecture is indication-parameterized precisely so that future projects can specialize it without re-deriving the methodology.
4. **Methodology release**: the constraint cascade itself, with full target-blind implementation and provenance, will be released so that other groups can apply it to other modalities (mRNA, AAV, antibody-drug conjugate) and other indications.

---

## 9. Summary in one paragraph

The current standard of care for chronic weight management (the GLP-1 receptor agonist class) has transformed treatment but leaves substantial unmet need — gastrointestinal intolerance, lean mass loss, rebound on discontinuation, β-cell dependency, injection administration, cost, and non-response. Our laboratory has developed a delivery platform — self-amplifying RNA encoded into a sublingual microneedle patch — that addresses several of these limitations but is fundamentally incompatible with the chemistry of the existing GLP-1 drugs. The platform's question is therefore not "what beats semaglutide" but "what natively-deliverable secreted protein addresses an unmet metabolic need that GLP-1 cannot reach." We built a target-blind, modality-constrained AI cascade that compresses the ~20,000 reviewed human protein-coding genes through five sequential boolean gates plus a final opportunity ranker; specialized to obesity (the cascade's L2 evidence gate and L6 opportunity ranker take an indication parameter), it produces a 17-candidate obesity-scoped shortlist of signaling secreted proteins that are both disease-linked and genuinely deliverable by saRNA. A data-driven Layer 5 (OmniPath receptor mapping + Human Protein Atlas tissue/secretome data + Allen Mouse Brain ISH) enforces systemic-endocrine deliverability — removing higher-evidence but undeliverable proteins such as BDNF and NRG1, and admitting GDF15 only because Allen ISH rescues its otherwise-undetectable GFRAL receptor. The cascade ranks GDF15 **#3 of 17**; it does not crown it. The final selection is a transparent human-synthesis step (§6): from the shortlist we pass over the two higher-ranked candidates for clear reasons (CCK — no evidence the native, sustained peptide works; HMGB1 — a misannotated damage signal) and choose GDF15 on three independently verifiable derisking signals — the hyperemesis gravidarum natural experiment (direct proof the native protein drives weight loss), the 2017 characterization of the restricted GFRAL receptor, and Phase 1 industrial validation of the GFRAL axis via NGM120. The wet-lab mouse data is the actual scientific test; the cascade plus this human synthesis is the justification for choosing GDF15 to test first.
