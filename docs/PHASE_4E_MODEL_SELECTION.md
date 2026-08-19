# Fase 4E — Seleção formal do modelo

## Objetivo e contrato herdado

A Fase 4E aplica a regra experimental congelada para escolher a família que seguirá para
threshold OOF, refit e avaliação temporal final. A decisão usa exclusivamente as tabelas
versionadas da comparação 4D e o contrato 3D; nenhum dataset, OOF ou resultado de 2025 foi
carregado, e nenhum modelo foi treinado.

O contrato pré-especificado define Average Precision (AP) para `target_grave=True` como
métrica primária e a média aritmética não ponderada das três APs temporais como valor de
ranking. A seleção deve usar o maior `ap_unweighted_mean`. Empate exato interromperia a fase,
sem regra de desempate criada retrospectivamente.

## Candidatos e resultados comparativos

| Modelo | AP Fold 1 | AP Fold 2 | AP Fold 3 | AP média | AP std | Rank AP | Rank Fold 3 | Rank std |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0,386681 | 0,396058 | 0,397786 | 0,393508 | 0,004879 | 3 | 3 | 1 |
| Random Forest | 0,388096 | 0,399673 | 0,400183 | 0,395984 | 0,005582 | 2 | 2 | 2 |
| XGBoost | 0,390375 | 0,404968 | 0,407090 | 0,400811 | 0,007430 | 1 | 1 | 3 |

Os valores integrais de AP média validados são `0.3935082935577437`, `0.3959839275865431` e
`0.40081097458169895`, respectivamente. Existe exatamente um `primary_metric_rank=1`, e ele
coincide com o único `argmax` recalculado da AP média.

## Modelo selecionado e justificativa

O modelo formalmente selecionado é:

```text
model_id = phase_4c_xgboost_baseline
family = xgboost_gradient_boosted_trees
role = baseline_candidate
```

**XGBoost é selecionado por apresentar a maior AP média não ponderada nos três folds
internos.** Essa é a única regra que causa a seleção.

O desvio padrão populacional (`0.007430307892479644`) descreve estabilidade temporal, e a AP
do Fold 3 (`0.4070898952179728`) representa a validação interna mais recente. Eles são
informações complementares e não substituem a métrica primária. Da mesma forma, ROC-AUC média
(`0.6308499409937857`) e Brier médio (`0.19389746858763426`) não foram usados como critério,
desempate ou score composto.

## Magnitude descritiva dos deltas

A diferença de AP média observada do selecionado foi:

- XGBoost − Logistic Regression: `0.00730268102395526`;
- XGBoost − Random Forest: `0.004827046995155848`.

São diferenças descritivas nos folds observados. Não houve bootstrap, teste de hipótese,
intervalo de confiança ou alegação de significância estatística, clínica ou operacional.

## Checklist e proteção de 2025

O checklist contém 13 verificações substantivas e resultou em **13 PASS e 0 FAIL**. Ele
confirma três candidatos, três folds, anos 2022–2024, métrica e agregação congeladas, rank 1
único, concordância entre rank e argmax, reconciliação das tabelas 4D, contrato versionado do
selecionado e ausência de threshold, refit, tuning posterior ou resultado de 2025.

2025 permanece `2025_reserved`: não foi usado para seleção, desempate ou qualquer avaliação.
O threshold continua `false`; nenhum OOF foi lido ou analisado nesta fase.

## Congelamento pós-seleção

A seleção congela conceitualmente:

- família: XGBoost;
- configuração: exatamente o contrato publicado na Fase 4C, sem novo tuning;
- preprocessing: exatamente a receita train-only da Fase 3E;
- features: exatamente as 22 colunas físicas autorizadas pelas Fases 3B/3C;
- desenho dos folds: exatamente a Fase 3D.

Nenhum `learning_rate`, `max_depth`, `n_estimators`, `subsample`, `colsample_bytree`,
`scale_pos_weight` ou outro hiperparâmetro foi reavaliado ou alterado após a comparação.

## Limitações e próximo passo

A escolha segue uma regra pré-especificada sobre três folds anuais e não demonstra
superioridade causal ou estatisticamente significativa. AP std, Fold 3 e métricas secundárias
continuam diagnósticos. A avaliação final ainda não ocorreu.

O próximo passo é a **Fase 4F — seleção de threshold**, usando exclusivamente as previsões
OOF temporais de 2022–2024 do XGBoost conforme o contrato já congelado. Não há threshold
selecionado nesta fase.
