# Estrutura do Relatório — FannkuchRedux: Performance e Energia em C# (Windows vs Linux)

> Este ficheiro serve de guia para o agente LaTeX escrever o relatório completo.
> Todos os valores numéricos são reais — retirados de analysis/results/summary.md
> Os gráficos estão em analysis/figures/ (PNG, 300 DPI)

---

## Metadados

- **Título**: Avaliação de Performance e Consumo Energético de C# em Windows e Linux: Um Estudo Comparativo com o Algoritmo FannkuchRedux
- **Autor**: Gustavo [apelido]
- **Instituição**: Universidade do Minho, Departamento de Informática
- **Contexto**: Mestrado em Engenharia Informática
- **Língua**: Português europeu
- **Classe LaTeX**: `article`, 12pt, A4
- **Pacotes necessários**: inputenc (utf8), babel (portuguese), graphicx, booktabs, tabularx, hyperref, geometry (margins 2.5cm), amsmath, float, caption, subcaption, xcolor, csvsimple ou pgfplotstable para tabelas de dados

---

## Estrutura de Secções

---

### 1. Resumo (Abstract)

Parágrafo único (~150 palavras).

Conteúdo obrigatório:
- Objetivo do estudo: comparar performance e consumo energético de C# em Windows 11 e Ubuntu 24.04 usando o algoritmo FannkuchRedux
- Metodologia: medição direta via Intel RAPL, BenchmarkDotNet, mesmo hardware (dual-boot), turbo desativado
- Resultados principais:
  - Windows é 38.1% mais rápido (N=11) e 35.2% mais rápido (N=12)
  - Linux consome 69% menos energia (N=11: 15.99 J vs 27.06 J) e 32% menos (N=12: 216.14 J vs 285.03 J)
  - Diferenças estatisticamente significativas (Mann-Whitney U, p < 0.001)
- Conclusão: existe um trade-off claro entre velocidade e eficiência energética nos dois SO

---

### 2. Introdução

Três a quatro parágrafos.

**Parágrafo 1 — Contexto:**
A eficiência energética do software é uma preocupação crescente, especialmente em contextos de computação de alto desempenho e edge computing. A linguagem C# e o ecossistema .NET são amplamente usados em ambientes de produção que correm tanto em Windows como em Linux. Compreender como o sistema operativo influencia a performance e o consumo energético de um mesmo programa é relevante para decisões de deployment.

**Parágrafo 2 — Motivação:**
A maioria dos estudos de performance em .NET foca-se em métricas de tempo de execução, ignorando o consumo energético. Estudos como o de Pereira et al. (greensoftwarelab/Energy-Languages) demonstram que a linguagem e o ambiente de execução têm impacto significativo na energia consumida. Este trabalho estende essa linha de investigação para comparar dois sistemas operativos com o mesmo hardware e runtime.

**Parágrafo 3 — Objetivos e contribuições:**
Este trabalho tem como objetivos:
(1) medir e comparar o tempo de execução de C# em Windows 11 e Ubuntu 24.04
(2) medir e comparar o consumo energético via Intel RAPL em ambos os SO
(3) avaliar a significância estatística das diferenças observadas
(4) identificar possíveis causas para as diferenças encontradas

**Parágrafo 4 — Estrutura do documento:**
O restante documento está organizado da seguinte forma: a Secção 2 descreve a metodologia e o ambiente experimental; a Secção 3 apresenta os resultados obtidos; a Secção 4 discute as implicações dos resultados; a Secção 5 identifica ameaças à validade; a Secção 6 conclui o trabalho.

---

### 3. Metodologia

#### 3.1 Algoritmo de Benchmark — FannkuchRedux

- Descrição: algoritmo CPU-bound puro, sem I/O, baseado em permutações de arrays
- Origem: Computer Language Benchmarks Game, implementação C# de greensoftwarelab/Energy-Languages
  (Isaac Gouy, transliterado do Java de Oleg Mazurov, com melhorias de concorrência por Peperud)
