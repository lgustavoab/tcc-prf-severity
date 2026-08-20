# Análise da Gravidade de Acidentes em Rodovias Federais

Projeto de Trabalho de Conclusão de Curso dedicado à análise de características associadas à gravidade de acidentes registrados em rodovias federais brasileiras e à avaliação de modelos de aprendizado de máquina por meio de validação temporal.

## Dashboard

**Acesse a versão publicada:** <https://tcc-prf-severity.vercel.app>

O dashboard é uma interface complementar ao TCC para apresentar resultados científicos e agregações descritivas. Ele não treina modelos nem recalcula resultados congelados.

## Sobre o estudo

A pesquisa utiliza dados públicos da Polícia Rodoviária Federal (PRF), agrupados por ocorrência, referentes ao período de 2021 a 2025. O objetivo é investigar características associadas à gravidade das ocorrências registradas e avaliar modelos capazes de distinguir acidentes graves dos não graves.

Neste estudo, grave significa uma ocorrência com pelo menos uma pessoa morta ou ferida gravemente:

```text
target_grave = (mortos > 0) OR (feridos_graves > 0)
```

Essa é a definição operacional adotada para a variável-alvo, não uma definição universal de gravidade.

## Pergunta de pesquisa

> Quais características temporais, geográficas, meteorológicas e viárias estão associadas à gravidade dos acidentes registrados em rodovias federais brasileiras e em que medida modelos de aprendizado de máquina conseguem identificar ocorrências graves?

A pergunta foi desdobrada em cinco questões sobre associações descritivas, capacidade preditiva, comparação dos modelos, consistência temporal e avaliação final em 2025.

## Dados

| Item | Descrição |
| --- | --- |
| Fonte | Polícia Rodoviária Federal — PRF, Dados Abertos |
| Unidade de análise | Acidente agrupado por ocorrência |
| Período | 2021–2025 |
| Ocorrências | 342.624 |
| Ocorrências graves | 96.857 |
| Proporção grave | 28,27% |

## Fonte dos dados

Os arquivos anuais estão no [Portal de Dados Abertos da PRF](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf), acompanhado pelo [dicionário oficial de acidentes](https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dicionario-acidentes). Para cada ano de 2021 a 2025, deve ser baixada a modalidade **Agrupados por ocorrência**; as bases agrupadas por pessoa não integram o dataset principal.

| Ano | Base PRF | Arquivo esperado no projeto |
| --- | --- | --- |
| 2021 | Agrupados por ocorrência | `datatran2021.csv` |
| 2022 | Agrupados por ocorrência | `datatran2022.csv` |
| 2023 | Agrupados por ocorrência | `datatran2023.csv` |
| 2024 | Agrupados por ocorrência | `datatran2024.csv` |
| 2025 | Agrupados por ocorrência | `datatran2025.csv` |

O contrato de ingestão espera esses nomes exatos. Após baixar e, quando necessário, extrair o CSV do arquivo compactado, não renomeie os CSVs: coloque-os em `data/raw/`. Os arquivos brutos são tratados como imutáveis e ignorados pelo Git.

## Como reproduzir o projeto

Há três usos distintos: visualizar os resultados no dashboard publicado; executar localmente apenas o frontend; ou reproduzir a análise científica com Python e os cinco RAW. O repositório não possui um único comando end-to-end: a reprodução usa entry points explícitos e contratos metodológicos versionados em `reports/`.

### 1. Pré-requisitos

