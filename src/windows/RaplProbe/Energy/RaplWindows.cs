using LibreHardwareMonitor.Hardware;

namespace RaplProbe.Energy;

// Snapshot of all RAPL domains captured in a single hardware.Update() call.
public readonly struct RaplSnapshot
{
    public DateTime Timestamp        { get; init; }
    public long     PackageMicrojoules { get; init; }
    public long     CoresMicrojoules   { get; init; }
    public long?    UncoreMicrojoules  { get; init; }
    public long?    DramMicrojoules    { get; init; }
}

// Wraps LibreHardwareMonitorLib to expose Intel RAPL domains as cumulative µJ counters.
// Requires the process to run as Administrator.
// LHM exposes RAPL as instantaneous Watts (derived internally from MSR deltas).
// This class integrates those power readings over elapsed wall-clock time to produce µJ.
public sealed class RaplWindows : IRaplReader, IDisposable
{
    private readonly Computer  _computer;
    private readonly IHardware _cpu;

    private readonly ISensor? _packagePower;
    private readonly ISensor? _coresPower;
    private readonly ISensor? _uncorePower;
    private readonly ISensor? _dramPower;

    private long _packageUj;
    private long _coresUj;
    private long _uncoreUj;
    private long _dramUj;
    private long _lastTickMs;
    private long _lastRefreshMs = -1;

    public bool IsPackageAvailable => _packagePower is not null;
    public bool IsCoresAvailable   => _coresPower   is not null;
    public bool IsUncoreAvailable  => _uncorePower  is not null;
    public bool IsDramAvailable    => _dramPower    is not null;

    public string CpuName => _cpu.Name;

    // Returns all Power sensors found on the CPU — used for diagnostics.
    public IEnumerable<(string Name, float? Value)> AllPowerSensors()
        => _cpu.Sensors
               .Where(s => s.SensorType == SensorType.Power)
               .Select(s => (s.Name, s.Value));

    // True if at least one sensor returned a non-zero value after the first Refresh().
    // False indicates the kernel driver (WinRing0) could not read the MSRs.
    public bool IsDriverReadingMsrs =>
        (_packagePower?.Value ?? 0f) != 0f ||
        (_coresPower?.Value   ?? 0f) != 0f ||
        (_dramPower?.Value    ?? 0f) != 0f;

    public RaplWindows()
    {
        _computer = new Computer { IsCpuEnabled = true };
        _computer.Open();

        _cpu = _computer.Hardware.FirstOrDefault(h => h.HardwareType == HardwareType.Cpu)
               ?? throw new InvalidOperationException(
                   "LibreHardwareMonitorLib did not find any CPU hardware. " +
                   "Make sure the process is running as Administrator.");

        _cpu.Update();

        foreach (var sensor in _cpu.Sensors)
        {
            if (sensor.SensorType != SensorType.Power) continue;
            switch (sensor.Name)
            {
                case "CPU Package":  _packagePower = sensor; break;
                case "CPU Cores":    _coresPower   = sensor; break;
                case "CPU Graphics": _uncorePower  = sensor; break;
                case "CPU Memory":   _dramPower    = sensor; break;
            }
        }

        _lastTickMs = Environment.TickCount64;
    }

    // Refreshes sensors and accumulates energy. Time-gated to avoid double-counting
    // when multiple Read methods are called in the same millisecond.
    public void Refresh()
    {
        long now = Environment.TickCount64;
        if (now == _lastRefreshMs) return;

        _cpu.Update();

        double elapsedSeconds = (now - _lastTickMs) / 1_000.0;
        _lastTickMs    = now;
        _lastRefreshMs = now;

        _packageUj += ToMicrojoules(_packagePower?.Value, elapsedSeconds);
        _coresUj   += ToMicrojoules(_coresPower?.Value,   elapsedSeconds);
        _uncoreUj  += ToMicrojoules(_uncorePower?.Value,  elapsedSeconds);
        _dramUj    += ToMicrojoules(_dramPower?.Value,     elapsedSeconds);
    }

    // Returns a consistent snapshot of all domains from a single Refresh() call.
    public RaplSnapshot TakeSnapshot()
    {
        Refresh();
        return new RaplSnapshot
        {
            Timestamp         = DateTime.Now,
            PackageMicrojoules = _packageUj,
            CoresMicrojoules   = _coresUj,
            UncoreMicrojoules  = IsUncoreAvailable ? _uncoreUj : null,
            DramMicrojoules    = IsDramAvailable   ? _dramUj   : null,
        };
    }

    // IRaplReader — each call does a single Refresh before returning the cumulative total.
    public long ReadPackageEnergyMicrojoules() { Refresh(); return _packageUj; }
    public long ReadCoresEnergyMicrojoules()   { Refresh(); return _coresUj;   }

    public void Dispose() => _computer.Close();

    private static long ToMicrojoules(float? watts, double elapsedSeconds)
        => watts.HasValue ? (long)(watts.Value * elapsedSeconds * 1_000_000) : 0L;
}
