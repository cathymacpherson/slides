# Rebuilds the slide 8 and 9 figures in the same style as the slide 7 CRQA plot.
# Data: "final datasets/study2" from https://osf.io/3a59k (Macpherson et al., 2026).
# Requires ggplot2 and glmmTMB.
#
# Usage: Rscript scripts/make_plots.R "<path>/final datasets/study2" <output dir>
# Then copy the three PNGs into ../assets/.

if (nzchar(Sys.getenv("RLIB"))) .libPaths(c(Sys.getenv("RLIB"), .libPaths()))
suppressPackageStartupMessages({ library(ggplot2); library(glmmTMB) })
args <- commandArgs(trailingOnly = TRUE)
data_dir <- args[1]; out_dir <- args[2]

# Slide 7 house style
cond_levels <- c("Office", "Cafe", "Food", "Party")
cond_labels <- c("Office", "Café", "Food court", "Party")
cond_cols <- c(Office = "#d7e4ee", Cafe = "#98bad2", Food = "#4b79a4", Party = "#2a4e6e")
err_col <- "#424242"
noise_db <- c(Office = 60, Cafe = 70, Food = 80, Party = 87.5)
font <- "Times New Roman"

theme_slide <- function() {
  theme_classic(base_size = 22, base_family = font) +
    theme(
      axis.line = element_line(linewidth = 1.6, colour = "black", lineend = "square"),
      axis.ticks = element_line(linewidth = 1.6, colour = "black"),
      axis.ticks.length = unit(7, "pt"),
      axis.text = element_text(colour = "black", size = 20),
      axis.title = element_text(colour = "black", size = 24),
      axis.title.y = element_text(margin = margin(r = 12)),
      axis.title.x = element_text(margin = margin(t = 12)),
      legend.position = "bottom",
      legend.title = element_blank(),
      legend.text = element_text(size = 20, margin = margin(l = 6, r = 26)),
      legend.key.width = unit(34, "pt"),
      legend.key.height = unit(16, "pt"),
      plot.margin = margin(14, 18, 10, 10),
      plot.background = element_rect(fill = "transparent", colour = NA),
      panel.background = element_rect(fill = "transparent", colour = NA),
      legend.background = element_rect(fill = "transparent", colour = NA),
      legend.key = element_rect(fill = "transparent", colour = NA)
    )
}
save_png <- function(p, file, w, h) {
  png(file.path(out_dir, file), width = w, height = h, units = "in", res = 300, type = "quartz", bg = "transparent")
  print(p); invisible(dev.off())
}
sem <- function(x) sd(x) / sqrt(length(x))

dfa <- read.csv(file.path(data_dir, "study2_dfa_models.csv"))
cc <- read.csv(file.path(data_dir, "study2_cc_models.csv"))

# Per participant x trial means
ind <- aggregate(cbind(alpha = head_mag_alpha, oirs) ~ pair + role + trial + environment, dfa, mean)
ind$environment <- factor(ind$environment, levels = cond_levels)

# ---- Slide 8a: alpha by noise condition (participant-level means +/- SEM) ----
pp <- aggregate(alpha ~ pair + role + environment, ind, mean)
a_sum <- do.call(rbind, lapply(split(pp, pp$environment), function(d)
  data.frame(environment = d$environment[1], mean = mean(d$alpha), se = sem(d$alpha))))
a_sum$environment <- factor(a_sum$environment, levels = cond_levels)
p_alpha <- ggplot(a_sum, aes(environment, mean)) +
  geom_errorbar(aes(ymin = mean - se, ymax = mean + se), width = 0.16, linewidth = 1.4, colour = err_col) +
  geom_point(aes(fill = environment), shape = 21, size = 9, stroke = 1.6, colour = "black") +
  scale_fill_manual(values = cond_cols, labels = cond_labels) +
  scale_x_discrete(labels = NULL) +
  scale_y_continuous(limits = c(0.93, 1.02), breaks = seq(0.93, 1.02, 0.03),
                     labels = function(x) sprintf("%.2f", x), expand = c(0, 0)) +
  labs(x = NULL, y = expression("Movement structure (" * alpha * ")")) +
  guides(fill = guide_legend(nrow = 2, override.aes = list(size = 7))) +
  theme_slide() + theme(axis.ticks.x = element_line(linewidth = 1.6))
save_png(p_alpha, "noise-alpha-results.png", 5.6, 6.0)

