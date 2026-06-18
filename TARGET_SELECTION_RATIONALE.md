# Why We Chose GDF15

*An accessible explanation of our target selection rationale for the saRNA-sublingual delivery platform.*

**Lab**: Cheng Lab, Columbia University, Department of Biomedical Engineering / Department of Medicine.
**Project**: Self-amplifying RNA + sublingual microneedle delivery of a secreted endocrine factor for obesity, type 2 diabetes, and metabolic-associated steatohepatitis (MASH).

**Document version**: 2026-06-18 (revised with Layer 5 expert deliverability curation, indication-parameterized L2/L6, and gate-then-rank layer ordering). All numbers below derive from the cascade applied to fully real public data (Open Targets 26.03, NHGRI-EBI GWAS Catalog latest, UniProt SwissProt human reviewed, ChEMBL via REST API by indication, PubMed E-utilities literature counts) plus a hand-curated 23-gene exclusion list for deliverability failure modes that public databases do not cover.

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

We assembled what we call a **target cascade**. Starting from the full set of ~20,000 reviewed human protein-coding genes, the pipeline applies six sequential layers. The first five (L1 through L5) are **boolean gates**: a candidate either passes each filter or it does not. The sixth (L6) is the **ranker**: it does not filter the admissible set, only orders it by an opportunity index. The execution order matches the layer numbering — gates run first, then the surviving candidates are ranked.

### Layer 1 — Modality compatibility

This layer asks: *can our delivery platform actually produce this protein in functional form?* We require:

- The protein must be **secreted** (so that cells producing it locally can release it into circulation).
- It must be composed entirely of the **20 standard amino acids** (so that ribosomes can synthesize it).
- It must **not require post-translational chemical modifications** (no chemical lipidation, no PEGylation).
- Its **open reading frame must fit within ~4500 base pairs** (the saRNA payload limit after accounting for the replicase machinery).
- It must have an **intrinsic plasma half-life of at least about an hour** (so that continuous expression can sustain therapeutic concentration).

These criteria are evaluated against the UniProt SwissProt database, which provides curated annotations for each human protein's subcellular localization, sequence length, signal peptide, and post-translational modifications.

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

**Layer 3 result**: **239** candidates retained (filtered from 852, removing 613 mostly-enzyme and transport-protein candidates).

### Layer 4 — Safety baseline (confirmatory audit)

We compile a list of historically failed metabolic-disease drug targets (CETP, cannabinoid receptor 1, 5-HT2C receptor, DGAT1) and verify that no candidate on the shortlist matches it. These four targets have well-documented clinical failures — torcetrapib/evacetrapib/anacetrapib cardiovascular liability, rimonabant psychiatric adverse events leading to withdrawal, lorcaserin cardiovascular and oncologic signal leading to withdrawal, multiple Phase 2 DGAT1 failures.

In our cascade this layer is structurally vacuous: it excludes **zero** candidates, because all four historical failures are non-secreted GPCRs (CNR1, HTR2C) or non-secreted enzymes (DGAT1) that are already excluded by Layer 1's secretion requirement, and the one that *is* secreted (CETP, a lipid transport protein) is already excluded by Layer 3's restriction to direct signaling protein classes.

The vacuity is itself a finding worth recording. The chemistries that produced most historical metabolic clinical failures — small-molecule GPCR ligands and small-molecule enzyme inhibitors — are precisely the modalities the saRNA platform cannot deliver in the first place. The platform's structural constraint inherently routes us away from the most well-trodden failure paths.

**Layer 4 result**: **239** candidates retained (0 excluded by audit; 0 excluded by audit *because* L1+L3 already covered all four historical failures).

### Layer 5 — Expert deliverability curation

Layer 1's modality filter is a coarse, structural check: secreted plus an ORF that fits the saRNA payload. It is not sufficient on its own. There are at least four failure modes that make a structurally-modality-compatible protein actually un-deliverable in practice, none of which are recorded in any of our five public databases. We add Layer 5 as a manual, audit-trailed expert curation step. Each excluded gene is annotated with one of four failure-mode tags.

