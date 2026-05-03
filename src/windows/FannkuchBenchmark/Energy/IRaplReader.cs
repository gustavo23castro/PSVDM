namespace FannkuchBenchmark.Energy;

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
    // TakeSnapshot captures Package, PP0 (cores), and DRAM domains atomically.
    RaplSnapshot TakeSnapshot();
    void Dispose();
}
