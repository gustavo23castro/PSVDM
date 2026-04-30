#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export BENCHMARK_RESULTS_ROOT="$REPO_ROOT/results"

# Ensure results directories exist
mkdir -p "$REPO_ROOT/results/linux/energy"
mkdir -p "$REPO_ROOT/results/linux/BenchmarkDotNet.Artifacts"

# Apply performance settings
echo "Setting CPU governor to performance..."
sudo cpupower frequency-set -g performance > /dev/null
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo > /dev/null

echo "BENCHMARK_RESULTS_ROOT=$BENCHMARK_RESULTS_ROOT"
echo "Launching benchmark..."

cd "$REPO_ROOT/src/linux/FannkuchBenchmark"
dotnet run -c Release -- "$@"
