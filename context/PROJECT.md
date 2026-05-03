# Project: C# Energy & Performance Benchmarking — Windows vs Linux

## Overview

This project measures and compares the **execution performance** and **energy consumption** of C# running a CPU-bound algorithm (FannkuchRedux) on the same physical machine under two operating systems: **Windows 11 Pro** and **Ubuntu 24.04 LTS**.

The work will produce:
- An academic **report** (interim deliverable)
- A **presentation**
- A peer-reviewed **article**

---

## Research Questions

1. Is there a statistically significant difference in **execution time** between Windows 11 and Ubuntu 24.04 for a CPU-bound C# workload?
2. Is there a measurable difference in **energy consumption** (Joules) between the two platforms for the same workload?
3. Can observed differences be attributed to OS-level factors (scheduler, JIT behaviour, power management)?

---

## Benchmarks

### FannkuchRedux

- Source: [greensoftwarelab/Energy-Languages](https://github.com/greensoftwarelab/Energy-Languages/tree/master/CSharp/fannkuch-redux)
  — contributed by Isaac Gouy, transliterated from Oleg Mazurov's Java program; concurrency fix and minor improvements by Peperud
- Classification: CPU-bound, no I/O, minimal heap allocation
- Why this benchmark:
  - Deterministic and reproducible
  - Exercises integer arithmetic and array access patterns
  - Well-known in cross-language performance literature
  - GC pressure is negligible, isolating JIT and scheduler behaviour
- Variant benchmarked: N=11 and N=12 (`[Params(11, 12)]`)
  - N=10 dropped due to thermal instability from short run duration
  - Multi-thread-only algorithm (`Environment.ProcessorCount + 1` Task threads); no single-thread variant
- Benchmark class: `FannkuchBenchmarks`, method `Run()`

### BinaryTrees

- Source: [greensoftwarelab/Energy-Languages](https://github.com/greensoftwarelab/Energy-Languages/tree/master/CSharp/binary-trees)
  — contributed by Marek Safar; concurrency added by Peperud
- Classification: GC-bound / memory-bound, recursive tree allocation
- Why this benchmark:
  - Complementary to FannkuchRedux: exercises GC and memory subsystem instead of pure CPU arithmetic
  - Standard Computer Language Benchmarks Game benchmark
  - Heavy heap allocation (hundreds of MB per run), stresses GC across generations
- Variant benchmarked: N=16 and N=18 (`[Params(16, 18)]`)
  - N=16: fast (~0.8 s, ~227 MB), N=18: medium (~4 s, ~1 GB)
  - Multi-threaded: `Task.Run` parallelism with over-parallelisation for deep trees (depth > 18)
- Benchmark class: `BinaryTreesBenchmark`, method `Run()`
- Energy CSV: `results/linux/energy/energy_bt.csv`

---

## Scope & Constraints

- **Same physical hardware** for both OS environments (dual-boot)
- **.NET version**: same SDK version on both OS (to be confirmed — target .NET 9)
- Energy measurement via **hardware RAPL counters** (not software estimation)
- No virtualisation, no Docker — bare metal only
- Benchmarks run on **AC power**, performance governor active
- Turbo Boost **disabled** during measurement runs to reduce variance

---

## Expected Outputs

| Artifact | Format | Language |
|---|---|---|
| Interim report | PDF / DOCX | Portuguese |
| Presentation | PPTX | Portuguese |
| Article | LaTeX / PDF | English |
| Raw results | CSV + JSON | — |
| Analysis scripts | Python (pandas/matplotlib) | — |

---

## Status

- [x] Hardware selected and characterised
- [x] Measurement strategy defined (RAPL direct, BenchmarkDotNet)
- [ ] Repository structure created
- [ ] .NET projects scaffolded (Windows + Linux)
- [ ] Baseline benchmarks collected
- [ ] Energy harness integrated
- [ ] Results analysis
- [ ] Report written
- [ ] Article drafted
