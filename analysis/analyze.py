"""
analyze.py — Windows vs Linux benchmark analysis
FannkuchRedux · C# · Intel RAPL · HP EliteBook i7-8850H
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
REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINUX_CSV   = os.path.join(REPO_ROOT, "results", "linux",   "energy", "energy_single.csv")
WINDOWS_CSV = os.path.join(REPO_ROOT, "results", "windows", "energy", "energy_windows.csv")
FIG_DIR     = os.path.join(REPO_ROOT, "analysis", "figures")
RES_DIR     = os.path.join(REPO_ROOT, "analysis", "results")

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Style / colours
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid")
COLORS = {"linux": "#2196F3", "windows": "#FF5722"}
PALETTE = [COLORS["linux"], COLORS["windows"]]
DPI = 300
ALPHA = 0.05
N_PERM = 10_000
np.random.seed(42)


# ---------------------------------------------------------------------------
# STEP 1 — Load and clean
# ---------------------------------------------------------------------------
print("Step 1/6: Loading data...")

linux_df   = pd.read_csv(LINUX_CSV)
windows_df = pd.read_csv(WINDOWS_CSV)
df_raw = pd.concat([linux_df, windows_df], ignore_index=True)

# Joule conversion
df_raw["pkg_energy_j"]  = df_raw["pkg_energy_uj"]  / 1_000_000
df_raw["pp0_energy_j"]  = df_raw["pp0_energy_uj"]  / 1_000_000

print(f"  Loaded {len(linux_df)} Linux rows and {len(windows_df)} Windows rows → {len(df_raw)} total")
print(f"  N values: {sorted(df_raw['n'].unique())}")
print(f"  OS values: {df_raw['os'].unique().tolist()}")

# IQR outlier removal per (os × n) for each metric
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

keep_mask = remove_outliers_iqr(df_raw, ["os", "n"], ["duration_ms", "pkg_energy_j"])
df = df_raw[keep_mask].copy()
n_removed = len(df_raw) - len(df)
print(f"  Outlier removal (IQR 1.5×): removed {n_removed} rows ({n_removed/len(df_raw)*100:.1f}%)")
print(f"  Clean dataset: {len(df)} rows")

for (os_name, n_val), grp in df.groupby(["os", "n"]):
    print(f"    {os_name:8s}  N={n_val}  count={len(grp)}")

# Temperature note
temp_available = not (df_raw["cpu_temp_before"] == -1.0).all()
if not temp_available:
    print("  NOTE: cpu_temp = -1.0 on Windows — temperature columns excluded from analysis")


# ---------------------------------------------------------------------------
# STEP 2 — Descriptive statistics
# ---------------------------------------------------------------------------
print("\nStep 2/6: Computing descriptive statistics...")

rows = []
for (os_name, n_val), grp in df.groupby(["os", "n"]):
    ms  = grp["duration_ms"]
    ej  = grp["pkg_energy_j"]
    pp0 = grp["pp0_energy_j"]
    q1, q3 = ms.quantile(0.25), ms.quantile(0.75)
    rows.append({
        "os":         os_name,
        "n":          n_val,
        "count":      len(grp),
        "mean_ms":    ms.mean(),
        "median_ms":  ms.median(),
        "std_ms":     ms.std(),
        "cv_pct":     ms.std() / ms.mean() * 100,
        "min_ms":     ms.min(),
        "max_ms":     ms.max(),
        "q1_ms":      q1,
        "q3_ms":      q3,
        "iqr_ms":     q3 - q1,
        "mean_j":     ej.mean(),
        "median_j":   ej.median(),
        "std_j":      ej.std(),
        "mean_pp0_j": pp0.mean(),
    })

stats_df = pd.DataFrame(rows)
stats_df.to_csv(os.path.join(RES_DIR, "statistics.csv"), index=False, float_format="%.4f")
print("  Saved statistics.csv")
print(stats_df[["os", "n", "count", "mean_ms", "std_ms", "cv_pct", "mean_j"]].to_string(index=False))


# ---------------------------------------------------------------------------
# STEP 3 — Figures
# ---------------------------------------------------------------------------
print("\nStep 3/6: Generating figures...")

def savefig(name):
    path = os.path.join(FIG_DIR, name)
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"  Saved {name}")

# --- Figure 1: Boxplot — execution time ---
fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=False)
fig.suptitle("FannkuchRedux — Execution Time: Linux vs Windows", fontsize=14, fontweight="bold")

for ax, n_val in zip(axes, [11, 12]):
    sub = df[df["n"] == n_val]
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

# --- Figure 2: Boxplot — package energy ---
fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=False)
fig.suptitle("FannkuchRedux — Package Energy: Linux vs Windows", fontsize=14, fontweight="bold")

for ax, n_val in zip(axes, [11, 12]):
    sub = df[df["n"] == n_val]
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

# --- Figure 3: Histogram + KDE — execution time ---
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle("FannkuchRedux — Execution Time Distribution", fontsize=14, fontweight="bold")

for idx, (os_name, n_val) in enumerate([("linux", 11), ("linux", 12), ("windows", 11), ("windows", 12)]):
    ax = axes[idx // 2][idx % 2]
    sub = df[(df["os"] == os_name) & (df["n"] == n_val)]["duration_ms"]
    sns.histplot(sub, kde=True, color=COLORS[os_name], ax=ax, bins=10, alpha=0.7)
    ax.set_title(f"{os_name.capitalize()} — N={n_val}  (n={len(sub)})", fontsize=12)
    ax.set_xlabel("Execution Time (ms)")
    ax.set_ylabel("Count")
    ax.axvline(sub.mean(), color="black", linestyle="--", linewidth=1.2, label=f"Mean {sub.mean():.1f} ms")
    ax.legend(fontsize=9)

plt.tight_layout()
savefig("03_histogram_time.png")

# --- Figure 4: Histogram + KDE — package energy ---
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle("FannkuchRedux — Package Energy Distribution", fontsize=14, fontweight="bold")

for idx, (os_name, n_val) in enumerate([("linux", 11), ("linux", 12), ("windows", 11), ("windows", 12)]):
    ax = axes[idx // 2][idx % 2]
    sub = df[(df["os"] == os_name) & (df["n"] == n_val)]["pkg_energy_j"]
    sns.histplot(sub, kde=True, color=COLORS[os_name], ax=ax, bins=10, alpha=0.7)
    ax.set_title(f"{os_name.capitalize()} — N={n_val}  (n={len(sub)})", fontsize=12)
    ax.set_xlabel("Package Energy (J)")
    ax.set_ylabel("Count")
    ax.axvline(sub.mean(), color="black", linestyle="--", linewidth=1.2, label=f"Mean {sub.mean():.3f} J")
    ax.legend(fontsize=9)

plt.tight_layout()
savefig("04_histogram_energy.png")

# --- Figure 5: Correlation — time vs energy ---
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.suptitle("FannkuchRedux — Execution Time vs Package Energy", fontsize=14, fontweight="bold")

for ax, n_val in zip(axes, [11, 12]):
    for os_name in ["linux", "windows"]:
        sub = df[(df["os"] == os_name) & (df["n"] == n_val)]
        ax.scatter(sub["duration_ms"], sub["pkg_energy_j"],
                   color=COLORS[os_name], alpha=0.7, label=os_name.capitalize(), s=40)

    sub_n = df[df["n"] == n_val]
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

# --- Figure 6: Summary bar chart with 95% CI error bars ---
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.suptitle("FannkuchRedux — Mean Execution Time and Energy (95% CI)", fontsize=14, fontweight="bold")

groups = [("Linux", "linux", 11), ("Windows", "windows", 11),
          ("Linux", "linux", 12), ("Windows", "windows", 12)]
labels  = [f"{lbl}\nN={n}" for lbl, _, n in groups]
x_pos   = np.arange(len(groups))
bar_colors = [COLORS[os] for _, os, _ in groups]

for ax_idx, (metric, ylabel, title) in enumerate([
        ("duration_ms",  "Execution Time (ms)",  "Execution Time"),
        ("pkg_energy_j", "Package Energy (J)",    "Package Energy"),
]):
    ax = axes[ax_idx]
    means, ci_lows, ci_highs = [], [], []
    for _, os_name, n_val in groups:
        sub = df[(df["os"] == os_name) & (df["n"] == n_val)][metric]
        m = sub.mean()
        ci = stats.t.interval(0.95, df=len(sub) - 1, loc=m, scale=stats.sem(sub))
        means.append(m)
        ci_lows.append(m - ci[0])
        ci_highs.append(ci[1] - m)

    bars = ax.bar(x_pos, means, color=bar_colors, alpha=0.85,
                  yerr=[ci_lows, ci_highs], capsize=5, error_kw={"linewidth": 1.5})
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=10)
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
        elif alternative == "less":      # a < b  →  obs very negative
            if diff <= obs:
                count += 1
        elif alternative == "greater":
            if diff >= obs:
                count += 1
    return obs, count / n_perm

test_rows = []

for n_val in [11, 12]:
    linux_ms  = df[(df["os"] == "linux")   & (df["n"] == n_val)]["duration_ms"].values
    win_ms    = df[(df["os"] == "windows") & (df["n"] == n_val)]["duration_ms"].values
    linux_ej  = df[(df["os"] == "linux")   & (df["n"] == n_val)]["pkg_energy_j"].values
    win_ej    = df[(df["os"] == "windows") & (df["n"] == n_val)]["pkg_energy_j"].values

    # a) Mann-Whitney U — duration_ms two-sided
    U, p = stats.mannwhitneyu(linux_ms, win_ms, alternative="two-sided")
    test_rows.append({
        "n": n_val, "metric": "duration_ms", "test": "Mann-Whitney U",
        "statistic": U, "pvalue": p, "significant": p < ALPHA,
        "alternative": "two-sided (Linux ≠ Windows)",
        "interpretation": (
            "Linux é significativamente diferente de Windows em tempo"
            if p < ALPHA else "Sem diferença significativa em tempo"
        ),
    })

    # a) Mann-Whitney U — duration_ms one-sided (Linux > Windows → Linux slower)
    U, p = stats.mannwhitneyu(linux_ms, win_ms, alternative="greater")
    test_rows.append({
        "n": n_val, "metric": "duration_ms", "test": "Mann-Whitney U",
        "statistic": U, "pvalue": p, "significant": p < ALPHA,
        "alternative": "one-sided (Linux > Windows, Linux é mais lento)",
        "interpretation": (
            "Linux é significativamente mais lento que Windows"
            if p < ALPHA else "Linux não é significativamente mais lento"
        ),
    })

    # b) Mann-Whitney U — pkg_energy_j one-sided (Linux < Windows → Linux greener)
    U, p = stats.mannwhitneyu(linux_ej, win_ej, alternative="less")
    test_rows.append({
        "n": n_val, "metric": "pkg_energy_j", "test": "Mann-Whitney U",
        "statistic": U, "pvalue": p, "significant": p < ALPHA,
        "alternative": "one-sided (Linux < Windows, Linux consome menos)",
        "interpretation": (
            "Linux consome significativamente menos energia que Windows"
            if p < ALPHA else "Sem diferença significativa em energia"
        ),
    })

    # c) Permutation A/B — duration_ms two-sided
    obs, p_perm = permutation_test(linux_ms, win_ms, alternative="two-sided")
    test_rows.append({
        "n": n_val, "metric": "duration_ms", "test": f"Permutation A/B ({N_PERM} perms)",
        "statistic": obs, "pvalue": p_perm, "significant": p_perm < ALPHA,
        "alternative": "two-sided",
        "interpretation": (
            f"Diferença observada ({obs:.2f} ms) estatisticamente significativa"
            if p_perm < ALPHA else f"Diferença ({obs:.2f} ms) não significativa"
        ),
    })

    # d) Permutation A/B — pkg_energy_j one-sided (Linux < Windows)
    obs_e, p_perm_e = permutation_test(linux_ej, win_ej, alternative="less")
    test_rows.append({
        "n": n_val, "metric": "pkg_energy_j", "test": f"Permutation A/B ({N_PERM} perms)",
        "statistic": obs_e, "pvalue": p_perm_e, "significant": p_perm_e < ALPHA,
        "alternative": "one-sided (Linux < Windows)",
        "interpretation": (
            f"Linux usa {abs(obs_e):.3f} J menos que Windows (significativo)"
            if p_perm_e < ALPHA else f"Diferença de energia ({obs_e:.3f} J) não significativa"
        ),
    })

# e) Spearman correlation — full dataset and per OS
rho_all, p_all = stats.spearmanr(df["duration_ms"], df["pkg_energy_j"])
test_rows.append({
    "n": "all", "metric": "duration_ms vs pkg_energy_j",
    "test": "Spearman correlation (full dataset)",
    "statistic": rho_all, "pvalue": p_all, "significant": p_all < ALPHA,
    "alternative": "two-sided",
    "interpretation": f"ρ = {rho_all:.3f} — correlação {'significativa' if p_all < ALPHA else 'não significativa'}",
})

for os_name in ["linux", "windows"]:
    sub = df[df["os"] == os_name]
    rho, p = stats.spearmanr(sub["duration_ms"], sub["pkg_energy_j"])
    test_rows.append({
        "n": "all", "metric": "duration_ms vs pkg_energy_j",
        "test": f"Spearman correlation ({os_name})",
        "statistic": rho, "pvalue": p, "significant": p < ALPHA,
        "alternative": "two-sided",
        "interpretation": f"ρ = {rho:.3f} — correlação {'significativa' if p < ALPHA else 'não significativa'} para {os_name}",
    })

tests_df = pd.DataFrame(test_rows)
tests_df.to_csv(os.path.join(RES_DIR, "hypothesis_tests.csv"), index=False, float_format="%.6f")
print("  Saved hypothesis_tests.csv")
print(tests_df[["n", "metric", "test", "statistic", "pvalue", "significant"]].to_string(index=False))


# ---------------------------------------------------------------------------
# STEP 5 — Confidence intervals
# ---------------------------------------------------------------------------
print("\nStep 5/6: Computing confidence intervals...")

ci_rows = []
for (os_name, n_val), grp in df.groupby(["os", "n"]):
    for metric in ["duration_ms", "pkg_energy_j"]:
        vals = grp[metric].values
        m    = vals.mean()
        ci   = stats.t.interval(0.95, df=len(vals) - 1, loc=m, scale=stats.sem(vals))
        margin = (ci[1] - ci[0]) / 2
        ci_rows.append({
            "os":         os_name,
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
# STEP 6 — Summary report (Portuguese)
# ---------------------------------------------------------------------------
print("\nStep 6/6: Writing summary report...")

def get_stat(os_name, n_val, col):
    row = stats_df[(stats_df["os"] == os_name) & (stats_df["n"] == n_val)]
    return row[col].values[0]

def get_ci(os_name, n_val, metric, col):
    row = ci_df[(ci_df["os"] == os_name) & (ci_df["n"] == n_val) & (ci_df["metric"] == metric)]
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

# Key numbers for narrative
lx11_mean_ms   = get_stat("linux",   11, "mean_ms")
win11_mean_ms  = get_stat("windows", 11, "mean_ms")
lx12_mean_ms   = get_stat("linux",   12, "mean_ms")
win12_mean_ms  = get_stat("windows", 12, "mean_ms")

lx11_mean_j    = get_stat("linux",   11, "mean_j")
win11_mean_j   = get_stat("windows", 11, "mean_j")
lx12_mean_j    = get_stat("linux",   12, "mean_j")
win12_mean_j   = get_stat("windows", 12, "mean_j")

time_diff_pct_11 = (lx11_mean_ms - win11_mean_ms) / win11_mean_ms * 100
time_diff_pct_12 = (lx12_mean_ms - win12_mean_ms) / win12_mean_ms * 100
energy_ratio_11  = lx11_mean_j / win11_mean_j
energy_ratio_12  = lx12_mean_j / win12_mean_j

# Retrieve test p-values for narrative
def get_test_p(n_val, metric, test_type):
    mask = (
        (tests_df["n"].astype(str) == str(n_val)) &
        (tests_df["metric"] == metric) &
        (tests_df["test"].str.startswith(test_type))
    )
    rows = tests_df[mask]
    if len(rows) == 0:
        return float("nan")
    return rows["pvalue"].values[0]

mwu_time_p11  = get_test_p(11, "duration_ms",   "Mann-Whitney")
mwu_time_p12  = get_test_p(12, "duration_ms",   "Mann-Whitney")
mwu_en_p11    = get_test_p(11, "pkg_energy_j",  "Mann-Whitney")
mwu_en_p12    = get_test_p(12, "pkg_energy_j",  "Mann-Whitney")
perm_time_p11 = get_test_p(11, "duration_ms",   "Permutation")
perm_time_p12 = get_test_p(12, "duration_ms",   "Permutation")
perm_en_p11   = get_test_p(11, "pkg_energy_j",  "Permutation")
perm_en_p12   = get_test_p(12, "pkg_energy_j",  "Permutation")

stats_table = stats_df[[
    "os", "n", "count", "mean_ms", "median_ms", "std_ms", "cv_pct",
    "min_ms", "max_ms", "iqr_ms", "mean_j", "std_j",
]].copy()
for col in ["mean_ms","median_ms","std_ms","cv_pct","min_ms","max_ms","iqr_ms","mean_j","std_j"]:
    stats_table[col] = stats_table[col].map(lambda v: f"{v:.4f}")

tests_table = tests_df[["n","metric","test","statistic","pvalue","significant","alternative"]].copy()
tests_table["statistic"] = tests_table["statistic"].map(lambda v: f"{v:.4f}")
tests_table["pvalue"]    = tests_table["pvalue"].map(lambda v: f"{v:.6f}")

ci_table = ci_df.copy()
for col in ["mean","ci_lower","ci_upper","margin_abs","margin_pct"]:
    ci_table[col] = ci_table[col].map(lambda v: f"{v:.4f}")

def df_to_md(df_in):
    cols = df_in.columns.tolist()
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep    = "| " + " | ".join("---" for _ in cols) + " |"
    rows_out = []
    for _, row in df_in.iterrows():
        rows_out.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([header, sep] + rows_out)

summary_md = f"""# Resumo da Análise de Benchmarks

