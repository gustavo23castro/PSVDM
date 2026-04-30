# Architecture & Measurement Strategy

## Tool Decisions

### Performance Measurement: BenchmarkDotNet

- **Repo**: https://github.com/dotnet/BenchmarkDotNet
- **Why**: Industry standard for .NET microbenchmarking. Handles JIT warm-up, GC pauses, statistical analysis, and outlier detection automatically.
- **Key features used**:
  - `[Benchmark]` attribute on methods
  - `Job.Default` with explicit iteration counts
  - `MemoryDiagnoser` to confirm near-zero allocations (expected for FannkuchRedux)
  - CSV/JSON exporters for results
- **Do NOT use**: BenchmarkDotNet's built-in energy diagnoser — it is not available cross-platform with RAPL precision. Use our own harness instead.

### Energy Measurement: RAPL direct access (NOT CodeCarbon)

CodeCarbon was evaluated and **rejected** for this project because:
- On Windows it falls back to TDP-based estimation, not real measurement
- Creates methodological asymmetry between OS environments
- Not reproducible or citable at hardware level

**Chosen approach: read RAPL hardware counters directly on both platforms.**

#### Linux
```
/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj   ← Package energy (microjoules)
/sys/class/powercap/intel-rapl/intel-rapl:0:0/energy_uj ← PP0 / cores
```
Read before and after benchmark run. Delta = energy consumed in µJ.

#### Windows
- **Library**: `LibreHardwareMonitorLib` (NuGet)
- **Version**: 0.9.x (supports .NET 9)
- **Requires**: Run as Administrator
- **Sensor path**: `Computer → CPU → Power (Watts)` — integrate over time to get Joules

---

## Project Structure

```
csharp-energy-benchmark/
├── context/                    # This folder — Claude Code context
├── src/
│   ├── windows/
│   │   └── FannkuchBenchmark/
│   │       ├── FannkuchBenchmark.csproj   (.NET 9, Windows TFM)
│   │       ├── Benchmarks/
│   │       │   ├── FannkuchCore.cs          (Energy-Languages reference algorithm)
│   │       │   └── FannkuchBenchmarks.cs    (BDN benchmark class)
│   │       ├── Energy/
│   │       │   └── RaplWindows.cs          (LibreHardwareMonitorLib wrapper)
│   │       └── Program.cs
│   └── linux/
│       └── FannkuchBenchmark/
│           ├── FannkuchBenchmark.csproj   (.NET 9, Linux TFM)
│           ├── Benchmarks/
│           │   ├── FannkuchCore.cs          (Energy-Languages reference algorithm)
│           │   └── FannkuchBenchmarks.cs    (BDN benchmark class)
│           ├── Energy/
│           │   └── RaplLinux.cs             (powercap sysfs reader)
│           └── Program.cs
├── results/
│   ├── windows/
│   │   ├── BenchmarkDotNet.Artifacts/
│   │   └── energy/
│   └── linux/
│       ├── BenchmarkDotNet.Artifacts/
│       └── energy/
├── docs/
├── scripts/
│   ├── setup-linux.sh
│   └── setup-windows.ps1
├── analysis/                   # Python scripts for plotting and stats
│   └── compare_results.py
├── .gitignore
└── README.md
```

---

## Measurement Protocol

### Per benchmark run:

1. Verify environment (AC power, governor, turbo disabled)
2. Let CPU idle for 5 minutes
3. Read RAPL baseline (`energy_before`)
4. Start BenchmarkDotNet run
5. Read RAPL after (`energy_after`)
6. `energy_consumed_J = (energy_after - energy_before) / 1_000_000`
7. Record: time (BDN), energy (J), CPU temp (before/after), ambient conditions

### Statistical requirements:
- Minimum **30 iterations** per benchmark variant
- Report: Mean, Median, StdDev, P95, P99
- Discard runs where CPU temp exceeded **85°C** during measurement (throttle indicator)
- Use BenchmarkDotNet's outlier detection on timing data

---

## Benchmark Variants

> **Algorithm:** Energy-Languages reference implementation
> ([greensoftwarelab/Energy-Languages](https://github.com/greensoftwarelab/Energy-Languages/tree/master/CSharp/fannkuch-redux)).
> Contributed by Isaac Gouy, transliterated from Oleg Mazurov's Java program;
> concurrency fix and minor improvements by Peperud.
> The algorithm is inherently multi-threaded (`Environment.ProcessorCount + 1` Task threads,
> `NCHUNKS = 150` work-stealing chunks). `[Params(11, 12)]` — N=10 was dropped due to
> thermal instability from short run duration.

| Variant | Description | Expected insight |
|---|---|---|
| `FannkuchBenchmarks_N11` | n=11 | Baseline JIT + energy signal |
| `FannkuchBenchmarks_N12` | n=12 | Longer run, better statistical coverage |

---

## .NET Configuration

```xml
<!-- Both projects -->
<PropertyGroup>
  <TargetFramework>net9.0</TargetFramework>
  <AllowUnsafeBlocks>true</AllowUnsafeBlocks>  <!-- may be needed for RAPL on Linux -->
  <Optimize>true</Optimize>
  <Configuration>Release</Configuration>
</PropertyGroup>
```

**Always build and run in `Release` configuration.** BenchmarkDotNet enforces this but make it explicit.

---

## Dependencies

### Windows project

```xml
<PackageReference Include="BenchmarkDotNet" Version="0.14.*" />
<PackageReference Include="LibreHardwareMonitorLib" Version="0.9.*" />
```

### Linux project

```xml
<PackageReference Include="BenchmarkDotNet" Version="0.14.*" />
<!-- No LibreHardwareMonitorLib — use sysfs directly -->
```
