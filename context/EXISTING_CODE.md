# Existing Code Analysis — PSVDMold

Source path analysed: `../PSVDMold/SVDMBenchmark/SVDMBenchmark/`

---

## 1. Algorithm — FannkuchRedux.cs

### Full implementation

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading; // Adicionado para suportar Thread
using System.Threading.Tasks;
using System.Numerics;
using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

namespace SVDMBenchmark
{
    // Apenas mudamos o nome da classe de Program para FannkuchRedux
    public class FannkuchRedux
    {
        private const int MAX_N = 16;
        private static readonly int[] _factorials = new int[MAX_N + 1];
        private static int _n;
        private static int _checksum;
        private static byte _maxFlips;
        private static int _blockCount;
        private static int _blockSize;

        [MethodImpl(MethodImplOptions.AggressiveOptimization)]
        // Mudamos Main para MainMethod para não conflitar com o Program.cs
        // E mudamos para PUBLIC para o Benchmark o conseguir ver
        public static void MainMethod(string[] args)
        {
            _n = args.Length > 0 ? int.Parse(args[0]) : 12;

            // Start Setup
            var factorials = _factorials;
            factorials[0] = 1;
            var factN = 1;
            for (var x = 0; x < MAX_N;)
            {
                factN *= ++x;
                factorials[x] = factN;
            }

            // End Setup
            // Thread Setup
            var nThreads = 4;
            var maxBlocks = 96 / 4;
            _blockCount = maxBlocks * nThreads;
            _blockSize = factorials[_n] / _blockCount;
            var threads = new Thread[nThreads];
            for (var i = 1; i < nThreads; i++)
                (threads[i] = new Thread(() => pfannkuchThread()) { IsBackground = true, Priority = ThreadPriority.Highest }).Start();
            Console.Out.Write("");
            pfannkuchThread();
            for (var i = 1; i < threads.Length; i++)
                threads[i].Join();
            Console.Out.WriteLineAsync(_checksum + "\nPfannkuchen(" + _n + ") = " + _maxFlips);
        }

        [MethodImpl(MethodImplOptions.AggressiveOptimization)]
        private static void pfannkuchThread()
        {
            var masks_shift = new Vector128<byte>[16];
            var c0 = Vector128<byte>.Zero;
            var c1 = Vector128.Create((byte)1);
            var ramp = Vector128.Create((byte)0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15);
            var ramp1 = Sse2.ShiftRightLogical128BitLane(ramp, 1);
            var vX = Sse2.Subtract(c0, ramp);
            var old = ramp;
            for (var x = 0; x < MAX_N; x++)
            {
                var v2 = Sse41.BlendVariable(vX, ramp, vX);
                var v1 = Sse41.BlendVariable(ramp1, v2, Sse2.Subtract(vX, c1));
                old = Ssse3.Shuffle(old, v1);
                masks_shift[x] = old;
                vX = Sse2.Add(vX, c1);
            }
            // ... (inner loop body — see source file for full listing)
        }
    }
}
```

### Match against CLBG reference

**Not a direct copy of the CLBG C# reference.** Key differences:

- The CLBG C# reference entry uses a scalar loop with `int[]` array manipulation.
- This implementation uses **x86 SIMD intrinsics** (`System.Runtime.Intrinsics.X86`): `Sse2`, `Sse41`, `Ssse3` — it appears to be adapted from a high-performance community submission, not the canonical CLBG entry.
- Threading model is `Thread[]` with manual work-stealing via `Interlocked.Decrement(ref _blockCount)`, not `Parallel.For`.
- `nThreads` is **hardcoded to 4**; not parameterised.
- All state (`_n`, `_checksum`, `_maxFlips`, `_blockCount`, `_blockSize`) is **static mutable** — this is not safe for concurrent BenchmarkDotNet runs without re-initialisation between iterations.
- There is a **duplicate line** at the end of `pfannkuchThread()`: `if (maxFlips > _maxFlips) _maxFlips = (byte)maxFlips;` appears twice (lines 166–167 in source).
- The algorithm is **always multi-threaded** — there is no single-thread variant.
- Requires SSE4.1 + SSSE3 + SSE2 CPU support. The i7-8850H supports all of these, but this implementation will not compile or run on ARM.

---

## 2. Benchmark Class — Program.cs

### Class name and attributes

```csharp
[MemoryDiagnoser]
[SimpleJob(RuntimeMoniker.Net90)]
public class Benchmarks
```

- Class name: `Benchmarks`
- Jobs configured: `[SimpleJob(RuntimeMoniker.Net90)]` — single job, .NET 9 JIT only
- No NativeAOT job configured
- No custom exporters — neither `[CsvMeasurementsExporter]` nor `[JsonExporter]` are present

### `[Params]` values

```csharp
[Params(7, 8, 9, 10, 11, 12)]
public int N { get; set; }
```

Six values: **7, 8, 9, 10, 11, 12**. Values 7, 8, 9 are not in ARCHITECTURE.md's benchmark table, which lists only 10, 11 (single-thread) and 11, 12 (multi-thread).

### `[Benchmark]` methods

One method:

```csharp
[Benchmark]
public void RodarAlgoritmo()
{
    FannkuchRedux.MainMethod(new string[] { N.ToString() });
}
```

- Method name: `RodarAlgoritmo` — **Portuguese**, violates CONVENTIONS.md which requires English names
- No `[GlobalSetup]` — the factorial table and thread setup happen inside `MainMethod` on every call, adding setup overhead into the measured time
- No separate single-thread / multi-thread benchmark classes

### Entry point

```csharp
public class Program
{
    public static void Main(string[] args)
    {
        BenchmarkRunner.Run<Benchmarks>();
    }
}
```

Standard BDN runner. No custom configuration, no output path override, no RAPL integration.

---

## 3. csproj — SVDMBenchmark.csproj

```xml
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="BenchmarkDotNet" Version="0.15.8" />
    <PackageReference Include="BenchmarkDotNet.Diagnostics.Windows" Version="0.15.8" />
  </ItemGroup>

