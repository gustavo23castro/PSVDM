"""
analyze.py — Windows vs Linux benchmark analysis
FannkuchRedux + BinaryTrees · C# · Intel RAPL · HP EliteBook i7-8850H
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINUX_CSV      = os.path.join(REPO_ROOT, "results", "linux",   "energy", "energy_single.csv")
WINDOWS_CSV    = os.path.join(REPO_ROOT, "results", "windows", "energy", "energy_windows.csv")
BT_LINUX_CSV   = os.path.join(REPO_ROOT, "results", "linux",   "energy", "energy_bt.csv")
BT_WINDOWS_CSV = os.path.join(REPO_ROOT, "results", "windows", "energy", "energy_bt_windows.csv")
FIG_DIR        = os.path.join(REPO_ROOT, "analysis", "figures")
RES_DIR        = os.path.join(REPO_ROOT, "analysis", "results")

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Style / colours
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid")
COLORS  = {"linux": "#2196F3", "windows": "#FF5722"}
PALETTE = [COLORS["linux"], COLORS["windows"]]
DPI     = 300
ALPHA   = 0.05
N_PERM  = 10_000
np.random.seed(42)


# ---------------------------------------------------------------------------
# STEP 1 — Load and clean
# ---------------------------------------------------------------------------
print("Step 1/6: Loading data...")

linux_df      = pd.read_csv(LINUX_CSV)
windows_df    = pd.read_csv(WINDOWS_CSV)
bt_linux_df   = pd.read_csv(BT_LINUX_CSV)
bt_windows_df = pd.read_csv(BT_WINDOWS_CSV)

linux_df["algorithm"]      = "FannkuchRedux"
windows_df["algorithm"]    = "FannkuchRedux"
bt_linux_df["algorithm"]   = "BinaryTrees"
bt_windows_df["algorithm"] = "BinaryTrees"

df_raw = pd.concat([linux_df, windows_df, bt_linux_df, bt_windows_df], ignore_index=True)

# Joule conversion
df_raw["pkg_energy_j"]  = df_raw["pkg_energy_uj"]  / 1_000_000
df_raw["pp0_energy_j"]  = df_raw["pp0_energy_uj"]  / 1_000_000
df_raw["dram_energy_j"] = df_raw["dram_energy_uj"]  / 1_000_000

print(f"  Loaded {len(linux_df)} FR-Linux + {len(windows_df)} FR-Windows + "
      f"{len(bt_linux_df)} BT-Linux + {len(bt_windows_df)} BT-Windows = {len(df_raw)} total")
print(f"  OS values: {df_raw['os'].unique().tolist()}")
print(f"  Algorithms: {df_raw['algorithm'].unique().tolist()}")

# IQR outlier removal per (os × algorithm × n)
def remove_outliers_iqr(df, group_cols, metric_cols):
    mask = pd.Series(True, index=df.index)
    for keys, grp in df.groupby(group_cols):
        for col in metric_cols:
            q1 = grp[col].quantile(0.25)
            q3 = grp[col].quantile(0.75)
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outlier_idx = grp[(grp[col] < lo) | (grp[col] > hi)].index
            mask[outlier_idx] = False
    return mask

keep_mask = remove_outliers_iqr(
    df_raw, ["os", "algorithm", "n"],
    ["duration_ms", "pkg_energy_j", "dram_energy_j"]
)
df = df_raw[keep_mask].copy()
n_removed = len(df_raw) - len(df)
print(f"  Outlier removal (IQR 1.5×): removed {n_removed} rows ({n_removed/len(df_raw)*100:.1f}%)")
print(f"  Clean dataset: {len(df)} rows")

print(f"\n  {'OS':<10}  {'Algorithm':<14}  {'N':>3}  {'Count':>6}")
print(f"  {'-'*40}")
for (os_name, algo, n_val), grp in df.groupby(["os", "algorithm", "n"]):
    print(f"  {os_name:<10}  {algo:<14}  {n_val:>3}  {len(grp):>6}")

temp_available = not (df_raw["cpu_temp_before"] == -1.0).all()
if not temp_available:
    print("  NOTE: cpu_temp = -1.0 on Windows — temperature columns excluded from analysis")


# ---------------------------------------------------------------------------
# STEP 2 — Descriptive statistics
# ---------------------------------------------------------------------------
print("\nStep 2/6: Computing descriptive statistics...")

rows = []
for (os_name, algo, n_val), grp in df.groupby(["os", "algorithm", "n"]):
    ms   = grp["duration_ms"]
    ej   = grp["pkg_energy_j"]
    pp0  = grp["pp0_energy_j"]
    dram = grp["dram_energy_j"]
    q1, q3 = ms.quantile(0.25), ms.quantile(0.75)
    dram_ratio = (dram.mean() / ej.mean() * 100) if ej.mean() > 0 else 0
    rows.append({
        "os":               os_name,
        "algorithm":        algo,
        "n":                n_val,
        "count":            len(grp),
        "mean_ms":          ms.mean(),
        "median_ms":        ms.median(),
        "std_ms":           ms.std(),
        "cv_pct":           ms.std() / ms.mean() * 100,
        "min_ms":           ms.min(),
        "max_ms":           ms.max(),
        "q1_ms":            q1,
        "q3_ms":            q3,
        "iqr_ms":           q3 - q1,
        "mean_j":           ej.mean(),
        "median_j":         ej.median(),
        "std_j":            ej.std(),
        "mean_pp0_j":       pp0.mean(),
        "mean_dram_j":      dram.mean(),
        "std_dram_j":       dram.std(),
        "dram_pkg_ratio_pct": dram_ratio,
    })

stats_df = pd.DataFrame(rows)
stats_df.to_csv(os.path.join(RES_DIR, "statistics.csv"), index=False, float_format="%.4f")
print("  Saved statistics.csv")

print("\n  FannkuchRedux:")
fr_stats = stats_df[stats_df["algorithm"] == "FannkuchRedux"]
print(fr_stats[["os","n","count","mean_ms","std_ms","cv_pct","mean_j","mean_dram_j","dram_pkg_ratio_pct"]].to_string(index=False))

print("\n  BinaryTrees:")
bt_stats = stats_df[stats_df["algorithm"] == "BinaryTrees"]
print(bt_stats[["os","n","count","mean_ms","std_ms","cv_pct","mean_j","mean_dram_j","dram_pkg_ratio_pct"]].to_string(index=False))


# ---------------------------------------------------------------------------
# STEP 3 — Figures
# ---------------------------------------------------------------------------
print("\nStep 3/6: Generating figures...")

def savefig(name):
    path = os.path.join(FIG_DIR, name)
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved {name}")

fr = df[df["algorithm"] == "FannkuchRedux"]
bt = df[df["algorithm"] == "BinaryTrees"]

# --- Figure 1: Boxplot — FannkuchRedux execution time ---
fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=False)
fig.suptitle("FannkuchRedux — Execution Time: Linux vs Windows", fontsize=14, fontweight="bold")

for ax, n_val in zip(axes, [11, 12]):
    sub = fr[fr["n"] == n_val]
    sns.boxplot(data=sub, x="os", y="duration_ms", palette=COLORS, ax=ax,
                order=["linux", "windows"], width=0.5, linewidth=1.5)
    sns.stripplot(data=sub, x="os", y="duration_ms", palette=COLORS, ax=ax,
                  order=["linux", "windows"], size=4, alpha=0.6, jitter=True)
    ax.set_title(f"N = {n_val}", fontsize=13)
    ax.set_xlabel("Operating System")
    ax.set_ylabel("Execution Time (ms)")
    ax.set_xticklabels(["Linux", "Windows"])

plt.tight_layout()
savefig("01_boxplot_time.png")

# --- Figure 2: Boxplot — FannkuchRedux package energy ---
fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=False)
fig.suptitle("FannkuchRedux — Package Energy: Linux vs Windows", fontsize=14, fontweight="bold")

for ax, n_val in zip(axes, [11, 12]):
    sub = fr[fr["n"] == n_val]
    sns.boxplot(data=sub, x="os", y="pkg_energy_j", palette=COLORS, ax=ax,
                order=["linux", "windows"], width=0.5, linewidth=1.5)
    sns.stripplot(data=sub, x="os", y="pkg_energy_j", palette=COLORS, ax=ax,
                  order=["linux", "windows"], size=4, alpha=0.6, jitter=True)
    ax.set_title(f"N = {n_val}", fontsize=13)
    ax.set_xlabel("Operating System")
    ax.set_ylabel("Package Energy (J)")
    ax.set_xticklabels(["Linux", "Windows"])

plt.tight_layout()
savefig("02_boxplot_energy.png")

# --- Figure 3: Histogram + KDE — FannkuchRedux execution time ---
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle("FannkuchRedux — Execution Time Distribution", fontsize=14, fontweight="bold")

for idx, (os_name, n_val) in enumerate([("linux", 11), ("linux", 12), ("windows", 11), ("windows", 12)]):
    ax = axes[idx // 2][idx % 2]
    sub = fr[(fr["os"] == os_name) & (fr["n"] == n_val)]["duration_ms"]
    sns.histplot(sub, kde=True, color=COLORS[os_name], ax=ax, bins=10, alpha=0.7)
    ax.set_title(f"{os_name.capitalize()} — N={n_val}  (n={len(sub)})", fontsize=12)
    ax.set_xlabel("Execution Time (ms)")
    ax.set_ylabel("Count")
    ax.axvline(sub.mean(), color="black", linestyle="--", linewidth=1.2, label=f"Mean {sub.mean():.1f} ms")
    ax.legend(fontsize=9)

plt.tight_layout()
savefig("03_histogram_time.png")

# --- Figure 4: Histogram + KDE — FannkuchRedux package energy ---
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle("FannkuchRedux — Package Energy Distribution", fontsize=14, fontweight="bold")

for idx, (os_name, n_val) in enumerate([("linux", 11), ("linux", 12), ("windows", 11), ("windows", 12)]):
    ax = axes[idx // 2][idx % 2]
    sub = fr[(fr["os"] == os_name) & (fr["n"] == n_val)]["pkg_energy_j"]
    sns.histplot(sub, kde=True, color=COLORS[os_name], ax=ax, bins=10, alpha=0.7)
    ax.set_title(f"{os_name.capitalize()} — N={n_val}  (n={len(sub)})", fontsize=12)
    ax.set_xlabel("Package Energy (J)")
    ax.set_ylabel("Count")
    ax.axvline(sub.mean(), color="black", linestyle="--", linewidth=1.2, label=f"Mean {sub.mean():.3f} J")
    ax.legend(fontsize=9)

plt.tight_layout()
savefig("04_histogram_energy.png")

# --- Figure 5: Correlation — FannkuchRedux time vs energy ---
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.suptitle("FannkuchRedux — Execution Time vs Package Energy", fontsize=14, fontweight="bold")

for ax, n_val in zip(axes, [11, 12]):
    for os_name in ["linux", "windows"]:
        sub = fr[(fr["os"] == os_name) & (fr["n"] == n_val)]
        ax.scatter(sub["duration_ms"], sub["pkg_energy_j"],
                   color=COLORS[os_name], alpha=0.7, label=os_name.capitalize(), s=40)

    sub_n = fr[fr["n"] == n_val]
    rho, pval = stats.spearmanr(sub_n["duration_ms"], sub_n["pkg_energy_j"])
    sig_str = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
    ax.text(0.05, 0.95, f"Spearman ρ = {rho:.3f}\np = {pval:.2e} {sig_str}",
            transform=ax.transAxes, fontsize=10, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    ax.set_title(f"N = {n_val}", fontsize=13)
    ax.set_xlabel("Execution Time (ms)")
    ax.set_ylabel("Package Energy (J)")
    ax.legend()

plt.tight_layout()
savefig("05_correlation.png")

# --- Figure 6: Summary bar chart — FannkuchRedux with 95% CI ---
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.suptitle("FannkuchRedux — Mean Execution Time and Energy (95% CI)", fontsize=14, fontweight="bold")

groups_fr  = [("Linux", "linux", 11), ("Windows", "windows", 11),
              ("Linux", "linux", 12), ("Windows", "windows", 12)]
labels_fr  = [f"{lbl}\nN={n}" for lbl, _, n in groups_fr]
x_pos      = np.arange(len(groups_fr))
bar_colors = [COLORS[os] for _, os, _ in groups_fr]

for ax_idx, (metric, ylabel, title) in enumerate([
        ("duration_ms",  "Execution Time (ms)",  "Execution Time"),
        ("pkg_energy_j", "Package Energy (J)",    "Package Energy"),
]):
    ax = axes[ax_idx]
    means, ci_lows, ci_highs = [], [], []
    for _, os_name, n_val in groups_fr:
        sub = fr[(fr["os"] == os_name) & (fr["n"] == n_val)][metric]
        m   = sub.mean()
        ci  = stats.t.interval(0.95, df=len(sub) - 1, loc=m, scale=stats.sem(sub))
        means.append(m)
        ci_lows.append(m - ci[0])
        ci_highs.append(ci[1] - m)

    bars = ax.bar(x_pos, means, color=bar_colors, alpha=0.85,
                  yerr=[ci_lows, ci_highs], capsize=5, error_kw={"linewidth": 1.5})
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels_fr, fontsize=10)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=13)

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                f"{mean:.1f}", ha="center", va="bottom", fontsize=9)

    patches = [mpatches.Patch(color=COLORS["linux"],   label="Linux"),
               mpatches.Patch(color=COLORS["windows"], label="Windows")]
    ax.legend(handles=patches)

plt.tight_layout()
savefig("06_summary_bar.png")

# --- Figure 7: Boxplot — BinaryTrees execution time ---
bt_n_vals = sorted(bt["n"].unique())
fig, axes = plt.subplots(1, len(bt_n_vals), figsize=(6 * len(bt_n_vals), 6), sharey=False)
if len(bt_n_vals) == 1:
    axes = [axes]
fig.suptitle("BinaryTrees — Execution Time: Linux vs Windows", fontsize=14, fontweight="bold")

for ax, n_val in zip(axes, bt_n_vals):
    sub = bt[bt["n"] == n_val]
    sns.boxplot(data=sub, x="os", y="duration_ms", palette=COLORS, ax=ax,
                order=["linux", "windows"], width=0.5, linewidth=1.5)
    sns.stripplot(data=sub, x="os", y="duration_ms", palette=COLORS, ax=ax,
                  order=["linux", "windows"], size=4, alpha=0.6, jitter=True)
    ax.set_title(f"N = {n_val}", fontsize=13)
    ax.set_xlabel("Operating System")
    ax.set_ylabel("Execution Time (ms)")
    ax.set_xticklabels(["Linux", "Windows"])

plt.tight_layout()
savefig("07_bt_boxplot_time.png")

# --- Figure 8: Boxplot — BinaryTrees package energy ---
fig, axes = plt.subplots(1, len(bt_n_vals), figsize=(6 * len(bt_n_vals), 6), sharey=False)
if len(bt_n_vals) == 1:
    axes = [axes]
fig.suptitle("BinaryTrees — Package Energy: Linux vs Windows", fontsize=14, fontweight="bold")

for ax, n_val in zip(axes, bt_n_vals):
    sub = bt[bt["n"] == n_val]
    sns.boxplot(data=sub, x="os", y="pkg_energy_j", palette=COLORS, ax=ax,
                order=["linux", "windows"], width=0.5, linewidth=1.5)
    sns.stripplot(data=sub, x="os", y="pkg_energy_j", palette=COLORS, ax=ax,
                  order=["linux", "windows"], size=4, alpha=0.6, jitter=True)
    ax.set_title(f"N = {n_val}", fontsize=13)
    ax.set_xlabel("Operating System")
    ax.set_ylabel("Package Energy (J)")
    ax.set_xticklabels(["Linux", "Windows"])

plt.tight_layout()
savefig("08_bt_boxplot_energy.png")

# --- Figure 9: DRAM ratio comparison ---
fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle("DRAM Energy as % of Package — CPU-bound vs GC-bound",
             fontsize=14, fontweight="bold")

dram_groups = [
    ("FannkuchRedux\nLinux",   "FannkuchRedux", "linux"),
    ("FannkuchRedux\nWindows", "FannkuchRedux", "windows"),
    ("BinaryTrees\nLinux",     "BinaryTrees",   "linux"),
    ("BinaryTrees\nWindows",   "BinaryTrees",   "windows"),
]
dram_colors = [COLORS["linux"], COLORS["windows"], COLORS["linux"], COLORS["windows"]]
dram_vals   = []
for _, algo, os_name in dram_groups:
    rows_sel = stats_df[(stats_df["algorithm"] == algo) & (stats_df["os"] == os_name)]
    dram_vals.append(rows_sel["dram_pkg_ratio_pct"].mean())

x_d = np.arange(len(dram_groups))
bars = ax.bar(x_d, dram_vals, color=dram_colors, alpha=0.85, width=0.5)
ax.set_xticks(x_d)
ax.set_xticklabels([g[0] for g in dram_groups], fontsize=11)
ax.set_ylabel("DRAM Energy / Package Energy (%)")
ax.set_xlabel("Algorithm & OS")

for bar, val in zip(bars, dram_vals):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

# Hatching to distinguish FR vs BT
for bar in bars[:2]:
    bar.set_hatch("//")
patches = [
    mpatches.Patch(facecolor=COLORS["linux"],   label="Linux"),
    mpatches.Patch(facecolor=COLORS["windows"], label="Windows"),
    mpatches.Patch(facecolor="white", edgecolor="black", hatch="//", label="FannkuchRedux"),
    mpatches.Patch(facecolor="white", edgecolor="black", label="BinaryTrees"),
]
ax.legend(handles=patches, loc="upper left")
plt.tight_layout()
savefig("09_dram_comparison.png")

# --- Figure 10: 2×2 algorithm comparison ---
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Algorithm Comparison — Linux vs Windows (Mean ± 95% CI)",
             fontsize=15, fontweight="bold")

panel_cfg = [
    (axes[0][0], fr,  "duration_ms",  "Execution Time (ms)",  "FannkuchRedux — Time",  [11, 12]),
    (axes[0][1], bt,  "duration_ms",  "Execution Time (ms)",  "BinaryTrees — Time",    bt_n_vals),
    (axes[1][0], fr,  "pkg_energy_j", "Package Energy (J)",   "FannkuchRedux — Energy",[11, 12]),
    (axes[1][1], bt,  "pkg_energy_j", "Package Energy (J)",   "BinaryTrees — Energy",  bt_n_vals),
]

for ax, subset, metric, ylabel, title, n_vals in panel_cfg:
    for os_name, color in COLORS.items():
        means, ci_lo, ci_hi, xs = [], [], [], []
        for n_val in n_vals:
            sub = subset[(subset["os"] == os_name) & (subset["n"] == n_val)][metric]
            if len(sub) < 2:
                continue
            m   = sub.mean()
            ci  = stats.t.interval(0.95, df=len(sub) - 1, loc=m, scale=stats.sem(sub))
            means.append(m)
            ci_lo.append(m - ci[0])
            ci_hi.append(ci[1] - m)
            xs.append(n_val)

        ax.errorbar(xs, means,
                    yerr=[ci_lo, ci_hi],
                    marker="o", linewidth=2, markersize=7,
                    color=color, label=os_name.capitalize(),
                    capsize=5, capthick=1.5)

    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("N")
    ax.set_ylabel(ylabel)
    ax.set_xticks(n_vals)
    ax.legend()

plt.tight_layout()
savefig("10_algorithm_comparison.png")


# ---------------------------------------------------------------------------
# STEP 4 — Hypothesis tests
# ---------------------------------------------------------------------------
print("\nStep 4/6: Running hypothesis tests...")

def permutation_test(a, b, n_perm=N_PERM, alternative="two-sided"):
    obs = np.mean(a) - np.mean(b)
    combined = np.concatenate([a, b])
    n_a = len(a)
    count = 0
    for _ in range(n_perm):
        np.random.shuffle(combined)
        diff = np.mean(combined[:n_a]) - np.mean(combined[n_a:])
        if alternative == "two-sided":
            if abs(diff) >= abs(obs):
                count += 1
        elif alternative == "less":
            if diff <= obs:
                count += 1
        elif alternative == "greater":
            if diff >= obs:
                count += 1
    return obs, count / n_perm

test_rows = []

algo_n_map = {
    "FannkuchRedux": [11, 12],
    "BinaryTrees":   bt_n_vals,
}

for algo, n_vals in algo_n_map.items():
    subset = df[df["algorithm"] == algo]
    for n_val in n_vals:
        linux_ms   = subset[(subset["os"] == "linux")   & (subset["n"] == n_val)]["duration_ms"].values
        win_ms     = subset[(subset["os"] == "windows") & (subset["n"] == n_val)]["duration_ms"].values
        linux_ej   = subset[(subset["os"] == "linux")   & (subset["n"] == n_val)]["pkg_energy_j"].values
        win_ej     = subset[(subset["os"] == "windows") & (subset["n"] == n_val)]["pkg_energy_j"].values
        linux_dram = subset[(subset["os"] == "linux")   & (subset["n"] == n_val)]["dram_energy_j"].values
        win_dram   = subset[(subset["os"] == "windows") & (subset["n"] == n_val)]["dram_energy_j"].values

        base = {"algorithm": algo, "n": n_val}

        # Mann-Whitney — duration_ms two-sided
        U, p = stats.mannwhitneyu(linux_ms, win_ms, alternative="two-sided")
        test_rows.append({**base, "metric": "duration_ms", "test": "Mann-Whitney U",
            "statistic": U, "pvalue": p, "significant": p < ALPHA,
            "alternative": "two-sided (Linux ≠ Windows)",
            "interpretation": ("Linux é significativamente diferente de Windows em tempo"
                               if p < ALPHA else "Sem diferença significativa em tempo")})

        # Mann-Whitney — duration_ms one-sided (Linux > Windows)
        U, p = stats.mannwhitneyu(linux_ms, win_ms, alternative="greater")
        test_rows.append({**base, "metric": "duration_ms", "test": "Mann-Whitney U",
            "statistic": U, "pvalue": p, "significant": p < ALPHA,
            "alternative": "one-sided (Linux > Windows, Linux é mais lento)",
            "interpretation": ("Linux é significativamente mais lento que Windows"
                               if p < ALPHA else "Linux não é significativamente mais lento")})

        # Mann-Whitney — pkg_energy_j one-sided (Linux < Windows)
        U, p = stats.mannwhitneyu(linux_ej, win_ej, alternative="less")
        test_rows.append({**base, "metric": "pkg_energy_j", "test": "Mann-Whitney U",
            "statistic": U, "pvalue": p, "significant": p < ALPHA,
            "alternative": "one-sided (Linux < Windows, Linux consome menos)",
            "interpretation": ("Linux consome significativamente menos energia que Windows"
                               if p < ALPHA else "Sem diferença significativa em energia")})

        # Mann-Whitney — dram_energy_j two-sided
        U, p = stats.mannwhitneyu(linux_dram, win_dram, alternative="two-sided")
        test_rows.append({**base, "metric": "dram_energy_j", "test": "Mann-Whitney U",
            "statistic": U, "pvalue": p, "significant": p < ALPHA,
            "alternative": "two-sided (Linux ≠ Windows)",
            "interpretation": ("Diferença significativa em energia DRAM"
                               if p < ALPHA else "Sem diferença significativa em energia DRAM")})

        # Permutation — duration_ms two-sided
        obs, p_perm = permutation_test(linux_ms, win_ms, alternative="two-sided")
        test_rows.append({**base, "metric": "duration_ms", "test": f"Permutation A/B ({N_PERM} perms)",
            "statistic": obs, "pvalue": p_perm, "significant": p_perm < ALPHA,
            "alternative": "two-sided",
            "interpretation": (f"Diferença observada ({obs:.2f} ms) estatisticamente significativa"
                               if p_perm < ALPHA else f"Diferença ({obs:.2f} ms) não significativa")})

        # Permutation — pkg_energy_j one-sided (Linux < Windows)
        obs_e, p_perm_e = permutation_test(linux_ej, win_ej, alternative="less")
        test_rows.append({**base, "metric": "pkg_energy_j", "test": f"Permutation A/B ({N_PERM} perms)",
            "statistic": obs_e, "pvalue": p_perm_e, "significant": p_perm_e < ALPHA,
            "alternative": "one-sided (Linux < Windows)",
            "interpretation": (f"Linux usa {abs(obs_e):.3f} J menos que Windows (significativo)"
                               if p_perm_e < ALPHA else f"Diferença de energia ({obs_e:.3f} J) não significativa")})

        # Permutation — dram_energy_j two-sided
        obs_d, p_perm_d = permutation_test(linux_dram, win_dram, alternative="two-sided")
        test_rows.append({**base, "metric": "dram_energy_j", "test": f"Permutation A/B ({N_PERM} perms)",
            "statistic": obs_d, "pvalue": p_perm_d, "significant": p_perm_d < ALPHA,
            "alternative": "two-sided",
            "interpretation": (f"Diferença DRAM ({obs_d:.4f} J) estatisticamente significativa"
                               if p_perm_d < ALPHA else f"Diferença DRAM ({obs_d:.4f} J) não significativa")})

# Spearman correlations — per algorithm
for algo in ["FannkuchRedux", "BinaryTrees"]:
    sub_algo = df[df["algorithm"] == algo]
    rho_all, p_all = stats.spearmanr(sub_algo["duration_ms"], sub_algo["pkg_energy_j"])
    test_rows.append({
        "algorithm": algo, "n": "all", "metric": "duration_ms vs pkg_energy_j",
        "test": f"Spearman correlation ({algo})",
        "statistic": rho_all, "pvalue": p_all, "significant": p_all < ALPHA,
        "alternative": "two-sided",
        "interpretation": f"ρ = {rho_all:.3f} — correlação {'significativa' if p_all < ALPHA else 'não significativa'}",
    })
    for os_name in ["linux", "windows"]:
        sub = sub_algo[sub_algo["os"] == os_name]
        rho, p = stats.spearmanr(sub["duration_ms"], sub["pkg_energy_j"])
        test_rows.append({
            "algorithm": algo, "n": "all", "metric": "duration_ms vs pkg_energy_j",
            "test": f"Spearman correlation ({algo} {os_name})",
            "statistic": rho, "pvalue": p, "significant": p < ALPHA,
            "alternative": "two-sided",
            "interpretation": f"ρ = {rho:.3f} — correlação {'significativa' if p < ALPHA else 'não significativa'} para {os_name}",
        })

tests_df = pd.DataFrame(test_rows)
tests_df.to_csv(os.path.join(RES_DIR, "hypothesis_tests.csv"), index=False, float_format="%.6f")
print("  Saved hypothesis_tests.csv")
print(tests_df[["algorithm","n","metric","test","statistic","pvalue","significant"]].to_string(index=False))


# ---------------------------------------------------------------------------
# STEP 5 — Confidence intervals
# ---------------------------------------------------------------------------
print("\nStep 5/6: Computing confidence intervals...")

ci_rows = []
for (os_name, algo, n_val), grp in df.groupby(["os", "algorithm", "n"]):
    for metric in ["duration_ms", "pkg_energy_j", "dram_energy_j"]:
        vals = grp[metric].values
        m    = vals.mean()
        ci   = stats.t.interval(0.95, df=len(vals) - 1, loc=m, scale=stats.sem(vals))
        margin = (ci[1] - ci[0]) / 2
        ci_rows.append({
            "os":         os_name,
            "algorithm":  algo,
            "n":          n_val,
            "metric":     metric,
            "mean":       m,
            "ci_lower":   ci[0],
            "ci_upper":   ci[1],
            "margin_abs": margin,
            "margin_pct": margin / m * 100,
        })

ci_df = pd.DataFrame(ci_rows)
ci_df.to_csv(os.path.join(RES_DIR, "confidence_intervals.csv"), index=False, float_format="%.6f")
print("  Saved confidence_intervals.csv")
print(ci_df.to_string(index=False))


# ---------------------------------------------------------------------------
# STEP 6 — Summary report
# ---------------------------------------------------------------------------
print("\nStep 6/6: Writing summary report...")

def get_stat(algo, os_name, n_val, col):
    row = stats_df[(stats_df["algorithm"] == algo) &
                   (stats_df["os"] == os_name) & (stats_df["n"] == n_val)]
    return row[col].values[0]

def get_ci(algo, os_name, n_val, metric, col):
    row = ci_df[(ci_df["algorithm"] == algo) & (ci_df["os"] == os_name) &
                (ci_df["n"] == n_val) & (ci_df["metric"] == metric)]
    return row[col].values[0]

def pval_str(p):
    if p < 0.001:
        return f"{p:.2e} (***)"
    elif p < 0.01:
        return f"{p:.4f} (**)"
    elif p < 0.05:
        return f"{p:.4f} (*)"
    else:
        return f"{p:.4f} (ns)"

def get_test_p(algo, n_val, metric, test_type):
    mask = (
        (tests_df["algorithm"] == algo) &
        (tests_df["n"].astype(str) == str(n_val)) &
        (tests_df["metric"] == metric) &
        (tests_df["test"].str.startswith(test_type))
    )
    rows = tests_df[mask]
    return float("nan") if len(rows) == 0 else rows["pvalue"].values[0]

def df_to_md(df_in):
    cols = df_in.columns.tolist()
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep    = "| " + " | ".join("---" for _ in cols) + " |"
    rows_out = []
    for _, row in df_in.iterrows():
        rows_out.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([header, sep] + rows_out)

# FannkuchRedux narrative numbers
lx11_mean_ms  = get_stat("FannkuchRedux", "linux",   11, "mean_ms")
win11_mean_ms = get_stat("FannkuchRedux", "windows", 11, "mean_ms")
lx12_mean_ms  = get_stat("FannkuchRedux", "linux",   12, "mean_ms")
win12_mean_ms = get_stat("FannkuchRedux", "windows", 12, "mean_ms")
lx11_mean_j   = get_stat("FannkuchRedux", "linux",   11, "mean_j")
win11_mean_j  = get_stat("FannkuchRedux", "windows", 11, "mean_j")
lx12_mean_j   = get_stat("FannkuchRedux", "linux",   12, "mean_j")
win12_mean_j  = get_stat("FannkuchRedux", "windows", 12, "mean_j")
time_diff_pct_11 = (lx11_mean_ms - win11_mean_ms) / win11_mean_ms * 100
time_diff_pct_12 = (lx12_mean_ms - win12_mean_ms) / win12_mean_ms * 100
energy_ratio_11  = lx11_mean_j / win11_mean_j
energy_ratio_12  = lx12_mean_j / win12_mean_j

mwu_time_p11  = get_test_p("FannkuchRedux", 11, "duration_ms",  "Mann-Whitney")
mwu_time_p12  = get_test_p("FannkuchRedux", 12, "duration_ms",  "Mann-Whitney")
mwu_en_p11    = get_test_p("FannkuchRedux", 11, "pkg_energy_j", "Mann-Whitney")
mwu_en_p12    = get_test_p("FannkuchRedux", 12, "pkg_energy_j", "Mann-Whitney")
perm_time_p11 = get_test_p("FannkuchRedux", 11, "duration_ms",  "Permutation")
perm_time_p12 = get_test_p("FannkuchRedux", 12, "duration_ms",  "Permutation")
perm_en_p11   = get_test_p("FannkuchRedux", 11, "pkg_energy_j", "Permutation")
perm_en_p12   = get_test_p("FannkuchRedux", 12, "pkg_energy_j", "Permutation")

# BinaryTrees narrative numbers (first n value)
bt_n0  = bt_n_vals[0]
bt_n1  = bt_n_vals[-1]
bt_lx0_ms   = get_stat("BinaryTrees", "linux",   bt_n0, "mean_ms")
bt_win0_ms  = get_stat("BinaryTrees", "windows", bt_n0, "mean_ms")
bt_lx1_ms   = get_stat("BinaryTrees", "linux",   bt_n1, "mean_ms")
bt_win1_ms  = get_stat("BinaryTrees", "windows", bt_n1, "mean_ms")
bt_lx0_j    = get_stat("BinaryTrees", "linux",   bt_n0, "mean_j")
bt_win0_j   = get_stat("BinaryTrees", "windows", bt_n0, "mean_j")
bt_lx1_j    = get_stat("BinaryTrees", "linux",   bt_n1, "mean_j")
bt_win1_j   = get_stat("BinaryTrees", "windows", bt_n1, "mean_j")

fr_dram_linux_pct   = stats_df[(stats_df["algorithm"]=="FannkuchRedux") & (stats_df["os"]=="linux")]["dram_pkg_ratio_pct"].mean()
fr_dram_windows_pct = stats_df[(stats_df["algorithm"]=="FannkuchRedux") & (stats_df["os"]=="windows")]["dram_pkg_ratio_pct"].mean()
bt_dram_linux_pct   = stats_df[(stats_df["algorithm"]=="BinaryTrees")   & (stats_df["os"]=="linux")]["dram_pkg_ratio_pct"].mean()
bt_dram_windows_pct = stats_df[(stats_df["algorithm"]=="BinaryTrees")   & (stats_df["os"]=="windows")]["dram_pkg_ratio_pct"].mean()

spearman_fr_row = tests_df[tests_df["test"] == "Spearman correlation (FannkuchRedux)"]
rho_fr = spearman_fr_row["statistic"].values[0] if len(spearman_fr_row) else float("nan")
p_fr   = spearman_fr_row["pvalue"].values[0]    if len(spearman_fr_row) else float("nan")

stats_table = stats_df[[
    "os","algorithm","n","count","mean_ms","median_ms","std_ms","cv_pct",
    "min_ms","max_ms","iqr_ms","mean_j","std_j","mean_dram_j","dram_pkg_ratio_pct",
]].copy()
for col in ["mean_ms","median_ms","std_ms","cv_pct","min_ms","max_ms","iqr_ms",
            "mean_j","std_j","mean_dram_j","dram_pkg_ratio_pct"]:
    stats_table[col] = stats_table[col].map(lambda v: f"{v:.4f}")

tests_table = tests_df[["algorithm","n","metric","test","statistic","pvalue","significant","alternative"]].copy()
tests_table["statistic"] = tests_table["statistic"].map(lambda v: f"{v:.4f}")
tests_table["pvalue"]    = tests_table["pvalue"].map(lambda v: f"{v:.6f}")

ci_table = ci_df.copy()
for col in ["mean","ci_lower","ci_upper","margin_abs","margin_pct"]:
    ci_table[col] = ci_table[col].map(lambda v: f"{v:.4f}")

summary_md = f"""# Resumo da Análise de Benchmarks

