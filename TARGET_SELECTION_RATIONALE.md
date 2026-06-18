# Why We Chose GDF15

*An accessible explanation of our target selection rationale for the saRNA-sublingual delivery platform.*

**Lab**: Cheng Lab, Columbia University, Department of Biomedical Engineering / Department of Medicine.
**Project**: Self-amplifying RNA + sublingual microneedle delivery of a secreted endocrine factor for obesity, type 2 diabetes, and metabolic-associated steatohepatitis (MASH).
**Document version**: 2026-06-18. All numbers below derive from the cascade applied to fully real public data (Open Targets 26.03, NHGRI-EBI GWAS Catalog latest, UniProt SwissProt human reviewed, ChEMBL via REST API by indication, PubMed E-utilities literature counts).

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

## 4. The pipeline: a five-layer constraint cascade

We assembled what we call a **target cascade**. Starting from the full set of ~20,000 reviewed human protein-coding genes, the pipeline applies five sequential filters, each backed by a different public database and each justified independently. A gene is admitted to the final shortlist only if it passes all five.

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

- An Open Targets Platform association score above a low threshold (≥ 0.05) for obesity, T2D, NAFLD, or MASH. Open Targets aggregates 20+ independent evidence sources, so a non-zero score implies multi-source support.
- At least one genome-wide-significant GWAS hit (p < 5×10⁻⁸) in the NHGRI-EBI GWAS Catalog for a metabolic trait (BMI, hemoglobin A1c, liver fat fraction, type 2 diabetes, lipid panel, etc.).
- A substantial body of indexed PubMed literature (≥ 50 publications) connecting the gene to metabolic context.

**Layer 2 result**: approximately **852** candidates retained.

### Layer 3 — Druggability

A target with strong disease evidence is still useless if it cannot be acted on pharmacologically. This layer admits genes whose protein class is known to be tractable for drug development (receptors, secreted hormones and cytokines, kinases, etc.) or for which ChEMBL records any prior bioactivity data.

**Layer 3 result**: virtually all Layer-2 passes also pass Layer 3 in our current cascade (~852).

### Layer 4 — Opportunity ranking

This layer does not filter; it ranks. We compute an **opportunity index** for each remaining candidate:

```
opportunity = evidence_strength / (1 + max_clinical_phase)
```

The numerator captures aggregate biological support (OT scores summed across diseases, GWAS hit count, log-scaled literature density). The denominator penalizes targets that are already heavily invested in industrially — a target with a Phase 3 program is much less of an *opportunity* for academic discovery than a target with equally strong evidence and no Phase 2 program. This deliberately steers the ranking toward **underdeveloped high-evidence opportunities** rather than rediscovering targets that pharma is already actively developing.

### Layer 5 — Safety baseline

A small list of historically failed targets (CETP, cannabinoid receptor 1, 5-HT2C receptor, DGAT1) is excluded outright. These targets have well-documented clinical failures (cardiovascular liability, psychiatric adverse events, post-approval withdrawal) that override any computational score.

**Layer 5 result**: **851** final admissible candidates.

### Implementation notes

The cascade is implemented entirely in target-blind code — no gene symbol of interest is hard-coded as a filter or as a special case. Every filtering decision is recorded with provenance so any candidate's inclusion or exclusion can be traced back to specific records in the public databases. The full implementation has been run against current Open Targets (version 26.03), GWAS Catalog (latest), ChEMBL (via REST API), and UniProt (SwissProt human reviewed).

---

## 5. Narrowing further: obesity-specific candidates

The 851-candidate shortlist includes targets with evidence for any of {obesity, T2D, NAFLD, MASH}. Some of these candidates are primarily relevant to lipid disorders (the apolipoprotein family, lipase enzymes) or hepatic-only conditions. For our project's primary indication of chronic weight management, we examined which candidates have *specifically obesity* evidence — defined as either an Open Targets association score above threshold for the obesity disease term, or at least one GWAS hit for body mass index.

**Obesity-specific subset**: **426** candidates (about half of the full shortlist).

This is the working pool from which the lab's first-cargo decision was made. It includes well-known names (leptin, the apolipoproteins, FGF21, GDF15) alongside less-discussed candidates that turned out to have strong genetic support — brain-derived neurotrophic factor (BDNF, with 12 BMI-significant GWAS hits), BMP8A (a brown-fat thermogenesis regulator), BRINP3 (a poorly studied secreted protein with 12 BMI GWAS hits), and the activin/inhibin family members (INHBE, recently flagged by the Inversago/Pfizer obesity-protective genetics program).

