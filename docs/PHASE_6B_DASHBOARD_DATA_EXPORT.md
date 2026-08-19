# Fase 6B — Exportação dos dados estáticos do dashboard

## 1. Objetivo

A Fase 6B materializa a camada de dados definida pela arquitetura 6A. O pipeline transforma
o dataset analítico congelado e tabelas científicas publicadas em JSONs estáticos, auditados e
versionados em `dashboard/public/data/`. Nenhum frontend, modelo ou cálculo experimental foi
implementado nesta fase.

## 2. Arquitetura implementada

O fluxo efetivo é:

```text
dataset analítico 3C + tabelas científicas congeladas
        ↓
Python + Polars
        ↓
validação, reconciliação e serialização canônica
        ↓
publicação com backup e rollback
        ↓
dashboard/public/data/*.json
```

A implementação está separada em:

- `src/tcc_prf_severity/dashboard/contracts.py`: paths, assets, status científicos, dimensões
  permitidas e caveats;
- `src/tcc_prf_severity/dashboard/export.py`: leitura, transformação, validação, manifesto,
  reconciliação, hashes e publicação;
- `scripts/export_dashboard_data.py`: wrapper CLI fino;
- `tests/test_dashboard_export.py`: schemas, fronteiras, igualdade com fontes, determinismo e
  rollback.

## 3. Comando canônico

O timestamp UTC foi capturado uma vez e reutilizado nas duas execuções de aceitação:

```powershell
$generatedAt = "2026-08-19T21:59:46.8033684Z"
uv run python scripts/export_dashboard_data.py --generated-at $generatedAt
```

O valor canônico gravado no manifesto é `2026-08-19T21:59:46.8033684Z`. Com as mesmas fontes e
o mesmo `generated_at`, as duas materializações produziram lista de arquivos, bytes e hashes
SHA-256 idênticos.

## 4. Fontes e fronteira científica

Somente `OVERVIEW`, `EXPLORATION` e `GEOGRAPHY` leem o dataset
`data/processed/prf_primary_analytical_2021_2025.parquet`. Antes da agregação, o exportador
verifica o Parquet, o esquema e o manifesto 3C. As fontes RAW, o interim, modelos, OOF e
predições individuais não são carregados.

Os assets `FROZEN_RESULT` são cópias estruturadas de valores publicados nas tabelas 4D–4I e
nas tabelas acadêmicas T2 e A1. AP, ROC-AUC, Brier, calibração, threshold, matriz de confusão e
Tree SHAP não são recalculados.

## 5. Schemas físicos

Todo asset possui `metadata` com `schema_version`, `asset_id`, `part_id`,
`scientific_status`, `source_artifacts` e `required_caveats`. Assets tabulares usam `data` como
lista; nesses casos `row_count = len(data)`. Assets cujo conteúdo principal é objeto único
usam `row_count = 1`.

As quatro medidas exploratórias são:

- `total_occurrences`;
- `severe_occurrences`;
- `non_severe_occurrences`;
- `severe_proportion`.

Os números permanecem numéricos e não são formatados como percentuais pt-BR. A serialização
usa UTF-8, indentação de dois espaços, `allow_nan=False`, ordem determinística e newline final.

## 6. Escopos exploratórios

O asset lógico `EXPLORATION` possui duas partes físicas independentes:

- `temporal.json`: `source_year × dia_semana × hour`, com 840 combinações observadas;
- `contextual.json`: `source_year × tipo_pista × condicao_metereologica × uso_solo`, com 256
  combinações observadas.

Não existe produto cartesiano entre os dois escopos e não são criadas células zero. A parte
`geography.json` contém 1.288 combinações observadas de `source_year × uf × br`, preserva BR 0
e fornece `br_by_uf` para a dependência UF → BR.

## 7. Assets gerados

O manifesto cobre 12 assets lógicos em 14 partes físicas; contando o próprio manifesto, são
15 arquivos JSON.

