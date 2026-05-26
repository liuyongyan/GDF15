# Autonomous Loop Specification: Designing an AI Discovery Pipeline that Rediscovers GDF15

**Status:** Draft v1.1 — input for `/humanize:gen-plan` → `/humanize:start-rlcr-loop`
**Authors:** Cheng Lab, Columbia University
**Target venue:** Cell (main journal)
**Last updated:** 2026-05-27

---

## 0. Abstract (paper-level, what the final result must support)

Tirzepatide and other GLP-1/GIP agonists have transformed obesity treatment but require weekly subcutaneous injections, lose efficacy after discontinuation, and erode lean mass — limitations that constrain long-term adherence and the quality of weight loss. To identify a protein target capable of resolving these limitations simultaneously, we built a pre-registered AI discovery pipeline that scored ~1,200 candidates across a structured set of orthogonal evidence dimensions, with a six-persona simulated-reviewer ensemble providing in-pipeline adversarial critique. Growth differentiation factor 15 (GDF15) ranked first — a hindbrain-acting cytokine whose multi-axis metabolic profile has long been recognized but whose 2-hour plasma half-life made recombinant-protein development clinically impractical. To revive this orphaned target, we encoded GDF15 in a self-amplifying RNA (saRNA) delivered through a sublingual microneedle patch worn for 10 minutes once daily — an at-home, needle-free administration that converts oral mucosa into a self-renewing GDF15 source and is operationally simpler than the weekly injections that define current standard of care. Across three mouse models of obesity-associated MASH, this intervention recapitulated the AI-predicted profile: durable, dose-dependent fat-mass reduction with preserved lean mass, improved insulin sensitivity, and reversal of hepatic steatosis. By coupling adversarially-validated AI target rediscovery with a delivery platform that is both more practical than current injectables and capable of resurrecting pharmacokinetically intractable targets, this work establishes a generalizable framework for next-generation metabolic therapeutics.

---

## 1. What This Document Is

This document specifies a **two-layer autonomous system** that will be implemented and executed via `/humanize:start-rlcr-loop`:

- **Inner layer — the AI Discovery Pipeline.** A program that takes a research question ("find a better weight-loss drug than Tirzepatide") and produces a ranked list of protein targets, recommended delivery modalities, and predicted phenotypic profiles. The pipeline does not know which target the wet lab has validated.
- **Outer layer — the Design Loop.** A meta-process that iteratively improves the Pipeline by: proposing changes → implementing them → running the Pipeline → evaluating the output against ground truth and against methodological-rigor criteria → reviewing whether the changes were principled → iterating until termination.

The user will sleep while the loop runs. The user reviews the final state in the morning.

The expected end state: a Cell-grade AI discovery Pipeline whose ranked output puts GDF15 in the top-tier candidates, supported by independently verifiable evidence dimensions, robust to ablation, and accompanied by a six-persona simulated peer review that endorses the methodology.

---

## 2. Project Context

The Cheng Lab recently published a self-amplifying RNA-LNP platform (Zhang et al., *Science* 2026, doi:10.1126/science.adu9394) for cardiac repair via *Nppa*-encoded pro-ANP. We have separately completed unpublished mouse work adapting this platform to a new target (GDF15), a new delivery route (sublingual microneedles), and a new indication (obesity + insulin resistance + MASH). The wet-lab data shows efficacy with a body-composition profile favorable on lean-mass preservation.

The Cell paper has two halves:

- **Section 1 — AI-driven target rediscovery.** The Pipeline that this loop will produce.
- **Section 2+ — Platform application.** The wet-lab demonstration (already complete).

The narrative is: **AI identified GDF15 as the optimal target; the Cheng Lab platform happens to be ideally suited to deliver it.**

---

## 3. The Inner Layer: AI Discovery Pipeline Specification

### 3.1 IO Contract

**Input.** A structured research question:

```json
{
  "question": "Find a better weight-loss drug than Tirzepatide.",
  "phenotype_profile_desired": {
    "fat_mass_reduction": "high",
    "lean_mass_preservation": "high",
    "glycemic_control": "high",
    "hepatic_steatosis_reduction": "high",
    "durability_after_discontinuation_or_with_infrequent_dosing": "high",
    "patient_administration_burden": "low"
  },
  "indication_context": "adults with co-existing obesity, type 2 diabetes (or prediabetes/insulin resistance), and MASH/NAFLD"
}
```