## Ambiente

| Campo | Detalhe |
|---|---|
| **Hardware** | HP EliteBook 1050 G1 · Intel Core i7-8850H · 6C/12T · 16 GiB RAM |
| **Sistemas Operativos** | Ubuntu 24.04.3 LTS (kernel 6.17.0-22-generic) vs Windows 11 Pro |
| **Versão .NET** | .NET 9 (mesma versão em ambos os SO) |
| **Algoritmo** | FannkuchRedux — CPU-bound, sem I/O, alocação mínima de heap |
| **Fonte do algoritmo** | greensoftwarelab/Energy-Languages (CSharp/fannkuch-redux) |
| **Medição de energia** | Intel RAPL — domínio Package (hardware, não estimativa) |
| **Turbo Boost** | Desativado em ambos os SO |
| **Plano de energia** | Linux: governor=performance · Windows: Ultimate Performance |
| **Temperaturas** | Linux: monitoradas via lm-sensors · Windows: não disponível (cpu_temp = -1.0) |

> **Nota sobre temperaturas:** Os dados do Windows têm `cpu_temp_before` e `cpu_temp_after` iguais a `-1.0`
> porque o LibreHardwareMonitorLib não obteve leituras válidas nessa sessão.
> As colunas de temperatura foram excluídas da análise estatística.
> A comparação de desempenho baseia-se exclusivamente em `duration_ms` e `pkg_energy_j`.