- Git;
- [uv](https://docs.astral.sh/uv/);
- Python 3.14 — o projeto aceita `>=3.14,<3.15`, `.python-version` seleciona `3.14` e a materialização final registrada usou Python 3.14.6;
- Node.js com npm, somente para o dashboard; a versão de Node.js não está fixada no repositório.

### 2. Clonar e preparar o ambiente Python

```powershell
git clone https://github.com/lgustavoab/tcc-prf-severity.git
cd tcc-prf-severity
uv sync --locked
```

O `uv` sincroniza o ambiente usando `pyproject.toml` e o lockfile versionado.

### 3. Auditar os RAW e construir o interim

Depois de colocar os cinco CSVs em `data/raw/`, execute:

```powershell
uv run prf-audit
uv run prf-build-interim
uv run prf-verify-interim
```

`prf-audit` é o primeiro comando da pipeline. O build publica o Parquet intermediário e seu manifesto; o verifier apenas verifica os artefatos existentes, sem reconstruí-los.

### 4. Reproduzir as análises e a modelagem

Esta é a ordem real dos entry points científicos:

```powershell
uv run prf-eda-general
uv run prf-eda-temporal
uv run prf-eda-geographic
uv run prf-eda-road-environment
uv run prf-eda-occurrence-dynamics
uv run prf-eda-severity-associations
uv run prf-audit-temporal-drift
uv run prf-build-analytical
uv run prf-verify-analytical
uv run prf-design-experiment
uv run prf-validate-preprocessing
uv run prf-run-logistic-baseline
uv run prf-run-random-forest-baseline
uv run prf-run-xgboost-baseline
uv run prf-compare-models
uv run prf-select-model
uv run prf-select-threshold
uv run prf-refit-final-model
uv run prf-evaluate-final-2025
uv run prf-interpret-final-model
```

Os documentos em `docs/` registram os contratos, pré-requisitos e artefatos de cada fase. Não há comando que reconstrua automaticamente a redação e as decisões científicas documentais das Fases 5A–5F.

### 5. Regenerar figuras e JSONs

Após os resultados científicos, as figuras acadêmicas podem ser regeneradas com:

```powershell
uv run python scripts/generate_phase_5d_academic_visuals.py
```

Os JSONs necessários para visualizar o dashboard já estão versionados em `dashboard/public/data/`. Para regenerá-los a partir do dataset analítico e das tabelas científicas versionadas, use o timestamp canônico da publicação:

```powershell
uv run python scripts/export_dashboard_data.py --generated-at 2026-08-19T21:59:46.8033684Z
```

### 6. Validar o projeto Python

```powershell
uv run ruff check .
uv run pyright
uv run pytest
```

`ruff format .` modifica arquivos e, por isso, não integra essa validação somente leitura.

### 7. Executar o dashboard localmente

O diretório possui `package-lock.json`; uma instalação limpa usa:

```powershell
cd dashboard
npm ci
npm run dev
```

O Next.js usa por padrão <http://localhost:3000>. O comando `npm run check` agrega lint, typecheck, build e verificação da exportação estática; esses scripts também podem ser executados separadamente.

## Metodologia

O estudo abrange auditoria e preparação dos dados, EDA, política de features, prevenção de leakage, validação temporal, comparação de Regressão Logística, Random Forest e XGBoost, seleção formal, escolha do limiar, avaliação final em 2025 e interpretação com Tree SHAP.

```text
2021            → validação em 2022
2021–2022       → validação em 2023
2021–2023       → validação em 2024
refit 2021–2024 → avaliação final em 2025
```

## Principais resultados

Na análise descritiva, a proporção de ocorrências graves foi de 32,47% em Plena Noite e 25,30% em Pleno dia. Em pistas simples, foi de 33,71%, ante 23,35% em pistas duplas. Também foram observadas diferenças geográficas e meteorológicas, sem interpretação causal.

| Modelo | AP média nas validações temporais           |
| --- | ---: |
| Regressão Logística | 0,3935 |
| Random Forest | 0,3960 |
| XGBoost | 0,4008 |

O XGBoost foi selecionado pela regra previamente definida de maior Average Precision (AP) média, mas as diferenças absolutas entre os três modelos foram pequenas.

Na avaliação temporal final de 2025, o XGBoost obteve AP de 0,3974, ROC-AUC de 0,6286 e Brier de 0,1938. O desempenho permaneceu próximo ao observado durante o desenvolvimento, sem uso de 2025 para selecionar o modelo ou o limiar.

## O que o dashboard oferece

O site possui nove páginas: Sobre o estudo, Visão Geral, Exploração, Geografia, Modelos, Validação Temporal, Limiar de Decisão, Interpretação e Metodologia.

- os resultados de aprendizado de máquina são congelados e somente leitura;
- os filtros exploratórios operam sobre agregações previamente publicadas;
- o frontend não treina modelos, executa inferência ou modifica métricas científicas.

## Tecnologias

- **Ciência de dados:** Python, Polars, scikit-learn, XGBoost, Pandera e uv.
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

- O conjunto contém acidentes registrados e não inclui um denominador de exposição ao tráfego.
- As proporções apresentadas descrevem a gravidade entre os acidentes registrados e não representam o risco de uma pessoa sofrer um acidente ao trafegar pela rodovia.
- As associações observadas não demonstram relações causais.
- A disponibilidade operacional real das variáveis no instante inicial da PRF não foi validada.
- O desempenho preditivo observado não implica prontidão para uso operacional.

## Status

- Pesquisa experimental e dashboard concluídos.
- Dashboard publicado na Vercel.
- Etapa de redação acadêmica do TCC em andamento.