## Ambiente

| Campo | Detalhe |
|---|---|
| **Hardware** | HP EliteBook 1050 G1 · Intel Core i7-8850H · 6C/12T · 16 GiB RAM |
| **Sistemas Operativos** | Ubuntu 24.04.3 LTS (kernel 6.17.0-22-generic) vs Windows 11 Pro |
| **Versão .NET** | .NET 9 (mesma versão em ambos os SO) |
| **Algoritmos** | FannkuchRedux (CPU-bound) + BinaryTrees (GC-bound / Memory-bound) |
| **Fonte dos algoritmos** | greensoftwarelab/Energy-Languages (CSharp) |
| **Medição de energia** | Intel RAPL — domínios Package e DRAM (hardware, não estimativa) |
| **Turbo Boost** | Desativado em ambos os SO |
| **Plano de energia** | Linux: governor=performance · Windows: Ultimate Performance |
| **Temperaturas** | Linux: monitoradas via lm-sensors · Windows: não disponível (cpu_temp = -1.0) |

> **Nota sobre temperaturas:** Os dados do Windows têm `cpu_temp_before` e `cpu_temp_after` iguais a `-1.0`
> porque o LibreHardwareMonitorLib não obteve leituras válidas nessa sessão.
> As colunas de temperatura foram excluídas da análise estatística.

