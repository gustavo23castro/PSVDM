# Metodologia de Análise de Dados — Referência para o Projeto

> Baseado nas aulas de "Análise de dados para Engenharia de Software" (Paulo J. Azevedo, UMinho)
> Aplicado ao estudo: *Performance e Consumo Energético de C# — Windows vs Linux*

---

## 1. Estatísticas Básicas (Sufficient Statistics)

O primeiro passo é sempre calcular as medidas de tendência central e de dispersão.

```python
import pandas as pd

df = pd.read_csv('energy_single.csv')
print(df[['duration_ms', 'pkg_energy_uj']].describe())
print(df.groupby('n')[['duration_ms', 'pkg_energy_uj']].describe())
```

**Métricas obrigatórias a reportar:**

| Métrica | Descrição | Relevância no projeto |
|---|---|---|
| Média (mean) | Tendência central | Tempo médio e energia média por N e SO |
| Mediana | Resistente a outliers | Comparação robusta |
| Desvio padrão (std) | Dispersão | Estabilidade do ambiente de medição |
| Mínimo / Máximo | Amplitude | Detetar throttling |
| Q1, Q3, IQR | Quartis | Base para boxplot e outliers |

---

## 2. Visualização — Boxplot

Mostra graficamente localização, distribuição e assimetria dos dados através dos quartis.

```python
import seaborn as sns
import matplotlib.pyplot as plt

sns.boxplot(data=df, x='n', y='duration_ms', hue='os')
plt.title('Tempo de execução por N e SO')
plt.show()
```

**Definições:**
- **IQR** = Q3 − Q1 (tamanho da caixa)
- **Bigodes**: Q1 − 1.5×IQR até Q3 + 1.5×IQR
- **Outliers**: pontos fora dos bigodes

**Remoção de outliers** (se necessário antes da análise estatística):
```python
Q1 = df['duration_ms'].quantile(0.25)
Q3 = df['duration_ms'].quantile(0.75)
IQR = Q3 - Q1
df_clean = df[(df['duration_ms'] >= Q1 - 1.5*IQR) &
              (df['duration_ms'] <= Q3 + 1.5*IQR)]
```

---

## 3. Density Estimation & Histogramas

Para estudar a distribuição dos dados e verificar se se aproxima de uma Normal.

```python
# Histograma com KDE
sns.histplot(data=df, x='duration_ms', hue='os', kde=True, bins=20)

# KDE explícito
from sklearn.neighbors import KernelDensity
import numpy as np

kde = KernelDensity(kernel='gaussian', bandwidth=10).fit(
    df[df['os']=='linux'][['duration_ms']])
```

**Interpretação:** Se a distribuição for claramente não-Normal (assimétrica, bimodal), usar testes não-paramétricos (Wilcoxon, Mann-Whitney) em vez de testes paramétricos (t-test).

---

## 4. Correlação

Estudar a relação entre variáveis — por exemplo, entre energia e tempo de execução.

```python
from scipy import stats

# Relação linear
pearson_r, p = stats.pearsonr(df['duration_ms'], df['pkg_energy_uj'])

# Relação não-linear (mais robusto para dados de benchmark)
spearman_rho, p = stats.spearmanr(df['duration_ms'], df['pkg_energy_uj'])
kendall_tau, p  = stats.kendalltau(df['duration_ms'], df['pkg_energy_uj'])

print(f"Pearson r={pearson_r:.3f}")
print(f"Spearman rho={spearman_rho:.3f}  p={p:.4f}")
print(f"Kendall tau={kendall_tau:.3f}   p={p:.4f}")
```

**Quando usar cada um:**
- **Pearson**: relações lineares, dados normalmente distribuídos
- **Spearman / Kendall**: relações não-lineares ou dados não-normais (recomendado para dados de benchmark)

**O p-value** representa a probabilidade de obter este resultado se a correlação fosse zero. Se p < 0.05, a correlação é estatisticamente significativa.

---

## 5. Testes de Hipóteses

### 5.1 Conceitos fundamentais

| Conceito | Definição |
|---|---|
| **H0** (hipótese nula) | O desempenho de Windows e Linux é equivalente |
| **H1** (hipótese alternativa) | O desempenho é diferente (two-sided) |
| **p-value** | P(observar este resultado ou mais extremo dado H0 verdadeira) |
| **α** | Grau de significância — tipicamente 0.05 (5%) |
| **Erro Tipo I** | Rejeitar H0 quando ela é verdadeira (α) |
| **Erro Tipo II** | Não rejeitar H0 quando ela é falsa (β) |

**Regra de decisão:** Se p-value < α → rejeitar H0 → diferença estatisticamente significativa.

### 5.2 Escolha do teste

Para comparar Windows vs Linux:

| Situação | Teste recomendado |
|---|---|
| Amostras independentes (Linux vs Windows) | **Mann-Whitney U** |
| Mesma amostra em duas condições | Wilcoxon signed-rank |
| Verificar significância empírica | A/B test (permutação) |

**Para este projeto: Mann-Whitney U** — Linux e Windows são amostras independentes recolhidas em sessões separadas.

### 5.3 Wilcoxon Signed-Rank Test

Teste não-paramétrico para duas amostras **dependentes** (emparelhadas). Avalia se a mediana das diferenças é diferente de zero.

```python
from scipy.stats import wilcoxon

res = wilcoxon(linux_times, windows_times,
               zero_method='wilcox',
               alternative='two-sided',
               method='exact')
print(f"W={res.statistic:.3f}  p={res.pvalue:.4f}")
```