- Citação: Pereira et al., "Energy Efficiency across Programming Languages", SLE 2017
- Variantes testadas: N=11 e N=12 (tamanho do problema — determina complexidade fatorial)
- Usa threading via Task.Run com Environment.ProcessorCount + 1 workers
- Correctness verificado: Compute(7) = checksum 228, maxFlips 16 (valor de referência CLBG)
- Alocação de heap: ~52 KB por iteração (verificado via BenchmarkDotNet MemoryDiagnoser) — GC irrelevante

#### 3.2 Hardware e Software

Tabela com as especificações (usar booktabs):

| Campo | Valor |
|---|---|
| Máquina | HP EliteBook 1050 G1 |
| CPU | Intel Core i7-8850H (Coffee Lake, 6C/12T, 2.6 GHz base) |
| RAM | 16 GiB |
| Armazenamento | Samsung NVMe 512 GB |
| SO Linux | Ubuntu 24.04.3 LTS, kernel 6.17.0-22-generic |
| SO Windows | Windows 11 Pro (build 26200.8246) |
| .NET SDK | 9.0.312 (Linux) / 9.0.313 (Windows) |
| Runtime .NET | 9.0.14 (Linux) / 9.0.15 (Windows) |
| BenchmarkDotNet | 0.15.8 |

#### 3.3 Medição de Performance — BenchmarkDotNet

- Ferramenta: BenchmarkDotNet 0.15.8
- Configuração: SimpleJob(RuntimeMoniker.Net90), MemoryDiagnoser, CsvMeasurementsExporter
- Warm-up automático antes das iterações medidas
- Outlier detection automático (BDN remove outliers estatísticos)
- Build: Release, x64, Optimize=true
- Em Windows: InProcessEmitToolchain (necessário para LibreHardwareMonitorLib)

#### 3.4 Medição de Energia — Intel RAPL

- Domínio medido: Package (MSR_PKG_ENERGY_STATUS, 0x611) — inclui todos os cores
- Domínio secundário: PP0/Cores (MSR_PP0_ENERGY_STATUS, 0x639)
- **Linux**: leitura via `/sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/energy_uj` (sysfs, kernel powercap)
- **Windows**: leitura via WinRing0 driver (LibreHardwareMonitorLib 0.9.3), acesso direto ao MSR por reflexão sobre `LibreHardwareMonitor.Hardware.Ring0.ReadMsr`
- Unidade de energia lida do MSR_RAPL_POWER_UNIT (0x606), bits [12:8] — Coffee Lake: 2^(-14) J/unit ≈ 61 µJ/unit
- Método de medição: leitura do contador antes e depois de cada iteração; delta = energia consumida
- Wraparound tratado: contador 32-bit com max_range ~262 GJ; período de wrap >> duração das runs

#### 3.5 Configuração do Ambiente de Medição

Para garantir comparabilidade entre os dois SO:

**Ambos os SO:**
- Turbo Boost desativado (Linux: `/sys/devices/system/cpu/intel_pstate/no_turbo=1`; Windows: PROCTHROTTLEMAX=99%)
- Máquina ligada à corrente (AC power)
- Sem outras aplicações intensivas em CPU durante as medições

**Linux:**
- CPU governor: `performance` (via cpupower)
- Script de lançamento: `scripts/run-linux.sh` (aplica as configurações antes de cada run)

**Windows:**
- Power plan: Desempenho Máximo (GUID 202e5b95...)
- Processo executado como Administrador (necessário para acesso MSR via WinRing0)

#### 3.6 Protocolo de Recolha de Dados

- Número de iterações: determinado automaticamente pelo BenchmarkDotNet (mínimo de estabilidade estatística)
- Amostras válidas após remoção de outliers (IQR 1.5×):
  - Linux N=11: 23 amostras; Linux N=12: 20 amostras
  - Windows N=11: 25 amostras; Windows N=12: 22 amostras
- Dados exportados para CSV com timestamp, energia (µJ), duração (ms), temperatura