# ---- Slide 8b: complexity matching, real vs pseudo (pair-level means +/- SEM) ----
pr <- aggregate(alpha_corr_z ~ pair + pair_type, cc, mean)
cm_sum <- do.call(rbind, lapply(split(pr, pr$pair_type), function(d)
  data.frame(pair_type = d$pair_type[1], mean = mean(d$alpha_corr_z), se = sem(d$alpha_corr_z))))
cm_sum$pair_type <- factor(cm_sum$pair_type, levels = c("pseudo", "actual"), labels = c("Pseudo pairs", "Real pairs"))
p_cm <- ggplot(cm_sum, aes(pair_type, mean, fill = pair_type)) +
  geom_col(width = 0.8, colour = "black", linewidth = 1.6) +
  geom_errorbar(aes(ymin = mean - se, ymax = mean + se), width = 0.16, linewidth = 1.4, colour = err_col) +
  scale_fill_manual(values = c("Pseudo pairs" = "#e4e4e2", "Real pairs" = unname(cond_cols["Party"]))) +
  scale_y_continuous(limits = c(0, 0.08), breaks = seq(0, 0.08, 0.02),
                     labels = function(x) sprintf("%.2f", x), expand = c(0, 0)) +
  scale_x_discrete(labels = NULL) +
  labs(x = NULL, y = "Complexity matching (Fisher z)") +
  guides(fill = guide_legend(nrow = 2)) +
  theme_slide()
save_png(p_cm, "noise-complexity-matching.png", 5.6, 6.0)

# ---- Slide 9: repairs by alpha (same aggregation and model as the paper's R_MEMs.ipynb) ----
ob <- aggregate(head_mag_alpha ~ pair + role + environment + oirs, dfa, mean)
names(ob)[names(ob) == "head_mag_alpha"] <- "alpha"
ob$environment <- factor(ob$environment, levels = cond_levels)
ob$noise_c <- noise_db[as.character(ob$environment)] - mean(noise_db[as.character(ob$environment)])
ob$alpha_c <- ob$alpha - mean(ob$alpha)
ob$pair <- factor(ob$pair)
m <- glmmTMB(oirs ~ alpha_c * noise_c + (1 + alpha_c | pair), family = nbinom2, data = ob)
cat("alpha coefficient (paper b = 3.748):\n"); print(summary(m)$coefficients$cond)
grid <- data.frame(alpha = seq(min(ob$alpha), max(ob$alpha), length.out = 200))
grid$alpha_c <- grid$alpha - mean(ob$alpha); grid$noise_c <- 0
X <- model.matrix(~ alpha_c * noise_c, grid)
eta <- drop(X %*% fixef(m)$cond); se_eta <- sqrt(rowSums((X %*% vcov(m)$cond) * X))
grid$fit <- exp(eta); grid$lo <- exp(eta - 1.96 * se_eta); grid$hi <- exp(eta + 1.96 * se_eta)
ind <- ob
cap <- 15
ind$oirs_plot <- pmin(ind$oirs, cap)
p_oir <- ggplot() +
  geom_point(data = ind, aes(alpha, oirs_plot, fill = environment), shape = 21, size = 3.4,
             stroke = 0.5, colour = "black", alpha = 0.75,
             position = position_jitter(width = 0, height = 0.15, seed = 1)) +
  geom_ribbon(data = grid, aes(alpha, ymin = lo, ymax = hi), fill = "#2a4e6e", alpha = 0.18) +
  geom_line(data = grid, aes(alpha, fit), colour = "black", linewidth = 2) +
  scale_fill_manual(values = cond_cols, labels = cond_labels) +
  scale_y_continuous(limits = c(-0.4, cap + 0.6), breaks = c(0, 5, 10, 15),
                     labels = c("0", "5", "10", ">15"), expand = c(0, 0)) +
  scale_x_continuous(breaks = seq(0.7, 1.4, 0.1)) +
  labs(x = expression("Movement structure (" * alpha * ")"), y = "Repair requests") +
  guides(fill = guide_legend(nrow = 1, override.aes = list(size = 6, alpha = 1))) +
  theme_slide() +
  theme(
    axis.text = element_text(size = 16),
    axis.title = element_text(size = 19),
    legend.text = element_text(size = 16, margin = margin(l = 5, r = 20))
  )
save_png(p_oir, "noise-alpha-repairs.png", 8.0, 6.2)
