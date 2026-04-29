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
4. How do results scale from **single-threaded** to **multi-threaded** execution?

---

## Algorithm: FannkuchRedux

- Source: [Computer Language Benchmarks Game](https://benchmarksgame-team.pages.debian.net/benchmarksgame/)
- Classification: CPU-bound, no I/O, minimal heap allocation
- Why this benchmark:
  - Deterministic and reproducible
  - Exercises integer arithmetic and array access patterns
  - Well-known in cross-language performance literature
  - GC pressure is negligible, isolating JIT and scheduler behaviour
- Variants to benchmark:
  - Single-threaded baseline
  - Multi-threaded (`Parallel.For`) — doubles the dataset and adds scheduling dimension

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
