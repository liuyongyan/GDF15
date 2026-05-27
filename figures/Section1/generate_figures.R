#!/usr/bin/env Rscript
# Cell Section 1 figure generator (AC-12).
#
# Produces seven publication-grade figures as both PNG (>=300 dpi) and PDF in
# figures/Section1/output/, derived from runs/round_N/ artifacts:
#   Fig 1: pipeline architecture overview (target-blind DAG)
#   Fig 2: candidate universe summary
#   Fig 3: per-dim z-score heatmap (top 25)
#   Fig 4: composite ranking (top 25)
#   Fig 5: anti-bias gauntlet PASS/FAIL panel
#   Fig 6: reviewer ensemble (per-persona blocker counts + adjudication)
#   Fig 7: post-hoc platform compatibility funnel
#
# Usage:
#   Rscript figures/Section1/generate_figures.R [--round N]
#   --round  : numeric round directory under runs/. Default: latest numeric round_N.
#
# Behavior:
#   - At startup, verifies required R packages are installed. Missing -> exit non-zero
#     with "missing-package: <pkg>" on stderr.
#   - For each figure, if a required artifact is missing, emits a clear stderr
#     warning naming the artifact and figure, then SKIPS that figure (does not
#     produce a misleading placeholder plot).

# ---- Package check ----
required_packages <- c("ggplot2", "scales", "cowplot", "jsonlite", "dplyr", "tidyr")
missing_pkgs <- required_packages[!(required_packages %in% rownames(installed.packages()))]
if (length(missing_pkgs) > 0) {
  for (p in missing_pkgs) cat(sprintf("missing-package: %s\n", p), file = stderr())
  quit(status = 1)
}

suppressPackageStartupMessages({
  library(ggplot2)
  library(scales)
  library(cowplot)
  library(jsonlite)
  library(dplyr)
  library(tidyr)
})

# null-coalesce operator (base R doesn't have it; ggplot2/rlang would but importing rlang explicitly is unnecessary)
`%||%` <- function(a, b) if (is.null(a) || (length(a) == 1 && is.na(a))) b else a

# Script-path detection that works under Rscript invocation
script_path_args <- commandArgs(trailingOnly = FALSE)
file_arg <- script_path_args[grep("^--file=", script_path_args)]
if (length(file_arg) > 0) {
  script_path <- normalizePath(sub("^--file=", "", file_arg[1]), mustWork = FALSE)
  script_dir <- dirname(script_path)
} else {
  script_dir <- getwd()
}

# ---- CLI ----
args <- commandArgs(trailingOnly = TRUE)
round_n <- NULL
if (length(args) > 0) {
  for (i in seq_along(args)) {
    if (args[i] == "--round" && i < length(args)) {
      round_n <- as.integer(args[i + 1])
    }
  }
}

repo_root <- normalizePath(file.path(script_dir, "..", ".."), mustWork = FALSE)
# Fallback if running interactively without script path
if (!dir.exists(repo_root) || !file.exists(file.path(repo_root, "plan.md"))) {
  repo_root <- getwd()
}

if (is.null(round_n)) {
  runs_dir <- file.path(repo_root, "runs")
  if (!dir.exists(runs_dir)) {
    cat("ERROR: runs/ directory does not exist\n", file = stderr())
    quit(status = 1)
  }
  candidates <- list.files(runs_dir, pattern = "^round_[0-9]+$", full.names = FALSE)
  if (length(candidates) == 0) {
    cat("ERROR: no runs/round_N/ directories found\n", file = stderr())
    quit(status = 1)
  }
  round_n <- max(as.integer(sub("^round_", "", candidates)))
}

run_dir <- file.path(repo_root, "runs", sprintf("round_%d", round_n))
out_dir <- file.path(repo_root, "figures", "Section1", "output")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
cat(sprintf("generate_figures: round=%d  run_dir=%s  out_dir=%s\n", round_n, run_dir, out_dir))

