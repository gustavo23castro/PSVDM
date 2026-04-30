using System.Diagnostics;
using System.Runtime.Versioning;
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Jobs;
using FannkuchBenchmark.Energy;

namespace FannkuchBenchmark;

[MemoryDiagnoser]
[SimpleJob(RuntimeMoniker.Net90)]
[CsvMeasurementsExporter]
[JsonExporter]
[SupportedOSPlatform("linux")]
public class FannkuchBenchmarks
{
    [Params(11, 12)]
    public int N { get; set; }

    private IRaplReader? _rapl;
    private StreamWriter? _energyCsv;
    private int _iteration;
    private long _maxEnergyRange = 0;

    [GlobalSetup]
    public void Setup()
    {
        _rapl = new RaplLinux();
        _iteration = 0;
        _maxEnergyRange = ReadMaxEnergyRange();

        var energyDir = FindResultsDir("energy");
        Directory.CreateDirectory(energyDir);
        var csvPath = Path.Combine(energyDir, "energy_single.csv");
        var isNew = !File.Exists(csvPath);
        _energyCsv = new StreamWriter(csvPath, append: true);
        if (isNew)
            _energyCsv.WriteLine("timestamp,os,variant,n,thread_mode,iteration,pkg_energy_uj,pp0_energy_uj,duration_ms,cpu_temp_before,cpu_temp_after");
    }

    [GlobalCleanup]
    public void Cleanup()
    {
        _energyCsv?.Flush();
        _energyCsv?.Dispose();
        _rapl?.Dispose();
    }

    [Benchmark]
    public (int, int) Run()
    {
        _iteration++;
        var tempBefore = ReadCpuTemp();
        var pkgBefore  = _rapl!.ReadPackageEnergyMicrojoules();
        var pp0Before  = _rapl!.ReadCoresEnergyMicrojoules();

        var sw = Stopwatch.StartNew();
        var result = FannkuchCore.Compute(N);
        sw.Stop();

        var pkgAfter  = _rapl!.ReadPackageEnergyMicrojoules();
        var pp0After  = _rapl!.ReadCoresEnergyMicrojoules();
        var tempAfter = ReadCpuTemp();

        var pkgDelta = pkgAfter >= pkgBefore
            ? pkgAfter - pkgBefore
            : (_maxEnergyRange - pkgBefore) + pkgAfter;
        var pp0Delta = pp0After >= pp0Before
            ? pp0After - pp0Before
            : (_maxEnergyRange - pp0Before) + pp0After;

        _energyCsv!.WriteLine(
            $"{DateTime.UtcNow:o},linux,Fannkuch,{N},multi,{_iteration}," +
            $"{pkgDelta},{pp0Delta},{sw.Elapsed.TotalMilliseconds:F3}," +
            $"{tempBefore:F1},{tempAfter:F1}");

        return result;
    }

    private static double ReadCpuTemp()
    {
        const string path = "/sys/class/thermal/thermal_zone14/temp";
        try { return int.Parse(File.ReadAllText(path).Trim()) / 1000.0; }
        catch { return -1; }
    }

    private static string FindResultsDir(string subdir)
    {
        var root = Environment.GetEnvironmentVariable("BENCHMARK_RESULTS_ROOT");
        if (root is null)
            throw new InvalidOperationException(
                "BENCHMARK_RESULTS_ROOT is not set. " +
                "Use scripts/run-linux.sh to launch benchmarks.");
        return Path.Combine(root, "linux", subdir);
    }

    private static long ReadMaxEnergyRange()
    {
        const string path = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/max_energy_range_uj";
        try { return long.Parse(File.ReadAllText(path).Trim()); }
        catch { return 262143328850; } // Coffee Lake fallback
    }
}