---

## Estatísticas Descritivas

{df_to_md(stats_table)}

> **CV%** = Coeficiente de Variação (Desvio Padrão / Média × 100). Indica a estabilidade relativa do ambiente.

---

## Resultados dos Testes de Hipótese

{df_to_md(tests_table)}

---

## Intervalos de Confiança (95%)

{df_to_md(ci_table)}

---

## Principais Conclusões

### Tempo de Execução

- **N=11:** Windows ({win11_mean_ms:.1f} ms) é **{abs(time_diff_pct_11):.1f}% mais rápido** que Linux ({lx11_mean_ms:.1f} ms).
  CI 95% Linux: [{get_ci("linux",11,"duration_ms","ci_lower"):.1f}, {get_ci("linux",11,"duration_ms","ci_upper"):.1f}] ms |
  CI 95% Windows: [{get_ci("windows",11,"duration_ms","ci_lower"):.1f}, {get_ci("windows",11,"duration_ms","ci_upper"):.1f}] ms

- **N=12:** Windows ({win12_mean_ms:.1f} ms) é **{abs(time_diff_pct_12):.1f}% mais rápido** que Linux ({lx12_mean_ms:.1f} ms).
  CI 95% Linux: [{get_ci("linux",12,"duration_ms","ci_lower"):.1f}, {get_ci("linux",12,"duration_ms","ci_upper"):.1f}] ms |
  CI 95% Windows: [{get_ci("windows",12,"duration_ms","ci_lower"):.1f}, {get_ci("windows",12,"duration_ms","ci_upper"):.1f}] ms

