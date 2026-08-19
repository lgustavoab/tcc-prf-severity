# TCC — Gravidade de Acidentes em Rodovias Federais

Projeto de Ciência de Dados para analisar fatores associados à gravidade de acidentes registrados pela Polícia Rodoviária Federal (PRF) entre 2021 e 2025 e, posteriormente, avaliar modelos de aprendizado de máquina.

## Estado atual

**Fase 3A — Auditoria Temporal e Drift das Features concluída.**

Nesta fase o projeto:

- preserva os CSVs oficiais sem alteração;
- valida a presença e ordem das 30 colunas esperadas;
- padroniza apenas tipos técnicos;
- cria a definição operacional de `target_grave` (`mortos > 0` ou `feridos_graves > 0`), sem usar
  `classificacao_acidente`;
- valida tipos, nulabilidade, categorias estáveis e limites numéricos com Pandera;
- valida IDs, relações entre contagens, ano, target e dia da semana entre colunas;
- gera relatório de qualidade por ano;
- mantém divergências na decomposição de `pessoas` como métrica de auditoria, não como erro;
- consolida os cinco anos em um Parquet validado antes e depois da persistência;
- registra proveniência, hashes e versões em um manifesto;
- verifica o Parquet e sua proveniência sem reconstruir ou modificar os artefatos;
- caracteriza volume anual, estabilidade do target, nulidade e cardinalidade básica;
- caracteriza mês, dia da semana, hora e fase do dia, incluindo estabilidade descritiva anual;
- caracteriza macrorregião, UF, BR e município, separando volume de proporção grave;
- caracteriza tipo de pista, uso do solo, sentido, meteorologia e componentes multivalorados
  de traçado, separando volume, proporção grave, amostra e estabilidade anual;
- caracteriza tipo e causa registrados, mudanças de taxonomia e distribuições exatas de
  pessoas e veículos, sem decidir sua elegibilidade futura como features;
- consolida oito achados centrais e separa evidência descritiva de elegibilidade preditiva;
- encerra a EDA com uma síntese científica, uma matriz autoritativa de elegibilidade e um
  inventário de verificações temporais futuras;
- audita as 22 variáveis sinalizadas comparando 2021–2024 com 2025, com TVD descritiva,
  categorias não vistas, bins numéricos definidos somente no desenvolvimento e prevalências
  multilabel de traçado;
- ainda não remove ou imputa registros, faz análises causais, feature engineering ou machine
  learning.

Consulte o [`contrato de dados`](docs/DATA_CONTRACT.md) e a documentação do
[`dataset intermediário`](docs/INTERIM_DATASET.md). O aceite formal da fundação está em
[`docs/PHASE_1_ACCEPTANCE.md`](docs/PHASE_1_ACCEPTANCE.md). A síntese e o aceite da EDA estão
em [`docs/PHASE_2_EDA_SYNTHESIS.md`](docs/PHASE_2_EDA_SYNTHESIS.md) e
[`docs/PHASE_2_ACCEPTANCE.md`](docs/PHASE_2_ACCEPTANCE.md).
Os métodos e resultados da auditoria temporal estão em
[`docs/PHASE_3A_TEMPORAL_DRIFT.md`](docs/PHASE_3A_TEMPORAL_DRIFT.md).

## Requisitos

- Python 3.14
- uv

## Dados

Baixe os arquivos oficiais agrupados por ocorrência da PRF e coloque-os em `data/raw/`:

```text
datatran2021.csv
datatran2022.csv
datatran2023.csv
datatran2024.csv
datatran2025.csv
```

Os dados brutos não são versionados no Git.

## Instalação

```powershell
uv sync --locked
```

O `uv.lock` deve ser versionado no repositório. Ele é gerenciado pelo uv; não deve ser editado manualmente.

## Auditoria

```powershell
uv run prf-audit
```

Saídas esperadas:

```text
artifacts/audit/audit_2021_2025.json
artifacts/audit/audit_summary.csv
```

## Dataset intermediário

```powershell
uv run prf-build-interim
```

Saídas locais, derivadas e ignoradas pelo Git:

```text
data/interim/prf_accidents_2021_2025.parquet
artifacts/interim/interim_manifest.json
```

## Reprodução da fundação de dados

```powershell
uv sync --locked
uv run prf-audit
uv run prf-build-interim
uv run prf-verify-interim
```

- `uv sync --locked`: reproduz o ambiente definido no `uv.lock`.
- `prf-audit`: valida os RAW e reproduz as métricas de qualidade.
- `prf-build-interim`: reconstrói e publica o par Parquet + manifesto.
- `prf-verify-interim`: verifica, sem reconstruir, contrato, baseline, manifesto e hashes RAW.

## Qualidade

