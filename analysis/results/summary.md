# Resumo da Análise de Benchmarks

## Ambiente

| Campo | Detalhe |
|---|---|
| **Hardware** | HP EliteBook 1050 G1 · Intel Core i7-8850H · 6C/12T · 16 GiB RAM |
| **Sistemas Operativos** | Ubuntu 24.04.3 LTS (kernel 6.17.0-22-generic) vs Windows 11 Pro |
| **Versão .NET** | .NET 9 (mesma versão em ambos os SO) |
| **Algoritmos** | FannkuchRedux (CPU-bound) + BinaryTrees (GC-bound / Memory-bound) |
| **Fonte dos algoritmos** | greensoftwarelab/Energy-Languages (CSharp) |
| **Medição de energia** | Intel RAPL — domínios Package e DRAM (hardware, não estimativa) |
| **Turbo Boost** | Desativado em ambos os SO |
| **Plano de energia** | Linux: governor=performance · Windows: Ultimate Performance |
| **Temperaturas** | Linux: monitoradas via lm-sensors · Windows: não disponível (cpu_temp = -1.0) |

> **Nota sobre temperaturas:** Os dados do Windows têm `cpu_temp_before` e `cpu_temp_after` iguais a `-1.0`
> porque o LibreHardwareMonitorLib não obteve leituras válidas nessa sessão.
> As colunas de temperatura foram excluídas da análise estatística.

---

## Estatísticas Descritivas

| os | algorithm | n | count | mean_ms | median_ms | std_ms | cv_pct | min_ms | max_ms | iqr_ms | mean_j | std_j | mean_dram_j | dram_pkg_ratio_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linux | BinaryTrees | 16 | 80 | 192.3905 | 192.1395 | 8.6025 | 4.4714 | 172.7930 | 215.2160 | 10.4023 | 2.0966 | 0.1208 | 0.2123 | 10.1258 |
| linux | BinaryTrees | 18 | 22 | 1246.1497 | 1250.1445 | 20.8872 | 1.6761 | 1200.0540 | 1276.8800 | 33.1480 | 12.8782 | 0.1957 | 1.4254 | 11.0686 |
| linux | FannkuchRedux | 11 | 25 | 643.0014 | 637.9910 | 11.1967 | 1.7413 | 633.0270 | 671.8280 | 13.6470 | 17.4244 | 0.5176 | 0.4843 | 2.7792 |
| linux | FannkuchRedux | 12 | 24 | 8663.9062 | 8663.4955 | 27.6782 | 0.3195 | 8606.4410 | 8712.6180 | 36.8420 | 232.1621 | 0.8093 | 6.2205 | 2.6794 |
| windows | BinaryTrees | 16 | 123 | 148.2752 | 148.1600 | 8.8656 | 5.9792 | 125.2630 | 170.0660 | 12.2895 | 4.3054 | 0.7226 | 0.2141 | 4.9721 |
| windows | BinaryTrees | 18 | 49 | 1107.7788 | 1109.4440 | 30.5409 | 2.7569 | 1044.2440 | 1187.8670 | 41.8500 | 29.0882 | 1.6176 | 1.4627 | 5.0284 |
| windows | FannkuchRedux | 11 | 23 | 448.3000 | 447.7840 | 3.7871 | 0.8448 | 443.5450 | 460.4070 | 4.3490 | 27.0130 | 2.1230 | 0.3185 | 1.1790 |
| windows | FannkuchRedux | 12 | 19 | 6293.8922 | 6281.2170 | 38.9165 | 0.6183 | 6240.8450 | 6383.5230 | 35.9160 | 281.4361 | 3.6442 | 3.7240 | 1.3232 |

> **CV%** = Coeficiente de Variação. **dram_pkg_ratio_pct** = DRAM Energy / Package Energy × 100.

---

## FannkuchRedux (CPU-bound)

### Tempo de Execução

- **N=11:** Windows (448.3 ms) é **43.4% mais rápido** que Linux (643.0 ms).
  CI 95% Linux: [638.4, 647.6] ms |
  CI 95% Windows: [446.7, 449.9] ms

- **N=12:** Windows (6293.9 ms) é **37.7% mais rápido** que Linux (8663.9 ms).
  CI 95% Linux: [8652.2, 8675.6] ms |
  CI 95% Windows: [6275.1, 6312.6] ms