---

## Estatísticas Descritivas

{df_to_md(stats_table)}

> **CV%** = Coeficiente de Variação. **dram_pkg_ratio_pct** = DRAM Energy / Package Energy × 100.

---

## FannkuchRedux (CPU-bound)

### Tempo de Execução

- **N=11:** Windows ({win11_mean_ms:.1f} ms) é **{abs(time_diff_pct_11):.1f}% mais rápido** que Linux ({lx11_mean_ms:.1f} ms).
  CI 95% Linux: [{get_ci("FannkuchRedux","linux",11,"duration_ms","ci_lower"):.1f}, {get_ci("FannkuchRedux","linux",11,"duration_ms","ci_upper"):.1f}] ms |
  CI 95% Windows: [{get_ci("FannkuchRedux","windows",11,"duration_ms","ci_lower"):.1f}, {get_ci("FannkuchRedux","windows",11,"duration_ms","ci_upper"):.1f}] ms

- **N=12:** Windows ({win12_mean_ms:.1f} ms) é **{abs(time_diff_pct_12):.1f}% mais rápido** que Linux ({lx12_mean_ms:.1f} ms).
  CI 95% Linux: [{get_ci("FannkuchRedux","linux",12,"duration_ms","ci_lower"):.1f}, {get_ci("FannkuchRedux","linux",12,"duration_ms","ci_upper"):.1f}] ms |
  CI 95% Windows: [{get_ci("FannkuchRedux","windows",12,"duration_ms","ci_lower"):.1f}, {get_ci("FannkuchRedux","windows",12,"duration_ms","ci_upper"):.1f}] ms

