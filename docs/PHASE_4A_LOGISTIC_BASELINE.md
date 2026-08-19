# Fase 4A — Regressão Logística baseline

## Objetivo e contrato herdado

A Fase 4A executa a primeira modelagem preditiva do projeto. Ela estabelece uma Regressão
Logística baseline nos três folds expanding-window congelados, sem escolher modelo final,
threshold ou hiperparâmetros. A entrada continua sendo o dataset analítico da 3C, com os 22
predictors definidos pelo esquema; o preprocessing é construído pela fábrica aprovada na 3E.

Cada fold cria um novo `Pipeline(preprocessor, classifier)`. Encoder, scaler e classificador
são ajustados conjuntamente apenas no treino e aplicados depois à validação. Metadata e
`target_grave` não entram em X; `target_grave=True` permanece a classe positiva.

## Configuração fixa

A configuração foi congelada antes da execução:

```text
LogisticRegression(
    solver="newton-cholesky",
    C=1.0,
    l1_ratio=0.0,
    class_weight=None,
    fit_intercept=True,
    tol=1e-4,
    max_iter=500,
)
```

`l1_ratio=0.0` estabelece regularização L2 no contrato atual, com força padrão `C=1.0` e sem
pesos de classe. `newton-cholesky` é adequado a este baseline porque o número de observações é
muito maior que a dimensionalidade one-hot (até 223 features nos folds), tornando administrável
o custo quadrático da Hessiana em número de features. Não houve comparação de solver, C,
`class_weight` ou qualquer busca de hiperparâmetros.

## Folds e preprocessing

Foram treinados exatamente três pipelines transitórios:

1. 2021 → validação 2022;
2. 2021–2022 → validação 2023;
3. 2021–2023 → validação 2024.

As nove categóricas receberam one-hot train-only com `handle_unknown="ignore"`; `km` recebeu
`StandardScaler` train-only; os 12 indicadores de traçado seguiram por passthrough. As
dimensões resultantes foram 215, 220 e 223. Nenhum pipeline, encoder, scaler ou modelo fitado
foi persistido.

## Métricas

Average Precision (AP), calculada por `sklearn.metrics.average_precision_score` para
`target_grave=True`, é a métrica primária. O valor agregado é a média aritmética não ponderada
das três APs, acompanhada do desvio padrão populacional (`ddof=0`) e da AP do Fold 3. Não foi
calculada uma AP única sobre o OOF concatenado para ranking.

ROC-AUC e Brier score são métricas secundárias. No Brier, `True` é a classe positiva e a
entrada é `P(target_grave=True)`. Recall, precision, F1 e matriz de confusão usam exclusivamente
o corte fixo 0,5 como referência; ele não é um threshold selecionado.

| Fold | Validação | Prevalência grave | AP | ROC-AUC | Brier | Recall @0,5 | Precision @0,5 | F1 @0,5 | TN / FP / FN / TP | Features | Iterações |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2022 | 0,284943 | 0,386681 | 0,616975 | 0,196452 | 0,032647 | 0,541441 | 0,061581 | 45.688 / 509 / 17.808 / 601 | 215 | 3 |
| 2 | 2023 | 0,283505 | 0,396058 | 0,627378 | 0,194450 | 0,042578 | 0,543161 | 0,078965 | 47.866 / 688 / 18.394 / 818 | 220 | 3 |
| 3 | 2024 | 0,281932 | 0,397786 | 0,628779 | 0,193558 | 0,042424 | 0,561257 | 0,078886 | 51.847 / 684 / 19.750 / 875 | 223 | 3 |

Resultados agregados:

- AP média não ponderada: 0,3935082935577437;
- desvio padrão populacional da AP: 0,004878870165386994;
- AP do Fold 3: 0,3977855869271569;
- ROC-AUC média: 0,6243776293022905;
- Brier médio: 0,1948197255602965.

A prevalência de cada validação é apenas uma referência descritiva para interpretar AP; não é
performance de um `DummyClassifier`. Os valores observados não são classificados isoladamente
como bons ou ruins e não sustentam interpretação causal.

## Convergência e calibração

Os três ajustes convergiram em três iterações, frente ao limite de 500, sem
`ConvergenceWarning`. Convergência numérica não implica qualidade preditiva.

A tabela de calibração contém dez bins quantílicos por fold, totalizando 30 linhas, com média
da probabilidade prevista e taxa positiva observada. É um diagnóstico do modelo original:
nenhum `CalibratedClassifierCV`, Platt scaling ou isotonic regression foi ajustado.

## Previsões OOF

`data/processed/phase_4a_logistic_oof_predictions.parquet` reúne 205.528 linhas, uma por ID das
validações de 2022, 2023 e 2024. O arquivo está ordenado por `source_year, id`, preserva o
target e contém probabilidades finitas em `[0, 1]`. Não contém 2021 ou 2025. Seu SHA-256 nesta
execução é `a8837ffc5ca68341ec1cd18da3cc040a6daa9aec2c5b5e3c7ee233e5975b2e60`.

O OOF não foi usado para procurar threshold. Essa escolha permanece reservada à Fase 4F caso
a Regressão Logística seja selecionada.

## Fronteira de 2025, limitações e próximo passo

2025 não participou de fit, transformação, predição, calibração ou métrica. Também não houve
refit em 2021–2024. A baseline usa uma única especificação linear e não testa interações,
relações não lineares, pesos de classe ou tuning; métricas @0,5 são apenas diagnósticas. A base
continua limitada a ocorrências registradas e o resultado não estima causalidade nem risco de
ocorrer acidente.

O próximo passo é a **Fase 4B — Random Forest**, sob os mesmos folds e contrato experimental,
sem consultar 2025.
