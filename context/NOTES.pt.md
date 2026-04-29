# Notas do Projeto (Português)

## Contexto Académico

- UC / contexto: trabalho individual / artigo académico
- Instituição: Universidade do Minho (UMinho), Braga
- Área: Engenharia Informática — Mestrado
- Objetivo final: artigo publicável sobre eficiência energética de C# em diferentes SO

---

## Decisões Tomadas

### Porquê FannkuchRedux?
- É um benchmark CPU-bound puro — isola o comportamento do runtime sem ruído de I/O
- Amplamente usado na literatura de benchmarking cross-linguagem (Computer Language Benchmarks Game)
- Permite comparação futura com outras linguagens (Go, Rust, Java) se o trabalho for expandido

### Porquê abandonar o CodeCarbon?
- Em Windows usa estimativas baseadas em TDP, não medições reais
- Criaria assimetria metodológica: Linux mediria com RAPL real, Windows com estimativa
- Para um artigo, essa assimetria seria uma fraqueza crítica na revisão por pares

### Porquê RAPL direto?
- O i7-8850H (Coffee Lake) tem suporte RAPL completo: Package, PP0, PP1, DRAM
- Em Linux: leitura via `/sys/class/powercap/intel-rapl/` (sem dependências extra)
- Em Windows: `LibreHardwareMonitorLib` NuGet (ativamente mantido, suporta .NET 9)
- Mesma fonte de dados físicos nos dois SO → comparação metodologicamente sólida

---

## Riscos Identificados

### Throttling térmico
O EliteBook 1050 G1 tem 6+ anos. Com 6 cores a 100%, pode fazer throttling.
- **Mitigação**: desligar turbo boost, monitorizar temperatura, descartar runs acima de 85°C
- Documentar explicitamente na secção de metodologia do artigo

### Disco quase cheio (Linux)
A partição `/` está a 85% de uso (41GB de 48GB).
- **Ação**: limpar antes de começar recolha de dados

### Variância RAPL
O Intel filtrou as leituras RAPL (IPU 2021.2) por razões de segurança (side-channel).
- Afeta Linux e Windows igualmente
- **Mitigação**: muitas iterações, reportar distribuição estatística completa

---

## Perguntas em Aberto

- [ ] Qual versão exata do .NET SDK usar? (target: .NET 9, confirmar disponibilidade no Windows)
- [ ] Devo incluir resultados de temperatura na análise principal ou apenas como metadado de qualidade?
- [ ] O artigo vai comparar apenas Windows vs Linux, ou também single vs multi-thread como dimensão separada?
- [ ] Revista / conferência alvo para submissão?

---

## Sessões com Claude Code

### Como usar esta pasta
Ao iniciar uma sessão com Claude Code, passa os ficheiros relevantes como contexto:
- Para scaffolding de código: `PROJECT.md` + `ARCHITECTURE.md` + `CONVENTIONS.md`
- Para setup de ambiente: `HARDWARE.md`
- Para revisão geral: todos os ficheiros

### Prompt base recomendado para Claude Code
```
Lê os ficheiros em context/ antes de qualquer ação.
Projeto: benchmark C# FannkuchRedux, Windows vs Linux, energia via RAPL.
Hardware: Intel i7-8850H, dual-boot Windows 11 Pro / Ubuntu 24.04.
Sê consistente com CONVENTIONS.md.
```

---

## Log de Progresso

| Data | Ação |
|---|---|
| 2025-01 | Definição do tema e abordagem metodológica |
| 2025-01 | Avaliação e rejeição do CodeCarbon para Windows |
| 2025-01 | Escolha do LibreHardwareMonitorLib para RAPL em Windows |
| 2025-01 | Estrutura do repositório definida |
| 2025-01 | Pasta context/ criada e populada |
