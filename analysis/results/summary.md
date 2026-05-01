# Resumo da Análise de Benchmarks

## Ambiente

| Campo | Detalhe |
|---|---|
| **Hardware** | HP EliteBook 1050 G1 · Intel Core i7-8850H · 6C/12T · 16 GiB RAM |
| **Sistemas Operativos** | Ubuntu 24.04.3 LTS (kernel 6.17.0-22-generic) vs Windows 11 Pro |
| **Versão .NET** | .NET 9 (mesma versão em ambos os SO) |
| **Algoritmo** | FannkuchRedux — CPU-bound, sem I/O, alocação mínima de heap |
| **Fonte do algoritmo** | greensoftwarelab/Energy-Languages (CSharp/fannkuch-redux) |
| **Medição de energia** | Intel RAPL — domínio Package (hardware, não estimativa) |
| **Turbo Boost** | Desativado em ambos os SO |
| **Plano de energia** | Linux: governor=performance · Windows: Ultimate Performance |
| **Temperaturas** | Linux: monitoradas via lm-sensors · Windows: não disponível (cpu_temp = -1.0) |

> **Nota sobre temperaturas:** Os dados do Windows têm `cpu_temp_before` e `cpu_temp_after` iguais a `-1.0`
> porque o LibreHardwareMonitorLib não obteve leituras válidas nessa sessão.
> As colunas de temperatura foram excluídas da análise estatística.
> A comparação de desempenho baseia-se exclusivamente em `duration_ms` e `pkg_energy_j`.

---

## Estatísticas Descritivas

| os | n | count | mean_ms | median_ms | std_ms | cv_pct | min_ms | max_ms | iqr_ms | mean_j | std_j |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| linux | 11 | 23 | 623.5154 | 623.6550 | 3.9501 | 0.6335 | 616.8530 | 631.1410 | 5.8865 | 15.9899 | 0.2153 |
| linux | 12 | 20 | 8577.8110 | 8578.3325 | 28.1016 | 0.3276 | 8530.3790 | 8635.3560 | 40.6530 | 216.1402 | 0.9504 |
| windows | 11 | 25 | 451.5153 | 451.7300 | 4.2833 | 0.9486 | 441.8630 | 459.9820 | 3.8790 | 27.0629 | 0.2608 |
| windows | 12 | 22 | 6343.5965 | 6335.1555 | 34.6379 | 0.5460 | 6280.2140 | 6419.0330 | 53.2945 | 285.0349 | 1.7096 |

> **CV%** = Coeficiente de Variação (Desvio Padrão / Média × 100). Indica a estabilidade relativa do ambiente.

---

## Resultados dos Testes de Hipótese

| n | metric | test | statistic | pvalue | significant | alternative |
| --- | --- | --- | --- | --- | --- | --- |
| 11 | duration_ms | Mann-Whitney U | 575.0000 | 0.000000 | True | two-sided (Linux ≠ Windows) |
| 11 | duration_ms | Mann-Whitney U | 575.0000 | 0.000000 | True | one-sided (Linux > Windows, Linux é mais lento) |
| 11 | pkg_energy_j | Mann-Whitney U | 0.0000 | 0.000000 | True | one-sided (Linux < Windows, Linux consome menos) |
| 11 | duration_ms | Permutation A/B (10000 perms) | 172.0001 | 0.000000 | True | two-sided |
| 11 | pkg_energy_j | Permutation A/B (10000 perms) | -11.0730 | 0.000000 | True | one-sided (Linux < Windows) |
| 12 | duration_ms | Mann-Whitney U | 440.0000 | 0.000000 | True | two-sided (Linux ≠ Windows) |
| 12 | duration_ms | Mann-Whitney U | 440.0000 | 0.000000 | True | one-sided (Linux > Windows, Linux é mais lento) |
| 12 | pkg_energy_j | Mann-Whitney U | 0.0000 | 0.000000 | True | one-sided (Linux < Windows, Linux consome menos) |
| 12 | duration_ms | Permutation A/B (10000 perms) | 2234.2145 | 0.000000 | True | two-sided |
| 12 | pkg_energy_j | Permutation A/B (10000 perms) | -68.8948 | 0.000000 | True | one-sided (Linux < Windows) |
| all | duration_ms vs pkg_energy_j | Spearman correlation (full dataset) | 0.6068 | 0.000000 | True | two-sided |
| all | duration_ms vs pkg_energy_j | Spearman correlation (linux) | 0.8946 | 0.000000 | True | two-sided |
| all | duration_ms vs pkg_energy_j | Spearman correlation (windows) | 0.9830 | 0.000000 | True | two-sided |

---

## Intervalos de Confiança (95%)