**(a) Native plasma half-life too short for saRNA-sustained therapy.** saRNA delivers steady-state expression of a protein over days. If the protein's intrinsic plasma half-life is on the order of minutes, the steady-state circulating concentration cannot reach the therapeutic window regardless of the expression rate. Every existing clinical-stage drug against these targets uses a chemically-modified analog — Fc-fusion, lipidation, or PEGylation — that the saRNA modality cannot encode. The genes excluded under this mode are **FGF21** (native human plasma t½ ~30 min; all clinical programs use Fc-fusion), **CCK**, **PYY**, **GIP**, **GCG** (the glucagon/GLP-1 locus), and **GHRL** (ghrelin) — every native incretin or gut-peptide hormone with native t½ in the minutes range. This is the same wall that prevents native GLP-1 from being a viable saRNA cargo.

**(b) Requires tissue-specific PC1/2 cleavage to produce the active peptide.** Many neuroendocrine peptides are encoded as inactive prohormones that are cleaved by prohormone convertases PC1/PC2 (PCSK1, PCSK2). These convertases are expressed only in specialized neuroendocrine cells. Mucosal cells producing a saRNA-encoded prohormone will release the uncleaved precursor into circulation, which is not biologically active. The genes excluded under this mode are **POMC** (would require cleavage to α-MSH, β-endorphin, ACTH), **PCSK1N** (proSAAS), **INS** (insulin requires β-cell-specific PC1/2), **IAPP** (amylin requires PC1/2 and C-terminal amidation), **GAST**, **NPY**, and **AGRP**.

**(c) Obligate heterodimer; single-ORF expression yields a non-functional product.** Some cytokines and growth factors are obligate two-subunit complexes that must be co-expressed in the same cell at matched stoichiometry. A single-ORF saRNA construct cannot produce both subunits. Multi-cistronic saRNA designs exist but are an open engineering problem outside the current platform scope. The genes excluded under this mode are the IL-12 family (**IL12B** = p40, **IL23A** = p19, **IL27** = p28, **EBI3**, which pair to form IL-12, IL-23, IL-27, and IL-35), and the inhibin βC and βE subunits (**INHBC**, **INHBE**), whose homodimeric activin-C/E forms have unclear or immature pharmacology.

**(d) Annotated as secreted-signaling by UniProt but actually not.** Database annotation pipelines sometimes flag a protein as "secreted" because it has been detected extracellularly, even though its primary biological role is not as an extracellular signaling ligand. Choosing such a protein as a drug-target cargo is biologically inappropriate. The genes excluded under this mode are **MAPT** (tau, which is primarily an intracellular microtubule-binding protein and the principal driver of Alzheimer-type neurodegeneration when extracellular), **HMGB1** (a nuclear chromatin protein released only as a damage-associated alarmin), and **LTBP3** (a structural scaffold for latent TGFβ rather than an active ligand).

This layer is explicitly a *human/expert annotation* layer, not a database-derived filter. Its scope (the specific genes excluded and the failure-mode tag attached to each) is fully written out in the cascade source code so that any candidate's exclusion can be audited and challenged. We treat this as a known limitation of the methodology: the four failure modes above would, in principle, be capturable from structured databases (UniProt half-life annotations, prohormone-processing databases, complex-portal heterodimer annotations) if the right curated sources existed at sufficient coverage. They presently do not.

**Layer 5 result** *(metabolic scope)*: **219** final admissible candidates (20 excluded from the L4 set of 239: 6 short-half-life, 6 prohormone-processing, 5 heterodimer-required, 3 misclassified-secreted). *(obesity scope: **112** final admissible; t2d: 121; mash: 83.)*

### Layer 6 — Opportunity ranking (the final step)

Layers 1-5 are all boolean gates: a candidate either passes or it does not. Layer 6 is qualitatively different — it does not filter, it ranks the admissible set. We compute an **opportunity index** for each surviving candidate:

```
opportunity = evidence_strength / (1 + max_clinical_phase)
```

The numerator captures aggregate biological support (OT scores summed across the indication's diseases, GWAS hit count over the indication's traits, log-scaled literature density where applicable). The denominator penalizes targets that are already heavily invested in industrially — a target with a Phase 3 program is much less of an *opportunity* for academic discovery than a target with equally strong evidence and no Phase 2 program. This deliberately steers the ranking toward **underdeveloped high-evidence opportunities** rather than rediscovering targets that pharma is already actively developing.