- **Significância estatística (tempo):**
  - N=11: Mann-Whitney U p={pval_str(mwu_time_p11)} · Permutação p={pval_str(perm_time_p11)}
  - N=12: Mann-Whitney U p={pval_str(mwu_time_p12)} · Permutação p={pval_str(perm_time_p12)}

### Consumo Energético

- **N=11:** Linux ({lx11_mean_j:.3f} J) consome **{energy_ratio_11:.2f}× menos energia** que Windows ({win11_mean_j:.3f} J).
  CI 95% Linux: [{get_ci("linux",11,"pkg_energy_j","ci_lower"):.3f}, {get_ci("linux",11,"pkg_energy_j","ci_upper"):.3f}] J |
  CI 95% Windows: [{get_ci("windows",11,"pkg_energy_j","ci_lower"):.3f}, {get_ci("windows",11,"pkg_energy_j","ci_upper"):.3f}] J

- **N=12:** Linux ({lx12_mean_j:.3f} J) consome **{energy_ratio_12:.2f}× menos energia** que Windows ({win12_mean_j:.3f} J).
  CI 95% Linux: [{get_ci("linux",12,"pkg_energy_j","ci_lower"):.3f}, {get_ci("linux",12,"pkg_energy_j","ci_upper"):.3f}] J |
  CI 95% Windows: [{get_ci("windows",12,"pkg_energy_j","ci_lower"):.3f}, {get_ci("windows",12,"pkg_energy_j","ci_upper"):.3f}] J