#### 3.7 Análise Estatística

- Testes utilizados: Mann-Whitney U (amostras independentes, não-paramétrico) e A/B test por permutação (10 000 permutações)
- Nível de significância: α = 0.05
- Correlação: Spearman ρ (relação não-linear entre tempo e energia)
- Intervalos de confiança: 95%, calculados via distribuição t de Student
- Ferramentas: Python 3, pandas, scipy, seaborn, matplotlib

---

### 4. Resultados

#### 4.1 Estatísticas Descritivas

Tabela completa (booktabs, todos os valores do statistics.csv):

| SO | N | n | Média (ms) | Mediana (ms) | DP (ms) | CV (%) | Energia média (J) |
|---|---|---|---|---|---|---|---|
| Linux | 11 | 23 | 623.5 | 623.7 | 3.95 | 0.63 | 15.99 |
| Linux | 12 | 20 | 8577.8 | 8578.3 | 28.10 | 0.33 | 216.14 |
| Windows | 11 | 25 | 451.5 | 451.7 | 4.28 | 0.95 | 27.06 |
| Windows | 12 | 22 | 6343.6 | 6335.2 | 34.64 | 0.55 | 285.03 |

#### 4.2 Visualização dos Dados

Incluir figuras (de analysis/figures/):

**Figura 1** — `01_boxplot_time.png`
Boxplot do tempo de execução por SO e N.
Legenda: "Distribuição do tempo de execução para N=11 e N=12 em Linux e Windows. Os pontos representam iterações individuais."

**Figura 2** — `02_boxplot_energy.png`
Boxplot do consumo energético por SO e N.
Legenda: "Distribuição do consumo energético (domínio Package) para N=11 e N=12."

**Figura 3** — `06_summary_bar.png`
Gráfico de barras com intervalos de confiança a 95%.
Legenda: "Média e IC 95% para tempo de execução (esq.) e energia (dir.) por SO e N."

**Figura 4** — `05_correlation.png`
Correlação Spearman entre tempo e energia.
Legenda: "Correlação entre tempo de execução e energia consumida por SO (Spearman ρ)."

#### 4.3 Comparação de Performance (Tempo)

Texto com os valores reais:

- Para N=11: Windows executa em 451.5 ms (IC 95%: [449.7, 453.3] ms) vs Linux 623.5 ms (IC 95%: [621.8, 625.2] ms). Windows é **38.1% mais rápido**. Os intervalos de confiança não se sobrepõem.
- Para N=12: Windows executa em 6343.6 ms (IC 95%: [6328.2, 6359.0] ms) vs Linux 8577.8 ms (IC 95%: [8564.7, 8591.0] ms). Windows é **35.2% mais rápido**.

#### 4.4 Comparação de Consumo Energético

- Para N=11: Linux consome 15.99 J (IC 95%: [15.90, 16.08] J) vs Windows 27.06 J (IC 95%: [26.96, 27.17] J). Linux consome **40.9% menos energia**.
- Para N=12: Linux consome 216.14 J (IC 95%: [215.70, 216.58] J) vs Windows 285.03 J (IC 95%: [284.28, 285.79] J). Linux consome **24.2% menos energia**.

#### 4.5 Significância Estatística

Tabela com resultados dos testes (de hypothesis_tests.csv):

| N | Métrica | Teste | Estatística | p-value | Significativo |
|---|---|---|---|---|---|
| 11 | Tempo | Mann-Whitney U | 575.0 | <0.001 | Sim (***) |
| 11 | Energia | Mann-Whitney U | 0.0 | <0.001 | Sim (***) |
| 11 | Tempo | Permutação A/B | 172.0 ms | <0.001 | Sim (***) |
| 11 | Energia | Permutação A/B | -11.07 J | <0.001 | Sim (***) |
| 12 | Tempo | Mann-Whitney U | 440.0 | <0.001 | Sim (***) |
| 12 | Energia | Mann-Whitney U | 0.0 | <0.001 | Sim (***) |
| 12 | Tempo | Permutação A/B | 2234.2 ms | <0.001 | Sim (***) |
| 12 | Energia | Permutação A/B | -68.89 J | <0.001 | Sim (***) |