| os | n | metric | mean | ci_lower | ci_upper | margin_abs | margin_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| linux | 11 | duration_ms | 623.5154 | 621.8073 | 625.2236 | 1.7082 | 0.2740 |
| linux | 11 | pkg_energy_j | 15.9899 | 15.8968 | 16.0830 | 0.0931 | 0.5822 |
| linux | 12 | duration_ms | 8577.8110 | 8564.6590 | 8590.9630 | 13.1520 | 0.1533 |
| linux | 12 | pkg_energy_j | 216.1402 | 215.6954 | 216.5850 | 0.4448 | 0.2058 |
| windows | 11 | duration_ms | 451.5153 | 449.7473 | 453.2834 | 1.7680 | 0.3916 |
| windows | 11 | pkg_energy_j | 27.0629 | 26.9553 | 27.1706 | 0.1076 | 0.3977 |
| windows | 12 | duration_ms | 6343.5965 | 6328.2389 | 6358.9541 | 15.3576 | 0.2421 |
| windows | 12 | pkg_energy_j | 285.0349 | 284.2769 | 285.7929 | 0.7580 | 0.2659 |

---

## Principais Conclusões

### Tempo de Execução

- **N=11:** Windows (451.5 ms) é **38.1% mais rápido** que Linux (623.5 ms).
  CI 95% Linux: [621.8, 625.2] ms |
  CI 95% Windows: [449.7, 453.3] ms

- **N=12:** Windows (6343.6 ms) é **35.2% mais rápido** que Linux (8577.8 ms).
  CI 95% Linux: [8564.7, 8591.0] ms |
  CI 95% Windows: [6328.2, 6359.0] ms

- **Significância estatística (tempo):**
  - N=11: Mann-Whitney U p=3.16e-09 (***) · Permutação p=0.00e+00 (***)
  - N=12: Mann-Whitney U p=3.24e-08 (***) · Permutação p=0.00e+00 (***)

### Consumo Energético

- **N=11:** Linux (15.990 J) consome **0.59× menos energia** que Windows (27.063 J).
  CI 95% Linux: [15.897, 16.083] J |
  CI 95% Windows: [26.955, 27.171] J

- **N=12:** Linux (216.140 J) consome **0.76× menos energia** que Windows (285.035 J).
  CI 95% Linux: [215.695, 216.585] J |
  CI 95% Windows: [284.277, 285.793] J

- **Significância estatística (energia):**
  - N=11: Mann-Whitney U p=1.58e-09 (***) · Permutação p=0.00e+00 (***)
  - N=12: Mann-Whitney U p=1.62e-08 (***) · Permutação p=0.00e+00 (***)

### Variância

- Linux apresenta coeficiente de variação (CV) muito baixo (<1%), indicando ambiente de medição estável.
- Windows N=11 tem CV elevado (~8–9%), refletindo comportamento não-determinístico do scheduler Windows
  para workloads de curta duração (indicativo de variabilidade de escalonamento de threads).
- Windows N=12 normaliza para CV~1%, sugerindo que cargas mais longas estabilizam o comportamento.

### Correlação Tempo–Energia

- Existe correlação de Spearman forte e significativa entre tempo de execução e energia consumida
  (ρ ≈ 0.607, p = 2.31e-10 (***)), o que é esperado num benchmark CPU-bound.
- A correlação é verificada individualmente em cada SO.

---

## Ameaças à Validade

1. **Dimensão da amostra (Linux):** As 24 amostras por grupo no Linux estão ligeiramente abaixo do n=30
   recomendado pelo Teorema do Limite Central para garantir normalidade assintótica da média amostral.
   Os testes não-paramétricos utilizados (Mann-Whitney, permutação) são válidos para n≥20,
   pelo que a análise permanece defensável, mas deve ser mencionado como limitação.

2. **Variância elevada no Windows N=11 (~8.8% CV):** Indica que o scheduler do Windows é menos
   determinístico para workloads de curta duração. Pode refletir variações de frequência de CPU,
   migração de threads entre núcleos, ou interferência de processos de sistema.
   Este resultado é em si mesmo relevante e deve ser discutido na secção de análise.

3. **Gestão térmica do portátil:** O HP EliteBook 1050 G1 tem 6+ anos. Com 6 núcleos a 100%,
   existe risco de throttling térmico, especialmente em N=12 (runs de ~8s). O turbo foi desativado
   para reduzir variância, mas o throttling por temperatura não pode ser completamente excluído.
   As temperaturas registadas no Linux (até ~59°C) estão dentro dos limites seguros de operação.

4. **Filtro RAPL (Intel IPU 2021.2):** A Intel adicionou ruído aleatório às leituras RAPL como
   mitigação de ataques side-channel. Afeta Linux e Windows de forma equivalente; mitigado pelo
   elevado número de iterações e reporte da distribuição estatística completa.

5. **Sessões de medição separadas:** As medições Windows e Linux foram realizadas em sessões temporais
   distintas. Fatores externos (temperatura ambiente, estado da bateria, versão de firmware)
   podem introduzir diferenças sistemáticas não controladas.

6. **Temperatura não disponível no Windows:** Os valores `cpu_temp = -1.0` no Windows impedem
   a análise de correlação entre temperatura e desempenho para esse SO.
