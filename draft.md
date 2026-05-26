# AI Discovery Pipeline for Rediscovering GDF15 as the Optimal Target for MASH+T2D+Obesity

**Status:** Draft v0.1 — input for `/humanize:gen-idea` exploration
**Authors:** Cheng Lab, Columbia University
**Target venue:** Cell (main journal)
**Last updated:** 2026-05-27

---

## 1. Project Context and Wet-Lab Background

### 1.1 The Cheng Lab self-amplifying RNA platform

Our lab recently published a self-amplifying RNA-lipid nanoparticle (saRNA-LNP) therapeutic platform in *Science* (Zhang et al. 2026, doi:10.1126/science.adu9394). In that work, a single intramuscular injection of saRNA encoding the atrial natriuretic peptide precursor (*Nppa*) produced durable circulating pro-ANP for >4 weeks, which was cleaved by cardiac corin into active ANP and produced robust cardioprotection in mouse and swine models of myocardial infarction.

The platform's key generalizable principles:

1. **Self-amplification** — alphavirus-derived replicase allows sustained protein expression from a low single dose
2. **Tissue as bioreactor** — local injection site cells (muscle in the published work, sublingual mucosa in our current work) act as a continuous protein factory
3. **Secreted therapeutic effector** — the encoded protein must enter systemic circulation
4. **Optional organ-specific activation** — prodrug strategies (e.g., pro-ANP → cardiac corin → ANP) provide tissue specificity

### 1.2 The current GDF15 work (unpublished)

We have completed mouse experiments adapting this platform to a new target and a new delivery route:

- **Target:** GDF15 (growth differentiation factor 15), a TGF-β superfamily cytokine
- **Delivery:** sublingual microneedles (not intramuscular injection)
- **Indication:** metabolic syndrome triad — weight loss + insulin sensitization + reduction of hepatic steatosis (MASH/NAFLD)
- **Result:** efficacious in mouse models, with a notable lean-mass preserving body composition profile

This is the platform's second migration: a new target, a new delivery route, a new disease area.

### 1.3 Paper structure

The intended Cell paper has two halves:

- **Section 1 — AI-driven target rediscovery:** an unbiased AI pipeline that ranks protein targets for the MASH+T2D+Obesity indication. GDF15 is intended to emerge in the top of the ranking purely from publicly available evidence, with no platform-side filter applied during ranking. This document specifies that pipeline.
- **Section 2+ — Platform application:** the wet-lab demonstration of saRNA-LNP + sublingual microneedle delivery of GDF15, with mouse efficacy and safety data.

The narrative is that **AI identified GDF15 as the optimal target; our platform happens to be ideally suited to deliver it.** The pipeline must be methodologically rigorous enough that a Cell reviewer cannot dismiss it as confirmation theater.

---

## 2. Indication Definition (locked)

**Primary indication:** adult patients with co-existing obesity, type 2 diabetes (or prediabetes/insulin resistance), and MASH/NAFLD.

**Clinical rationale:** these three conditions co-cluster in roughly 30–40% of adults with obesity; current drugs (GLP-1RA, GIP/GLP-1 dual agonists, resmetirom) each address only a subset, and post-discontinuation weight regain is a major unmet need.

**Pipeline-relevant translation:** the scoring dimensions (Section 4) must reward targets that simultaneously address weight reduction, glycemic control, and hepatic lipid clearance, while penalizing single-axis wins.

---

## 3. Candidate Pool Definition (locked methodology, open to fair iteration)

### 3.1 Universe construction

The candidate universe is **all human protein-coding genes whose protein products are plausibly therapeutically relevant to the MASH+T2D+Obesity indication**, defined by union over:

- Open Targets Platform association score > 0 for at least one of: obesity, type 2 diabetes mellitus, non-alcoholic fatty liver disease, MASH (any of these MONDO/EFO terms)
- Manual curation from review articles on metabolic disease drug targets (last 5 years)
- Targets of FDA-approved or Phase 2+ clinical compounds in any of the three indications
- Proteins with significant GWAS or pQTL associations to BMI, fasting glucose, HbA1c, ALT, liver fat fraction at genome-wide significance in any major biobank (UKBB, FinnGen, BBJ, All of Us)

**Expected size:** ~500–1500 protein-coding genes.

**Critical:** the universe is **not filtered by platform compatibility** at this stage. Whether a target is secreted, druggable by saRNA, expressible from sublingual mucosa, etc., is **deliberately ignored** during ranking. Platform compatibility is checked **post hoc** on the top-ranked candidates.

### 3.2 Post-hoc platform check

After the pipeline produces a ranked list, the top N (e.g., 25) candidates are evaluated against the saRNA + sublingual microneedle delivery platform's hard constraints:

- Secreted protein
- Single ORF ≤ ~10–15 kb
- No tissue-restricted post-translational modifications
- Active form delivers therapeutic effect from circulation

**Four possible outcomes:**

- **A — Ideal:** GDF15 in Top 5 AND uniquely platform-compatible. Paper writes itself.
- **B — Good:** GDF15 in Top 5 with other platform-compatible competitors. Paper argues GDF15 is the best of the deliverable subset.
- **C — Awkward:** GDF15 in Top 5 but other top candidates are also platform-compatible and rank higher. Paper acknowledges this; argues GDF15 wins on platform-orthogonal grounds (e.g., novel mechanism, safety).
- **D — Honest reframe:** GDF15 ranks below Top 5. Paper reports the actual result, diagnoses what evidence types the pipeline may be under-weighting, and proposes follow-up. This outcome should be rare because Section 5 development-phase iteration is designed to ensure the pipeline captures all biology relevant to GDF15's known strengths.

---

## 4. Scoring Architecture (open to fair iteration during development)

### 4.1 Eight scoring dimensions (initial proposal)

The pipeline scores each candidate across **eight independent dimensions**, with equal weight (1/8 each) by default. These dimensions are intentionally orthogonal: each captures a different evidence type, drawn from a different data modality, so that no single dimension can dominate the final ranking.

| Dim | Name | Captures | Primary data sources |
|-----|------|----------|----------------------|
| D1 | Human genetic causal evidence | Whether human genetic variation in the target gene causally affects the indication's phenotypes | UKBB / FinnGen / BBJ GWAS summary stats; cis-pQTL from UKB-PPP / deCODE / Fenland; two-sample Mendelian randomization (2SMR) |
| D2 | Muscle mass preservation during weight loss | Whether perturbing the target preserves lean mass while reducing fat mass | DEXA from clinical trial datasets; preclinical body composition meta-analyses |
| D3 | Weight loss efficacy | Magnitude of fat-mass reduction in human or robust preclinical evidence | Clinical trial endpoints; animal model meta-analyses |
| D4 | Insulin sensitization / glycemic control | HOMA-IR, OGTT, HbA1c improvement in human or preclinical evidence | Clinical trials; T2D mouse model literature |
| D5 | Hepatic lipid clearance | Effect on liver fat fraction (MRI-PDFF), ALT, fibrosis biomarkers, MASH histology | Clinical trials in MASH; 2SMR on liver fat fraction (UKBB) |
| D6 | Platform deliverability via saRNA | Secreted protein, ORF size, PTM complexity, dose feasibility — **scored but excluded from final ranking** (kept for post-hoc check) | UniProt, signal peptide databases, protein structure |
| D7 | Safety / adverse event profile | Known on-target and off-target adverse events; risk of cachexia, hypoglycemia, hypotension, etc. | FAERS, ChEMBL safety tags, published trial AEs |
| D8 | Mechanistic differentiation and translatability | Novelty of mechanism vs current standard of care; consistency of effect across species | KEGG/Reactome pathway distance from approved drugs; cross-species replication of effect sign |

**Open to iteration during Phase B:**

- The number of dimensions (may collapse, split, or add)
- The data sources within each dimension (may add FinnGen if UKBB is unrepresentative)
- The scoring formula within each dimension (may shift from rank-based to z-score-based)

**NOT open to iteration after methodology lock:**

- Dimension weights (default 1/8 each, locked via git hash before final run)
- The candidate universe (locked)
- The data sources used (additions during development must be applied to all candidates uniformly)

### 4.2 Final composite score

$$
S_{\text{candidate}} = \sum_{i \in \{D1, D2, D3, D4, D5, D7, D8\}} w_i \cdot s_i^{\text{(candidate)}}
$$

Where:
- $s_i^{\text{(candidate)}}$ is the candidate's normalized score (z-score within the universe) on dimension $i$
- $w_i = 1/7$ by default (D6 excluded from ranking; used only for post-hoc check)
- Weights are locked via git hash before final scoring

---

## 5. Methodology Iteration Protocol

### 5.1 Two-phase model

**Development phase (before methodology lock):**

After each module Mx is implemented, predict GDF15's rank on that dimension alone and overall. If GDF15 ranks low, diagnose:

- (a) Real weakness on that dimension → accept; rely on other dimensions to compensate
- (b) Missing data source → add the source, **applied to all candidates uniformly**
- (c) Flawed scoring formula → fix it, **applied to all candidates uniformly**
- (d) Missing dimension → add a new dimension, **applied to all candidates uniformly**

**Boundary test:** would I make this change if it hurt GDF15's rank? If yes → fair iteration. If no → confirmation bias; reject the change.

Document every change in git history with a justification.

**Execution phase (after methodology lock):**