# ---- Helpers ----
read_json_safe <- function(path) {
  if (!file.exists(path)) return(NULL)
  tryCatch(fromJSON(path, simplifyVector = FALSE), error = function(e) NULL)
}

read_tsv_safe <- function(path) {
  if (!file.exists(path)) return(NULL)
  tryCatch(read.delim(path, sep = "\t", header = TRUE, stringsAsFactors = FALSE),
           error = function(e) NULL)
}

warn_skip <- function(fig_id, artifact) {
  cat(sprintf("generate_figures: SKIP Fig %s — missing artifact: %s\n", fig_id, artifact),
      file = stderr())
}

# R2 fix: skip_fig also unlinks stale PNG/PDF so an old figure does not linger and mislead.
skip_fig <- function(fig_id, artifact, basename) {
  png_path <- file.path(out_dir, paste0(basename, ".png"))
  pdf_path <- file.path(out_dir, paste0(basename, ".pdf"))
  unlinked <- character()
  if (file.exists(png_path)) { unlink(png_path); unlinked <- c(unlinked, basename(png_path)) }
  if (file.exists(pdf_path)) { unlink(pdf_path); unlinked <- c(unlinked, basename(pdf_path)) }
  msg <- sprintf("generate_figures: SKIP Fig %s — missing artifact: %s", fig_id, artifact)
  if (length(unlinked) > 0) {
    msg <- paste0(msg, sprintf(" (removed stale: %s)", paste(unlinked, collapse = ", ")))
  }
  cat(msg, "\n", file = stderr())
}

save_fig <- function(plt, basename, w = 8, h = 6) {
  png_path <- file.path(out_dir, paste0(basename, ".png"))
  pdf_path <- file.path(out_dir, paste0(basename, ".pdf"))
  ggsave(png_path, plt, width = w, height = h, dpi = 300, units = "in")
  ggsave(pdf_path, plt, width = w, height = h, units = "in", device = "pdf")
  cat(sprintf("generate_figures: wrote %s + %s\n", basename(png_path), basename(pdf_path)))
}

# ---- Load shared artifacts ----
output_json <- read_json_safe(file.path(run_dir, "output.json"))
verdict <- read_json_safe(file.path(run_dir, "reviewer_ensemble_verdict.json"))
val_summary <- read_json_safe(file.path(run_dir, "anti_bias", "_validation_summary.json"))
platform_tsv <- read_tsv_safe(file.path(run_dir, "platform_compatibility_top25.tsv"))
# R3 fix: Fig 6 reads adjudications from run-local verdict ONLY (no sidecar JSON).

# ============================================================
# Fig 1 — Pipeline architecture overview (target-blind DAG)
# ============================================================
{
  steps <- data.frame(
    x = c(1, 2, 3, 4, 5, 6, 7),
    y = c(2, 2, 2, 2, 2, 2, 2),
    label = c("Input\nvalidate", "Universe\nbuild", "Per-dim\nscoring", "Anti-bias\ngauntlet",
              "Reviewer\nensemble", "Output\nassemble", "Walkthrough\n+ Figures"),
    phase = c("IO", "Build", "Score", "Audit", "Audit", "IO", "Report")
  )
  edges <- data.frame(x = 1:6, xend = 2:7, y = 2, yend = 2)
  phase_colors <- c(IO = "#9DB4C0", Build = "#5C6B73", Score = "#253237",
                     Audit = "#C2A878", Report = "#73937E")
  p1 <- ggplot() +
    geom_segment(data = edges, aes(x = x + 0.4, xend = xend - 0.4, y = y, yend = yend),
                 arrow = arrow(length = unit(0.15, "inches")), linewidth = 0.6,
                 color = "grey40") +
    geom_tile(data = steps, aes(x = x, y = y, fill = phase), width = 0.8, height = 0.8) +
    geom_text(data = steps, aes(x = x, y = y, label = label), size = 3.2, color = "white") +
    scale_fill_manual(values = phase_colors, name = "Phase") +
    coord_cartesian(xlim = c(0.5, 7.5), ylim = c(1, 3)) +
    labs(title = "Figure 1 | AI discovery pipeline architecture",
         subtitle = sprintf("Target-blind methodology pre-registered at v1.0-methodology-locked  |  Round %d", round_n)) +
    theme_void() +
    theme(plot.title = element_text(size = 14, face = "bold"),
          plot.subtitle = element_text(size = 10, color = "grey30"),
          legend.position = "bottom",
          plot.margin = margin(15, 15, 15, 15))
  save_fig(p1, "Fig1_architecture", w = 10, h = 4)
}

