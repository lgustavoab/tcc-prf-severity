# Fase 3E — Pipeline de preprocessing

## Objetivo

A Fase 3E congela e valida a receita de preprocessing do conjunto principal antes da
modelagem. Toda transformação aprendida é ajustada exclusivamente nas linhas de treino de
cada fold temporal e aplicada depois à respectiva validação. Esta fase não treina modelos,
não calcula métricas preditivas e não seleciona threshold.

## Contrato de entrada

A entrada é `data/processed/prf_primary_analytical_2021_2025.parquet`, validada com o esquema
e o manifesto da Fase 3C. As 22 colunas com `role = predictor` e
`included_in_model_matrix = true` são obtidas de
`reports/tables/phase_3c_analytical_schema.csv`; não existe uma segunda lista independente de
predictors.

`id`, `source_year`, `data_inversa` e `target_grave` não entram no `ColumnTransformer`.
`source_year` serve somente para selecionar os folds. O preprocessing é estritamente não
supervisionado em relação ao target.

## Grupos e transformações

As nove variáveis categóricas são:

- `month_name`;
- `dia_semana`;
- `hour`;
- `uf`;
- `br`;
- `sentido_via`;
- `condicao_metereologica`;
- `tipo_pista`;
- `uso_solo`.

Embora armazenados como inteiros, `hour` e `br` são tratados como categorias por sua
semântica. O bloco usa `OneHotEncoder(handle_unknown="ignore", drop=None,
min_frequency=None, max_categories=None, sparse_output=True)`. Assim, todas as categorias do
treino são preservadas, inclusive `Ignorado`, `Não Informado` e `br = 0`; validação e 2025
jamais fornecem vocabulário ao encoder.

`km` é a única variável numérica contínua e usa `StandardScaler`, ajustado somente no treino
do fold. Não são usados bins, clipping, winsorização, log ou imputação, e `km = 0` permanece
uma entrada válida.

As 12 colunas `tracado_*`, identificadas no esquema pelo conceito
`tracado_via_components`, são validadas como 0/1 e seguem por `passthrough`, sem encoding,
escala ou imputação.

O `ColumnTransformer` usa os blocos `categorical`, `numeric` e `binary`, com
`remainder="drop"` e saída esparsa. Como a Fase 3C não encontrou missingness, qualquer null
inesperado causa falha; nenhum imputer foi introduzido.

## Política de categorias desconhecidas

`handle_unknown="ignore"` permite transformar uma categoria de validação ausente no treino,
mas não a oculta da auditoria. Para cada variável categórica e fold, a tabela
`phase_3e_unknown_category_audit.csv` registra as categorias aprendidas, a cardinalidade da
validação, categorias desconhecidas, ocorrências afetadas e proporção das linhas de validação.
Uma categoria desconhecida é um diagnóstico temporal, não um erro automático.

## Validação temporal real

Cada fold recebe uma nova instância não fitada do preprocessor:

| Fold | Fit | Transform | Linhas fit | Linhas validation | Categóricas OHE | Saída total | Unknowns por feature | Linhas com algum unknown |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2021 | 2022 | 64.567 | 64.606 | 202 | 215 | 12 | 12 |
| 2 | 2021–2022 | 2023 | 129.173 | 67.766 | 207 | 220 | 3 | 3 |
| 3 | 2021–2023 | 2024 | 196.939 | 73.156 | 210 | 223 | 3 | 3 |

As dimensões diferem porque cada encoder aprende somente o vocabulário de seu treino. Isso é
esperado e não é corrigido com um vocabulário global. Em todos os folds, a composição foi uma
matriz `csr_matrix` esparsa, com uma coluna de `km`, 12 indicadores de traçado e zero valores
não finitos tanto no treino quanto na validação.

Os unknowns reais ocorreram somente em `br`:

- Fold 1: BRs 265, 342, 430, 437 e 485; 12 linhas de 2022 (0,018574%);
- Fold 2: BRs 352, 494 e 498; 3 linhas de 2023 (0,004427%);
- Fold 3: BRs 307, 363 e 466; 3 linhas de 2024 (0,004101%).

As demais oito variáveis categóricas tiveram zero categorias desconhecidas. A tabela de
resumo distingue a soma de ocorrências por feature das linhas deduplicadas com pelo menos um
unknown.

## Rastreabilidade e artefatos

Após cada fit, os nomes de saída são recuperados deterministicamente pelo
`ColumnTransformer`, incluindo one-hot, `numeric__km` e os 12 nomes do bloco binário. O
resultado de auditoria mantém anos de fit, ano transformado, linhas, nomes e categorias
aprendidas. Nenhum desses estados fitados é salvo como pickle, joblib, encoder, scaler ou
`ColumnTransformer`.

As saídas versionadas são:

- `reports/tables/phase_3e_preprocessing_contract.csv`;
- `reports/tables/phase_3e_fold_preprocessing_summary.csv`;
- `reports/tables/phase_3e_unknown_category_audit.csv`.

## Fronteira de 2025 e próximo passo

O arquivo contém 2025 fisicamente, mas a rotina executa somente os três folds da Fase 3D. Em
2025 não houve fit, transform, contagem de unknown, inspeção de dimensionalidade ou cálculo de
métrica. O futuro refit em 2021–2024 deverá criar uma nova instância do preprocessor dentro do
pipeline selecionado; essa etapa não pertence à Fase 3E.

O próximo passo poderá avaliar modelos dentro do protocolo temporal congelado, sempre
encapsulando uma nova receita de preprocessing no pipeline de cada fold. Nenhum modelo ou
resultado preditivo foi produzido aqui.