Layer 6 is *indication-scoped in lockstep with Layer 2*: when the cascade is run with `--indication obesity`, both the L2 evidence gate and the L6 opportunity ranker restrict to obesity evidence only. This keeps gate and ranker consistent and prevents a candidate from being "boosted" by evidence in indications it was not gated on.

The honest scope of what Layer 6 produces is *a ranking, not a discovery*. The opportunity formula uses hand-set weights (GWAS bonus of 0.5 per hit capped at 10, PubMed log-density coefficient of 0.1) that have not been calibrated against any ground-truth outcome dataset. Rankings near the top should be read as a *tier* rather than a precise ordering: candidates within the top decile of the obesity-scoped shortlist should all be regarded as defensible cargos, with the choice among them determined by additional information beyond the cascade.

**Two phase-penalty corrections** are applied to make the L6 denominator reflect *crowded active development* rather than just "highest clinical phase ever reached":

1. **Indication-scoped phase**: ChEMBL `max_phase` is recorded per (compound, indication). The original cascade collapsed across all 9 queried indication tags (obesity, T2D, MASH, NAFLD, cardiovascular, heart failure, dyslipidemia, cachexia, muscle wasting) by taking the gene-wise maximum. This wrongly penalized targets whose only clinical advancement was in an off-direction indication — e.g. TNF Phase 3 trials are for *cachexia* (excess weight loss in cancer), the opposite of obesity, yet TNF's obesity-scoped opportunity was being divided by `(1 + 3) = 4`. The corrected logic counts a ChEMBL row only if its indication matches the cascade's `--indication` scope. Under `--indication obesity`, TNF / IL6 / IL1A / IL1B all revert to effective phase 0 (their Phase 2-3 advancement was for cachexia or T2D, not obesity); only MSTN retains its obesity-row Phase 2 (bimagrumab, anti-ActRII), which is genuinely an active obesity competitor.

2. **Withdrawn-flag overlay**: A compound's `max_phase=4` (approved/marketed) flag does not distinguish currently-marketed drugs from drugs that were approved then later withdrawn for safety. We re-queried ChEMBL's molecule endpoint for `withdrawn_flag` across all 389 compounds in our subset with `max_phase >= 2`. Of 17 withdrawn compounds found, 0 affect a cascade-admissible candidate — every withdrawn compound's primary target is a non-secreted GPCR, ion channel, transporter, or nuclear receptor that Layer 1 (secretion requirement) or Layer 3 (signaling-class requirement) already excludes. This is another instance of the same modality-driven finding noted at Layer 4: the historical metabolic clinical failures are concentrated in protein classes our delivery platform cannot address, so they cannot pollute our shortlist by either route.

### Implementation notes

The first five cascade layers are implemented entirely in target-blind code — no gene symbol of interest is hard-coded as a filter or as a special case. Layer 6 is necessarily target-specific (it is a curated exclusion list), but each entry carries an explicit failure-mode tag in source code, and the inclusion/exclusion of any given gene can be traced. The full implementation has been run against current Open Targets (version 26.03), GWAS Catalog (latest), ChEMBL (via REST API), UniProt (SwissProt human reviewed), and PubMed (via NCBI E-utilities for 1,918 modality-compatible candidate genes).

---

## 5. The obesity-scoped shortlist

For this paper's primary indication of chronic weight management, we run the cascade with `--indication obesity`, which restricts Layer 2's disease scope to the obesity term and the BMI GWAS trait, and restricts Layer 4's opportunity scoring to the same. This is the indication-specialized instance of the same six-layer cascade described in §4 — not a separate post-cascade narrowing step.

**Obesity-scoped final shortlist**: **112** candidates. Cascade chain: 19,327 → L1=1,921 → L2=426 → L3=128 → L4=128 → L5=112, then L6 ranks those 112.

### Top 20 of the obesity-scoped L6 ranking