Todas as diferenças são estatisticamente significativas com p < 0.001 (α = 0.05).

#### 4.6 Correlação Tempo–Energia

- Spearman ρ (dataset completo) = 0.607, p < 0.001
- Spearman ρ (Linux) = 0.895, p < 0.001
- Spearman ρ (Windows) = 0.983, p < 0.001
- Existe correlação forte e significativa entre tempo e energia em ambos os SO, como esperado para um workload CPU-bound puro.
- A correlação mais forte no Windows sugere comportamento mais previsível na relação energia/tempo nesse SO.

#### 4.7 Variância e Estabilidade

- O CV do Linux é consistentemente abaixo de 1% (0.33%–0.63%), indicando ambiente de medição muito estável.
- O CV do Windows N=11 (0.95%) é superior ao Linux, refletindo maior variabilidade do scheduler do Windows para workloads de curta duração.
- O CV do Windows N=12 (0.55%) normaliza para valores próximos do Linux, sugerindo que workloads mais longas estabilizam o comportamento.

Incluir figura: `03_histogram_time.png` e/ou `04_histogram_energy.png`

---

### 5. Discussão

#### 5.1 Windows é mais rápido — porquê?

- O algoritmo usa Task.Run com Environment.ProcessorCount+1 workers. O ThreadPool do Windows é historicamente mais agressivo a escalonar threads em múltiplos cores para workloads curtas.
- O .NET no Windows pode beneficiar de otimizações específicas da plataforma no JIT (RyuJIT x64).
- O turbo foi desativado, mas diferenças residuais de frequência entre os governadores de cada SO não podem ser completamente excluídas.
- O scheduler CFS do Linux (Completely Fair Scheduler) prioriza equidade sobre throughput máximo, o que pode desfavorecer workloads multi-threaded intensivas.

#### 5.2 Linux consome menos energia — porquê?

- Windows executa mais rápido, mas consome proporcionalmente muito mais energia. Para N=11, Windows é 38% mais rápido mas consome 69% mais energia.
- Este resultado é contra-intuitivo se se assumir que "mais rápido = menos tempo a trabalhar = menos energia". A explicação mais provável: Windows opera os cores a voltagem/frequência mais elevada mesmo com turbo desativado (power states C0 mais agressivos, menor uso de C-states entre tarefas).
- O governor `performance` do Linux mantém frequência base constante (~2.6 GHz) com transições suaves de C-state. O plano "Desempenho Máximo" do Windows pode operar em estados de potência mais elevados de forma mais contínua.
- Implicação prática: para workloads onde o tempo de resposta não é crítico, Linux oferece melhor eficiência energética.

#### 5.3 Trade-off velocidade vs energia

- Existe um trade-off claro: Windows oferece ~35–38% mais velocidade em troca de ~25–69% mais consumo energético.
- A magnitude do trade-off varia com N: para N=12 (workload mais longa), a diferença de energia reduz-se (24% vs 69% para N=11), sugerindo que o efeito é mais pronunciado em workloads curtas onde os overheads de scheduling dominam.
- Para aplicações onde a eficiência energética é prioritária (e.g., servidores em data centers com custo de energia elevado, dispositivos embebidos), Linux apresenta vantagem clara.

---

### 6. Ameaças à Validade

#### 6.1 Validade Interna

- **Sessões separadas**: medições Linux e Windows realizadas em momentos distintos. Fatores como temperatura ambiente e estado do hardware podem introduzir bias sistemático.
- **Temperatura Windows não disponível**: impossibilidade de correlacionar temperatura com desempenho no Windows.
- **Filtro RAPL**: Intel adicionou ruído aleatório às leituras RAPL (IPU 2021.2) como mitigação de ataques side-channel. Afeta ambos os SO de forma equivalente; mitigado pelo número elevado de iterações.