- **Significância (tempo):**
  - N=11: Mann-Whitney p=3.16e-09 (***) · Permutação p=0.00e+00 (***)
  - N=12: Mann-Whitney p=2.64e-08 (***) · Permutação p=0.00e+00 (***)

### Consumo Energético

- **N=11:** Linux (17.424 J) vs Windows (27.013 J) — rácio 0.65×
- **N=12:** Linux (232.162 J) vs Windows (281.436 J) — rácio 0.82×

- **Significância (energia):**
  - N=11: Mann-Whitney p=1.58e-09 (***) · Permutação p=0.00e+00 (***)
  - N=12: Mann-Whitney p=1.32e-08 (***) · Permutação p=0.00e+00 (***)

### DRAM Energy (FannkuchRedux)

- Linux: DRAM representa em média **2.7%** da energia total do package.
- Windows: DRAM representa em média **1.3%** da energia total do package.
- Baixo rácio DRAM confirma natureza **CPU-bound** (alocação mínima de heap).

---

## BinaryTrees (GC-bound / Memory-bound)

### Tempo de Execução

- **N=16:** Linux 192.4 ms vs Windows 148.3 ms
- **N=18:** Linux 1246.1 ms vs Windows 1107.8 ms

### Consumo Energético

- **N=16:** Linux 2.097 J vs Windows 4.305 J
- **N=18:** Linux 12.878 J vs Windows 29.088 J

### DRAM Energy (BinaryTrees)

- Linux: DRAM representa em média **10.6%** da energia total do package.
- Windows: DRAM representa em média **5.0%** da energia total do package.
- Rácio DRAM claramente superior ao de FannkuchRedux, confirmando natureza **GC-bound / Memory-bound**.

---

## Cross-algorithm comparison (DRAM ratio)

| Algoritmo | OS | DRAM % do Package |
|---|---|---|
| FannkuchRedux | Linux | 2.7% |
| FannkuchRedux | Windows | 1.3% |
| BinaryTrees | Linux | 10.6% |
| BinaryTrees | Windows | 5.0% |

BinaryTrees apresenta um rácio DRAM substancialmente maior que FannkuchRedux,
evidenciando o impacto da gestão de memória (GC) no consumo energético de subsistema DRAM.
Esta diferença é capturada pela Figura 9 (09_dram_comparison.png).

---

## Resultados dos Testes de Hipótese

