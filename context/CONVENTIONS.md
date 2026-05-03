# Code Conventions & Project Standards

## General

- Language: **C# 13** (with .NET 9)
- Style: Microsoft default C# conventions
- All benchmark logic must be **identical** between Windows and Linux projects
- Only the `Energy/` layer differs between platforms
- No third-party logging frameworks — use `Console.WriteLine` for diagnostic output
- No dependency injection frameworks — keep projects minimal and auditable

---

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Classes | PascalCase | `FannkuchSingleThread` |
| Methods | PascalCase | `RunBenchmark()` |
| Local variables | camelCase | `energyBefore` |
| Constants | UPPER_SNAKE | `MAX_ITERATIONS` |
| Files | Match class name | `FannkuchSingleThread.cs` |
| BDN benchmark methods | `[Benchmark]` + descriptive name | `SingleThread_N10()` |

---

## BenchmarkDotNet Conventions

```csharp
// Always use these attributes on benchmark classes
[MemoryDiagnoser]           // Confirms near-zero allocations
[SimpleJob(RuntimeMoniker.Net90)]
[CsvMeasurementsExporter]   // For results/ folder
[JsonExporter]              // For analysis scripts

public class FannkuchSingleThread
{
    [Params(10, 11)]        // n values — drives problem size
    public int N;

    [Benchmark]
    public int Run() => Fannkuch.Compute(N);
}
```

- Never put setup logic inside `[Benchmark]` methods — use `[GlobalSetup]`
- Always specify `[Params]` explicitly rather than hardcoding
- Export results to `../../results/{os}/BenchmarkDotNet.Artifacts/`

---

## Energy Harness Conventions

Both platforms expose the same interface:

```csharp
// Energy/IRaplReader.cs (shared interface + snapshot struct)
public readonly struct RaplSnapshot
{
    public long PackageMicrojoules { get; init; }
    public long CoresMicrojoules   { get; init; }
    public long DramMicrojoules    { get; init; }
}

public interface IRaplReader
{
    long ReadPackageEnergyMicrojoules();
    long ReadCoresEnergyMicrojoules();
    long ReadDramEnergyMicrojoules();
    RaplSnapshot TakeSnapshot(); // captures Package, PP0 (cores), and DRAM
    void Dispose();
}
```

Usage pattern — use `TakeSnapshot()` to read all three domains atomically:

```csharp
var rapl = new RaplLinux(); // or new RaplWindows()
var before = rapl.TakeSnapshot();
// ... run workload ...
var after = rapl.TakeSnapshot();
var pkgJoules  = (after.PackageMicrojoules - before.PackageMicrojoules) / 1_000_000.0;
var dramJoules = (after.DramMicrojoules    - before.DramMicrojoules)    / 1_000_000.0;
```

> ⚠️ RAPL counters wrap around (32-bit accumulator). For Coffee Lake the wrap period
> is ~60 seconds at full load. Always check `after >= before`; if not, add the max counter value.
> Max value is in `/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/max_energy_range_uj` on Linux.

---

## Results File Conventions

BenchmarkDotNet output goes to:
```
results/
  windows/YYYY-MM-DD/BenchmarkDotNet.Artifacts/
  linux/YYYY-MM-DD/BenchmarkDotNet.Artifacts/
```

Energy CSV files (hand-rolled, one row per run):
```
results/
  windows/YYYY-MM-DD/energy/
  linux/YYYY-MM-DD/energy/
```

Energy CSV format:
```
timestamp,os,variant,n,thread_mode,iteration,pkg_energy_uj,pp0_energy_uj,dram_energy_uj,duration_ms,cpu_temp_before,cpu_temp_after
2025-01-15T14:32:00,linux,FannkuchST,11,single,1,45231000,38120000,1250000,1823,52.0,67.0
```

---

## Git Conventions

- Commit messages: `[area] short description` — e.g. `[linux] add RAPL sysfs reader`
- Areas: `linux`, `windows`, `results`, `analysis`, `docs`, `context`
- **Never commit** BenchmarkDotNet build artifacts (`bin/`, `obj/`)
- **Do commit** results CSVs and JSON — they are the research data
- Branch strategy: work on `main` directly (solo project)

---

## .gitignore Essentials

```gitignore
# .NET build artifacts
bin/
obj/
*.user
.vs/
.idea/

# OS noise
.DS_Store
Thumbs.db

# BenchmarkDotNet temp (NOT results)
BenchmarkDotNet.Artifacts/*/bin/

# Python analysis
__pycache__/
.venv/
*.pyc
```