By raw opportunity score, GDF15 ranks **#112 of 426** in this obesity-specific shortlist (and **#178 of 851** in the full cascade-admissible set). It is admissible — it passes every layer of the cascade — but it is not the single mathematically highest-scoring target. We do not claim it is. The top of the opportunity-ranked obesity shortlist is occupied by APOE (primarily an Alzheimer's gene with incidental BMI association), BDNF (12 BMI GWAS hits, but limited by blood-brain-barrier transit historically), RSPO3 and LPL (lipid metabolism rather than weight loss specifically), and ANGPTL4 (another lipid regulator).

---

## 6. Why GDF15 was chosen as the first cargo

The cascade ranking is one input to a target-selection decision but not the only one. Three pieces of evidence about GDF15 specifically were decisive for our choice, none of which are captured by the kind of structured databases the cascade reads from.

### The hyperemesis gravidarum natural experiment

In 2024, a multi-institution study published in *Nature* (Fejzo et al.) established that the severe nausea and weight loss of hyperemesis gravidarum during pregnancy is caused by **elevated endogenous GDF15** acting on its receptor in the hindbrain. This is, in effect, an unintentional human dose-response study: when a woman's GDF15 levels rise during early pregnancy, she experiences sustained anorexia and significant body weight loss. The effect is dramatic, well-documented across thousands of patients, and unambiguous about the direction of causation.

No other candidate on our obesity shortlist has this strength of *human in-vivo* evidence. BDNF, BMP8A, BRINP3, and other top-cascade candidates rely on rodent models or genetic association markers — both of which are weaker forms of causal evidence than what hyperemesis gravidarum provides for GDF15. This is an important asymmetry, and the cascade cannot capture it because no public structured database encodes "endogenous level of this protein produces this body composition change in humans."

### A receptor characterized in 2017

The receptor through which GDF15 acts (GFRAL) was identified in 2017 by three independent research groups simultaneously, all publishing in top journals. GFRAL is expressed in a highly restricted region of the hindbrain — the area postrema and the nucleus tractus solitarius — and essentially nowhere else in the body.

This anatomical specificity has two practical implications. First, systemic GDF15 produced from our sublingual platform will reach all tissues but will only act through this restricted neural circuit, limiting off-target effects compared to receptors that are widely expressed. Second, the side effect profile is *predictable*: the area postrema is also the brain's nausea-control center, so the expected adverse effect is nausea — the same side effect as GLP-1, mediated through a different pathway. We are not committing to a target whose adverse event profile will surprise us in Phase 1.

By contrast, several other cascade-top candidates have less mature receptor pharmacology. The receptor mechanism for BMP8A's brown-fat effect remains debated. BRINP3 has minimal published pharmacology. INHBE was only recently associated with metabolic phenotype, and its receptor pharmacology is at an early stage. Choosing a target with a well-characterized receptor reduces translational risk.

### Industry derisking via NGM120

Pfizer (through its acquisition of NGM Biopharmaceuticals) advanced **NGM120 — a GFRAL antagonist** — into Phase 1 clinical trials for cancer-associated cachexia. We are interested in the *opposite* application: a GFRAL *agonist* for weight loss. The fact that an antagonist has cleared safety screening at Phase 1 doses tells us several things about the axis: that GFRAL can be drugged at therapeutic exposures, that the safety profile is generally acceptable at human doses, and that the manufacturing supply chain exists to produce GFRAL-targeting biologics. None of this guarantees that our agonist will succeed, but it removes a category of risk that an entirely novel target axis would carry.

This signal is also invisible to the cascade. Our ChEMBL query is restricted to metabolic indications; NGM120's cachexia trial is not indexed under those query terms. We add it explicitly as cascade-external information.

### Execution readiness

The Cheng Lab has already designed the saRNA construct encoding GDF15, optimized the sublingual microneedle formulation for this cargo, and generated initial mouse pharmacokinetic and weight-loss data with the combined platform. If we pivoted to BDNF, BMP8A, or another cascade-top candidate, this work would need to be repeated for the new cargo — a delay of approximately six months and substantial additional reagent expense.

