# TCC — Gravidade de Acidentes em Rodovias Federais

Projeto de Ciência de Dados para analisar fatores associados à gravidade de acidentes registrados pela Polícia Rodoviária Federal (PRF) entre 2021 e 2025 e, posteriormente, avaliar modelos de aprendizado de máquina.

## Estado atual

**Fase 1C — Dataset intermediário padronizado em Apache Parquet.**

Nesta fase o projeto:

- preserva os CSVs oficiais sem alteração;
- valida a presença e ordem das 30 colunas esperadas;
- padroniza apenas tipos técnicos;
- cria o target oficial `target_grave` (`mortos > 0` ou `feridos_graves > 0`), sem usar
  `classificacao_acidente`;
- valida tipos, nulabilidade, categorias estáveis e limites numéricos com Pandera;
- valida IDs, relações entre contagens, ano, target e dia da semana entre colunas;
- gera relatório de qualidade por ano;
- mantém divergências na decomposição de `pessoas` como métrica de auditoria, não como erro;
- consolida os cinco anos em um Parquet validado antes e depois da persistência;
- registra proveniência, hashes e versões em um manifesto;
- ainda não remove ou imputa registros, faz feature engineering ou machine learning.

Consulte o [`contrato de dados`](docs/DATA_CONTRACT.md) e a documentação do
[`dataset intermediário`](docs/INTERIM_DATASET.md).

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
uv lock
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

## Qualidade

```powershell
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
```

## Grupos planejados

As dependências das fases futuras já estão separadas no `pyproject.toml`:

- `ml`: scikit-learn, XGBoost, Optuna, MLflow e SHAP;
- `viz`: JupyterLab, Matplotlib, Plotly e Streamlit.

Elas não são necessárias para concluir a Fase 1.

## Princípio metodológico

O projeto não pretende prever **se** um acidente ocorrerá. A base contém somente ocorrências registradas. A futura modelagem avaliará, dado que uma ocorrência aconteceu, a capacidade de características contextuais ajudarem a identificar ocorrências com ferido grave ou morte.