| algorithm | n | metric | test | statistic | pvalue | significant | alternative |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FannkuchRedux | 11 | duration_ms | Mann-Whitney U | 575.0000 | 0.000000 | True | two-sided (Linux ≠ Windows) |
| FannkuchRedux | 11 | duration_ms | Mann-Whitney U | 575.0000 | 0.000000 | True | one-sided (Linux > Windows, Linux é mais lento) |
| FannkuchRedux | 11 | pkg_energy_j | Mann-Whitney U | 0.0000 | 0.000000 | True | one-sided (Linux < Windows, Linux consome menos) |
| FannkuchRedux | 11 | dram_energy_j | Mann-Whitney U | 575.0000 | 0.000000 | True | two-sided (Linux ≠ Windows) |
| FannkuchRedux | 11 | duration_ms | Permutation A/B (10000 perms) | 194.7014 | 0.000000 | True | two-sided |
| FannkuchRedux | 11 | pkg_energy_j | Permutation A/B (10000 perms) | -9.5886 | 0.000000 | True | one-sided (Linux < Windows) |
| FannkuchRedux | 11 | dram_energy_j | Permutation A/B (10000 perms) | 0.1658 | 0.000000 | True | two-sided |
| FannkuchRedux | 12 | duration_ms | Mann-Whitney U | 456.0000 | 0.000000 | True | two-sided (Linux ≠ Windows) |
| FannkuchRedux | 12 | duration_ms | Mann-Whitney U | 456.0000 | 0.000000 | True | one-sided (Linux > Windows, Linux é mais lento) |
| FannkuchRedux | 12 | pkg_energy_j | Mann-Whitney U | 0.0000 | 0.000000 | True | one-sided (Linux < Windows, Linux consome menos) |
| FannkuchRedux | 12 | dram_energy_j | Mann-Whitney U | 456.0000 | 0.000000 | True | two-sided (Linux ≠ Windows) |
| FannkuchRedux | 12 | duration_ms | Permutation A/B (10000 perms) | 2370.0140 | 0.000000 | True | two-sided |
| FannkuchRedux | 12 | pkg_energy_j | Permutation A/B (10000 perms) | -49.2740 | 0.000000 | True | one-sided (Linux < Windows) |
| FannkuchRedux | 12 | dram_energy_j | Permutation A/B (10000 perms) | 2.4965 | 0.000000 | True | two-sided |
| BinaryTrees | 16 | duration_ms | Mann-Whitney U | 9840.0000 | 0.000000 | True | two-sided (Linux ≠ Windows) |
| BinaryTrees | 16 | duration_ms | Mann-Whitney U | 9840.0000 | 0.000000 | True | one-sided (Linux > Windows, Linux é mais lento) |
| BinaryTrees | 16 | pkg_energy_j | Mann-Whitney U | 0.0000 | 0.000000 | True | one-sided (Linux < Windows, Linux consome menos) |
| BinaryTrees | 16 | dram_energy_j | Mann-Whitney U | 4741.0000 | 0.662522 | False | two-sided (Linux ≠ Windows) |
| BinaryTrees | 16 | duration_ms | Permutation A/B (10000 perms) | 44.1153 | 0.000000 | True | two-sided |
| BinaryTrees | 16 | pkg_energy_j | Permutation A/B (10000 perms) | -2.2088 | 0.000000 | True | one-sided (Linux < Windows) |
| BinaryTrees | 16 | dram_energy_j | Permutation A/B (10000 perms) | -0.0018 | 0.466300 | False | two-sided |
| BinaryTrees | 18 | duration_ms | Mann-Whitney U | 1078.0000 | 0.000000 | True | two-sided (Linux ≠ Windows) |
| BinaryTrees | 18 | duration_ms | Mann-Whitney U | 1078.0000 | 0.000000 | True | one-sided (Linux > Windows, Linux é mais lento) |
| BinaryTrees | 18 | pkg_energy_j | Mann-Whitney U | 0.0000 | 0.000000 | True | one-sided (Linux < Windows, Linux consome menos) |
| BinaryTrees | 18 | dram_energy_j | Mann-Whitney U | 298.0000 | 0.002786 | True | two-sided (Linux ≠ Windows) |
| BinaryTrees | 18 | duration_ms | Permutation A/B (10000 perms) | 138.3709 | 0.000000 | True | two-sided |
| BinaryTrees | 18 | pkg_energy_j | Permutation A/B (10000 perms) | -16.2100 | 0.000000 | True | one-sided (Linux < Windows) |
| BinaryTrees | 18 | dram_energy_j | Permutation A/B (10000 perms) | -0.0372 | 0.004900 | True | two-sided |
| FannkuchRedux | all | duration_ms vs pkg_energy_j | Spearman correlation (FannkuchRedux) | 0.5957 | 0.000000 | True | two-sided |
| FannkuchRedux | all | duration_ms vs pkg_energy_j | Spearman correlation (FannkuchRedux linux) | 0.9328 | 0.000000 | True | two-sided |
| FannkuchRedux | all | duration_ms vs pkg_energy_j | Spearman correlation (FannkuchRedux windows) | 0.8182 | 0.000000 | True | two-sided |
| BinaryTrees | all | duration_ms vs pkg_energy_j | Spearman correlation (BinaryTrees) | 0.3180 | 0.000000 | True | two-sided |
| BinaryTrees | all | duration_ms vs pkg_energy_j | Spearman correlation (BinaryTrees linux) | 0.8423 | 0.000000 | True | two-sided |
| BinaryTrees | all | duration_ms vs pkg_energy_j | Spearman correlation (BinaryTrees windows) | 0.7213 | 0.000000 | True | two-sided |

---

## Intervalos de Confiança (95%)

