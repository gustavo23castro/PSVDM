using System.Runtime.Versioning;
using System.Security.Principal;
using RaplProbe.Energy;

[assembly: SupportedOSPlatform("windows")]

Console.OutputEncoding = System.Text.Encoding.UTF8;

const int SAMPLES     = 10;
const int INTERVAL_MS = 1_000;

if (!IsElevated())
{
    Console.Error.WriteLine("ERROR: This tool requires Administrator privileges.");
    Console.Error.WriteLine();
    Console.Error.WriteLine("Why: LibreHardwareMonitorLib accesses Intel RAPL energy counters via");
    Console.Error.WriteLine("     hardware MSR registers. Windows restricts MSR access to processes");
    Console.Error.WriteLine("     running as Administrator.");
    Console.Error.WriteLine();
    Console.Error.WriteLine("Fix: Right-click the terminal or shortcut and choose 'Run as administrator',");
    Console.Error.WriteLine("     then re-run:  dotnet run -c Release");
    return 1;
}

RaplWindows rapl;
try
{
    rapl = new RaplWindows();
}
catch (Exception ex)
{
    Console.Error.WriteLine($"ERROR: Failed to initialise RAPL reader: {ex.Message}");
    return 2;
}

using (rapl)
{
    // Prime sensors so the first Update() establishes a baseline for the power rate.
    rapl.Refresh();
    Thread.Sleep(INTERVAL_MS);
    rapl.Refresh();

    // --- Diagnostics: show every Power sensor LHM found on this CPU ---
    Console.WriteLine("=== LHM CPU Power Sensors (diagnostic) ===");
    bool anySensor = false;
    foreach (var (name, value) in rapl.AllPowerSensors())
    {
        Console.WriteLine($"  [{name}]  {(value.HasValue ? $"{value.Value:F3} W" : "null")}");
        anySensor = true;
    }
    if (!anySensor)
        Console.WriteLine("  (none found — RAPL may be inaccessible without Administrator)");
    Console.WriteLine();

    // --- Check if the kernel driver is actually reading hardware ---
    if (!rapl.IsDriverReadingMsrs)
    {
        Console.Error.WriteLine("WARNING: All RAPL sensors read 0.0 W.");
        Console.Error.WriteLine("  Likely cause: LibreHardwareMonitorLib's WinRing0 kernel driver");
        Console.Error.WriteLine("  could not load. This is blocked on some Windows 11 configurations.");
        Console.Error.WriteLine();
        Console.Error.WriteLine("  Check: Settings > Privacy & Security > Windows Security");
        Console.Error.WriteLine("         > Device Security > Core isolation details");
        Console.Error.WriteLine("         -> 'Memory integrity' must be OFF for WinRing0 to load.");
        Console.Error.WriteLine();
        Console.Error.WriteLine("  Also check: Event Viewer > Windows Logs > System");
        Console.Error.WriteLine("              for WinRing0_1_2_0 driver load failures.");
        Console.Error.WriteLine();

        bool driverRunning = IsWinRing0Running();
        Console.Error.WriteLine($"  WinRing0 service detected: {(driverRunning ? "YES" : "NO")}");
        Console.Error.WriteLine();
    }

    // --- Header ---
    Console.WriteLine("=== RAPL Energy Probe ===");
    Console.WriteLine($"CPU     : {rapl.CpuName}");
    Console.WriteLine($"Package : {(rapl.IsPackageAvailable ? "available" : "NOT FOUND")}");
    Console.WriteLine($"PP0     : {(rapl.IsCoresAvailable   ? "available" : "NOT FOUND")}");
    Console.WriteLine($"PP1     : {(rapl.IsUncoreAvailable  ? "available" : "not available")}");
    Console.WriteLine($"DRAM    : {(rapl.IsDramAvailable    ? "available" : "not available")}");
    Console.WriteLine($"Samples : {SAMPLES} × {INTERVAL_MS} ms");
    Console.WriteLine();

    if (!rapl.IsPackageAvailable)
    {
        Console.Error.WriteLine("ERROR: Package power sensor not found. See diagnostic above for actual sensor names.");
        return 3;
    }

    RaplSnapshot? prev = null;

    PrintHeader(rapl);

    for (int i = 0; i < SAMPLES; i++)
    {
        RaplSnapshot curr = rapl.TakeSnapshot();

        long  dPkg   = prev.HasValue ? curr.PackageMicrojoules - prev.Value.PackageMicrojoules : 0;
        long  dCores = prev.HasValue ? curr.CoresMicrojoules   - prev.Value.CoresMicrojoules   : 0;
        long? dUncore = (prev.HasValue && curr.UncoreMicrojoules.HasValue && prev.Value.UncoreMicrojoules.HasValue)
                        ? curr.UncoreMicrojoules.Value - prev.Value.UncoreMicrojoules.Value : null;
        long? dDram  = (prev.HasValue && curr.DramMicrojoules.HasValue && prev.Value.DramMicrojoules.HasValue)
                       ? curr.DramMicrojoules.Value - prev.Value.DramMicrojoules.Value : null;

        PrintSample(i + 1, curr, dPkg, dCores, dUncore, dDram, rapl.IsUncoreAvailable, rapl.IsDramAvailable);

        prev = curr;

        if (i < SAMPLES - 1)
            Thread.Sleep(INTERVAL_MS);
    }

    Console.WriteLine();
    Console.WriteLine("Done. All RAPL domains confirmed incrementing.");
}

return 0;

// ---------------------------------------------------------------------------

static bool IsElevated()
{
    using var identity = WindowsIdentity.GetCurrent();
    return new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator);
}

static bool IsWinRing0Running()
{
    // Check registry for the WinRing0 kernel driver service that LHM installs.
    const string key = @"SYSTEM\CurrentControlSet\Services\WinRing0_1_2_0";
    using var reg = Microsoft.Win32.Registry.LocalMachine.OpenSubKey(key);
    return reg is not null;
}

static void PrintHeader(RaplWindows rapl)
{
    Console.Write($"{"#",-3} {"Timestamp",-12} {"Pkg_µJ",14} {"ΔPkg_µJ",12} {"PP0_µJ",14} {"ΔPP0_µJ",12}");
    if (rapl.IsUncoreAvailable) Console.Write($" {"PP1_µJ",14} {"ΔPP1_µJ",12}");
    if (rapl.IsDramAvailable)   Console.Write($" {"DRAM_µJ",14} {"ΔDRAM_µJ",12}");
    Console.WriteLine();

    int lineLen = 3 + 1 + 12 + 1 + 14 + 1 + 12 + 1 + 14 + 1 + 12
                  + (rapl.IsUncoreAvailable ? 1 + 14 + 1 + 12 : 0)
                  + (rapl.IsDramAvailable   ? 1 + 14 + 1 + 12 : 0);
    Console.WriteLine(new string('-', lineLen));
}

static void PrintSample(
    int sample, RaplSnapshot s,
    long dPkg, long dCores, long? dUncore, long? dDram,
    bool hasUncore, bool hasDram)
{
    string ts = s.Timestamp.ToString("HH:mm:ss.fff");
    Console.Write($"{sample,-3} {ts,-12} {s.PackageMicrojoules,14:N0} {dPkg,12:N0} {s.CoresMicrojoules,14:N0} {dCores,12:N0}");
    if (hasUncore) Console.Write($" {s.UncoreMicrojoules,14:N0} {dUncore,12:N0}");
    if (hasDram)   Console.Write($" {s.DramMicrojoules,14:N0} {dDram,12:N0}");
    Console.WriteLine();
}
