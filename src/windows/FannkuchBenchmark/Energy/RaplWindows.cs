using System.Reflection;
using LibreHardwareMonitor.Hardware;

namespace FannkuchBenchmark.Energy;

// Reads Intel RAPL MSR_PKG_ENERGY_STATUS (0x611) and MSR_PP0_ENERGY_STATUS (0x639)
// directly via the WinRing0 kernel driver loaded by LibreHardwareMonitorLib.
// Equivalent to Linux's /sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/energy_uj —
// a true cumulative µJ counter, not an integrated Watts × Δt approximation.
// Requires the process to run as Administrator.
public sealed class RaplWindows : IRaplReader, IDisposable
{
    private const uint MSR_RAPL_POWER_UNIT    = 0x606;
    private const uint MSR_PKG_ENERGY_STATUS  = 0x611;
    private const uint MSR_PP0_ENERGY_STATUS  = 0x639;
    private const uint MSR_DRAM_ENERGY_STATUS = 0x619;

    private readonly Computer   _computer;
    private readonly MethodInfo _readMsr;
    private readonly double     _energyUnitMultiplier; // µJ per raw counter unit

    public RaplWindows()
    {
        _computer = new Computer { IsCpuEnabled = true };
        _computer.Open(); // loads the WinRing0 kernel driver

        var ring0Type = typeof(Computer).Assembly
            .GetType("LibreHardwareMonitor.Hardware.Ring0");
        if (ring0Type is null)
            throw new InvalidOperationException("Ring0 type not found in LHM assembly.");

        _readMsr = ring0Type.GetMethod(
            "ReadMsr",
            BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic,
            null,
            new[] { typeof(uint), typeof(uint).MakeByRefType(), typeof(uint).MakeByRefType() },
            null)
            ?? throw new InvalidOperationException(
                "Ring0.ReadMsr method not found. Run as Administrator.");

        // MSR_RAPL_POWER_UNIT bits [12:8] = energy status units n; 1 raw unit = 2^(-n) J.
        // On Coffee Lake n is typically 14, giving ~61.04 µJ per unit.
        ReadRawMsr(MSR_RAPL_POWER_UNIT, out uint puEax, out _);
        int energyUnit = (int)((puEax >> 8) & 0x1F);
        _energyUnitMultiplier = 1_000_000.0 / Math.Pow(2, energyUnit);
    }

    private void ReadRawMsr(uint index, out uint eax, out uint edx)
    {
        var args = new object[] { index, (uint)0, (uint)0 };
        bool ok = (bool)_readMsr.Invoke(null, args)!;
        if (!ok)
            throw new InvalidOperationException(
                $"ReadMsr(0x{index:X3}) failed. Ensure process runs as Administrator.");
        eax = (uint)args[1];
        edx = (uint)args[2];
    }

    // RAPL energy counter is 32-bit (the high 32 bits in edx are reserved). Use eax only.
    private long ReadMsrMicrojoules(uint msrIndex)
    {
        ReadRawMsr(msrIndex, out uint eax, out _);
        return (long)(eax * _energyUnitMultiplier);
    }

    public long ReadPackageEnergyMicrojoules() => ReadMsrMicrojoules(MSR_PKG_ENERGY_STATUS);
    public long ReadCoresEnergyMicrojoules()   => ReadMsrMicrojoules(MSR_PP0_ENERGY_STATUS);
    // MSR_DRAM_ENERGY_STATUS uses the same energy unit as Package/PP0 on Coffee Lake.
    public long ReadDramEnergyMicrojoules()    => ReadMsrMicrojoules(MSR_DRAM_ENERGY_STATUS);

    public RaplSnapshot TakeSnapshot() => new()
    {
        PackageMicrojoules = ReadPackageEnergyMicrojoules(),
        CoresMicrojoules   = ReadCoresEnergyMicrojoules(),
        DramMicrojoules    = ReadDramEnergyMicrojoules(),
    };

    public void Dispose() => _computer.Close();
}