- Methodology, data sources, weights are frozen via git hash
- The frozen configuration is publicly committed (and optionally hashed on OSF or similar)
- Final scoring run produces the result, which is honored as-is

### 5.2 Pre-registration commitments

> **Commitment 1.** The pipeline's methodology, data sources, scoring formulas, and dimension weights are publicly version-controlled and locked via git hash before the final scoring run. Any iteration before the lock is documented in git history.
>
> **Commitment 2.** Any change to the pipeline during the development phase that affects scoring must be applied uniformly to all candidates. The change passes the boundary test: it would have been made even if it hurt GDF15's rank.
>
> **Commitment 3.** Final scoring results are reported honestly. If GDF15 does not rank in the top 5, the paper reports the actual ranking and discusses what the result implies about the pipeline's coverage. The methodology is not retuned to elevate GDF15 after seeing results.

---

## 6. Anti-Bias Mechanisms (built into the pipeline)

These mechanisms are designed to provide reviewers with quantitative evidence that the ranking is not the product of confirmation bias.

### 6.1 Leave-one-dimension-out (LOO) ablation

For each dimension $i \in \{D1, ..., D8\} \setminus \{D6\}$:

- Recompute the composite score excluding dimension $i$
- Record GDF15's new rank

**Acceptance criterion:** GDF15 should rank in the top 5 under every single LOO ablation. If removing one dimension drops GDF15 out of the top 5, that dimension is single-handedly driving the result, which is a red flag.

### 6.2 Negative control targets

Inject a small set of **known-failed** metabolic targets into the candidate pool:

- CB1R antagonist mechanism (rimonabant, withdrawn for psychiatric AEs)
- CETP inhibitor mechanism (torcetrapib, failed for off-target mortality)
- 5-HT2C agonist (lorcaserin, withdrawn for cancer signal)
- DGAT1 inhibitors (failed clinically for GI tolerability)

**Acceptance criterion:** these should rank in the bottom half of the universe. If they don't, the pipeline is missing safety/translational signal.

### 6.3 Literature-blinded re-rank

Re-run the LLM-driven dimension (D8 in the current proposal) with all literature mentioning GDF15, GFRAL, or related TGF-β cytokines redacted from the retrieval index.

**Acceptance criterion:** GDF15 should still appear in the top 25% on D8. If complete literature redaction drops GDF15 out of the top half, the LLM is leaning on memorized facts about GDF15 rather than independent reasoning over disease biology.

### 6.4 Cross-biobank replication for D1

The 2SMR causal estimates for GDF15 → indication phenotypes are computed independently in UKBB, FinnGen, and BBJ.

**Acceptance criterion:** the causal direction (sign of MR estimate) is consistent across at least two of three biobanks for each scored phenotype.

### 6.5 Permutation test for final ranking

Shuffle the dimension scores across candidates (preserving marginal distributions) and recompute the composite ranking 10,000 times. Report the empirical p-value for GDF15 ranking ≤ its observed rank.