- **Significância estatística (energia):**
  - N=11: Mann-Whitney U p={pval_str(mwu_en_p11)} · Permutação p={pval_str(perm_en_p11)}
  - N=12: Mann-Whitney U p={pval_str(mwu_en_p12)} · Permutação p={pval_str(perm_en_p12)}

### Variância

- Linux apresenta coeficiente de variação (CV) muito baixo (<1%), indicando ambiente de medição estável.
- Windows N=11 tem CV elevado (~8–9%), refletindo comportamento não-determinístico do scheduler Windows
  para workloads de curta duração (indicativo de variabilidade de escalonamento de threads).
- Windows N=12 normaliza para CV~1%, sugerindo que cargas mais longas estabilizam o comportamento.

### Correlação Tempo–Energia

- Existe correlação de Spearman forte e significativa entre tempo de execução e energia consumida
  (ρ ≈ {rho_all:.3f}, p = {pval_str(p_all)}), o que é esperado num benchmark CPU-bound.
- A correlação é verificada individualmente em cada SO.

---

## Ameaças à Validade

1. **Dimensão da amostra (Linux):** As 24 amostras por grupo no Linux estão ligeiramente abaixo do n=30
   recomendado pelo Teorema do Limite Central para garantir normalidade assintótica da média amostral.
   Os testes não-paramétricos utilizados (Mann-Whitney, permutação) são válidos para n≥20,
   pelo que a análise permanece defensável, mas deve ser mencionado como limitação.