# ============================================================
# Fig 2 — Candidate universe summary
# ============================================================
if (is.null(output_json)) {
  skip_fig("2", file.path(run_dir, "output.json"), "Fig2_candidate_universe")
} else {
  n_total <- output_json$ranked_targets_full_count %||% length(output_json$ranked_targets)
  n_top25 <- min(25, length(output_json$ranked_targets))
  n_emitted <- length(output_json$ranked_targets)
  funnel <- data.frame(
    stage = factor(c("Universe", "Emitted top-N", "Reviewed top-25"),
                   levels = c("Universe", "Emitted top-N", "Reviewed top-25")),
    count = c(n_total, n_emitted, n_top25)
  )
  p2 <- ggplot(funnel, aes(x = stage, y = count, fill = stage)) +
    geom_col(width = 0.6) +
    geom_text(aes(label = comma(count)), vjust = -0.5, size = 4.5) +
    scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.15))) +
    scale_fill_manual(values = c("#253237", "#5C6B73", "#9DB4C0"), guide = "none") +
    labs(title = "Figure 2 | Candidate universe and surfacing funnel",
         subtitle = sprintf("Round %d: deterministic, target-blind universe construction", round_n),
         x = NULL, y = "Candidates") +
    theme_minimal(base_size = 12) +
    theme(plot.title = element_text(face = "bold"))
  save_fig(p2, "Fig2_candidate_universe", w = 8, h = 5)
}

# ============================================================
# Fig 3 — Per-dim z-score heatmap (top 25)
# ============================================================
if (is.null(output_json) || length(output_json$ranked_targets) == 0) {
  skip_fig("3", file.path(run_dir, "output.json"), "Fig3_per_dim_heatmap")
} else {
  ranked <- output_json$ranked_targets[seq_len(min(25, length(output_json$ranked_targets)))]
  heat_df <- do.call(rbind, lapply(ranked, function(r) {
    pds <- r$per_dimension_scores
    if (is.null(pds)) return(NULL)
    data.frame(
      candidate = sprintf("candidate_%03d", r$rank %||% 0),
      dim = names(pds),
      z = unlist(pds),
      stringsAsFactors = FALSE
    )
  }))
  if (!is.null(heat_df) && nrow(heat_df) > 0) {
    heat_df$candidate <- factor(heat_df$candidate, levels = rev(unique(heat_df$candidate)))
    p3 <- ggplot(heat_df, aes(x = dim, y = candidate, fill = z)) +
      geom_tile(color = "white", linewidth = 0.3) +
      geom_text(aes(label = sprintf("%+.1f", z)), size = 2.5) +
      scale_fill_gradient2(low = "#3F6E94", mid = "white", high = "#B4555A",
                          midpoint = 0, name = "z-score") +
      labs(title = "Figure 3 | Per-dimension z-scores, anonymized top-25",
           subtitle = sprintf("Round %d: candidate IDs are blinded; row=candidate, col=dimension", round_n),
           x = NULL, y = NULL) +
      theme_minimal(base_size = 10) +
      theme(axis.text.x = element_text(angle = 35, hjust = 1),
            plot.title = element_text(face = "bold"))
    save_fig(p3, "Fig3_per_dim_heatmap", w = 10, h = 8)
  } else {
    skip_fig("3", "per_dimension_scores not present in ranked_targets", "Fig3_per_dim_heatmap")
  }
}

