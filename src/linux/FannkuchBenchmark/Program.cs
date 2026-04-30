using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Running;

var config = DefaultConfig.Instance
    .WithArtifactsPath(Path.Combine("..", "..", "..", "..", "results", "linux", "BenchmarkDotNet.Artifacts"));

BenchmarkSwitcher.FromAssembly(typeof(Program).Assembly).Run(args, config);