| Rank | Gene | Opp. score | OT obesity | BMI GWAS | Max phase | Protein class |
|---:|---|---:|---:|---:|---:|---|
|  1  | BDNF      | 5.61 | 0.61 | 12 | 0 | secreted_growth_factor |
|  2  | NRG1      | 3.70 | 0.20 |  7 | 0 | secreted_growth_factor |
|  3  | BMP8A     | 1.07 | 0.07 |  2 | 0 | secreted_growth_factor |
|  4  | IL34      | 1.01 | 0.01 |  2 | 0 | secreted_growth_factor |
|  5  | CALCB     | 1.00 | 0.00 |  2 | 0 | secreted_hormone |
|  6  | TAFA5     | 0.87 | 0.37 |  1 | 0 | secreted_cytokine |
|  7  | FGF5      | 0.86 | 0.36 |  1 | 0 | secreted_growth_factor |
|  8  | HBEGF     | 0.73 | 0.23 |  1 | 0 | secreted_growth_factor |
|  9  | ALKAL2    | 0.71 | 0.21 |  1 | 0 | secreted_cytokine |
| **10** | **→ GDF15 ←** | **0.62** | **0.12** | **1** | **0** | **secreted_hormone** |
| 11  | BMP7      | 0.56 | 0.06 |  1 | 0 | secreted_growth_factor |
| 12  | PNOC      | 0.53 | 0.03 |  1 | 0 | secreted_neuropeptide |
| 13  | GNRH2     | 0.52 | 0.02 |  1 | 0 | secreted_hormone |
| 14  | CCL28     | 0.51 | 0.01 |  1 | 0 | secreted_cytokine |
| 15  | MLN       | 0.51 | 0.01 |  1 | 0 | secreted_hormone |
| 16  | EFEMP1    | 0.51 | 0.01 |  1 | 0 | secreted_growth_factor |
| 17  | PDGFC     | 0.51 | 0.01 |  1 | 0 | secreted_growth_factor |
| 18  | IL17B     | 0.50 | 0.00 |  1 | 0 | secreted_cytokine |
| 19  | GDNF      | 0.35 | 0.35 |  0 | 0 | secreted_growth_factor |
| 20  | ADCYAP1   | 0.31 | 0.31 |  0 | 0 | secreted_hormone |

*(Reproducible via `python3 cascade.py --indication obesity`. Full 112-candidate ranking and per-gene cascade trace available in the same command output.)*

The top of this ranking is dominated by signaling growth factors with strong BMI GWAS support: BDNF (12 BMI-significant GWAS hits), NRG1 (7 BMI hits), BMP8A (a brown-fat thermogenesis regulator), interleukin-34, and calcitonin gene-related peptide β (CALCB). The middle tier (positions 6-20) consists mostly of signaling proteins with one BMI GWAS hit plus moderate Open Targets obesity scores: TAFA5, FGF5, HBEGF, ALKAL2, GDF15, BMP7, the prepronociceptin neuropeptide PNOC, MLN (motilin), and others. The remainder of the 112-candidate list contains additional well-known metabolic signaling proteins not visible in the top 20 — adiponectin (ADIPOQ), GDNF, neuregulin-4 (NRG4, a brown-adipose batokine), klotho (KL), interleukin-10, resistin (RETN), the irisin precursor FNDC5 — with progressively weaker obesity-specific evidence.

By obesity-scoped opportunity score, GDF15 ranks **#10 of 112**. It places in the top decile of the obesity-scoped shortlist. It is not the single mathematically highest-scoring target; we do not claim it is. The top of the opportunity-ranked list (BDNF, NRG1, BMP8A, IL34, CALCB) are also defensible cargos and represent natural candidates for subsequent validation studies of the same delivery platform.

Two categories of well-known metabolic hormones are conspicuously absent from this shortlist relative to a naïve cascade output: the gut/pancreatic peptide hormones (CCK, PYY, GIP, GCG/GLP-1, ghrelin, insulin) and the hypothalamic prohormones (POMC, PCSK1N, NPY). Their absence is not an oversight — these are exactly the targets excluded by Layer 5's deliverability curation (short native half-life, or required PC1/2 cleavage). They are pharmacologically interesting in other modalities (chemically-modified peptide drugs, gene therapy to neuroendocrine cells), but they are not deliverable as cargos by our platform.

---

## 6. Why GDF15 was chosen as the first cargo

