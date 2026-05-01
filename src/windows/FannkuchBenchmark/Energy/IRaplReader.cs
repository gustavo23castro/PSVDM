namespace FannkuchBenchmark.Energy;

public readonly struct RaplSnapshot
{
    public long PackageMicrojoules { get; init; }
    public long CoresMicrojoules   { get; init; }
}

public interface IRaplReader
{
    long ReadPackageEnergyMicrojoules();
    long ReadCoresEnergyMicrojoules();
    RaplSnapshot TakeSnapshot();
    void Dispose();
}