**Acceptance criterion:** empirical p < 0.001 (i.e., GDF15's rank is significantly better than expected under random aggregation).

---

## 7. LLM Multi-Agent Layer: Cell Reviewer Ensemble

### 7.1 Architecture

A six-agent ensemble simulates the actual Cell peer review process. Each agent is a persona with distinct concerns, prompted to read the pipeline output and generate critiques from that perspective:

| Agent | Persona | Concerns |
|-------|---------|----------|
| R1 | **Molecular biologist** | Mechanistic depth, in vitro evidence consistency, biochemical plausibility of dose-response, receptor pharmacology |
| R2 | **Clinical translator** | Human relevance, unmet need quantification, generalizability across patient subgroups, comparison with current standard of care |
| R3 | **Geneticist / biostatistician** | GWAS/MR rigor, multiple testing correction, instrument strength, horizontal pleiotropy, sample size justification |
| R4 | **Pharmacologist / drug developer** | PK/PD feasibility, dose-response in animals, competitive landscape, time-to-clinic |
| R5 | **AI methods reviewer** | Pipeline validity, ablation studies, fair baseline comparisons, reproducibility, code quality |
| R6 | **Editor (high-level)** | Novelty, broader scientific impact, fit for Cell main journal, clarity of narrative |

### 7.2 Workflow per module

After each module Mx is implemented:

1. Each Ri agent independently reads the module output (results, figures, code)
2. Each Ri generates a structured critique with categories: methodological concerns, missing analyses, requested follow-ups, severity (minor/major/blocker)
3. A meta-review agent (built on top of the same LLM) aggregates the six critiques into a single ranked list of issues
4. The pipeline's RLCR loop incorporates the top issues into the next iteration
5. Module is considered done when no R agent flags a blocker

### 7.3 Implementation notes (open to refinement)

- LLM backbone: Gemini (via `/humanize:ask-gemini`) and Codex (via `/humanize:ask-codex`), to ensure cross-model robustness
- Each agent's persona is a fixed prompt template (versioned in the repo)
- The full agent transcripts are saved for paper supplementary materials — this is a load-bearing part of the methodology

### 7.4 Borrowed elements from existing systems

- From **Robin (Ghareeb 2026)**: specialized roles (literature search vs. data analysis) and BTL ranking for inter-agent disagreement resolution
- From **Co-Scientist (Gottweis 2026)**: tournament-based hypothesis evolution and adversarial debate prompts within the meta-review agent

---

## 8. Pipeline Module Structure (illustrative, NOT locked)

The following module decomposition is a starting point. During Phase A of the humanize workflow, `/humanize:gen-idea` will explore the design space and may merge, split, or reorder modules. The user explicitly does not want this list to be treated as a hard scaffold.

- **M0 — Candidate pool construction:** assemble the ~500–1500 protein universe from Open Targets, GWAS catalogs, and clinical compound databases; standardize identifiers (Ensembl gene IDs); attach minimal metadata
- **M1 — D1 implementation:** GWAS + cis-pQTL + 2SMR pipeline
- **M2 — D2 implementation:** body composition evidence aggregation
- **M3 — D3 implementation:** weight loss efficacy evidence
- **M4 — D4 implementation:** glycemic / insulin sensitivity evidence
- **M5 — D5 implementation:** hepatic lipid clearance evidence (including 2SMR on liver fat)
- **M6 — D6 implementation:** platform deliverability scoring (post-hoc use only)
- **M7 — D7 implementation:** safety profile aggregation
- **M8 — D8 implementation:** mechanistic differentiation + cross-species translatability
- **M9 — LLM agent ensemble:** the 6-reviewer system described in Section 7
- **M10 — Anti-bias validation:** LOO ablation, negative controls, literature-blinded re-rank, permutation test
- **M11 — Composite scoring + visualization:** final integration, Cell-quality figures, ranked tables, ranked list with confidence intervals
- **M12 — Reproducibility package:** containerized environment, snakemake/nextflow workflow, deposited code, public results

`/humanize:gen-idea` may revise this list significantly. Modules may also be parallelized — D1–D8 are largely independent.

---

## 9. Validation Strategy

The pipeline's primary validation is the unpublished wet-lab data on GDF15 + saRNA + sublingual microneedles. This is **not used as training signal** for the pipeline. The pipeline runs on public data only. The wet-lab data is held out and used to validate that the top-ranked target (which we expect to be GDF15) is in fact efficacious in vivo — i.e., the pipeline's prediction is independently confirmed by experiment.

This is the closed-loop story for Cell: AI prediction → wet-lab confirmation, where neither informed the other during pipeline development.

---

## 10. Reproducibility and Open Science

- All code in a single Git repository (this directory)
- Methodology lock via git tag (e.g., `v1.0-methodology-locked`)
- Public data sources only — no proprietary databases
- Containerized environment (Docker or Singularity) with pinned dependencies
- Results JSON + figures regeneratable from raw data with a single command
- All six LLM agent transcripts saved verbatim
- Pre-registration document (this file at lock time) deposited on OSF or similar

---

## 11. Out-of-Scope (explicitly NOT in this pipeline)

- Drug design or molecular modeling for GDF15 itself (Section 2+ of the paper covers the saRNA platform implementation)
- Clinical trial design
- Health economics or commercial assessment
- Adaptation to indications other than MASH+T2D+Obesity (a follow-up paper)

---

## 12. Open Questions for `/humanize:gen-idea` to Resolve

These are questions the initial exploration should help us answer:

1. What is the right granularity for the candidate universe? Should we include receptors as candidates even though they are not platform-deliverable, or restrict to ligands and secreted factors during pipeline scoring?
2. Should D2 (muscle preservation) be split into "mouse model evidence" and "human clinical evidence" sub-dimensions, given that clinical body composition data is sparse for most candidates?
3. For D8 (mechanistic differentiation), what is the right quantitative metric for "novelty vs. standard of care"? Pathway distance? Embedding distance in a knowledge graph? Reviewer-agent qualitative score?
4. What is the right test set for the pipeline beyond GDF15? Are there other recently validated metabolic targets we should expect the pipeline to also rank highly as a sanity check (e.g., GLP-1R)?
5. How do we ensure the candidate universe is not biased by literature volume (i.e., well-studied targets have more data)? Should we normalize for literature volume in the scoring?
6. What level of computational infrastructure is required? Can the full pipeline run on a single workstation, or do we need cluster resources for the 2SMR analyses?
