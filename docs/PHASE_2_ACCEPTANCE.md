# Aceite da Fase 2 — Análise Exploratória

## Objetivo e escopo

A Fase 2 encerra a análise exploratória das 342.624 ocorrências registradas pela PRF entre
2021 e 2025. Foram concluídas:

- 2A — Caracterização Geral;
- 2B — Padrões Temporais;
- 2C — Padrões Geográficos;
- 2D — Via e Ambiente;
- 2E — Dinâmica das Ocorrências;
- 2F — Associação com Gravidade;
- 2G — Síntese Científica da EDA.

O baseline permanece em 96.857 ocorrências graves (28,2692%), com unidade de análise no nível
da ocorrência e `target_grave = (mortos > 0) OR (feridos_graves > 0)`.

## Critérios de aceite

- ambiente reproduzível e verificações estáticas aprovadas;
- 124 testes automatizados aprovados;
- interim e manifesto verificados, com cinco fontes RAW confirmadas;
- CLIs das Fases 2A–2F reproduzidas a partir do interim;
- oito achados centrais consolidados sem linguagem causal;
- matriz de elegibilidade adotada como autoridade para seleção futura;
- H001 preservada e 22 variáveis sinalizadas para avaliação de drift;
- RAW, interim, manifesto e target não modificados;
- `data/processed/` contém somente o `.gitkeep` preexistente;
- nenhuma feature, divisão treino/teste ou atividade de ML iniciada.

## Reprodução

```powershell
uv sync --locked
uv run prf-verify-interim
uv run prf-eda-general
uv run prf-eda-temporal
uv run prf-eda-geographic
uv run prf-eda-road-environment
uv run prf-eda-occurrence-dynamics
uv run prf-eda-severity-associations
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
```

## Artefatos principais

- síntese científica: `docs/PHASE_2_EDA_SYNTHESIS.md`;
- achados detalhados: `docs/EDA_FINDINGS.md`;
- memória científica curada: `docs/TCC_RESEARCH_LOG.md`;
- matriz de evidências: `reports/tables/phase_2f_association_evidence_matrix.csv`;
- matriz de elegibilidade: `reports/tables/phase_2f_modeling_eligibility_matrix.csv`;
- achados centrais: `reports/tables/phase_2f_core_findings.csv`;
- consistência temporal: `reports/tables/phase_2f_temporal_consistency_summary.csv`;
- decisões finais: `reports/tables/phase_2g_eda_decision_summary.csv`.

## Decisões metodológicas de fechamento

Os resultados descrevem gravidade entre ocorrências registradas, não risco de um acidente
ocorrer. Associação não implica causalidade. Tipo, causa, pessoas e veículos exigem decisão
metodológica específica; campos administrativos permanecem excluídos inicialmente; sete
campos estão bloqueados por leakage. A estabilidade anual do target não garante estabilidade
das features.

## Próximo passo oficial

Antes de criar dataset processed ou iniciar ML, deve-se definir formalmente o momento
preditivo, executar as verificações temporais previstas por H001 e resolver a elegibilidade de
`tipo_acidente`, `causa_acidente`, `pessoas` e `veiculos`. Somente depois dessas decisões pode
começar a preparação reproduzível para modelagem.

**Status:** Fase 2 aceita e encerrada; modelagem ainda não iniciada.