**Output.** A structured ranking:

```json
{
  "ranked_targets": [
    {
      "rank": 1,
      "target_symbol": "...",
      "ensembl_gene_id": "...",
      "composite_score": 0.0,
      "per_dimension_scores": { "...": 0.0 },
      "predicted_phenotype_profile": { "...": "..." },
      "recommended_delivery_modality": "...",
      "rationale_summary": "..."
    }
    // ... at least top 25 candidates
  ],
  "anti_bias_validation": {
    "loo_ablation": "...",
    "negative_controls": "...",
    "literature_blinded_rerank": "...",
    "permutation_test_p_value": 0.0
  },
  "reviewer_ensemble_verdict": {
    "R1_molecular_biologist": "...",
    "R2_clinical_translator": "...",
    "R3_geneticist_biostatistician": "...",
    "R4_pharmacologist": "...",
    "R5_ai_methods_reviewer": "...",
    "R6_editor": "...",
    "meta_review": "...",
    "blockers_remaining": []
  },
  "pre_registration_hash": "git-sha",
  "reproducibility": "command to reproduce all results"
}
```

### 3.2 Hard Constraints on the Pipeline

These constraints are non-negotiable. The loop's Codex reviewer must enforce them every round.

- **C1 — No leakage of the expected answer.** The Pipeline does not read `evaluator/expected_answer.json` and does not contain any hard-coded reference to GDF15 as a target of interest. Its only knowledge of GDF15 is what arrives through generic data sources (Open Targets, GWAS, literature, etc.) applied uniformly to all candidates.
- **C2 — Candidate universe constructed by inclusive rules.** ~500–1500 protein-coding genes, sourced via documented inclusion rules over Open Targets / GWAS catalogs / clinical-pipeline databases / literature. The universe is not filtered by platform deliverability at scoring time.
- **C3 — Multi-dimensional scoring.** At least 5 orthogonal scoring dimensions, each backed by independent data modalities. The Pipeline itself decides the exact count and naming. No single dimension may dominate the final composite by construction (no dimension weight > 0.4).
- **C4 — Six-persona reviewer ensemble (Inner Pipeline component).** The Pipeline itself instantiates the persona ensemble described in §5.3 as part of its scoring and reporting. The reviewers operate inside the Pipeline, evaluate the scientific soundness of the candidate ranking, and surface their critiques in the Pipeline's output JSON. This is a scientific peer-review function. (Note: this is distinct from the Loop's Codex review in §4.3 Step 6, which is a methodological integrity check on each round's proposed changes, not a science review.)
- **C5 — Anti-bias checks.** All five anti-bias mechanisms (§6) must run and report. Failure of any single check is reported but does not silently invalidate the ranking.
- **C6 — Reproducibility.** Single command runs the full pipeline from raw data sources to final output. Methodology is locked via git hash before final run.
- **C7 — Honest reporting.** If GDF15 (or any specific target) does not rank where expected, the Pipeline reports the actual ranking. Tuning the Pipeline post-hoc to elevate any specific target is forbidden (enforced by the loop's Codex review, see §4.5).

### 3.3 Platform-Compatibility Post-Hoc Check

After the Pipeline produces its ranked list, a separate (clearly labeled) post-hoc evaluation checks the top N candidates against the saRNA + sublingual microneedle delivery platform's hard constraints (secreted protein, ORF ≤ ~15 kb, no complex PTM, active form from circulation). This evaluation does not modify the ranking. It is reported as a separate analysis in the output JSON.

---

## 4. The Outer Layer: The Design Loop

### 4.1 Goal

Iteratively design, run, evaluate, and improve the Inner Pipeline until **all termination criteria (§4.6)** are met, or the budget is exhausted.

### 4.2 The External Evaluator

A program separate from the Pipeline, owned by the loop layer. The Evaluator:

- Has access to `evaluator/expected_answer.json`, which specifies the ground-truth answer:
  ```json
  {
    "expected_top_targets": ["GDF15"],
    "expected_delivery_modality": "self-amplifying RNA via sublingual microneedle patch",
    "rationale_visible_to_evaluator_only": "Cheng Lab wet-lab data validates GDF15 + saRNA + microneedles in three mouse models of MASH-associated obesity (unpublished). The Pipeline must rediscover this answer from public data alone."
  }
  ```
- Compares the Pipeline's output (§3.1) against the expected answer.
- Compares the Pipeline's anti-bias check results against thresholds.
- Compares the reviewer ensemble's verdicts.
- Produces a structured diagnostic report (`diagnostics/round_N.md`):
  - Is GDF15 in the top 5? (if no, by how much is it missed)
  - Which evidence dimensions support / weaken GDF15's ranking
  - Which anti-bias checks pass / fail
  - Which reviewer personas flagged blocker-level concerns
  - Specific suggestions for what the Pipeline could improve **methodologically** (not in a target-specific way)

### 4.3 The Loop Workflow Per Round

```
Round N (N = 1, 2, ..., MAX_ROUNDS):

  Step 1 — READ STATE
    Load pipeline/ (current Pipeline implementation)
    Load all prior diagnostics/ and reviews/
    Load draft.md (this document) as immutable spec

  Step 2 — PROPOSE
    Claude proposes changes to the Pipeline, with justification.
    Justification must pass the boundary test (§5.2): "Would I make this
    change if it hurt GDF15's rank?"
    The proposal is written to proposals/round_N.md before any code change.

  Step 3 — IMPLEMENT
    Claude writes/edits files in pipeline/ to enact the proposal.
    All edits must keep the Pipeline runnable end-to-end.

  Step 4 — RUN
    Execute the Pipeline on the input (§3.1) using a single canonical command.
    Capture full output to runs/round_N/output.json.
    Capture stderr, run time, and any errors to runs/round_N/log.txt.

  Step 5 — EVALUATE
    Run the External Evaluator on runs/round_N/output.json.
    Evaluator writes diagnostics/round_N.md.

  Step 6 — REVIEW  (Outer Loop — methodological integrity check, NOT a science review)
    Note: this Codex review is the Loop's own integrity check. It is distinct
    from the Inner Pipeline's 6-persona reviewer ensemble (§5.3), which evaluates
    the scientific soundness of the ranking and runs inside the Pipeline itself.
    
    /humanize:ask-codex is invoked with:
      - The proposal (Step 2)
      - The implementation diff (Step 3)
      - The diagnostic (Step 5)
    Codex must answer four questions in reviews/round_N.md:
      Q1: Were the proposed changes methodologically principled, or did they
          target-rig in favor of GDF15? (boundary test)
      Q2: Did the implementation faithfully execute the proposal?
      Q3: Is the diagnostic favorable enough to justify continuing iteration,
          or should we rollback (the round made things worse)?
      Q4: Are we close enough to termination (§4.6) to stop, or do we iterate
          again? If iterate, what should the next round focus on?

  Step 7 — DECIDE
    If Codex says "terminate" AND termination criteria pass → exit loop with success.
    If Codex says "rollback" → restore pipeline/ to start-of-round state, log lesson learned, continue.
    Otherwise → proceed to round N+1.

  Step 8 — COMMIT
    git add -A
    git commit -m "round N: <one-line summary of what happened>"
```

### 4.4 Round 0 (Bootstrap)

Round 0 builds a minimal-but-runnable Pipeline skeleton:

- Candidate universe = a small starter set (e.g., Open Targets top 200 for obesity)
- 3 starter dimensions (e.g., genetic causal, weight-loss efficacy, safety)
- Trivial reviewer ensemble (one stub per persona)
- Anti-bias checks present but possibly underpowered

The goal of Round 0 is not to find GDF15 — it is to make sure the Pipeline runs end-to-end so subsequent rounds can iterate.

### 4.5 Forbidden Changes (boundary-test enforcement)

Codex review must reject any change matching these patterns:

- Adding a dimension where only GDF15 has data
- Removing a dimension where GDF15 underperforms
- Re-weighting dimensions to push GDF15 up
- Restricting the candidate universe in a way that disproportionately removes GDF15's competitors
- Hard-coding GDF15-related identifiers in any non-evaluator code
- Cherry-picking data sources that uniquely favor GDF15

When uncertain, Codex applies the test: *"If this change happened to hurt GDF15, would I still endorse it as methodologically sound?"* If no → reject.

### 4.6 Termination Criteria (ALL must hold)

- **T1 — Output correctness.** GDF15 ranks in the Pipeline's top 5.
- **T2 — Anti-bias robustness.** All five anti-bias checks (§6) pass at their specified thresholds.
- **T3 — Negative controls.** Injected known-failed targets (rimonabant target CB1R, torcetrapib target CETP, etc.) rank in the bottom quartile.
- **T4 — Reviewer ensemble.** Meta-review yields no blocker-level critiques.
- **T5 — Reproducibility.** A single command runs the full Pipeline from scratch and reproduces the final output.
- **T6 — Methodology rigor.** Codex confirms across all rounds that no forbidden changes (§4.5) were merged.

If all six hold → terminate with success. Loop emits a final report (§4.8) and the user-readable README.

### 4.7 Budget and Failure Modes

- **MAX_ROUNDS.** Default 15.
- **MAX_WALLCLOCK.** Default 8 hours.
- **MAX_API_COST_PER_ROUND.** Soft cap; loop monitors estimated API spend.
- **Rate-limit handling.** If Codex / Gemini / Claude returns 429 or quota-exceeded, the loop pauses and writes a `RATE_LIMITED.md` file describing which API hit the limit and which environment variable (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) the user can set to switch to API billing. The loop does not silently fall back to a weaker model.
- **Convergence failure.** If 3 consecutive rounds yield no improvement on T1+T2+T3+T4, the loop halts with a `STUCK.md` describing what it tried and why no further progress seems possible.
- **Crashes.** Any uncaught exception during Pipeline execution → write `runs/round_N/crash.log`, treat as a failed round (counts toward budget), continue.

### 4.8 Final Output Artifacts (what user sees in the morning)

```
project-root/
├── draft.md                          # this document (immutable spec)
├── pipeline/                         # the final AI Discovery Pipeline
│   ├── README.md                     # how to run, what it does
│   ├── run_pipeline.sh               # single command to reproduce
│   ├── modules/                      # implementation
│   ├── data_sources/                 # cached data
│   └── ...
├── evaluator/
│   ├── expected_answer.json
│   └── evaluator.py
├── proposals/round_*.md              # what was proposed each round
├── runs/round_*/output.json          # what Pipeline produced each round
├── diagnostics/round_*.md            # Evaluator's report each round
├── reviews/round_*.md                # Codex's review each round
├── LOOP_SUMMARY.md                   # final summary: rounds run, what changed, outcome
└── FINAL_RESULT.md                   # user-readable final ranking + Section 1 figure sketches
```

---

## 5. Methodology Principles (HARD CONSTRAINTS, immutable across rounds)

### 5.1 Pre-Registration Commitments

1. **Pre-lock methodology transparency.** The Pipeline's methodology, data sources, scoring dimensions, and weights are version-controlled. Every round commits state to git with a structured message.
2. **Uniform application of changes.** Any data source or scoring change must be applied to all candidates. Documented in git history.
3. **Honest reporting.** Final results are reported as they are. If termination criteria are not met at MAX_ROUNDS, the loop reports best-effort state honestly without retuning to elevate any specific target.

### 5.2 Boundary Test (applied by Codex every round)

Every proposed change is tested: *"Would I make this change if it happened to hurt GDF15's rank?"* If the answer is no, the change is rejected.

### 5.3 Six-Persona Cell Reviewer Ensemble (Inner Pipeline component)

**Layer:** Inner Pipeline. The ensemble is part of the Pipeline's own scoring/reporting stack, not part of the outer Loop. The Loop reads the ensemble's verdict via the Pipeline's output JSON (`reviewer_ensemble_verdict`) and uses it as termination criterion T4.

**Function:** Scientific peer review of the candidate ranking. (Methodological integrity review of per-round proposed changes is a separate function performed by Codex in the outer Loop — see §4.3 Step 6 and §4.5.)

Each round, after the Pipeline runs, the reviewer ensemble is invoked. Each persona is a fixed prompt template (versioned in `pipeline/reviewers/`):

| Persona | Focus |
|---|---|
| R1 — Molecular biologist | Mechanistic depth, receptor pharmacology, in vitro consistency |
| R2 — Clinical translator | Human relevance, unmet need, comparison to SOC |
| R3 — Geneticist / biostatistician | GWAS/MR rigor, multiple testing, pleiotropy |
| R4 — Pharmacologist / drug developer | PK/PD, dose feasibility, competitive landscape |
| R5 — AI methods reviewer | Pipeline validity, ablation, reproducibility, fair baselines |
| R6 — Editor | Novelty, broader impact, Cell-fit |

Each persona produces a structured critique. A meta-review aggregates into a single verdict. Blocker-level critiques prevent termination (T4).

LLM backbone choice: at least two distinct models across the six personas (e.g., 3 personas via Gemini, 3 via Codex) to provide cross-model robustness.

---

## 6. Anti-Bias Mechanisms (must run every round; failures reported but non-blocking until terminate)

1. **Leave-one-dimension-out (LOO) ablation.** For each scoring dimension, recompute ranking with that dimension removed. GDF15 should remain in top 5 under every LOO. (Acceptance threshold: top 5 in all single-dim ablations.)
2. **Negative-control targets.** Injected known-failed metabolic targets (CB1R/rimonabant, CETP/torcetrapib, 5-HT2C/lorcaserin, DGAT1) must rank in the bottom quartile.
3. **Literature-blinded re-rank.** Any LLM-driven scoring is re-run with GDF15/GFRAL-related literature redacted from retrieval context. GDF15 should remain in top 25%.
4. **Cross-biobank replication.** Causal MR estimates for top candidates are computed independently in at least two biobanks (UKBB, FinnGen, BBJ). Sign-consistency is required.
5. **Permutation test.** Shuffle dimension scores across candidates 10,000 times. GDF15's observed rank must achieve empirical p < 0.001.

---

## 7. Validation Strategy

The unpublished wet-lab data on GDF15 + saRNA + sublingual microneedles is **not** used during Pipeline design or scoring. It serves as the external ground truth that defines the Evaluator's expected answer. The Pipeline operates exclusively on public data. This closed-loop story — AI prediction from public data → wet-lab confirmation from prior experiments — is the Cell paper's central narrative.

---

## 8. Reproducibility and Open Science

- All code in this single git repository.
- Methodology lock via git tag (e.g., `v1.0-methodology-locked`) at termination.
- Public data sources only.
- Containerized environment (Docker) with pinned dependencies in `pipeline/Dockerfile`.
- Single command (`./pipeline/run_pipeline.sh`) regenerates all results.
- All six reviewer transcripts saved verbatim.
- This document (the pre-registration document at lock time) deposited on OSF.

---

## 9. Out of Scope

- Drug design or molecular modeling for GDF15 itself (Cell paper Section 2+ covers the saRNA platform).
- Clinical trial design, health economics, commercial assessment.
- Adaptation to indications outside obesity + T2D + MASH (follow-up work).

---

## 10. Loop Termination Output: What the User Sees Tomorrow Morning

A single `FINAL_RESULT.md` summarizing:

- Whether termination was reached and at which round
- The final ranked top 25 candidates (or top 5 with full detail)
- Whether GDF15 is in the top 5 (and at what rank)
- Anti-bias check results
- Reviewer ensemble verdict + any remaining concerns
- The post-hoc platform-compatibility analysis for top 5
- A pointer to `pipeline/README.md` for how to re-run
- A draft of Cell paper Section 1 figure sketches (Fig 1: pipeline architecture; Fig 2: candidate universe; Fig 3: per-dim heatmap; Fig 4: composite ranking; Fig 5: anti-bias gauntlet; Fig 6: reviewer ensemble; Fig 7: post-hoc platform check)

If termination was not reached: a `STUCK.md` describing what is still failing and what the user should change in the spec or environment to unblock the loop.
