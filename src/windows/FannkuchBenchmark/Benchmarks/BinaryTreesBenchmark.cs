using System.Diagnostics;
using System.Globalization;
using System.Runtime.Versioning;
using BenchmarkDotNet.Attributes;
using FannkuchBenchmark.Energy;

namespace FannkuchBenchmark;

[MemoryDiagnoser]
[CsvMeasurementsExporter]
[JsonExporter]
[SupportedOSPlatform("windows")]
public class BinaryTreesBenchmark
{
    [Params(16, 18)]
    public int N { get; set; }

    private IRaplReader? _rapl;
    private StreamWriter? _energyCsv;
    private int _iteration;

    // LHM-derived counters accumulate in software and never wrap, so the
    // wraparound branch in Run() is dead code on Windows. The field exists
    // only to keep delta logic identical to the Linux benchmark.
    private readonly long _maxEnergyRange = long.MaxValue;

    [GlobalSetup]
    public void Setup()
    {
        _rapl = new RaplWindows();
        _iteration = 0;

        var energyDir = FindResultsDir("energy");
        Directory.CreateDirectory(energyDir);
        var csvPath = Path.Combine(energyDir, "energy_bt_windows.csv");
        var isNew = !File.Exists(csvPath);
        _energyCsv = new StreamWriter(csvPath, append: true);
        if (isNew)
            _energyCsv.WriteLine("timestamp,os,variant,n,thread_mode,iteration,pkg_energy_uj,pp0_energy_uj,dram_energy_uj,duration_ms,cpu_temp_before,cpu_temp_after");
    }

    [GlobalCleanup]
    public void Cleanup()
    {
        _energyCsv?.Flush();
        _energyCsv?.Dispose();
        _rapl?.Dispose();
    }

    [Benchmark]
    public (int, int, int[]) Run()
    {
        _iteration++;
        var tempBefore = ReadCpuTemp();
        var before = _rapl!.TakeSnapshot();

        var sw = Stopwatch.StartNew();
        var result = BinaryTreesCore.Compute(N);
        sw.Stop();

        var after = _rapl!.TakeSnapshot();
        var tempAfter = ReadCpuTemp();

        var pkgDelta = after.PackageMicrojoules >= before.PackageMicrojoules
            ? after.PackageMicrojoules - before.PackageMicrojoules
            : (_maxEnergyRange - before.PackageMicrojoules) + after.PackageMicrojoules;
        var pp0Delta = after.CoresMicrojoules >= before.CoresMicrojoules
            ? after.CoresMicrojoules - before.CoresMicrojoules
            : (_maxEnergyRange - before.CoresMicrojoules) + after.CoresMicrojoules;
        var dramDelta = after.DramMicrojoules >= before.DramMicrojoules
            ? after.DramMicrojoules - before.DramMicrojoules
            : (_maxEnergyRange - before.DramMicrojoules) + after.DramMicrojoules;

        // Force invariant culture: pt-PT uses ',' as the decimal separator, which
        // would clash with the CSV field delimiter and corrupt the output.
        var inv = CultureInfo.InvariantCulture;
        _energyCsv!.WriteLine(
            $"{DateTime.UtcNow:o},windows,BinaryTrees,{N},multi,{_iteration}," +
            $"{pkgDelta},{pp0Delta},{dramDelta},{sw.Elapsed.TotalMilliseconds.ToString("F3", inv)}," +
            $"{tempBefore.ToString("F1", inv)},{tempAfter.ToString("F1", inv)}");

        return result;
    }

    private static double ReadCpuTemp() => -1;

    private static string FindResultsDir(string subdir)
    {
        var root = Environment.GetEnvironmentVariable("BENCHMARK_RESULTS_ROOT");
        if (root is null)
            throw new InvalidOperationException(
                "BENCHMARK_RESULTS_ROOT is not set. " +
                "Use scripts/run-windows.ps1 to launch benchmarks.");
        return Path.Combine(root, "windows", subdir);
    }
}
