# Hardware & Environment Specification

## Test Machine

| Field | Value |
|---|---|
| **Model** | HP EliteBook 1050 G1 |
| **CPU** | Intel Core i7-8850H (Coffee Lake-H) |
| **Cores / Threads** | 6 cores / 12 threads |
| **Base / Boost clock** | 800 MHz idle / 4300 MHz max |
| **L2 Cache** | 1.5 MiB |
| **TDP** | 45W (laptop chassis — thermal throttling is a real risk) |
| **RAM** | 16 GiB |
| **Storage** | Samsung MZVLB512HAJQ NVMe SSD (476.94 GiB) |
| **GPU** | Intel UHD 630 (integrated) + NVIDIA GTX 1050 Mobile |
| **UEFI** | HP Q72 Ver. 01.29.01 (2024-09-24) |

## Operating Systems (dual-boot, same hardware)

| OS | Version | Kernel | Boot partition |
|---|---|---|---|
| **Ubuntu** | 24.04.3 LTS (Noble Numbat) | 6.17.0-22-generic | /dev/nvme0n1p5 |
| **Windows** | 11 Pro | — | /dev/nvme0n1p1 (EFI shared) |

---

## RAPL Energy Measurement Capability

The i7-8850H (Coffee Lake) exposes full Intel RAPL domains:

| RAPL Domain | MSR | Notes |
|---|---|---|
| `PACKAGE` | MSR_PKG_ENERGY_STATUS | Total CPU package — primary metric |
| `PP0` (cores) | MSR_PP0_ENERGY_STATUS | Compute cores only — most relevant for FannkuchRedux |
| `PP1` (uncore) | MSR_PP1_ENERGY_STATUS | Integrated GPU / uncore |
| `DRAM` | MSR_DRAM_ENERGY_STATUS | Memory subsystem |

**Linux access** — verified paths (use `/sys/devices/virtual/powercap/` exclusively; `/sys/class/powercap/` symlinks do NOT work for subdomain access on this machine):

| Domain | Path | Status |
|---|---|---|
| package-0 | `/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/energy_uj` | ✅ readable without sudo |
| core | `/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:0/energy_uj` | ✅ readable without sudo |
| uncore | `/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:1/energy_uj` | ✅ readable without sudo |
| dram | `/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/intel-rapl:0:2/energy_uj` | ✅ readable without sudo |

Permissions are managed by `/etc/udev/rules.d/99-rapl.rules` (`ACTION=="add"`, `chmod o+r` on each `energy_uj` file).

**Windows access**: `LibreHardwareMonitorLib` NuGet package (requires Administrator)

> ⚠️ Intel RAPL filtering (IPU 2021.2+) adds random noise to readings as a side-channel mitigation.
> This affects both Linux and Windows equally. Mitigate by using many iterations and reporting mean ± stddev.

---

## Benchmark Environment Configuration

### Linux (Ubuntu 24.04)

```bash
# Set CPU governor to performance (disable power saving)
sudo cpupower frequency-set -g performance

# Disable Intel Turbo Boost (reduces clock variance)
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

# Verify RAPL powercap interface is available
ls /sys/class/powercap/intel-rapl/

# Check current governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

### Windows 11 Pro

- Power Plan: **Ultimate Performance** (enable via `powercfg /duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61`)
- Intel Turbo Boost: disable via BIOS or ThrottleStop
- Run benchmark process as **Administrator** (required for LibreHardwareMonitorLib RAPL access)
- Close background apps: antivirus real-time scan, OneDrive sync, Windows Update

### Common (both OS)

- Machine on **AC power** — never battery during benchmarks
- Allow CPU to **cool to idle temperature** between benchmark runs (~5 min)
- Disk partition `/` at 85% usage on Linux — **clean up before data collection**
- No other CPU-intensive processes running during measurement

---

## Known Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Thermal throttling (laptop chassis, 6yo) | Disable turbo, monitor temps, discard outliers |
| RAPL noise from Intel filtering | High iteration count, report statistical distribution |
| Windows background processes | Ultimate Performance plan + manual process cleanup |
| Different .NET JIT warm-up behaviour | BenchmarkDotNet handles warm-up automatically |
| Battery state affecting frequency scaling | Always run on AC, check power plan before each session |