The cascade ranking is one input to a target-selection decision but not the only one. Three pieces of evidence about GDF15 specifically were decisive for our choice, none of which are captured by the kind of structured databases the cascade reads from.

### The hyperemesis gravidarum natural experiment

In 2024, a multi-institution study published in *Nature* (Fejzo et al.) established that the severe nausea and weight loss of hyperemesis gravidarum during pregnancy is caused by **elevated endogenous GDF15** acting on its receptor in the hindbrain. This is, in effect, an unintentional human dose-response study: when a woman's GDF15 levels rise during early pregnancy, she experiences sustained anorexia and significant body weight loss. The effect is dramatic, well-documented across thousands of patients, and unambiguous about the direction of causation.

No other candidate on our obesity shortlist has this strength of *human in-vivo* evidence. BDNF, NRG1, BMP8A, IL34, and other top-cascade candidates rely on rodent models or genetic association markers — both of which are weaker forms of causal evidence than what hyperemesis gravidarum provides for GDF15. This is an important asymmetry, and the cascade cannot capture it because no public structured database encodes "endogenous level of this protein produces this body composition change in humans."

### A receptor characterized in 2017

The receptor through which GDF15 acts (GFRAL) was identified in 2017 by three independent research groups simultaneously, all publishing in top journals. GFRAL is expressed in a highly restricted region of the hindbrain — the area postrema and the nucleus tractus solitarius — and essentially nowhere else in the body.

This anatomical specificity has two practical implications. First, systemic GDF15 produced from our sublingual platform will reach all tissues but will only act through this restricted neural circuit, limiting off-target effects compared to receptors that are widely expressed. Second, the side effect profile is *predictable*: the area postrema is also the brain's nausea-control center, so the expected adverse effect is nausea — the same side effect as GLP-1, mediated through a different pathway. We are not committing to a target whose adverse event profile will surprise us in Phase 1.

By contrast, several other cascade-top candidates have less mature receptor pharmacology. The receptor mechanism for BMP8A's brown-fat effect remains debated. NRG1's metabolic effect is mediated through ErbB-family receptors that are broadly expressed across tissues, making target-organ selectivity harder. ALKAL2 acts through ALK, a receptor tyrosine kinase whose chronic agonism carries oncogenic concern. Choosing a target with a well-characterized, anatomically-restricted receptor reduces translational risk.

### Industry derisking via NGM120

Pfizer (through its acquisition of NGM Biopharmaceuticals) advanced **NGM120 — a GFRAL antagonist** — into Phase 1 clinical trials for cancer-associated cachexia. We are interested in the *opposite* application: a GFRAL *agonist* for weight loss. The fact that an antagonist has cleared safety screening at Phase 1 doses tells us several things about the axis: that GFRAL can be drugged at therapeutic exposures, that the safety profile is generally acceptable at human doses, and that the manufacturing supply chain exists to produce GFRAL-targeting biologics. None of this guarantees that our agonist will succeed, but it removes a category of risk that an entirely novel target axis would carry.

This signal is also invisible to the cascade. Our ChEMBL query is restricted to metabolic indications; NGM120's cachexia trial is not indexed under those query terms. We add it explicitly as cascade-external information.

---

## 7. What we are and are not claiming

Because we are taking pains to frame this honestly, it is worth stating explicitly what this rationale does *not* claim:

- **We are not claiming GDF15 is mechanistically superior to GLP-1 for weight loss.** The semaglutide-tirzepatide-retatrutide trajectory has set a very high efficacy bar. GDF15-pathway agonists have not yet demonstrated comparable Phase 3 outcomes in obesity.
- **We are not claiming GDF15 will have fewer side effects than GLP-1.** Both pathways converge on the same anatomical nausea center. The side effect profile may turn out to be similar.
- **We are not claiming GDF15 is the only worthwhile cargo for our platform.** The cascade explicitly identifies BDNF, BMP8A, INHBE, and several other secreted proteins as defensible alternative cargos. Future studies should validate the platform with these as well.
- **We are not claiming the AI pipeline "discovered" GDF15.** It identified GDF15 as one of 112 admissible obesity-relevant signaling-protein candidates that are also genuinely deliverable by our platform, ranked #10 by L6 obesity-scoped opportunity score (top decile). The selection of GDF15 specifically was made by combining cascade admissibility with three cascade-external derisking signals — a decision that human investigators made transparently rather than one that an algorithm produced.

