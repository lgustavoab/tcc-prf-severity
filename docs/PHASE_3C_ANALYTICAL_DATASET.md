# Fase 3C — Dataset analítico principal

## Objetivo e fonte autoritativa

A Fase 3C materializa o dataset analítico principal sem iniciar machine learning. A fonte de
dados é `data/interim/prf_accidents_2021_2025.parquet`; o contrato autoritativo é
`reports/tables/phase_3b_primary_feature_set.csv`. A construção falha se esse contrato não
contiver, na ordem congelada, exatamente as 11 representações conceituais da Fase 3B.

O artefato final é `data/processed/prf_primary_analytical_2021_2025.parquet`. Ele conserva uma
linha por ocorrência e aplica apenas seleção, renomeação e derivações determinísticas.

## Papéis das colunas

O Parquet possui 26 colunas físicas, separadas formalmente no esquema:

- metadata: `id`, `source_year`, `data_inversa`;
- target: `target_grave`;
- predictors: 22 colunas físicas autorizadas.

Metadata sustenta identidade, proveniência e o futuro desenho temporal, mas não integra a
matriz de predictors. `data_inversa` permanece exclusivamente nesse papel. O target é
preservado do interim e sua definição é validada contra
`(mortos > 0) OR (feridos_graves > 0)`; as duas contagens não são levadas ao processed.

## Representações conceituais e predictors físicos

As 11 representações conceituais são:

1. `month_name`;
2. `dia_semana`;
3. `hour`;
4. `uf`;
5. `br`;
6. `km`;
7. `sentido_via`;
8. `condicao_metereologica`;
9. `tipo_pista`;
10. `uso_solo`;
11. `tracado_via_components`.

As dez primeiras geram dez colunas físicas. `tracado_via_components` gera 12 indicadores
binários, totalizando 22 predictors. Uma ocorrência pode ativar vários indicadores; tokens
repetidos na mesma ocorrência contam apenas uma vez.

| Rótulo da PRF | Coluna física |
|---|---|
| Aclive | `tracado_aclive` |
| Curva | `tracado_curva` |
| Declive | `tracado_declive` |
| Desvio Temporário | `tracado_desvio_temporario` |
| Em Obras | `tracado_em_obras` |
| Interseção de Vias | `tracado_intersecao_de_vias` |
| Ponte | `tracado_ponte` |
| Reta | `tracado_reta` |
| Retorno Regulamentado | `tracado_retorno_regulamentado` |
| Rotatória | `tracado_rotatoria` |
| Túnel | `tracado_tunel` |
| Viaduto | `tracado_viaduto` |

Os indicadores usam `UInt8` e aceitam somente 0 ou 1. Qualquer componente fora do
vocabulário validado na Fase 2D interrompe a construção.

## Derivações e preservação semântica

`month_name` é derivado de `data_inversa` pela lógica temporal já auditada e `hour` é derivado
de `horario`. `dia_semana` é preservado do interim. `horario` e `fase_dia` não permanecem no
artefato.

`km` continua numérico e observado, sem bins, escala, winsorização ou remoção de `km = 0`.
Também são preservados literalmente `br = 0`, `sentido_via = Não Informado` e
`condicao_metereologica = Ignorado`; esses valores não são convertidos em null nem imputados.

## Exclusões

O dataset não contém:

- leakage: `mortos`, `feridos_graves`, `feridos_leves`, `feridos`, `ilesos`, `ignorados` e
  `classificacao_acidente`;
- administrativas: `regional`, `delegacia` e `uop`;
- secondary only: `tipo_acidente`, `causa_acidente`, `pessoas` e `veiculos`;
- representações excluídas: `horario`, `fase_dia`, `municipio`, `latitude`, `longitude` e
  `tracado_via` bruto.

O cenário secundário não foi materializado.

## Ausência de preprocessing aprendido

A construção não ajusta encoder, scaler, imputer, bins, seleção, balanceamento ou qualquer
parâmetro estatístico. Como mês, hora e indicadores multilabel são determinísticos, nenhuma
informação de 2025 é usada para aprender transformações. O artefato ainda contém 2021–2025 e
`source_year` para permitir que a Fase 3D realize o split físico.

## Integridade confirmada

- 342.624 linhas e 342.624 IDs únicos;
- 26 colunas físicas totais;
- 22 predictors físicos;
- 96.857 ocorrências graves;
- prevalência de 28,2691814%;
- anos 2021, 2022, 2023, 2024 e 2025;
- zero valores nulos em todas as colunas finais;
- nenhuma linha removida ou adicionada.

## Esquema, manifesto e publicação

`reports/tables/phase_3c_analytical_schema.csv` registra nome, papel, representação
conceitual, fonte, derivação, dtype, nulabilidade, domínio e inclusão na futura matriz de
modelo.

`artifacts/processed/phase_3c_primary_analytical_manifest.json` registra métricas, dtypes,
missingness, colunas e mapa multilabel, além dos SHA-256 do Parquet analítico, do interim, do
contrato 3B e do esquema. Não há timestamp volátil. Parquet, esquema e manifesto são escritos
em temporários e publicados como conjunto com backup e rollback; falhas não deixam uma versão
parcial como estado válido.

## Reprodução e verificação

```powershell
uv run prf-verify-interim
uv run prf-build-analytical
uv run prf-verify-analytical
```

O build verifica o interim antes da construção. O verifier não reconstrói o artefato: ele
relê Parquet, contrato, esquema, manifesto e fonte, recalcula hashes, reconcilia papéis,
população, target, IDs, anos e indicadores e rejeita colunas proibidas.

## Limitações e próximo passo

A disponibilidade operacional campo a campo continua sendo uma premissa metodológica da
política 3B, não uma confirmação do fluxo interno da PRF. O processed ainda não é uma matriz
numericamente pronta para modelos: categorias permanecem sem encoding e `km` sem escala ou
imputação.

O próximo passo é a Fase 3D: materializar o desenho temporal com 2021–2024 para
desenvolvimento e 2025 para avaliação final, aprendendo qualquer preprocessing somente no
período de desenvolvimento. Nenhum split ou modelo foi criado na Fase 3C.