- **Significância (tempo):**
  - N=11: Mann-Whitney p={pval_str(mwu_time_p11)} · Permutação p={pval_str(perm_time_p11)}
  - N=12: Mann-Whitney p={pval_str(mwu_time_p12)} · Permutação p={pval_str(perm_time_p12)}

### Consumo Energético

- **N=11:** Linux ({lx11_mean_j:.3f} J) vs Windows ({win11_mean_j:.3f} J) — rácio {energy_ratio_11:.2f}×
- **N=12:** Linux ({lx12_mean_j:.3f} J) vs Windows ({win12_mean_j:.3f} J) — rácio {energy_ratio_12:.2f}×

- **Significância (energia):**
  - N=11: Mann-Whitney p={pval_str(mwu_en_p11)} · Permutação p={pval_str(perm_en_p11)}
  - N=12: Mann-Whitney p={pval_str(mwu_en_p12)} · Permutação p={pval_str(perm_en_p12)}

### DRAM Energy (FannkuchRedux)

- Linux: DRAM representa em média **{fr_dram_linux_pct:.1f}%** da energia total do package.
- Windows: DRAM representa em média **{fr_dram_windows_pct:.1f}%** da energia total do package.
- Baixo rácio DRAM confirma natureza **CPU-bound** (alocação mínima de heap).

