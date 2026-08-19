# Fase 4C — XGBoost baseline

## Objetivo e contrato herdado

A Fase 4C executa a terceira família preditiva sob o desenho experimental congelado nas
Fases 3D–3F. A entrada é o dataset analítico da 3C, com os 22 predictors do esquema
autoritativo; metadata e `target_grave` não entram em X. A versão contratada é XGBoost 3.3.0.
Esta fase avalia uma única configuração previamente definida: não seleciona modelo vencedor,
threshold ou hiperparâmetros.

Cada fold cria um novo `Pipeline(preprocessor, classifier)`. O preprocessing da Fase 3E e o
XGBClassifier são ajustados conjuntamente apenas no treino e aplicados depois à validação.
Nenhum dado de 2025 participa de fit, transformação, predição, auditoria, calibração ou
métrica.

## Configuração fixa

```text
XGBClassifier(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    min_child_weight=1.0,
    gamma=0.0,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.0,
    reg_lambda=1.0,
    objective="binary:logistic",
    eval_metric="logloss",
    tree_method="hist",
    device="cpu",
    n_jobs=-1,
    random_state=42,
    scale_pos_weight=1.0,
    booster="gbtree",
    enable_categorical=False,
    verbosity=0,
)
```

Os 300 rounds e `learning_rate=0.05` estabelecem uma baseline fixa com passo conservador;
`max_depth=6` limita a complexidade de cada árvore. `subsample=0.8` e
`colsample_bytree=0.8` introduzem subamostragem reprodutível; `reg_alpha=0` e
`reg_lambda=1` mantêm a regularização baseline. Não há reponderação da classe positiva.
`tree_method="hist"` e `device="cpu"` congelam o ambiente computacional alvo.

Não houve GridSearchCV, RandomizedSearchCV, Optuna, busca manual ou avaliação de outra
configuração. Também não houve `eval_set`, callback, `early_stopping_rounds` ou seleção de
`best_iteration`: cada Booster completou exatamente os 300 rounds definidos antes da
execução.

## Folds, preprocessing e classe positiva

Foram treinados exatamente três pipelines transitórios:

1. 2021 → validação 2022;
2. 2021–2022 → validação 2023;
3. 2021–2023 → validação 2024.

As nove categóricas receberam one-hot train-only; `km` recebeu `StandardScaler` train-only;
os 12 indicadores de traçado seguiram por passthrough. As matrizes permaneceram esparsas e
tiveram 215, 220 e 223 features. A representação comum foi preservada mesmo diante das
capacidades próprias do XGBoost para manter o contrato experimental entre famílias.

O target de origem permanece booleano: `False` é não grave e `True` é grave. O XGBClassifier
expõe essas classes como os valores numéricos 0 e 1. A implementação valida
`classes_ == [0, 1]`, localiza explicitamente a classe 1 e extrai `P(target_grave=True)`; essa
codificação não inverte a semântica do target.

## Métricas e resultados

Average Precision (AP), calculada por `sklearn.metrics.average_precision_score`, é a métrica
primária. A AP interna `aucpr` do XGBoost não foi usada como substituta. O resultado agregado
é a média aritmética não ponderada das três APs, acompanhada do desvio padrão populacional
(`ddof=0`) e da AP do Fold 3. Não foi usada AP sobre o OOF concatenado para ranking.

ROC-AUC e Brier score são métricas secundárias. Recall, precision, F1 e matriz de confusão
usam somente o corte fixo 0,5 como referência; nenhum threshold foi procurado ou selecionado.

| Fold | Validação | Prevalência grave | AP | ROC-AUC | Brier | Recall @0,5 | Precision @0,5 | F1 @0,5 | TN / FP / FN / TP | Features | Rounds |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2022 | 0,284943 | 0,390375 | 0,622101 | 0,195865 | 0,042371 | 0,540541 | 0,078582 | 45.534 / 663 / 17.629 / 780 | 215 | 300 |
| 2 | 2023 | 0,283505 | 0,404968 | 0,633669 | 0,193453 | 0,046638 | 0,577692 | 0,086307 | 47.899 / 655 / 18.316 / 896 | 220 | 300 |
| 3 | 2024 | 0,281932 | 0,407090 | 0,636780 | 0,192375 | 0,050327 | 0,591116 | 0,092757 | 51.813 / 718 / 19.587 / 1.038 | 223 | 300 |

Resultados agregados:

- AP média não ponderada: 0,40081097458169895;
- desvio padrão populacional da AP: 0,007430307892479644;
- AP do Fold 3: 0,4070898952179728;
- ROC-AUC média: 0,6308499409937857;
- Brier médio: 0,19389746858763426.

A prevalência é referência descritiva para interpretar AP. Os resultados não estabelecem
causalidade e esta fase não os usa para comparar formalmente XGBoost, Random Forest e
Regressão Logística.

## Calibração, rounds e OOF

A calibração diagnóstica usa dez bins quantílicos por fold e produz 30 linhas com a média da
probabilidade prevista e a taxa positiva observada. Nenhum calibrador foi ajustado.

Os Boosters reportaram 300 rounds completos em cada fold, exatamente iguais aos 300
configurados. Essa auditoria confirma a ausência de interrupção antecipada, mas não constitui
critério de seleção ou justificativa para alterar a configuração.

`data/processed/phase_4c_xgboost_oof_predictions.parquet` reúne 205.528 linhas, uma por ID das
validações de 2022, 2023 e 2024. O arquivo está ordenado por `source_year, id`, preserva o
target e contém probabilidades finitas entre 0,031965672969818115 e 0,7968423366546631. Não
contém 2021 ou 2025. Seu SHA-256 nesta execução é
`28925211b1542c2c7965b8b45cd6b5f360389f200ea197de57f9068f777a6bdb`.

O OOF não foi usado para buscar threshold. Esse uso continua reservado à fase específica e
somente ocorrerá após a seleção formal de uma família.

## Auditoria de reprodutibilidade da Random Forest

Durante a validação da 4C, duas reexecuções da Random Forest com a configuração preservada
(`random_state=42` e `n_jobs=-1`) mantiveram exatamente IDs, targets, folds e anos. Das
205.528 probabilidades, 89.588 não foram bitwise idênticas; a diferença absoluta máxima foi
`3.3306690738754696e-16`, a média foi `2.4697206337636872e-17`, o percentil 99 foi
`1.1102230246251565e-16` e o RMSE foi `4.0536620258397663e-17`. AP, ROC-AUC e Brier foram
exatamente iguais em todos os folds, assim como a AP média, e nenhuma decisão no corte fixo
0,5 mudou.

A diferença é compatível com ruído numérico de ponto flutuante na execução paralela e não
representa divergência preditiva substantiva. O SHA-256 do OOF da Random Forest identifica
uma materialização específica do arquivo; a equivalência científica entre reexecuções
paralelas da 4B não exige igualdade bitwise do Parquet. A validação de reprodução deve
considerar estrutura, targets, probabilidades numericamente equivalentes e métricas
reproduzidas, sem alterar a configuração ou substituir hashes históricos.

## Limitações e próximo passo

Esta é uma baseline única e não otimizada. Não houve tuning, early stopping, calibração,
seleção de threshold, refit em 2021–2024, avaliação final em 2025, interpretação de importância
ou persistência de modelo. A base contém somente ocorrências registradas; as métricas não
medem risco de ocorrer acidente e não sustentam interpretação causal.

O próximo passo é a **Fase 4D — Comparação temporal dos modelos**, sem consulta a 2025.