# ============================================================
# Fig 4 — Composite ranking (top 25)
# ============================================================
if (is.null(output_json) || length(output_json$ranked_targets) == 0) {
  skip_fig("4", file.path(run_dir, "output.json"), "Fig4_composite_ranking")
} else {
  ranked <- output_json$ranked_targets[seq_len(min(25, length(output_json$ranked_targets)))]
  comp_df <- data.frame(
    candidate = sapply(ranked, function(r) sprintf("candidate_%03d", r$rank %||% 0)),
    composite = sapply(ranked, function(r) r$composite_score %||% NA_real_),
    stringsAsFactors = FALSE
  )
  comp_df$candidate <- factor(comp_df$candidate, levels = rev(comp_df$candidate))
  p4 <- ggplot(comp_df, aes(x = composite, y = candidate)) +
    geom_col(fill = "#253237", width = 0.7) +
    geom_text(aes(label = sprintf("%+.3f", composite)), hjust = -0.1, size = 3) +
    scale_x_continuous(expand = expansion(mult = c(0, 0.15))) +
    labs(title = "Figure 4 | Composite z-score ranking (anonymized top-25)",
         subtitle = sprintf("Round %d: equally-weighted sum across 7 ranking-contributing dimensions", round_n),
         x = "Composite z-score", y = NULL) +
    theme_minimal(base_size = 10) +
    theme(plot.title = element_text(face = "bold"))
  save_fig(p4, "Fig4_composite_ranking", w = 8, h = 9)
}

# ============================================================
# Fig 5 — Anti-bias gauntlet PASS/FAIL panel
# ============================================================
if (is.null(val_summary)) {
  skip_fig("5", file.path(run_dir, "anti_bias", "_validation_summary.json"), "Fig5_anti_bias_gauntlet")
} else {
  statuses <- val_summary$statuses
  ab_df <- do.call(rbind, lapply(statuses, function(s) {
    data.frame(
      mechanism = s$mechanism %||% "?",
      status = s$status %||% "?",
      severity = s$severity %||% "?",
      actual = suppressWarnings(as.numeric(s$actual %||% NA)),
      threshold = suppressWarnings(as.numeric(s$threshold %||% NA)),
      stringsAsFactors = FALSE
    )
  }))
  ab_df$status_color <- ifelse(ab_df$status == "PASS", "PASS",
                          ifelse(ab_df$status == "FAIL", "FAIL", "SKIPPED"))
  p5 <- ggplot(ab_df, aes(x = mechanism, fill = status_color)) +
    geom_bar(stat = "count", width = 0.6) +
    geom_text(aes(label = paste0(status,
                                  ifelse(!is.na(actual),
                                         sprintf("\nactual=%.3g", actual), ""))),
              y = 0.5, vjust = 0.5, size = 3) +
    scale_fill_manual(values = c(PASS = "#7BAE7F", FAIL = "#B4555A", SKIPPED = "#9DB4C0"),
                      name = NULL) +
    labs(title = "Figure 5 | Anti-bias gauntlet — 5 mechanism status panel",
         subtitle = sprintf("Round %d  |  Hard fail=%s  Soft fail=%s",
                            round_n,
                            val_summary$failed_hard_count %||% "?",
                            val_summary$failed_soft_count %||% "?"),
         x = NULL, y = NULL) +
    theme_minimal(base_size = 11) +
    theme(axis.text.x = element_text(angle = 35, hjust = 1),
          axis.text.y = element_blank(),
          plot.title = element_text(face = "bold"))
  save_fig(p5, "Fig5_anti_bias_gauntlet", w = 10, h = 5)
}