---

## BinaryTrees (GC-bound / Memory-bound)

### Tempo de Execução

- **N={bt_n0}:** Linux {bt_lx0_ms:.1f} ms vs Windows {bt_win0_ms:.1f} ms
- **N={bt_n1}:** Linux {bt_lx1_ms:.1f} ms vs Windows {bt_win1_ms:.1f} ms

### Consumo Energético

- **N={bt_n0}:** Linux {bt_lx0_j:.3f} J vs Windows {bt_win0_j:.3f} J
- **N={bt_n1}:** Linux {bt_lx1_j:.3f} J vs Windows {bt_win1_j:.3f} J

### DRAM Energy (BinaryTrees)

- Linux: DRAM representa em média **{bt_dram_linux_pct:.1f}%** da energia total do package.
- Windows: DRAM representa em média **{bt_dram_windows_pct:.1f}%** da energia total do package.
- Rácio DRAM claramente superior ao de FannkuchRedux, confirmando natureza **GC-bound / Memory-bound**.

---

## Cross-algorithm comparison (DRAM ratio)

| Algoritmo | OS | DRAM % do Package |
|---|---|---|
| FannkuchRedux | Linux | {fr_dram_linux_pct:.1f}% |
| FannkuchRedux | Windows | {fr_dram_windows_pct:.1f}% |
| BinaryTrees | Linux | {bt_dram_linux_pct:.1f}% |
| BinaryTrees | Windows | {bt_dram_windows_pct:.1f}% |