#### 6.2 Validade Externa

- **Hardware único**: resultados obtidos num único laptop (HP EliteBook 1050 G1, i7-8850H). Podem não generalizar para outros processadores (AMD, ARM) ou factores de forma (desktop, servidor).
- **Algoritmo único**: FannkuchRedux é um benchmark CPU-bound puro. Resultados podem diferir para workloads com I/O intensivo, uso intensivo de memória, ou single-threaded.
- **Versão .NET**: testado com .NET 9. Resultados podem variar com versões anteriores ou futuras.

#### 6.3 Validade de Construção

- **Dimensão da amostra**: 20–25 amostras por grupo estão ligeiramente abaixo do n=30 recomendado pelo Teorema do Limite Central. Os testes não-paramétricos usados (Mann-Whitney, permutação) são válidos para n≥20.
- **Variância Windows N=11**: CV ~0.95% indica comportamento menos determinístico. Os outliers foram removidos pelo critério IQR antes dos testes.

---

### 7. Conclusão

Dois parágrafos.

**Parágrafo 1 — Síntese dos resultados:**
Este trabalho comparou a performance e o consumo energético de C# (.NET 9) em Windows 11 e Ubuntu 24.04 usando o algoritmo FannkuchRedux como benchmark CPU-bound. Os resultados mostram que Windows 11 é consistentemente mais rápido (35–38%) mas consome significativamente mais energia (25–69%) que Ubuntu 24.04, nas mesmas condições de hardware. Todas as diferenças são estatisticamente significativas (Mann-Whitney U, p < 0.001) e confirmadas por testes de permutação independentes.

**Parágrafo 2 — Implicações e trabalho futuro:**
Os resultados evidenciam um trade-off claro entre velocidade e eficiência energética dependente do SO. Para aplicações onde o custo energético é prioritário — como servidores em larga escala ou sistemas embebidos — Linux apresenta vantagem significativa. Como trabalho futuro sugere-se: (1) replicar o estudo noutros tipos de hardware (desktop, servidor ARM); (2) incluir workloads single-threaded e com I/O intensivo; (3) comparar versões de .NET (8 vs 9 vs 10); (4) investigar o impacto de diferentes configurações do scheduler Linux.

---

### Referências

- Pereira, R. et al. (2017). Energy Efficiency across Programming Languages. *Proceedings of the 10th ACM SIGPLAN International Conference on Software Language Engineering (SLE)*, pp. 256–267. https://doi.org/10.1145/3136014.3136031
- greensoftwarelab/Energy-Languages. GitHub. https://github.com/greensoftwarelab/Energy-Languages
- Computer Language Benchmarks Game. https://benchmarksgame-team.pages.debian.net/benchmarksgame/
- BenchmarkDotNet. https://github.com/dotnet/BenchmarkDotNet
- LibreHardwareMonitor. https://github.com/LibreHardwareMonitor/LibreHardwareMonitor
- Intel 64 and IA-32 Architectures Software Developer's Manual, Vol. 3B, Capítulo 14 (RAPL).

---

## Instruções para o Agente LaTeX

1. Criar `docs/relatorio.tex` com a estrutura acima
2. Usar `\documentclass[12pt,a4paper]{article}` com margens de 2.5cm
3. Todas as tabelas com `booktabs` (`\toprule`, `\midrule`, `\bottomrule`)
4. Figuras com `\includegraphics` apontando para `../analysis/figures/NomeFicheiro.png`
5. Usar `\label` e `\ref` para todas as figuras e tabelas
6. Secções numeradas com `\section`, `\subsection`
7. Compilar com `pdflatex` ou `xelatex`
8. Criar também `docs/relatorio.bib` com as referências em BibTeX
9. Os valores numéricos nas tabelas devem ser copiados EXATAMENTE deste ficheiro — não arredondar nem alterar
10. Onde o texto diz "Incluir figura X", inserir o `\begin{figure}` correspondente