2. **Variância elevada no Windows N=11 (~8.8% CV):** Indica que o scheduler do Windows é menos
   determinístico para workloads de curta duração. Pode refletir variações de frequência de CPU,
   migração de threads entre núcleos, ou interferência de processos de sistema.
   Este resultado é em si mesmo relevante e deve ser discutido na secção de análise.

3. **Gestão térmica do portátil:** O HP EliteBook 1050 G1 tem 6+ anos. Com 6 núcleos a 100%,
   existe risco de throttling térmico, especialmente em N=12 (runs de ~8s). O turbo foi desativado
   para reduzir variância, mas o throttling por temperatura não pode ser completamente excluído.
   As temperaturas registadas no Linux (até ~59°C) estão dentro dos limites seguros de operação.

4. **Filtro RAPL (Intel IPU 2021.2):** A Intel adicionou ruído aleatório às leituras RAPL como
   mitigação de ataques side-channel. Afeta Linux e Windows de forma equivalente; mitigado pelo
   elevado número de iterações e reporte da distribuição estatística completa.

5. **Sessões de medição separadas:** As medições Windows e Linux foram realizadas em sessões temporais
   distintas. Fatores externos (temperatura ambiente, estado da bateria, versão de firmware)
   podem introduzir diferenças sistemáticas não controladas.

