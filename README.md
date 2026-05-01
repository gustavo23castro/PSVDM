# C# Energy & Performance Benchmark: Windows vs Linux

**Measuring execution time and energy consumption of a CPU-bound C# workload on the same hardware under Windows 11 and Ubuntu 24.04.**

![.NET 9](https://img.shields.io/badge/.NET-9-512BD4) ![Ubuntu 24.04](https://img.shields.io/badge/Ubuntu-24.04-E95420) ![Windows 11](https://img.shields.io/badge/Windows-11-0078D4) ![BenchmarkDotNet 0.15.8](https://img.shields.io/badge/BenchmarkDotNet-0.15.8-orange)

---

## Overview

This project benchmarks the **FannkuchRedux** algorithm — a pure CPU-bound workload from the Computer Language Benchmarks Game — running as a .NET 9 application on two operating systems that share the same physical hardware (dual-boot). By eliminating hardware variability entirely, differences in execution time and energy consumption can be attributed to OS-level factors: scheduler behaviour, JIT tuning, power management, and RAPL reporting.

The central finding is a clear trade-off: **Windows is consistently faster, but Linux is dramatically more energy-efficient**. For N=11, Windows completes the benchmark 38% faster (452 ms vs 624 ms) yet consumes 69% more energy than Linux (27.1 J vs 16.0 J). The same pattern holds at N=12, where Windows is 35% faster but consumes 32% more energy. Both differences are statistically significant (Mann-Whitney U, p < 0.001; permutation test, p < 0.001 across all metrics and variants).

Energy is measured directly from **Intel RAPL hardware counters** — not software estimates — using the powercap sysfs interface on Linux and `LibreHardwareMonitorLib` (WinRing0/MSR) on Windows. The algorithm is the canonical C# reference implementation from [greensoftwarelab/Energy-Languages](https://github.com/greensoftwarelab/Energy-Languages/tree/master/CSharp/fannkuch-redux), the same corpus used in Pereira et al. "Energy Efficiency across Programming Languages", SLE 2017 (doi: 10.1145/3136014.3136031).

---

## Key Results

| Metric         | Linux (N=11) | Windows (N=11) | Linux (N=12) | Windows (N=12) |
|----------------|-------------|----------------|-------------|----------------|
| Mean time (ms) | 623.5       | 451.5          | 8577.8      | 6343.6         |
| Energy (J)     | 15.99       | 27.06          | 216.14      | 285.03         |
| CV (%)         | 0.63        | 0.95           | 0.33        | 0.55           |

All differences are statistically significant (Mann-Whitney U, p < 0.001; permutation A/B test, p < 0.001). 95% confidence intervals are tight (< 0.5% of mean for all groups), confirming a stable measurement environment.

> **Note:** The high CV for Windows N=11 (~0.95%) reflects non-deterministic thread scheduling for short workloads. Windows N=12 normalises to ~0.55%, consistent with longer runs stabilising scheduler behaviour.

---

## Repository Structure

```
PSVDM/
├── context/                        # Project documentation for Claude Code sessions
│   ├── PROJECT.md
│   ├── HARDWARE.md
│   ├── ARCHITECTURE.md
│   ├── CONVENTIONS.md
│   ├── NOTES.pt.md
│   ├── EXISTING_CODE.md
│   ├── ANALYSIS_METHODOLOGY.md
│   └── REPORT_STRUCTURE.md
├── src/
│   ├── linux/
│   │   ├── RaplProbe/              # RAPL validation tool (Linux)
│   │   └── FannkuchBenchmark/      # Main benchmark project (Linux)
│   └── windows/
│       ├── RaplProbe/              # RAPL validation tool (Windows)
│       └── FannkuchBenchmark/      # Main benchmark project (Windows)
├── results/
│   ├── linux/energy/               # Raw energy+timing CSV (Linux)
│   └── windows/energy/             # Raw energy+timing CSV (Windows)
├── analysis/
│   ├── analyze.py                  # Statistical analysis script
│   ├── figures/                    # Generated plots (PNG, 300 DPI)
│   └── results/                    # Statistics, hypothesis tests, CIs, summary
├── scripts/
│   ├── run-linux.sh                # Benchmark runner (sets governor, disables turbo)
│   └── run-windows.ps1             # Benchmark runner (sets power plan, disables turbo)
├── docs/
│   └── relatorio.tex               # Full report (LaTeX)
└── PSVDM.sln
```

---

## Hardware & Environment

| Field                | Value |
|----------------------|-------|
| Machine              | HP EliteBook 1050 G1 |
| CPU                  | Intel Core i7-8850H (Coffee Lake, 6C/12T) |
| RAM                  | 16 GiB |
| Linux                | Ubuntu 24.04.3 LTS, kernel 6.17.0-22-generic |
| Windows              | Windows 11 Pro |
| .NET                 | SDK 9.0 (same version on both OS) |
| Energy measurement   | Intel RAPL direct MSR access (Package domain) |
| Turbo Boost          | Disabled on both OS |
| Linux CPU governor   | `performance` |
| Windows power plan   | Ultimate Performance |

---

## Methodology Summary

Both operating systems run on the same physical machine (dual-boot), eliminating hardware variability as a confound. The measurement stack is:

- **Timing** — BenchmarkDotNet 0.15.8 handles JIT warm-up, GC pauses, iteration counting, and statistical reporting. The benchmark class is `FannkuchBenchmarks` with `[Params(11, 12)]`.
- **Energy** — Intel RAPL Package domain, read directly from hardware:
  - Linux: sysfs powercap interface (`/sys/devices/virtual/powercap/intel-rapl/`)
  - Windows: WinRing0 driver via `LibreHardwareMonitorLib` (Ring0 MSR reflection, requires Administrator)
- **Outlier removal** — IQR 1.5× rule applied per OS/N group before statistical tests.
- **Statistical tests** — Mann-Whitney U (non-parametric, two-sided and one-sided) and permutation A/B test (10 000 permutations) for both `duration_ms` and `pkg_energy_j`.
- **Confidence intervals** — 95% bootstrap CIs reported for mean time and mean energy per group.

Runs are performed on AC power with Turbo Boost disabled. CPU temperature is monitored on Linux via lm-sensors; no valid temperature readings were available on Windows (`LibreHardwareMonitorLib` returned −1.0 for this session, so temperature columns are excluded from statistical analysis).

---

## Running the Benchmarks

### Prerequisites

```bash
# Linux
sudo apt install linux-tools-common  # for cpupower
dotnet --version                     # must be 9.0+

# Windows (PowerShell as Administrator)
dotnet --version                     # must be 9.0+
```

### Linux

```bash
git clone <repo>
cd PSVDM

# Run benchmarks (sets performance governor + disables turbo automatically)
./scripts/run-linux.sh --filter "*FannkuchBenchmarks*"

# Results saved to:
# results/linux/energy/energy_single.csv
# results/linux/BenchmarkDotNet.Artifacts/
```

### Windows (PowerShell as Administrator)

```powershell
# Set execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run benchmarks
$env:BENCHMARK_RESULTS_ROOT = "$(Get-Location)\results"
cd src\windows\FannkuchBenchmark
dotnet run -c Release -- --filter "*FannkuchBenchmarks*"

# Results saved to:
# results\windows\energy\energy_windows.csv
```

---

## Analysis

```bash
cd PSVDM
pip install pandas numpy scipy scikit-learn matplotlib seaborn
python analysis/analyze.py

# Outputs:
# analysis/figures/   -- 6 plots (PNG, 300 DPI)
# analysis/results/   -- statistics.csv, hypothesis_tests.csv,
#                        confidence_intervals.csv, summary.md
```

---

## Algorithm

FannkuchRedux from the Computer Language Benchmarks Game.

- **Source**: [greensoftwarelab/Energy-Languages](https://github.com/greensoftwarelab/Energy-Languages/tree/master/CSharp/fannkuch-redux) — contributed by Isaac Gouy, transliterated from Oleg Mazurov's Java program; concurrency fix and minor improvements by Peperud.
- **Characteristics**: CPU-bound, no I/O, minimal heap allocation (~52 KB/iteration).
- **Threading**: `Task.Run` with `Environment.ProcessorCount + 1` workers, `NCHUNKS = 150` work-stealing chunks.
- **Correctness**: `Compute(7)` → checksum = 228, maxFlips = 16.
- **Variants**: N=11 (~450–620 ms/run) and N=12 (~6–9 s/run). N=10 was dropped due to thermal instability from short run duration.

---

## Citation

If you use this work, please cite:

```bibtex
@misc{csharp-energy-benchmark,
  author = {[author]},
  title  = {C\# Energy and Performance Benchmark: Windows vs Linux},
  year   = {2026},
  url    = {https://github.com/[user]/csharp-energy-benchmark}
}
```

And the original algorithm source:

```bibtex
@inproceedings{pereira2017energy,
  author    = {Pereira, Rui and others},
  title     = {Energy Efficiency across Programming Languages},
  booktitle = {Proceedings of SLE 2017},
  year      = {2017},
  doi       = {10.1145/3136014.3136031}
}
```

---

## License

MIT
