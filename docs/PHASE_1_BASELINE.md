# Fase 1 — Baseline da auditoria

Este arquivo registra os valores esperados para os cinco CSVs enviados e analisados em 18/08/2026. Ele serve como referência para a primeira execução local do comando `uv run prf-audit`.

## Resultado consolidado esperado

| Métrica | Valor |
|---|---:|
| Registros | 342.624 |
| IDs únicos | 342.624 |
| IDs duplicados | 0 |
| Graves — `target_grave` | 96.857 |
| Taxa de graves | 28,2692% |
| Falhas em `feridos = feridos_leves + feridos_graves` | 0 |
| Divergências na decomposição de `pessoas` | 18.538 |
| `br = 0` | 883 |
| `km = 0` | 1.652 |

## Resultado anual esperado

| Ano | Registros | Graves | Taxa de graves | Divergências `pessoas` |
|---|---:|---:|---:|---:|
| 2021 | 64.567 | 18.118 | 28,0608% | 3.517 |
| 2022 | 64.606 | 18.409 | 28,4943% | 3.547 |
| 2023 | 67.766 | 19.212 | 28,3505% | 3.767 |
| 2024 | 73.156 | 20.625 | 28,1932% | 3.884 |
| 2025 | 72.529 | 20.493 | 28,2549% | 3.823 |

## Integridade dos arquivos brutos

SHA-256 dos arquivos analisados:

```text
2021 b8ebf8352a5ad0d9d79a91a4dada665a1ec0bfca9fc2649e1c73fe80cfe6c4dd
2022 d11bbfdec9b5df6f08a083c63acb2c1b4d3bad71d31481d7ce1368d5fa38783a
2023 2e6a9eac714524822fc3150be4d0614e27c7f14aa674520c94e5d2e4089356dd
2024 a3b7423cf643acd5de12742f319d5456930b1f105b44df4b81fae560b40af64c
2025 bb844d45a07b5b50f5f76011e28f47e370fa6742e9211edac5510dcbe72ce4d8
```

Se a auditoria local produzir números diferentes, primeiro compare os hashes. A PRF pode atualizar retroativamente um arquivo anual, e isso deve ser registrado em vez de tratado automaticamente como erro do pipeline.

## Contrato definitivo

O target oficial é `target_grave = (mortos > 0) OR (feridos_graves > 0)`. A auditoria
aplica o [contrato de dados](DATA_CONTRACT.md) completo antes de produzir os relatórios.
`classificacao_acidente` não participa da construção do target.
