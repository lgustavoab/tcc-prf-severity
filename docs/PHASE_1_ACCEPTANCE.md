# Aceite da Fase 1 — Fundação de dados

## Objetivo

A Fase 1 estabelece uma fundação de dados reproduzível para estudar a gravidade das
ocorrências registradas pela Polícia Rodoviária Federal entre 2021 e 2025. O aceite comprova o
ambiente, a integridade das fontes, o contrato, a auditoria e a correspondência entre o Parquet
intermediário e seu manifesto de proveniência.

## Entregas da Fase 1

- **1A — Ambiente e auditoria reproduzível:** Python e dependências fixados pelo `uv.lock`,
  leitura dos cinco CSVs oficiais e relatório de qualidade.
- **1B — Contrato definitivo:** schema estrito, categorias estáveis, limites numéricos,
  invariantes entre colunas e definição operacional adotada para o target.
- **1C — Dataset intermediário:** consolidação técnica em Parquet Zstandard, validação antes e
  depois da escrita e manifesto com hashes e versões.
- **1D — Aceite formal:** verificação read-only do Parquet existente, do manifesto e das cinco
  fontes RAW atuais, sem reconstrução implícita.

## Baseline consolidado

| Métrica | Valor |
|---|---:|
| Período | 2021–2025 |
| Registros | 342.624 |
| Colunas RAW | 30 |
| Colunas interim | 32 |
| Ocorrências graves | 96.857 |
| Taxa de graves | 28,2692% |
| Anos presentes | 2021, 2022, 2023, 2024 e 2025 |
| IDs duplicados | 0 |
| Falhas em `feridos = feridos_leves + feridos_graves` | 0 |
| Divergências na decomposição de `pessoas` | 18.538 |
| `br = 0` | 883 |
| `km = 0` | 1.652 |

## Target e contrato

O target definitivo é:

```text
target_grave = (mortos > 0) OR (feridos_graves > 0)
```

`classificacao_acidente` não participa da regra. O [contrato de dados](DATA_CONTRACT.md)
mantém exatamente as 30 colunas oficiais e acrescenta `source_year` e `target_grave`. Ele
valida schema estrito, tipos, nulabilidade, categorias estáveis, limites e as invariantes de ID,
feridos, ano, target e dia da semana.

São bloqueantes: arquivo ou coluna ausente, tipo ou categoria inválida, limite numérico
violado, ID duplicado, identidade de feridos incorreta, ano divergente, target adulterado, dia
da semana incompatível, baseline de referência divergente, Parquet ilegível e falhas de
proveniência.

São métricas de qualidade não bloqueantes: as 18.538 divergências conhecidas na decomposição
de `pessoas`, os 883 registros com `br = 0` e os 1.652 registros com `km = 0`. Esses valores
são preservados e auditados, não corrigidos ou removidos.

## Arquitetura e proveniência

```text
5 CSVs oficiais em data/raw
        ↓ leitura e tipagem
contrato por ano
        ↓ consolidação cronológica
contrato e baseline consolidados
        ↓ escrita e releitura validadas
Parquet interim + manifesto SHA-256
        ↓ verificação read-only
fundação aceita
```

Os RAW nunca são alterados. `artifacts/interim/interim_manifest.json` registra o SHA-256 de
cada fonte, o SHA-256 e o tamanho do Parquet, métricas, anos, schema e versões relevantes. O
comando de aceite recalcula os hashes dos arquivos atuais e exige correspondência com o
manifesto.

Os arquivos de origem são oficiais da PRF. Os hashes abaixo são referências calculadas pelo
próprio projeto sobre os arquivos utilizados neste estudo, e não hashes publicados pela PRF.

Hashes RAW do baseline de referência do projeto:

```text
2021 b8ebf8352a5ad0d9d79a91a4dada665a1ec0bfca9fc2649e1c73fe80cfe6c4dd
2022 d11bbfdec9b5df6f08a083c63acb2c1b4d3bad71d31481d7ce1368d5fa38783a
2023 2e6a9eac714524822fc3150be4d0614e27c7f14aa674520c94e5d2e4089356dd
2024 a3b7423cf643acd5de12742f319d5456930b1f105b44df4b81fae560b40af64c
2025 bb844d45a07b5b50f5f76011e28f47e370fa6742e9211edac5510dcbe72ce4d8
```

## Reprodução e aceite

```powershell
uv sync --locked
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
uv run prf-audit
uv run prf-build-interim
uv run prf-verify-interim
```

O aceite exige Ruff sem erros, Pyright sem erros ou warnings, testes aprovados, auditoria no
baseline, Parquet com 342.624 × 32, 96.857 graves, cinco anos, IDs únicos, manifesto
correspondente e cinco fontes RAW com hashes confirmados.

`prf-build-interim` é o comando explícito de reconstrução. `prf-verify-interim` nunca
reconstrói: apenas lê e verifica os artefatos existentes.

## Limitações e trabalho ainda não realizado

A base contém apenas ocorrências registradas e não permite modelar a probabilidade de um
acidente acontecer. Ainda não foram realizados EDA, visualizações analíticas, notebooks,
limpeza analítica, imputação, tratamento de outliers, expansão de `tracado_via`, harmonização
de `causa_acidente` ou `tipo_acidente`, feature engineering, criação do dataset `processed`,
divisão treino/teste, treinamento de modelos, API ou dashboard.

## Autorização para a Fase 2

Com todos os critérios acima aprovados, a fundação de dados da Fase 1 está formalmente aceita.
Fica autorizada a abertura da **Fase 2 — Análise Exploratória de Dados (EDA)**, preservando o
Parquet interim como entrada imutável e registrando separadamente quaisquer decisões
analíticas futuras.