What we *are* claiming is methodological: that the modality-constrained constraint cascade is a systematic, auditable framework for narrowing a high-dimensional target selection problem down to a defensible shortlist, and that GDF15 belongs in that shortlist for principled reasons.

---

## 8. What comes next

The cascade and its rationale are inputs to a translational research program, not the program itself. The actual scientific tests are the wet-lab experiments that determine whether the saRNA-microneedle-GDF15 combination produces durable, well-tolerated body composition improvement in mouse models — and eventually in humans.

The immediate next steps are:

1. **Complete the cargo characterization in mouse models**: full pharmacokinetics of GDF15 expression after sublingual dosing; weight loss kinetics; body composition (DXA or NMR) to distinguish fat-mass from lean-mass change; glycemic control (oral glucose tolerance); hepatic steatosis improvement (histology and magnetic resonance spectroscopy); behavioral and tissue-level safety assessment.
2. **Comparator studies**: head-to-head comparison with semaglutide and (where feasible) with a GLP-1-Fc fusion delivered by the same saRNA-microneedle platform, to separate the contribution of the cargo from the contribution of the delivery modality.
3. **Platform expansion**: applying the same cascade and the same delivery platform to a second cargo from the obesity-scoped shortlist. The natural candidates are BDNF (top-ranked, although blood-brain-barrier transit historically limited its development; saRNA-driven systemic production may circumvent this), NRG1 (the #2 candidate on the obesity-scoped shortlist with 7 BMI GWAS hits), BMP8A (brown-fat thermogenesis regulator with strong rodent precedent), and NRG4 (brown-adipose batokine). Note that the well-known appetite-regulating gut peptides (CCK, PYY, GIP) are *not* on this expansion list because Layer 5 of the cascade excludes them on deliverability grounds (native plasma half-life too short, and in the case of PYY also requiring prohormone cleavage). A second cargo validation would convert the project from a single-target study into a delivery-platform study, which is a stronger publication-level contribution.

4. **Indication expansion**: re-running the same cascade with `--indication t2d` (121 candidates) or `--indication mash` (83 candidates) to identify saRNA-deliverable cargos for type 2 diabetes or metabolic-associated steatohepatitis. The cascade architecture is indication-parameterized precisely so that future projects can specialize it without re-deriving the methodology.
4. **Methodology release**: the constraint cascade itself, with full target-blind implementation and provenance, will be released so that other groups can apply it to other modalities (mRNA, AAV, antibody-drug conjugate) and other indications.

---

## 9. Summary in one paragraph

The current standard of care for chronic weight management (the GLP-1 receptor agonist class) has transformed treatment but leaves substantial unmet need — gastrointestinal intolerance, lean mass loss, rebound on discontinuation, β-cell dependency, injection administration, cost, and non-response. Our laboratory has developed a delivery platform — self-amplifying RNA encoded into a sublingual microneedle patch — that addresses several of these limitations but is fundamentally incompatible with the chemistry of the existing GLP-1 drugs. The platform's question is therefore not "what beats semaglutide" but "what natively-deliverable secreted protein addresses an unmet metabolic need that GLP-1 cannot reach." We built a target-blind, modality-constrained AI cascade that compresses the ~20,000 reviewed human protein-coding genes through five sequential evidence-based boolean gates plus a final opportunity ranker; specialized to obesity (the cascade's L2 evidence gate and L6 opportunity ranker take an indication parameter), it produces a 112-candidate obesity-scoped shortlist of signaling secreted proteins with obesity-relevant evidence that are also genuinely deliverable by saRNA. From this shortlist we selected GDF15 as the first cargo to validate experimentally — not because it ranks highest in any single score, but because it combines cascade admissibility (rank #10 of 112 in the obesity-scoped shortlist) with three independently verifiable derisking signals: the hyperemesis gravidarum natural experiment, characterization of the GFRAL receptor in 2017, and Phase 1 industrial validation of the GFRAL axis via NGM120. The wet-lab mouse data is the actual scientific test; the AI pipeline is the justification for choosing GDF15 to test first.
