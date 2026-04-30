using System.Runtime.Versioning;
using System.Text;
using RaplProbe.Energy;

[assembly: SupportedOSPlatform("linux")]

Console.OutputEncoding = Encoding.UTF8;

const int SAMPLES     = 10;
const int INTERVAL_MS = 1_000;

const string OUTPUT_DIR  = "results/linux";
const string OUTPUT_FILE = $"{OUTPUT_DIR}/rapl-probe-sample.txt";

RaplLinux rapl;
try
{
    rapl = new RaplLinux();
}
catch (InvalidOperationException ex)
{
    Console.Error.WriteLine("ERROR: RAPL initialisation failed.\n");
    Console.Error.WriteLine(ex.Message);
    return 1;
}

using (rapl)
{
    Directory.CreateDirectory(OUTPUT_DIR);
    using var file   = new StreamWriter(OUTPUT_FILE, append: false, Encoding.UTF8);
    using var output = new TeeWriter(Console.Out, file);

    output.WriteLine("=== Linux RAPL Energy Probe ===");
    output.WriteLine($"Samples : {SAMPLES} × {INTERVAL_MS} ms");
    output.WriteLine($"Output  : {OUTPUT_FILE}");
    output.WriteLine();
    output.WriteLine($"{"[HH:mm:ss]",-12} {"pkg_µJ",16} {"core_µJ",16} {"uncore_µJ",16} {"dram_µJ",16} {"delta_pkg_µJ",16}");
    output.WriteLine(new string('-', 94));

    RaplSnapshot? prev    = null;
    RaplSnapshot  first   = default;
    RaplSnapshot  current = default;

    for (int i = 0; i < SAMPLES; i++)
    {
        current = rapl.TakeSnapshot();

        if (i == 0) first = current;

        long deltaPkg = prev.HasValue
            ? rapl.Delta(prev.Value.PackageMicrojoules, current.PackageMicrojoules)
            : 0;

        string ts = current.Timestamp.ToString("HH:mm:ss");
        output.WriteLine(
            $"[{ts}]   " +
            $"{current.PackageMicrojoules,16:N0} " +
            $"{current.CoresMicrojoules,16:N0} " +
            $"{current.UncoreMicrojoules,16:N0} " +
            $"{current.DramMicrojoules,16:N0} " +
            $"{deltaPkg,16:N0}");

        prev = current;

        if (i < SAMPLES - 1)
            Thread.Sleep(INTERVAL_MS);
    }

    output.WriteLine();
    output.WriteLine("=== Totals ===");

    long totalPkg    = rapl.Delta(first.PackageMicrojoules,  current.PackageMicrojoules);
    long totalCore   = rapl.Delta(first.CoresMicrojoules,    current.CoresMicrojoules);
    long totalUncore = rapl.Delta(first.UncoreMicrojoules,   current.UncoreMicrojoules);
    long totalDram   = rapl.Delta(first.DramMicrojoules,     current.DramMicrojoules);

    output.WriteLine($"  package : {totalPkg,16:N0} µJ  ({totalPkg / 1_000_000.0:F4} J)");
    output.WriteLine($"  core    : {totalCore,16:N0} µJ  ({totalCore / 1_000_000.0:F4} J)");
    output.WriteLine($"  uncore  : {totalUncore,16:N0} µJ  ({totalUncore / 1_000_000.0:F4} J)");
    output.WriteLine($"  dram    : {totalDram,16:N0} µJ  ({totalDram / 1_000_000.0:F4} J)");
    output.WriteLine();
    output.WriteLine($"Results saved to: {OUTPUT_FILE}");
}

return 0;

// ---------------------------------------------------------------------------

// Writes every line to two TextWriters simultaneously.
sealed class TeeWriter(TextWriter a, TextWriter b) : TextWriter
{
    public override Encoding Encoding => a.Encoding;

    public override void WriteLine(string? value)
    {
        a.WriteLine(value);
        b.WriteLine(value);
    }

    public override void WriteLine()
    {
        a.WriteLine();
        b.WriteLine();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing) { a.Flush(); b.Flush(); }
        base.Dispose(disposing);
    }
}
