# TCC — Gravidade de Acidentes em Rodovias Federais

Projeto de Ciência de Dados para analisar fatores associados à gravidade de acidentes registrados pela Polícia Rodoviária Federal (PRF) entre 2021 e 2025 e, posteriormente, avaliar modelos de aprendizado de máquina.

## Estado atual

**Fase 1 — Ingestão e auditoria reproduzível.**

Nesta fase o projeto:

- preserva os CSVs oficiais sem alteração;
- valida a presença e ordem das 30 colunas esperadas;
- padroniza apenas tipos técnicos;
- cria um `target_grave_provisorio` para auditoria (`mortos > 0` ou `feridos_graves > 0`);
- valida o schema com Pandera;
- gera relatório de qualidade por ano;
- ainda não faz limpeza de negócio, feature engineering ou machine learning.

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

## Gerar Parquet padronizado

Após a auditoria ser aprovada:

```powershell
uv run prf-ingest
```

Saída:

```text
data/interim/prf_2021_2025_standardized.parquet
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