| Asset / parte | Linhas | Bytes | SHA-256 |
|---|---:|---:|---|
| META / default | 1 | 1.267 | `789ef663c2a7ace6702368ec61fdb82a716c2daeb6348cd431c097de4339cd61` |
| OVERVIEW / default | 6 | 2.137 | `569fd1aa6e7abb5c4d61eac377ac284957f21a2da49bf0d29f32540765aa6114` |
| EXPLORATION / temporal | 840 | 202.578 | `ac7e3fa435686d55858c64129617ebc82bbe5ab0fa0bf732eb9cbbdf26b07335` |
| EXPLORATION / contextual | 256 | 74.353 | `cefc725e90d27e89483c5ea54d9881357459bd3706bb6dbb20ad68bf31b5c39f` |
| GEOGRAPHY / default | 1.288 | 286.016 | `e8eb18c2d24c26f798a64a37a6cd8fe1d069734ac7464f85c8717fea0ff764e8` |
| MODEL_COMPARISON / default | 3 | 2.746 | `c73211d1757de8d2344c592015f4ce595a1d6a58aee6c8e3bd83e9897b2195b2` |
| TEMPORAL_VALIDATION / default | 9 | 4.146 | `bf1ca374efe755993bfde4038fd0efcdc9f4de15381eceb835855527c7c79c49` |
| FINAL_2025 / default | 6 | 4.073 | `f717a8d1b60a8459e56211e4b7a8432e07c1a7e9ad7445ac9dd38593b823baa7` |
| CALIBRATION_2025 / default | 10 | 3.040 | `5d72cb4c5c85940a03face8b58ec1a92cd807ed35f4cbfcefcce8cd5c87a2784` |
| THRESHOLD_2025 / default | 1 | 929 | `e5579439ba9f5af6f6a3cfec290ea8b639fe10a3150b6429efaae25bfa91c264` |
| INTERPRETATION / source_predictors | 22 | 7.500 | `ef902aaf547993c0a04d926a2196dd54844b50d517aabbb95d4b6b7c0aead7ac` |
| INTERPRETATION / transformed_top15 | 15 | 5.213 | `e0413ff09154e3e608842aa37358003ad51808bf5bbdbd9c95f86144f4c6be0c` |
| METHODOLOGY_DESIGN / default | 3 | 4.262 | `c1181026ade8fd83776ab99a57f8aa333382ec8fa202e6d1b5871c00a6f48fbb` |
| METHODOLOGY_FEATURES / default | 11 | 15.171 | `626f12989cd1c59482b2ad645ea37af1e8890865f608af2d46339faac756423a` |

O tamanho agregado das 14 partes é 613.431 bytes. O maior arquivo é
`geography/geography.json`, com 286.016 bytes; nenhum asset alcança o limiar de revisão de
2 MiB ou o limite impeditivo de 5 MiB.

## 8. Reconciliação

As três agregações exploratórias reconciliam com T1:

- 342.624 ocorrências;
- 96.857 graves;
- 245.767 não graves;
- totais e graves anuais idênticos para 2021–2025.

O relatório `reports/tables/phase_6b_reconciliation.csv` contém 116 checks PASS e 0 FAIL. Isso
inclui 27 comparações diretas — AP, ROC-AUC e Brier para cada uma das nove combinações de
modelo/fold — entre a validação temporal exportada e a tabela 4D. O relatório também verifica
igualdade direta dos valores exportados de comparação de modelos, avaliação final, threshold,
calibração e interpretação com seus CSVs congelados.

O inventário `reports/tables/phase_6b_asset_inventory.csv` reproduz as 14 entradas do
manifesto, incluindo paths, row counts, tamanhos, hashes, fontes, versão e status.

## 9. Manifesto, hashes e publicação

`manifest.json` declara `schema_version = "1"`, `generated_at`, período, escopo, definição do
target e uma entrada para cada parte física. O SHA-256 é calculado sobre os bytes finais do
asset serializado; cada arquivo é reaberto e verificado antes e depois da publicação.

O conjunto é inicialmente escrito em diretório temporário no mesmo filesystem. Arquivos
gerenciados anteriores são movidos para backup, os novos arquivos são publicados e o backup é
removido somente após sucesso. Uma falha remove partes novas e restaura exatamente as versões
anteriores. Arquivos não gerenciados dentro de `dashboard/public/data/` não são apagados.

## 10. Testes e checklist

Os testes cobrem agregação observada, invariantes por célula, timestamp UTC, schemas,
manifesto, hashes, row counts, fronteiras entre escopos, ausência de IDs individuais,
reconciliação global e anual, UF → BR, igualdade de resultados congelados, ausência de filtros
em `FROZEN_RESULT`, determinismo byte a byte, limites de tamanho, rollback e preservação de
JSON não gerenciado.

O checklist da fase registra 50 PASS e 0 FAIL. Não foram criadas dependências, frontend,
figuras, modelos, predições, inferência ou novos resultados científicos.

## 11. Limitações e próxima fase

Os JSONs são contratos de dados, não uma interface. Textos finais, componentes, rotas,
responsividade, acessibilidade e validação do build estático permanecem fora desta fase. A
Fase 6C poderá criar a infraestrutura Next.js/React/TypeScript e consumir exclusivamente os
assets versionados, sem abrir Parquet ou executar Python no frontend.