```powershell
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
```

## EDA — Caracterização geral

```powershell
uv run prf-eda-general
```

O comando verifica o interim e gera quatro tabelas em `reports/tables/` e duas figuras
científicas em `reports/figures/`. A lógica numérica oficial está em
`src/tcc_prf_severity/analysis/general.py`.

## EDA — Padrões temporais

```powershell
uv run prf-eda-temporal
```

O comando verifica o interim sem reconstruí-lo e gera dez tabelas temporais em
`reports/tables/` e sete figuras científicas em `reports/figures/`. As derivações de mês e hora
existem somente em memória; nenhum dataset processed é criado.

## EDA — Padrões geográficos

```powershell
uv run prf-eda-geographic
```

O comando verifica o interim, deriva macrorregião somente em memória e gera 15 tabelas e seis
figuras geográficas. As tabelas completas preservam `br = 0` e todas as categorias; rankings
de taxa de BR e município usam `n >= 500` apenas como critério editorial de destaque.

## EDA — Via e ambiente

```powershell
uv run prf-eda-road-environment
```

O comando verifica o interim sem reconstruí-lo e gera 14 tabelas e quatro figuras sobre tipo
de pista, uso do solo, sentido, meteorologia e componentes de `tracado_via`. A separação dos
componentes ocorre somente em memória; suas contagens não são mutuamente exclusivas. O corte
`n >= 500` é apenas um critério editorial para destaques de taxa em meteorologia e traçado;
`Ignorado` permanece nas tabelas completas, mas não é tratado como condição meteorológica
informada nesses destaques.

## EDA — Dinâmica das ocorrências

```powershell
uv run prf-eda-occurrence-dynamics
```

O comando verifica o interim sem reconstruí-lo e gera 17 tabelas e seis figuras sobre tipo de
acidente, causa registrada pela PRF, mudanças de taxonomia e contagens exatas de pessoas e
veículos. Não há harmonização, bins, remoção de outliers ou dataset processed. Essas variáveis
são permitidas na EDA associativa, mas sua elegibilidade para ML será decidida separadamente
devido à disponibilidade temporal e ao risco de leakage.

## EDA — Associação com gravidade

```powershell
uv run prf-eda-severity-associations
```

O comando verifica o interim e recalcula uma síntese das associações descritivas das Fases
2A–2E com `target_grave`. Ele gera quatro tabelas consolidadas e uma figura, incluindo uma
matriz conceitual de elegibilidade para modelagem futura. Não cria features, divisão
treino/teste, modelos ou dataset processed.

## Auditoria temporal das features

```powershell
uv run prf-audit-temporal-drift
```

O comando verifica o interim, lê o inventário autoritativo da Fase 2F e compara as 22
variáveis sinalizadas entre 2021–2024 e 2025. Gera sete tabelas e até três figuras sem criar
split, dataset processed, encoding, seleção definitiva de features ou modelo.

## Documentação científica

- [`PHASE_2_EDA_SYNTHESIS.md`](docs/PHASE_2_EDA_SYNTHESIS.md): síntese científica e resposta
  provisória da EDA à pergunta de pesquisa.
- [`PHASE_2_ACCEPTANCE.md`](docs/PHASE_2_ACCEPTANCE.md): aceite formal das Fases 2A–2G.
- [`TCC_RESEARCH_LOG.md`](docs/TCC_RESEARCH_LOG.md): memória científica curada de decisões,
  resultados confirmados, hipóteses e limitações.
- [`EDA_FINDINGS.md`](docs/EDA_FINDINGS.md): registro detalhado dos achados da Fase 2,
  inclusive resultados provisórios ou inconclusivos.
- [`PHASE_1_ACCEPTANCE.md`](docs/PHASE_1_ACCEPTANCE.md): evidência congelada do encerramento e
  aceite da fundação de dados.

## Grupos planejados

As dependências das fases futuras já estão separadas no `pyproject.toml`:

- `ml`: scikit-learn, XGBoost, Optuna, MLflow e SHAP;
- `viz`: JupyterLab, Plotly e Streamlit.

Matplotlib é uma dependência principal da geração das figuras científicas da Fase 2. Os grupos
`ml` e `viz` permanecem reservados para fases futuras.

## Próximo passo

A Fase 3B deve usar a auditoria temporal para definir momento preditivo, tratamento de
categorias desconhecidas, representações redundantes e elegibilidade metodológica, ainda sem
usar 2025 para aprender transformações.

## Princípio metodológico

O projeto não pretende prever **se** um acidente ocorrerá. A base contém somente ocorrências registradas. A futura modelagem avaliará, dado que uma ocorrência aconteceu, a capacidade de características contextuais ajudarem a identificar ocorrências com ferido grave ou morte.