- **H0**: mediana das diferenças = 0
- **H1**: mediana das diferenças != 0 (two-sided)

### 5.4 Mann-Whitney U Test (recomendado para este projeto)

Teste não-paramétrico para duas amostras **independentes**. Avalia se as distribuições são idênticas.

```python
from scipy.stats import mannwhitneyu

linux   = df[df['os']=='linux']['duration_ms']
windows = df[df['os']=='windows']['duration_ms']

# Two-sided: testar se são diferentes
U, p = mannwhitneyu(linux, windows, method='exact', alternative='two-sided')
print(f"U={U:.0f}  p={p:.6f}")

# One-sided: testar se Linux < Windows em energia
linux_e   = df[df['os']=='linux']['pkg_energy_uj']
windows_e = df[df['os']=='windows']['pkg_energy_uj']
U, p = mannwhitneyu(linux_e, windows_e, method='exact', alternative='less')
print(f"U={U:.0f}  p={p:.6f}")
```

- **H0**: distribuições são iguais
- **H1**: distribuições são diferentes

### 5.5 A/B Test (Empirical p-value por permutação)

Mais intuitivo, não assume nenhuma distribuição.

```python
import numpy as np

def ab_test(group_a, group_b, n_permutations=10000):
    observed_diff = np.mean(group_a) - np.mean(group_b)
    combined = np.concatenate([group_a, group_b])
    n_a = len(group_a)

    count = 0
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_diff = np.mean(combined[:n_a]) - np.mean(combined[n_a:])
        if abs(perm_diff) >= abs(observed_diff):
            count += 1

    return observed_diff, count / n_permutations

diff, pvalue = ab_test(linux.values, windows.values)
print(f"Diferenca observada: {diff:.2f}ms   p-value empirico: {pvalue:.4f}")
```

---

## 6. Intervalos de Confiança

```python
from scipy import stats
import numpy as np

linux_n11 = df[(df['os']=='linux') & (df['n']==11)]['duration_ms']
ci = stats.t.interval(0.95,
                      df=len(linux_n11)-1,
                      loc=np.mean(linux_n11),
                      scale=stats.sem(linux_n11))
print(f"IC 95%: [{ci[0]:.2f}, {ci[1]:.2f}] ms")
```

**Interpretação:** Se os ICs de Linux e Windows não se sobrepõem → diferença significativa.

---

## 7. Tamanho da Amostra

```python
# n = (1.96 * sigma / e)^2
# sigma = desvio padrao estimado, e = margem de erro desejada
sigma = df['duration_ms'].std()
e = 10  # margem de erro em ms
n_needed = (1.96 * sigma / e) ** 2
print(f"Runs necessarias: {n_needed:.0f}")
```

**Pelo Teorema do Limite Central:** com n >= 30 amostras, a média amostral tende para uma distribuição Normal, independentemente da distribuição original dos dados.

---

## 8. Aplicação ao Projeto — Checklist de Análise

### Dados disponíveis

| Ficheiro | OS | N amostras |
|---|---|---|
| `results/linux/energy/energy_single.csv` | Linux | 24 (N=11) + 24 (N=12) |
| `results/windows/energy/energy_windows.csv` | Windows | 29 (N=11) + 26 (N=12) |

### Hipóteses do projeto

```
H0_tempo:   mu_linux  = mu_windows   (tempo equivalente)
H1_tempo:   mu_linux != mu_windows   (two-sided)

H0_energia: mu_linux  = mu_windows   (energia equivalente)
H1_energia: mu_linux  < mu_windows   (one-sided — Linux consome menos)
```

### Análise a fazer (por ordem)

- [ ] 1. Estatísticas básicas — `describe()` por OS e N
- [ ] 2. Boxplots — `duration_ms` e `pkg_energy_uj` por OS e N
- [ ] 3. Histogramas + KDE — verificar normalidade
- [ ] 4. Correlação Spearman — `duration_ms` vs `pkg_energy_uj`
- [ ] 5. Mann-Whitney U — Linux vs Windows para N=11 e N=12 (tempo e energia)
- [ ] 6. A/B test — validação empírica
- [ ] 7. Intervalos de confiança — médias de tempo e energia
- [ ] 8. Gráficos finais — barras com IC para o artigo

---

## 9. Tens dados suficientes?

**Sim — os dados são suficientes para análise estatística.**

| Critério | Requisito | Projeto |
|---|---|---|
| Mann-Whitney fiável | n >= 20 | OK (24-29 por grupo) |
| TLC (distribuição Normal) | n >= 30 recomendado | Ligeiramente abaixo em Linux (24) |
| StdDev Linux | < 1% | OK — 0.44% |
| StdDev Windows N=12 | < 5% | OK — 1.1% |
| StdDev Windows N=11 | aceitável | 8.8% — discutir no artigo |

**Nota para o artigo:** As 24 amostras por grupo no Linux estão ligeiramente abaixo do n=30 recomendado pelo TLC. É defensável, mas deve ser mencionado como limitação na secção de *threats to validity*.

A maior variância do Windows N=11 (8.8% vs 0.44% no Linux) indica que o scheduler do Windows é menos determinístico para workloads curtas. Este resultado é em si mesmo interessante e deve ser discutido.

---

## 10. Packages Python necessários

```bash
pip install pandas numpy scipy scikit-learn matplotlib seaborn
```