</Project>
```

### Target framework

- `net9.0` — correct, matches ARCHITECTURE.md

### NuGet dependencies

| Package | Version | Note |
|---|---|---|
| `BenchmarkDotNet` | `0.15.8` | ARCHITECTURE.md specifies `0.14.*` — this is a newer release; functionally compatible, version policy to decide |
| `BenchmarkDotNet.Diagnostics.Windows` | `0.15.8` | **Windows-only package** — must not be included in the Linux project |

### Missing build properties

Compared to ARCHITECTURE.md's recommended `<PropertyGroup>`:

| Property | Present? |
|---|---|
| `<AllowUnsafeBlocks>true</AllowUnsafeBlocks>` | ❌ missing |
| `<Optimize>true</Optimize>` | ❌ missing |
| `<Configuration>Release</Configuration>` | ❌ missing |

No `<ArtifactsPath>` or custom output path to redirect BDN results to `results/`.

---

## 4. Gaps vs ARCHITECTURE.md and CONVENTIONS.md

### RAPL integration (IRaplReader)

- **No energy measurement code whatsoever.** `IRaplReader`, `RaplLinux.cs`, `RaplWindows.cs`, and `RaplReaderFactory` are all absent.
- No `energy_before` / `energy_after` reads around the benchmark.
- No energy CSV output.

### Energy CSV export

- No hand-rolled CSV writer for the format specified in CONVENTIONS.md:
  `timestamp,os,variant,n,thread_mode,iteration,pkg_energy_uj,pp0_energy_uj,duration_ms,cpu_temp_before,cpu_temp_after`

### Results output path

- BDN artifacts will land in the default `BenchmarkDotNet.Artifacts/` next to the project — not in `results/linux/BenchmarkDotNet.Artifacts/` as required by CONVENTIONS.md.
- No `ArtifactsPath` set in the csproj or runner config.

### Naming mismatches (CONVENTIONS.md)

| Location | Found | Required |
|---|---|---|
| Namespace | `SVDMBenchmark` | `FannkuchBenchmark` (matches project folder name in ARCHITECTURE.md) |
| Benchmark method | `RodarAlgoritmo()` | English name, e.g. `Run()` |
| Benchmark class | `Benchmarks` (generic) | `FannkuchSingleThread` / `FannkuchMultiThread` (separate classes) |
| `[Params]` | `(7, 8, 9, 10, 11, 12)` | `(10, 11)` for ST; `(11, 12)` for MT |

### Structural gaps

- No separation between single-thread and multi-thread benchmarks — the algorithm always uses 4 threads.
- No `[GlobalSetup]` method — factorial initialisation runs inside every measured iteration.
- `[CsvMeasurementsExporter]` and `[JsonExporter]` attributes missing from benchmark class.
- `BenchmarkDotNet.Diagnostics.Windows` included — incompatible with Linux build.
- Static mutable state in `FannkuchRedux` (`_checksum`, `_maxFlips`, `_blockCount`) is not reset between BDN iterations; results after the first iteration are incorrect.

---

## 5. Reuse Decision

### FannkuchRedux.cs → **copy with significant modifications**

Keep: the SSE2/SSSE3/SSE4.1 SIMD inner loop (`pfannkuchThread`) — it is the performant core and valid on the i7-8850H.

Must change before use:
1. Rename namespace from `SVDMBenchmark` to `FannkuchBenchmark`.
2. Extract the single-thread path: create a `pfannkuchSingle()` variant that runs on one thread without the `Thread[]` / `Interlocked` machinery.
3. Make `nThreads` a parameter instead of hardcoding 4; for `FannkuchMultiThread` pass `Environment.ProcessorCount`.
4. Replace all `static` mutable fields (`_checksum`, `_maxFlips`, `_blockCount`, `_blockSize`, `_n`) with instance or local state — static mutable state is broken under BDN's multi-iteration model.
5. Remove `MainMethod(string[] args)` entry point; expose a clean `Compute(int n)` return-value API instead.
6. Fix the duplicate `if (maxFlips > _maxFlips)` line.
7. Move to `Benchmarks/FannkuchCore.cs` (shared logic) + thin wrappers in `FannkuchSingleThread.cs` / `FannkuchMultiThread.cs`.

### Program.cs → **rewrite**

Nothing in this file is salvageable as-is:
- Benchmark class must be split into `FannkuchSingleThread` and `FannkuchMultiThread`.
- Method names must be English.
- `[Params]` must be corrected.
- `[CsvMeasurementsExporter]` and `[JsonExporter]` must be added.
- RAPL wrapper calls (`IRaplReader`) must be integrated.
- BDN `ArtifactsPath` must be configured to point to `results/`.

### SVDMBenchmark.csproj → **use as base with modifications**

The `net9.0` target and `BenchmarkDotNet` package are the correct starting point. Required changes:
1. Rename project file to `FannkuchBenchmark.csproj`.
2. Remove `BenchmarkDotNet.Diagnostics.Windows` from the Linux project (keep for Windows project only).
3. Add `<AllowUnsafeBlocks>true</AllowUnsafeBlocks>`.
4. Add `LibreHardwareMonitorLib` to Windows project only.
5. Decide on BDN version: ARCHITECTURE.md says `0.14.*`; old project uses `0.15.8`. Use `0.15.8` (newer, same API surface) and update ARCHITECTURE.md to reflect the actual version used.
6. Add `<ArtifactsPath>` or configure output path in `Program.cs` via `IConfig`.

---

## 6. Implementation Notes — src/linux/FannkuchBenchmark (2026-04-30)

### Deviations from the plan

**Energy/ namespace changed**
`IRaplReader.cs` and `RaplLinux.cs` were copied from `src/linux/RaplProbe/Energy/` with one
necessary change: the namespace was updated from `RaplProbe.Energy` to `FannkuchBenchmark.Energy`.
The implementation is otherwise verbatim.

**Static state replaced with `RunState` class**
All five static mutable fields (`_n`, `_checksum`, `_maxFlips`, `_blockCount`, `_blockSize`) were
replaced by a private sealed `RunState` class allocated once per `ComputeSingle`/`ComputeMulti`
call.  `_factorials` was kept as a `static readonly` field (initialized in a static constructor)
because it is constant across all runs.

**`_maxFlips` type changed from `byte` to `int`**
The original used `byte` for `_maxFlips` (max value 255), which is sufficient for any realistic N.
Changed to `int` in `RunState` to allow atomic CAS via `Interlocked.CompareExchange(ref int, ...)`.
This has no correctness impact for N ≤ 16.

**Thread-safe `MaxFlips` update**
The original's non-atomic `if (maxFlips > _maxFlips) _maxFlips = (byte)maxFlips;` was replaced
with an `Interlocked.CompareExchange` CAS loop on `RunState.MaxFlips`.

**Duplicate line removed**
The duplicate `if (maxFlips > _maxFlips) _maxFlips = (byte)maxFlips;` at lines 166–167 of the
original was removed; only one CAS loop now exists at the end of `PfannkuchThread`.

**Block count formula for single-thread**
`ComputeSingle` uses `blockCount = 24 * 1 = 24` blocks (original used 96 with 4 threads).
The single calling thread consumes all 24 blocks sequentially, covering the full permutation space.

**`[SupportedOSPlatform("linux")]` added to benchmark classes**
Both `FannkuchSingleThread` and `FannkuchMultiThread` were annotated with
`[SupportedOSPlatform("linux")]` to suppress CA1416 warnings from the `new RaplLinux()` call
inside `[GlobalSetup]`. This produces zero warnings on build.

**Energy CSV path uses repo-root finder**
The benchmark classes compute the energy CSV path by walking up from `AppContext.BaseDirectory`
until `PSVDM.sln` is found, then resolving `results/linux/energy/`.  This is robust regardless of
where `dotnet run` is invoked or how deep BDN's child process output directory is.
BDN's own `WithArtifactsPath` uses the `../../../../...` relative path specified in the task
(resolved from the child process working directory inside `bin/`).

**BDN artifacts path resolves inside `bin/`**
The 4-`..`-level relative path in `Program.cs` resolves from the BDN child process directory
(`bin/Release/net9.0/FannkuchBenchmark-.NET 9.0-1/bin/Release/net9.0/`) to
`bin/Release/net9.0/results/linux/BenchmarkDotNet.Artifacts/`.
This keeps BDN artifacts inside `bin/` rather than the repo-level `results/` directory.
For authoritative data collection, prefer the hand-rolled energy CSV (in `results/linux/energy/`)
or adjust the path to use an absolute route via `AppContext.BaseDirectory` before real runs.

### Verification (2026-04-30)

| Criterion | Result |
|---|---|
| `dotnet build -c Release` — zero warnings | ✅ 0 warnings, 0 errors |
| `--list flat` shows both Run methods | ✅ `FannkuchSingleThread.Run`, `FannkuchMultiThread.Run` |
| `--filter *SingleThread* --job Dry` — no errors | ✅ Completed 4 benchmark variants |
| Energy CSV created in `results/linux/energy/` | ✅ `energy_single.csv` with correct columns |
| No static mutable state in `FannkuchCore` | ✅ All state in `RunState` per call |
