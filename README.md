# Análise da Gravidade de Acidentes em Rodovias Federais

Projeto de Trabalho de Conclusão de Curso dedicado à análise de características associadas à
gravidade de acidentes registrados em rodovias federais brasileiras e à avaliação de modelos de aprendizado de máquina por meio de validação temporal.

## Dashboard

**Acesse a versão publicada:** <https://tcc-prf-severity.vercel.app>

O dashboard é uma interface complementar para explorar agregações descritivas e apresentar os
resultados científicos do estudo. Ele não treina modelos nem recalcula resultados de ML.

## Sobre o estudo

A pesquisa utiliza dados públicos da Polícia Rodoviária Federal (PRF) agrupados por ocorrência,
referentes ao período de 2021 a 2025. O objetivo é investigar características associadas à gravidade das ocorrências registradas e avaliar modelos capazes de distinguir acidentes graves dos não graves.

Neste estudo, uma ocorrência é classificada como grave quando possui ao menos uma pessoa morta ou ferida gravemente:

```text
target_grave = (mortos > 0) OR (feridos_graves > 0)
```

Essa é uma definição operacional adotada para a variável-alvo, não uma definição universal de
gravidade.

## Pergunta de pesquisa

> Quais características temporais, geográficas, meteorológicas e viárias estão associadas à gravidade dos acidentes registrados em rodovias federais brasileiras e em que medida modelos de aprendizado de máquina conseguem identificar ocorrências graves?

A pergunta foi desdobrada em cinco questões sobre associações descritivas, capacidade
preditiva, comparação dos modelos, consistência temporal e avaliação final em 2025.

## Dados

| Item | Descrição |
| --- | --- |
| Fonte | Polícia Rodoviária Federal — PRF |
| Período | 2021–2025 |
| Ocorrências | 342.624 |
| Ocorrências graves | 96.857 |
| Proporção grave | 28,27% |

O conjunto representa acidentes já registrados pela PRF. Ele não contém um denominador de exposição, como fluxo veicular, veículo-quilômetro ou número de viagens.

## Metodologia

O trabalho foi conduzido em etapas rastreáveis:

1. auditoria e preparação dos dados;
2. análise exploratória;
3. definição do conjunto de variáveis;
4. prevenção de vazamento de informação (*data leakage*);
5. validação temporal;
6. comparação entre Regressão Logística, Random Forest e XGBoost;
7. seleção formal do modelo;
8. definição do limiar de decisão com previsões temporais fora da amostra;
9. avaliação final em 2025;
10. interpretação do modelo com Tree SHAP.

O desenho temporal separou treinamento e validação cronologicamente:

```text
2021           → validação em 2022
2021–2022      → validação em 2023
2021–2023      → validação em 2024
refit 2021–2024 → avaliação final em 2025
```

## Principais resultados

Na análise descritiva, a proporção de ocorrências graves foi de 32,47% em Plena Noite e 25,30% em Pleno dia. Em pistas simples, foi de 33,71%, ante 23,35% em pistas duplas. Também foram observadas diferenças geográficas e meteorológicas, sem interpretação causal.

| Modelo | AP média nas validações temporais |
| --- | ---: |
| Regressão Logística | 0,3935 |
| Random Forest | 0,3960 |
| XGBoost | 0,4008 |

O XGBoost foi selecionado pela regra previamente definida de maior Average Precision (AP)
média. As diferenças absolutas entre os três modelos foram pequenas.

Na avaliação temporal final de 2025, o XGBoost obteve AP de 0,3974, ROC-AUC de 0,6286 e Brier de 0,1938. O desempenho permaneceu próximo ao observado durante o desenvolvimento, sem uso de 2025 para selecionar o modelo ou o limiar.

## O que o dashboard oferece

O site possui nove páginas: Sobre o estudo, Visão Geral, Exploração, Geografia, Modelos,
Validação Temporal, Limiar de Decisão, Interpretação e Metodologia.

- os resultados de aprendizado de máquina são congelados e somente leitura;
- os filtros exploratórios operam sobre agregações previamente publicadas;
- o frontend não treina modelos, executa inferência ou modifica métricas científicas.

## Tecnologias

- **Ciência de dados:** Python, Polars, scikit-learn, XGBoost e Pandera.
- **Dashboard:** Next.js, React, TypeScript, Recharts e Vercel.
- **Qualidade:** pytest, Ruff e Pyright.

## Estrutura do projeto

```text
dashboard/  Aplicação web estática e assets JSON publicados
data/       Dados brutos, intermediários e analíticos
docs/       Contratos, decisões metodológicas e documentação científica
reports/    Tabelas, figuras e artefatos de resultados
scripts/    Rotinas de verificação e geração controlada
src/        Código-fonte do pipeline de dados e modelagem
tests/      Testes automatizados
```

## Limitações

- O conjunto contém acidentes registrados, não a exposição total ao tráfego.
- As proporções apresentadas descrevem a gravidade entre os acidentes registrados e não representam o risco de uma pessoa sofrer um acidente ao trafegar pela rodovia.
- As associações observadas não demonstram relações causais.
- A disponibilidade operacional real das variáveis no instante inicial da PRF não foi validada.
- O desempenho preditivo observado não implica prontidão para uso operacional.

## Status

- Pesquisa experimental e dashboard concluídos.
- Dashboard publicado na Vercel.
- Etapa de redação acadêmica do TCC em andamento.