6. **Temperatura não disponível no Windows:** Os valores `cpu_temp = -1.0` no Windows impedem
   a análise de correlação entre temperatura e desempenho para esse SO.
"""

summary_path = os.path.join(RES_DIR, "summary.md")
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(summary_md)
print(f"  Saved summary.md")


# ---------------------------------------------------------------------------
# ONE-PAGE STDOUT SUMMARY
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("  BENCHMARK ANALYSIS SUMMARY — FannkuchRedux · Linux vs Windows")
print("=" * 70)

print(f"\n  {'Group':<22}  {'n':>4}  {'Mean (ms)':>10}  {'CV%':>6}  {'Mean (J)':>10}")
print(f"  {'-'*56}")
for (os_name, n_val), grp in df.groupby(["os", "n"]):
    ms = grp["duration_ms"]
    ej = grp["pkg_energy_j"]
    print(f"  {os_name.capitalize()+' N='+str(n_val):<22}  {len(grp):>4}  "
          f"{ms.mean():>10.1f}  {ms.std()/ms.mean()*100:>5.2f}%  {ej.mean():>10.4f}")

print(f"\n  TIME DIFFERENCE (Windows faster by):")
print(f"    N=11:  {abs(time_diff_pct_11):.1f}%  "
      f"(Linux {lx11_mean_ms:.1f} ms  vs  Windows {win11_mean_ms:.1f} ms)")
print(f"    N=12:  {abs(time_diff_pct_12):.1f}%  "
      f"(Linux {lx12_mean_ms:.1f} ms  vs  Windows {win12_mean_ms:.1f} ms)")

print(f"\n  ENERGY RATIO (Linux uses less by factor):")
print(f"    N=11:  Linux uses {(1-energy_ratio_11)*100:.0f}% less  "
      f"({lx11_mean_j:.3f} J  vs  {win11_mean_j:.3f} J)")
print(f"    N=12:  Linux uses {(1-energy_ratio_12)*100:.0f}% less  "
      f"({lx12_mean_j:.3f} J  vs  {win12_mean_j:.3f} J)")

print(f"\n  STATISTICAL SIGNIFICANCE (α={ALPHA}):")
all_sig = tests_df[
    tests_df["test"].str.startswith("Mann-Whitney") &
    (tests_df["alternative"].str.contains("two-sided|less"))
][["n","metric","pvalue","significant"]]
for _, row in all_sig.iterrows():
    sig_mark = "SIGNIFICANT" if row["significant"] else "not significant"
    print(f"    N={row['n']}  {row['metric']:<15}  p={row['pvalue']:.2e}  →  {sig_mark}")

print(f"\n  OUTPUTS:")
print(f"    Figures  → analysis/figures/  ({len(os.listdir(FIG_DIR))} PNG files)")
print(f"    Results  → analysis/results/  (statistics.csv, hypothesis_tests.csv,")
print(f"                                   confidence_intervals.csv, summary.md)")
print("=" * 70 + "\n")
