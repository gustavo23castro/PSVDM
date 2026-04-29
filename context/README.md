# csharp-energy-benchmark

Benchmarking C# execution performance and energy consumption on Windows 11 vs Ubuntu 24.04, using the same physical hardware (dual-boot).

**Algorithm**: FannkuchRedux (CPU-bound, Computer Language Benchmarks Game)  
**Hardware**: HP EliteBook 1050 G1 — Intel Core i7-8850H, 16 GiB RAM  
**Energy measurement**: Intel RAPL hardware counters (direct, not estimated)

## Repository Structure

```
├── context/        # Project context for Claude Code sessions
├── src/
│   ├── windows/    # .NET 9 project with LibreHardwareMonitorLib (RAPL)
│   └── linux/      # .NET 9 project with sysfs powercap RAPL reader
├── results/
│   ├── windows/    # BenchmarkDotNet output + energy CSVs
│   └── linux/
├── docs/           # Report, presentation, article drafts
├── scripts/        # Environment setup (Linux shell + Windows PowerShell)
└── analysis/       # Python scripts for statistical analysis and plots
```

## Quick Start

### Linux
```bash
# Setup environment
./scripts/setup-linux.sh

# Run benchmarks
cd src/linux/FannkuchBenchmark
dotnet run -c Release
```

### Windows (PowerShell, as Administrator)
```powershell
# Setup environment
.\scripts\setup-windows.ps1

# Run benchmarks
cd src\windows\FannkuchBenchmark
dotnet run -c Release
```

## Context Files

See [`context/`](context/) for full project documentation used with Claude Code:
- [`PROJECT.md`](context/PROJECT.md) — objectives and research questions
- [`HARDWARE.md`](context/HARDWARE.md) — machine specs and environment config
- [`ARCHITECTURE.md`](context/ARCHITECTURE.md) — tool decisions and measurement strategy
- [`CONVENTIONS.md`](context/CONVENTIONS.md) — code style and project structure
- [`NOTES.pt.md`](context/NOTES.pt.md) — notas em português
