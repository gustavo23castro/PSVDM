using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Jobs;
using BenchmarkDotNet.Running;
using BenchmarkDotNet.Toolchains.InProcess.Emit;

// All jobs run in-process. BDN's default child-process toolchain breaks the
// LibreHardwareMonitorLib WinRing0 driver install (the deeply-nested BDN-
// generated build dir is the trigger — temperature, clock and power MSR
// sensors all come back null even though the host is elevated). Running
// in-process keeps the LHM Computer instance inside the elevated host where
// the driver install succeeds.
//
// `--job Dry` from the CLI would otherwise be added as an extra job using
// the default child-process toolchain. We strip it from args and translate
// it into an in-process equivalent so it runs cleanly.
Job selectedJob = Job.Default;
var filteredArgs = new List<string>();
for (int i = 0; i < args.Length; i++)
{
    if (string.Equals(args[i], "--job", StringComparison.OrdinalIgnoreCase) &&
        i + 1 < args.Length &&
        string.Equals(args[i + 1], "Dry", StringComparison.OrdinalIgnoreCase))
    {
        selectedJob = Job.Dry;
        i++;
        continue;
    }
    filteredArgs.Add(args[i]);
}

var config = DefaultConfig.Instance
    .AddJob(selectedJob.WithToolchain(InProcessEmitToolchain.Instance))
    .WithArtifactsPath(Path.Combine("..", "..", "..", "..", "results", "windows", "BenchmarkDotNet.Artifacts"));

BenchmarkSwitcher.FromAssembly(typeof(Program).Assembly).Run(filteredArgs.ToArray(), config);
