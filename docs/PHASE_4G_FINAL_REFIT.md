# Fase 4G — Refit final 2021–2024

## Objetivo

A Fase 4G produz uma única materialização final do pipeline selecionado, ajustada em todo o
período de desenvolvimento 2021–2024 e congelada antes da abertura do holdout temporal.

Esta fase **não avalia capacidade preditiva**. Ela não calcula métricas in-sample, não gera
predições e não abre o ano de 2025. Seu único objetivo científico é materializar o pipeline que
será usado sem novo treinamento na Fase 4H.

## Modelo e configuração congelados

A seleção 4E permaneceu apontando para `phase_4c_xgboost_baseline`, família
`xgboost_gradient_boosted_trees`. O refit reutilizou diretamente
`build_xgboost_pipeline(groups)`, factory oficial da Fase 4C, e portanto preservou:

- XGBoost 3.3.0, booster `gbtree` e 300 estimadores;
- `learning_rate=0.05`, `max_depth=6`, `min_child_weight=1.0` e `gamma=0.0`;
- `subsample=0.8` e `colsample_bytree=0.8`;
- `reg_alpha=0.0`, `reg_lambda=1.0` e `scale_pos_weight=1.0`;
- objetivo `binary:logistic`, métrica interna `logloss` e `tree_method=hist` em CPU;
- `random_state=42`, `n_jobs=-1`, sem early stopping, callbacks, pesos de classe ou tuning.

Nenhum hiperparâmetro foi escolhido ou alterado nesta fase.

## Preprocessing e features

O pipeline combina a receita 3E e o XGBoost 4C. Os 22 predictors físicos vieram do schema 3C:
nove variáveis categóricas em one-hot, `km` padronizado e doze indicadores de traçado em
passthrough. ID, `source_year`, `data_inversa` e target não entraram em `X`.

Após o fit em todo o desenvolvimento, o preprocessor produziu **226 features transformadas**.
O valor foi derivado de `get_feature_names_out()` no objeto fitado; não foi presumido a partir
dos folds anteriores.

## Desenvolvimento e refit único

O Parquet analítico foi acessado por leitura lazy com filtro anterior à coleta. O DataFrame
entregue ao pipeline continha exclusivamente:

- anos 2021, 2022, 2023 e 2024;
- 270.095 linhas e 270.095 IDs únicos;
- 76.364 ocorrências graves e 193.731 não graves;
- prevalência positiva de 0,2827301505026009;
- target booleano e os 22 predictors autorizados.

Esses valores foram reconciliados com a partição experimental 3D e com o manifesto/schema 3C.
O pipeline recebeu um único `fit(X_development, y_development)` e completou 300/300 boosting
rounds, sem `eval_set`, interrupção antecipada ou novo ajuste.

## Ausência de avaliação

Não foram calculados AP, ROC-AUC, F1, matriz de confusão ou qualquer outra métrica no próprio
treino. Também não foram geradas probabilidades, decisões ou diagnósticos de calibração. Uma
métrica in-sample não seria necessária para auditar o objetivo estrutural desta fase.

## Threshold congelado

O threshold `0.23723246157169342` foi somente lido do artefato 4F e registrado no manifesto.
Ele não foi aplicado, recalculado ou comparado. A Fase 4H deverá usar exatamente esse cutoff
após verificar a identidade do pipeline persistido.

## Persistência e identidade

O pipeline fitado foi serializado com `pickle` da biblioteca padrão em:

```text
artifacts/models/phase_4g_xgboost_final_pipeline.pkl
```

O arquivo possui 1.204.426 bytes e SHA-256:

```text
c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351
```

O binário permanece ignorado pelo Git. O SHA identifica esta materialização congelada; uma
resserialização futura cientificamente equivalente não é obrigada a produzir bytes idênticos.
Entretanto, a Fase 4H desta execução deverá exigir exatamente o SHA registrado antes de
desserializar, impedindo o uso acidental de outro objeto.

A função `load_final_pipeline(path, expected_sha256)` verifica existência e SHA antes de
executar `pickle.load`, e depois exige um `sklearn.pipeline.Pipeline` com `preprocessor` e um
`XGBClassifier`. Pickles podem executar código durante a carga: somente artefatos produzidos
pelo próprio projeto, íntegros e confiáveis devem ser carregados.

## Ambiente da materialização

| Componente | Versão |
|---|---:|
| Python | 3.14.6 |
| scikit-learn | 1.9.0 |
| XGBoost | 3.3.0 |
| Polars | 1.43.2 |

## Proteção do holdout 2025

O ano de 2025 não integrou `X`, `y`, transformação, `predict_proba`, threshold, métrica ou
qualquer comparação. O manifesto registra `final_test_year=2025_reserved`,
`final_test_used=false` e `final_evaluation_performed=false`.

## Artefatos versionados e reprodução

```powershell
uv run prf-refit-final-model
```

O comando publica somente as auditorias versionáveis:

- `reports/tables/phase_4g_final_model_manifest.csv`;
- `reports/tables/phase_4g_refit_checklist.csv`.

O checklist concluiu com 16 PASS e 0 FAIL. O manifesto registra população, configuração,
rounds, dimensão transformada, threshold, versões, caminho, tamanho e SHA do pipeline.

## Limitações e congelamento para 4H

O objeto depende das versões registradas e do mecanismo de serialização Python. O SHA garante
integridade desta materialização, não equivalência universal entre ambientes. O refit não
fornece nova evidência de performance e não altera as conclusões OOF das fases anteriores.

Após a 4G ficam congelados: features 3B/3C, preprocessing 3E, XGBoost/configuração 4C,
threshold 4F e o arquivo identificado acima. O próximo passo é a **Fase 4H — avaliação
temporal final em 2025**, carregando este pipeline após validar seu SHA e sem novo fit.