This is not a scientific argument for GDF15 over BDNF or BMP8A; those candidates remain scientifically defensible and may be tested in subsequent work. It is a project-realism argument: GDF15 is the candidate where the lab's first paper can be completed within a reasonable timeline.

---

## 7. What we are and are not claiming

Because we are taking pains to frame this honestly, it is worth stating explicitly what this rationale does *not* claim:

- **We are not claiming GDF15 is mechanistically superior to GLP-1 for weight loss.** The semaglutide-tirzepatide-retatrutide trajectory has set a very high efficacy bar. GDF15-pathway agonists have not yet demonstrated comparable Phase 3 outcomes in obesity.
- **We are not claiming GDF15 will have fewer side effects than GLP-1.** Both pathways converge on the same anatomical nausea center. The side effect profile may turn out to be similar.
- **We are not claiming GDF15 is the only worthwhile cargo for our platform.** The cascade explicitly identifies BDNF, BMP8A, INHBE, and several other secreted proteins as defensible alternative cargos. Future studies should validate the platform with these as well.
- **We are not claiming the AI pipeline "discovered" GDF15.** It identified GDF15 as one of 426 admissible obesity-relevant candidates, ranked #112 by raw opportunity score. The selection of GDF15 specifically was made by combining cascade admissibility with three cascade-external derisking signals and with project execution readiness — a decision that human investigators made transparently rather than one that an algorithm produced.

What we *are* claiming is methodological: that the modality-constrained constraint cascade is a systematic, auditable framework for narrowing a high-dimensional target selection problem down to a defensible shortlist, and that GDF15 belongs in that shortlist for principled reasons.

---

## 8. What comes next

The cascade and its rationale are inputs to a translational research program, not the program itself. The actual scientific tests are the wet-lab experiments that determine whether the saRNA-microneedle-GDF15 combination produces durable, well-tolerated body composition improvement in mouse models — and eventually in humans.

The immediate next steps are:

1. **Complete the cargo characterization in mouse models**: full pharmacokinetics of GDF15 expression after sublingual dosing; weight loss kinetics; body composition (DXA or NMR) to distinguish fat-mass from lean-mass change; glycemic control (oral glucose tolerance); hepatic steatosis improvement (histology and magnetic resonance spectroscopy); behavioral and tissue-level safety assessment.
2. **Comparator studies**: head-to-head comparison with semaglutide and (where feasible) with a GLP-1-Fc fusion delivered by the same saRNA-microneedle platform, to separate the contribution of the cargo from the contribution of the delivery modality.
3. **Platform expansion**: applying the same cascade and the same delivery platform to a second cargo from the obesity-specific shortlist (BDNF and BMP8A are the two leading candidates). A second cargo validation would convert the project from a single-target study into a delivery-platform study, which is a stronger publication-level contribution.
4. **Methodology release**: the constraint cascade itself, with full target-blind implementation and provenance, will be released so that other groups can apply it to other modalities (mRNA, AAV, antibody-drug conjugate) and other indications.

---

## 9. Summary in one paragraph

The current standard of care for chronic weight management (the GLP-1 receptor agonist class) has transformed treatment but leaves substantial unmet need — gastrointestinal intolerance, lean mass loss, rebound on discontinuation, β-cell dependency, injection administration, cost, and non-response. Our laboratory has developed a delivery platform — self-amplifying RNA encoded into a sublingual microneedle patch — that addresses several of these limitations but is fundamentally incompatible with the chemistry of the existing GLP-1 drugs. The platform's question is therefore not "what beats semaglutide" but "what natively-deliverable secreted protein addresses an unmet metabolic need that GLP-1 cannot reach." We built a target-blind, modality-constrained AI cascade that compresses the ~20,000 reviewed human protein-coding genes through five sequential evidence-based filters down to 851 admissible candidates, of which 426 have specifically obesity-relevant evidence. From this shortlist we selected GDF15 as the first cargo to validate experimentally — not because it ranks highest in any single score, but because it combines cascade admissibility with three independently verifiable derisking signals (the hyperemesis gravidarum natural experiment, characterization of the GFRAL receptor in 2017, and Phase 1 industrial validation of the GFRAL axis via NGM120) plus execution readiness from existing lab work. The wet-lab mouse data is the actual scientific test; the AI pipeline is the justification for choosing GDF15 to test first.
