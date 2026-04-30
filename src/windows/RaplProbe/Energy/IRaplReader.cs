namespace RaplProbe.Energy;

public interface IRaplReader
{
    long ReadPackageEnergyMicrojoules();
    long ReadCoresEnergyMicrojoules();
    void Dispose();
}