| os | algorithm | n | metric | mean | ci_lower | ci_upper | margin_abs | margin_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linux | BinaryTrees | 16 | duration_ms | 192.3905 | 190.4761 | 194.3049 | 1.9144 | 0.9951 |
| linux | BinaryTrees | 16 | pkg_energy_j | 2.0966 | 2.0697 | 2.1235 | 0.0269 | 1.2827 |
| linux | BinaryTrees | 16 | dram_energy_j | 0.2123 | 0.2083 | 0.2163 | 0.0040 | 1.8954 |
| linux | BinaryTrees | 18 | duration_ms | 1246.1497 | 1236.8889 | 1255.4106 | 9.2608 | 0.7432 |
| linux | BinaryTrees | 18 | pkg_energy_j | 12.8782 | 12.7915 | 12.9650 | 0.0868 | 0.6738 |
| linux | BinaryTrees | 18 | dram_energy_j | 1.4254 | 1.4132 | 1.4377 | 0.0123 | 0.8595 |
| linux | FannkuchRedux | 11 | duration_ms | 643.0014 | 638.3797 | 647.6232 | 4.6218 | 0.7188 |
| linux | FannkuchRedux | 11 | pkg_energy_j | 17.4244 | 17.2107 | 17.6380 | 0.2136 | 1.2261 |
| linux | FannkuchRedux | 11 | dram_energy_j | 0.4843 | 0.4688 | 0.4998 | 0.0155 | 3.1992 |
| linux | FannkuchRedux | 12 | duration_ms | 8663.9062 | 8652.2187 | 8675.5937 | 11.6875 | 0.1349 |
| linux | FannkuchRedux | 12 | pkg_energy_j | 232.1621 | 231.8203 | 232.5038 | 0.3417 | 0.1472 |
| linux | FannkuchRedux | 12 | dram_energy_j | 6.2205 | 6.2008 | 6.2402 | 0.0197 | 0.3171 |
| windows | BinaryTrees | 16 | duration_ms | 148.2752 | 146.6927 | 149.8576 | 1.5825 | 1.0672 |
| windows | BinaryTrees | 16 | pkg_energy_j | 4.3054 | 4.1764 | 4.4343 | 0.1290 | 2.9957 |
| windows | BinaryTrees | 16 | dram_energy_j | 0.2141 | 0.2111 | 0.2170 | 0.0029 | 1.3773 |
| windows | BinaryTrees | 18 | duration_ms | 1107.7788 | 1099.0065 | 1116.5512 | 8.7724 | 0.7919 |
| windows | BinaryTrees | 18 | pkg_energy_j | 29.0882 | 28.6236 | 29.5528 | 0.4646 | 1.5973 |
| windows | BinaryTrees | 18 | dram_energy_j | 1.4627 | 1.4460 | 1.4793 | 0.0166 | 1.1375 |
| windows | FannkuchRedux | 11 | duration_ms | 448.3000 | 446.6624 | 449.9377 | 1.6377 | 0.3653 |
| windows | FannkuchRedux | 11 | pkg_energy_j | 27.0130 | 26.0950 | 27.9310 | 0.9180 | 3.3985 |
| windows | FannkuchRedux | 11 | dram_energy_j | 0.3185 | 0.3138 | 0.3231 | 0.0047 | 1.4674 |
| windows | FannkuchRedux | 12 | duration_ms | 6293.8922 | 6275.1350 | 6312.6493 | 18.7572 | 0.2980 |
| windows | FannkuchRedux | 12 | pkg_energy_j | 281.4361 | 279.6796 | 283.1925 | 1.7565 | 0.6241 |
| windows | FannkuchRedux | 12 | dram_energy_j | 3.7240 | 3.6626 | 3.7855 | 0.0614 | 1.6498 |

---

## Ameaças à Validade

1. **Dimensão da amostra (Linux):** As 24 amostras por grupo no Linux estão ligeiramente abaixo do n=30
   recomendado pelo Teorema do Limite Central. Os testes não-paramétricos utilizados são válidos para n≥20.

2. **Variância elevada no Windows N=11 (~8.8% CV):** Indica que o scheduler do Windows é menos
   determinístico para workloads de curta duração.

3. **Gestão térmica do portátil:** Com 6 núcleos a 100%, existe risco de throttling térmico,
   especialmente em N=12. O turbo foi desativado para reduzir variância.

4. **Filtro RAPL (Intel IPU 2021.2):** A Intel adicionou ruído aleatório às leituras RAPL como
   mitigação de ataques side-channel. Afeta Linux e Windows de forma equivalente.

5. **Sessões de medição separadas:** Medições Windows e Linux foram realizadas em sessões temporais
   distintas. Fatores externos podem introduzir diferenças sistemáticas não controladas.

6. **Temperatura não disponível no Windows:** Os valores `cpu_temp = -1.0` no Windows impedem
   a análise de correlação entre temperatura e desempenho para esse SO.
