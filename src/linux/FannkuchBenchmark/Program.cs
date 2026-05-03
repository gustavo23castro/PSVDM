using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Jobs;
using BenchmarkDotNet.Running;
using BenchmarkDotNet.Toolchains.InProcess.Emit;

// All jobs run in-process to avoid BDN's child-process toolchain searching
// upward for a .csproj and finding both src/linux and src/windows copies,
// which aborts with "Found more than one matching project file".
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
    .WithArtifactsPath(Path.Combine("..", "..", "..", "..", "results", "linux", "BenchmarkDotNet.Artifacts"));

BenchmarkSwitcher.FromAssembly(typeof(Program).Assembly).Run(filteredArgs.ToArray(), config);
