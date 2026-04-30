using System.Runtime.Versioning;

namespace RaplProbe.Energy;

// Snapshot of all RAPL domains from a single sysfs read pass.
public readonly struct RaplSnapshot
{
    public DateTime Timestamp          { get; init; }
    public long     PackageMicrojoules { get; init; }
    public long     CoresMicrojoules   { get; init; }
    public long     UncoreMicrojoules  { get; init; }
    public long     DramMicrojoules    { get; init; }
}

// Reads Intel RAPL energy counters via the powercap sysfs interface.
// Uses /sys/devices/virtual/powercap/ paths — /sys/class/powercap/ symlinks
// do NOT work for subdomain access on this machine (HP EliteBook 1050 G1).
// Requires either root or a udev rule granting world-read on energy_uj files:
//   /etc/udev/rules.d/99-rapl.rules
[SupportedOSPlatform("linux")]
public sealed class RaplLinux : IRaplReader, IDisposable
{
    private const string BASE = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0";

    private static readonly string PathPackage  = $"{BASE}/energy_uj";
    private static readonly string PathCore     = $"{BASE}/intel-rapl:0:0/energy_uj";
    private static readonly string PathUncore   = $"{BASE}/intel-rapl:0:1/energy_uj";
    private static readonly string PathDram     = $"{BASE}/intel-rapl:0:2/energy_uj";
    private static readonly string PathMaxRange = $"{BASE}/max_energy_range_uj";

    private readonly long _maxRange;

    public RaplLinux()
    {
        CheckReadability(PathPackage);
        CheckReadability(PathCore);
        CheckReadability(PathUncore);
        CheckReadability(PathDram);

        _maxRange = ReadRaw(PathMaxRange);
    }

    // Returns a consistent snapshot of all four domains.
    public RaplSnapshot TakeSnapshot() => new()
    {
        Timestamp          = DateTime.Now,
        PackageMicrojoules = ReadPackageEnergyMicrojoules(),
        CoresMicrojoules   = ReadCoresEnergyMicrojoules(),
        UncoreMicrojoules  = ReadRaw(PathUncore),
        DramMicrojoules    = ReadRaw(PathDram),
    };

    public long ReadPackageEnergyMicrojoules() => ReadRaw(PathPackage);
    public long ReadCoresEnergyMicrojoules()   => ReadRaw(PathCore);

    public void Dispose() { }

    // Computes delta accounting for counter wraparound (32-bit accumulator on Coffee Lake,
    // wraps at _maxRange µJ — roughly every 60 s at full load).
    public long Delta(long before, long after)
        => after >= before ? after - before : (_maxRange - before) + after;

    private static long ReadRaw(string path)
        => long.Parse(File.ReadAllText(path).Trim());

    private static void CheckReadability(string path)
    {
        if (!File.Exists(path))
            ThrowPermissionError(path, "file not found");

        try
        {
            File.ReadAllText(path);
        }
        catch (UnauthorizedAccessException)
        {
            ThrowPermissionError(path, "permission denied");
        }
    }

    private static void ThrowPermissionError(string path, string reason)
    {
        throw new InvalidOperationException(
            $"Cannot read RAPL energy file ({reason}):\n" +
            $"  {path}\n\n" +
            $"Fix: create /etc/udev/rules.d/99-rapl.rules with the following content,\n" +
            $"     then run 'sudo udevadm trigger' or reboot:\n\n" +
            $"  ACTION==\"add\", SUBSYSTEM==\"powercap\", KERNEL==\"intel-rapl:*\", " +
            $"ATTR{{energy_uj}}==\"*\", RUN+=\"/bin/chmod o+r /sys%p/energy_uj\"\n\n" +
            $"Or apply permissions manually right now (temporary, resets on reboot):\n" +
            $"  sudo chmod o+r /sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/energy_uj\n" +
            $"  sudo chmod o+r /sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/energy_uj\n" +
            $"  sudo chmod o+r /sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:1/energy_uj\n" +
            $"  sudo chmod o+r /sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:2/energy_uj");
    }
}
