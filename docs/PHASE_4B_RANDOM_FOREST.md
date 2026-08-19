# Fase 4B — Random Forest baseline

## Objetivo e contrato herdado

A Fase 4B executa uma Random Forest baseline sob o mesmo desenho experimental congelado nas
Fases 3D–3F e já usado na 4A. A entrada é o dataset analítico da 3C, com os 22 predictors do
esquema autoritativo; metadata e `target_grave` não entram em X, e `target_grave=True`
permanece a classe positiva. Esta fase avalia uma única configuração previamente definida:
não seleciona modelo vencedor, threshold ou hiperparâmetros.

Cada fold cria um novo `Pipeline(preprocessor, classifier)`. O preprocessing da Fase 3E e o
classificador são ajustados conjuntamente somente no treino e aplicados depois à validação.
Nenhum dado de 2025 participa de fit, transformação, predição, auditoria, calibração ou
métrica.

## Configuração fixa e limite de complexidade

A configuração foi congelada antes da execução:

```text
RandomForestClassifier(
    n_estimators=300,
    criterion="gini",
    max_depth=20,
    min_samples_split=2,
    min_samples_leaf=5,
    max_features="sqrt",
    bootstrap=True,
    oob_score=False,
    n_jobs=-1,
    random_state=42,
    class_weight=None,
    max_samples=None,
)
```

As 300 árvores formam um ensemble suficientemente amplo para uma baseline, sem busca do
número ótimo. `max_depth=20` estabelece um limite explícito de complexidade e memória;
`min_samples_leaf=5` evita folhas extremamente pequenas; `max_features="sqrt"` e bootstrap
preservam a configuração clássica de classificação. A validação oficial é temporal, por isso
`oob_score=False`. `random_state=42` favorece reprodutibilidade, `n_jobs=-1` paraleliza o
cálculo e `class_weight=None` mantém a distribuição observada, sem reponderação.

Não houve GridSearchCV, RandomizedSearchCV, Optuna, busca manual ou avaliação de configurações
alternativas. Os limites não foram modificados após observar os resultados.

## Folds e preprocessing

Foram treinados exatamente três pipelines transitórios:

1. 2021 → validação 2022;
2. 2021–2022 → validação 2023;
3. 2021–2023 → validação 2024.

As nove categóricas receberam one-hot train-only com categorias desconhecidas toleradas;
`km` recebeu `StandardScaler` train-only; os 12 indicadores de traçado seguiram por
passthrough. As matrizes permaneceram esparsas e tiveram 215, 220 e 223 features. O mesmo
preprocessing foi mantido deliberadamente para preservar a comparabilidade experimental,
embora árvores não exijam escala. Nenhum pipeline, preprocessor ou classificador fitado foi
persistido.

## Métricas e resultados

Average Precision (AP), calculada por `sklearn.metrics.average_precision_score` para
`target_grave=True`, é a métrica primária. O resultado agregado é a média aritmética não
ponderada das três APs, acompanhada do desvio padrão populacional (`ddof=0`) e da AP do Fold
3. Não foi usada uma AP sobre o OOF concatenado como critério principal.

ROC-AUC e Brier score são métricas secundárias. Recall, precision, F1 e matriz de confusão
usam somente o corte fixo 0,5 como referência; nenhum threshold foi procurado ou selecionado.

| Fold | Validação | Prevalência grave | AP | ROC-AUC | Brier | Recall @0,5 | Precision @0,5 | F1 @0,5 | TN / FP / FN / TP | Features |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2022 | 0,284943 | 0,388096 | 0,618544 | 0,196665 | 0,003422 | 0,649485 | 0,006809 | 46.163 / 34 / 18.346 / 63 | 215 |
| 2 | 2023 | 0,283505 | 0,399673 | 0,629422 | 0,194887 | 0,006819 | 0,590090 | 0,013482 | 48.463 / 91 / 19.081 / 131 | 220 |
| 3 | 2024 | 0,281932 | 0,400183 | 0,630337 | 0,193997 | 0,008921 | 0,599349 | 0,017581 | 52.408 / 123 / 20.441 / 184 | 223 |

Resultados agregados:

- AP média não ponderada: 0,3959839275865431;
- desvio padrão populacional da AP: 0,00558166427201829;
- AP do Fold 3: 0,4001833160938038;
- ROC-AUC média: 0,6261012009282653;
- Brier médio: 0,19518315938755074.

A prevalência de validação serve apenas como referência descritiva para interpretar AP. Os
resultados não estabelecem causalidade e esta fase não os usa para comparar formalmente a
Random Forest com a Regressão Logística.

## Calibração e estrutura das árvores

A calibração diagnóstica usa dez bins quantílicos por fold e produz 30 linhas com a média da
probabilidade prevista e a taxa positiva observada. Nenhum calibrador foi ajustado.

| Fold | Árvores | Profundidade média | Profundidade máxima | Nós médios | Máximo de nós |
|---:|---:|---:|---:|---:|---:|
| 1 | 300 | 20,000 | 20 | 1.862,927 | 2.481 |
| 2 | 300 | 20,000 | 20 | 2.775,713 | 3.767 |
| 3 | 300 | 20,000 | 20 | 3.592,353 | 4.965 |

O fato de todas as árvores atingirem o limite de profundidade é um diagnóstico de complexidade
desta configuração congelada, não um critério para alterá-la após a execução. Não foram calculados
ranking substantivo, seleção ou remoção de features por `feature_importances_`.

## Previsões OOF

`data/processed/phase_4b_random_forest_oof_predictions.parquet` reúne 205.528 linhas, uma por
ID das validações de 2022, 2023 e 2024. O arquivo está ordenado por `source_year, id`, preserva
o target e contém probabilidades finitas em `[0, 1]`. Não contém 2021 ou 2025. Seu SHA-256
nesta execução é `33ad1851e29b42f9e3f813638a1cf47f93397165e3b764cfe642cb0dd510c2da`.

O OOF não foi usado para procurar threshold. Esse uso permanece condicionado à futura fase
específica de threshold e somente ocorrerá se a Random Forest vier a ser selecionada.

## Limitações e próximo passo

Esta é uma baseline única e não otimizada. Não houve tuning, calibração, seleção de threshold,
refit em 2021–2024, avaliação final em 2025 nem persistência de modelo. A base contém somente
ocorrências registradas; as métricas não medem risco de ocorrer acidente e não sustentam
interpretação causal. A comparação formal entre candidatos pertence a uma fase posterior.

O próximo passo é a **Fase 4C — XGBoost**, sob o mesmo contrato temporal e sem consultar 2025.