BinaryTrees apresenta um rácio DRAM substancialmente maior que FannkuchRedux,
evidenciando o impacto da gestão de memória (GC) no consumo energético de subsistema DRAM.
Esta diferença é capturada pela Figura 9 (09_dram_comparison.png).

---

## Resultados dos Testes de Hipótese

{df_to_md(tests_table)}

---

## Intervalos de Confiança (95%)

{df_to_md(ci_table)}

---

## Ameaças à Validade

1. **Dimensão da amostra (Linux):** As 24 amostras por grupo no Linux estão ligeiramente abaixo do n=30
   recomendado pelo Teorema do Limite Central. Os testes não-paramétricos utilizados são válidos para n≥20.

2. **Variância elevada no Windows N=11 (~8.8% CV):** Indica que o scheduler do Windows é menos
   determinístico para workloads de curta duração.

3. **Gestão térmica do portátil:** Com 6 núcleos a 100%, existe risco de throttling térmico,
   especialmente em N=12. O turbo foi desativado para reduzir variância.

4. **Filtro RAPL (Intel IPU 2021.2):** A Intel adicionou ruído aleatório às leituras RAPL como
   mitigação de ataques side-channel. Afeta Linux e Windows de forma equivalente.

5. **Sessões de medição separadas:** Medições Windows e Linux foram realizadas em sessões temporais
   distintas. Fatores externos podem introduzir diferenças sistemáticas não controladas.