# ============================================================
# Fig 6 — Reviewer ensemble (per-persona blocker count + adjudication)
# ============================================================
if (is.null(verdict)) {
  skip_fig("6", file.path(run_dir, "reviewer_ensemble_verdict.json"), "Fig6_reviewer_ensemble")
} else {
  per <- verdict$per_persona
  rev_df <- do.call(rbind, lapply(names(per), function(p) {
    body <- per[[p]]
    if (!is.list(body)) return(NULL)
    data.frame(
      persona = p,
      backbone = body$backbone_used %||% "?",
      blockers_count = as.integer(body$blockers_count %||% 0),
      stringsAsFactors = FALSE
    )
  }))
  propagated <- length(verdict$blockers_remaining %||% list())
  # R3 fix: Fig 6 counts adjudications from the run-local verdict only.
  # Unique by non-empty adjudication_id to avoid double-counting if multiple
  # canonical entries happen to bind to the same propagated blocker.
  v_adj <- verdict$meta_review$adjudications %||% list()
  v_adj_ids <- unique(unlist(lapply(v_adj, function(a) {
    if (is.list(a) && !is.null(a$adjudication_id) && nzchar(a$adjudication_id)) a$adjudication_id else NULL
  })))
  n_adj_total <- length(v_adj_ids)
  p6 <- ggplot(rev_df, aes(x = persona, y = blockers_count, fill = backbone)) +
    geom_col(width = 0.6) +
    geom_text(aes(label = blockers_count), vjust = -0.3, size = 4) +
    scale_fill_manual(values = c(codex = "#5C6B73", gemini = "#C2A878", cache = "#9DB4C0",
                                  unknown = "grey50", `?` = "grey50"),
                      name = "Backbone") +
    scale_y_continuous(expand = expansion(mult = c(0, 0.2))) +
    labs(title = "Figure 6 | Reviewer ensemble — per-persona blocker counts",
         subtitle = sprintf("Round %d  |  Status: %s  |  Propagated blockers: %d  |  Adjudications on file: %d",
                            round_n,
                            verdict$status %||% "?",
                            propagated,
                            n_adj_total),
         x = NULL, y = "Parsed blockers_count") +
    theme_minimal(base_size = 11) +
    theme(axis.text.x = element_text(angle = 25, hjust = 1),
          plot.title = element_text(face = "bold"))
  save_fig(p6, "Fig6_reviewer_ensemble", w = 10, h = 6)
}

# ============================================================
# Fig 7 — Post-hoc platform compatibility funnel
# ============================================================
if (is.null(platform_tsv)) {
  skip_fig("7", file.path(run_dir, "platform_compatibility_top25.tsv"), "Fig7_post_hoc_platform")
} else {
  # Expect columns: rank, candidate, ..., compatibility status
  status_col <- NULL
  for (c in c("compatibility", "status", "platform_status", "pass")) {
    if (c %in% colnames(platform_tsv)) { status_col <- c; break }
  }
  if (is.null(status_col)) {
    # Fallback: take the last column as status
    status_col <- tail(colnames(platform_tsv), 1)
  }
  pf_df <- data.frame(
    status = as.character(platform_tsv[[status_col]]),
    stringsAsFactors = FALSE
  )
  pf_summary <- as.data.frame(table(pf_df$status), stringsAsFactors = FALSE)
  colnames(pf_summary) <- c("status", "count")
  p7 <- ggplot(pf_summary, aes(x = status, y = count, fill = status)) +
    geom_col(width = 0.6) +
    geom_text(aes(label = count), vjust = -0.3, size = 4) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.2))) +
    scale_fill_brewer(palette = "Set2", guide = "none") +
    labs(title = "Figure 7 | Post-hoc platform compatibility, top-25",
         subtitle = sprintf("Round %d  |  D8 platform deliverability excluded from composite; checked post-hoc", round_n),
         x = NULL, y = "Candidates") +
    theme_minimal(base_size = 11) +
    theme(plot.title = element_text(face = "bold"))
  save_fig(p7, "Fig7_post_hoc_platform", w = 8, h = 5)
}

cat("generate_figures: DONE\n")