6. **Temperatura não disponível no Windows:** Os valores `cpu_temp = -1.0` no Windows impedem
   a análise de correlação entre temperatura e desempenho para esse SO.
"""

summary_path = os.path.join(RES_DIR, "summary.md")
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(summary_md)
print("  Saved summary.md")


# ---------------------------------------------------------------------------
# ONE-PAGE STDOUT SUMMARY
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("  BENCHMARK ANALYSIS SUMMARY — FannkuchRedux + BinaryTrees")
print("  Linux vs Windows · Intel RAPL (Package + DRAM)")
print("=" * 70)

print(f"\n  {'Group':<30}  {'n':>3}  {'Mean (ms)':>10}  {'CV%':>6}  {'Mean (J)':>10}  {'DRAM%':>6}")
print(f"  {'-'*70}")
for (os_name, algo, n_val), grp in df.groupby(["os", "algorithm", "n"]):
    ms   = grp["duration_ms"]
    ej   = grp["pkg_energy_j"]
    dram = grp["dram_energy_j"]
    dram_pct = dram.mean() / ej.mean() * 100
    label = f"{algo} {os_name.capitalize()} N={n_val}"
    print(f"  {label:<30}  {len(grp):>3}  "
          f"{ms.mean():>10.1f}  {ms.std()/ms.mean()*100:>5.2f}%  "
          f"{ej.mean():>10.4f}  {dram_pct:>5.1f}%")

print(f"\n  FANNKUCHREDUX — TIME DIFFERENCE (Windows faster by):")
print(f"    N=11:  {abs(time_diff_pct_11):.1f}%  (Linux {lx11_mean_ms:.1f} ms  vs  Windows {win11_mean_ms:.1f} ms)")
print(f"    N=12:  {abs(time_diff_pct_12):.1f}%  (Linux {lx12_mean_ms:.1f} ms  vs  Windows {win12_mean_ms:.1f} ms)")

print(f"\n  FANNKUCHREDUX — ENERGY RATIO (Linux less by factor):")
print(f"    N=11:  {(1-energy_ratio_11)*100:.0f}% less  ({lx11_mean_j:.3f} J  vs  {win11_mean_j:.3f} J)")
print(f"    N=12:  {(1-energy_ratio_12)*100:.0f}% less  ({lx12_mean_j:.3f} J  vs  {win12_mean_j:.3f} J)")

print(f"\n  DRAM RATIO (memory-bound indicator):")
print(f"    FannkuchRedux Linux:    {fr_dram_linux_pct:.1f}%")
print(f"    FannkuchRedux Windows:  {fr_dram_windows_pct:.1f}%")
print(f"    BinaryTrees Linux:      {bt_dram_linux_pct:.1f}%")
print(f"    BinaryTrees Windows:    {bt_dram_windows_pct:.1f}%")

print(f"\n  STATISTICAL SIGNIFICANCE (α={ALPHA}) — Mann-Whitney U:")
mwu_rows = tests_df[
    tests_df["test"].str.startswith("Mann-Whitney") &
    (tests_df["alternative"].str.contains("two-sided|less"))
][["algorithm","n","metric","pvalue","significant"]]
for _, row in mwu_rows.iterrows():
    sig_mark = "SIGNIFICANT" if row["significant"] else "not significant"
    print(f"    {row['algorithm']:<14}  N={row['n']}  {row['metric']:<15}  p={row['pvalue']:.2e}  →  {sig_mark}")

print(f"\n  OUTPUTS:")
print(f"    Figures  → analysis/figures/  ({len(os.listdir(FIG_DIR))} PNG files)")
print(f"    Results  → analysis/results/  (statistics.csv, hypothesis_tests.csv,")
print(f"                                   confidence_intervals.csv, summary.md)")
print("=" * 70 + "\n")
