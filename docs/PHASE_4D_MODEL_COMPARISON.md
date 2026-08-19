# Fase 4D — Comparação temporal formal dos modelos

## Objetivo e modelos comparados

A Fase 4D consolida a Regressão Logística, a Random Forest e o XGBoost sob o contrato
temporal congelado da Fase 3. A comparação usa exclusivamente as tabelas publicadas pelas
Fases 4A–4C; nenhum dataset ou OOF foi carregado, nenhum modelo foi treinado e 2025 não foi
consultado.

Esta fase produz ranks e diferenças descritivas, mas não seleciona o modelo final. A decisão
formal pertence à Fase 4E.

## Comparabilidade experimental

Antes da consolidação, a rotina confirmou para as três famílias:

- exatamente três folds com validações em 2022, 2023 e 2024;
- mesmos períodos e números de linhas de treino e validação;
- mesmas prevalências da classe grave;
- mesmas dimensões transformadas: 215, 220 e 223;
- Average Precision como métrica primária e média não ponderada como agregação principal;
- `final_test_used=false` e `threshold_selected=false`;
- 2025 reservado à avaliação final.

Qualquer divergência nesses campos interrompe a comparação.

## Métrica primária e resultados por fold

Average Precision (AP) para `target_grave=True` permanece a métrica primária. Ela é calculada
separadamente em cada validação temporal; a agregação principal é a média aritmética não
ponderada, acompanhada do desvio padrão populacional e do Fold 3.

| Modelo | AP 2022 | AP 2023 | AP 2024 | AP média | AP std | Rank da média | Rank Fold 3 | Rank estabilidade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0,386681 | 0,396058 | 0,397786 | 0,393508 | 0,004879 | 3 | 3 | 1 |
| Random Forest | 0,388096 | 0,399673 | 0,400183 | 0,395984 | 0,005582 | 2 | 2 | 2 |
| XGBoost | 0,390375 | 0,404968 | 0,407090 | 0,400811 | 0,007430 | 1 | 1 | 3 |

Os valores integrais validados a partir das tabelas versionadas são:

- Logistic Regression: AP média `0.3935082935577437`;
- Random Forest: AP média `0.3959839275865431`;
- XGBoost: AP média `0.40081097458169895`.

Descritivamente, XGBoost apresentou a maior AP média e a maior AP no Fold 3; Random Forest
ficou entre as outras famílias em AP média; Logistic Regression apresentou o menor desvio
padrão. Rank não significa seleção final, e as diferenças não foram submetidas a teste de
significância.

## Estabilidade temporal

| Modelo | AP mínima | AP máxima | Range | Std populacional | Fold 1→2 | Fold 2→3 |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0,386681 | 0,397786 | 0,011105 | 0,004879 | 0,009377 | 0,001727 |
| Random Forest | 0,388096 | 0,400183 | 0,012088 | 0,005582 | 0,011577 | 0,000511 |
| XGBoost | 0,390375 | 0,407090 | 0,016715 | 0,007430 | 0,014594 | 0,002121 |

As APs aumentaram entre os três folds nas três famílias. Com apenas três pontos temporais,
isso é uma direção observada, não uma tendência estatística demonstrada. O Fold 3 é reportado
separadamente por ser a validação interna mais recente, sem substituir a agregação principal.

## Métricas secundárias

| Modelo | ROC-AUC média | Brier médio |
|---|---:|---:|
| Logistic Regression | 0,624378 | 0,194820 |
| Random Forest | 0,626101 | 0,195183 |
| XGBoost | 0,630850 | 0,193897 |

Maior ROC-AUC e menor Brier são direções descritivamente favoráveis, mas continuam
secundárias e não substituem AP. Recall, precision, F1 e matrizes de confusão no corte 0,5
permanecem diagnósticos de um cutoff não otimizado e não são usados para escolher modelo.

As tabelas de calibração existentes foram mantidas somente como diagnóstico. Não foi criado
score de calibração, calibrador ou interpretação definitiva das diferenças entre
probabilidade prevista e frequência observada.

## Deltas pareados de AP

Os deltas abaixo seguem `AP_b - AP_a`:

| Modelo A | Modelo B | Fold 1 | Fold 2 | Fold 3 | Média |
|---|---|---:|---:|---:|---:|
| Logistic | Random Forest | 0,001415 | 0,003614 | 0,002398 | 0,002476 |
| Logistic | XGBoost | 0,003694 | 0,008910 | 0,009304 | 0,007303 |
| Random Forest | XGBoost | 0,002279 | 0,005296 | 0,006907 | 0,004827 |

Essas diferenças são estimativas descritivas nos três folds observados. Não houve bootstrap,
teste estatístico, intervalo de confiança, score composto, soma de ranks ou ponderação.

## Reprodutibilidade da Random Forest

A auditoria já registrada permanece válida: reexecuções paralelas da Random Forest podem
produzir Parquets não bitwise idênticos, com diferenças de probabilidade da ordem de
`10^-16`, enquanto AP, ROC-AUC e Brier permanecem iguais. Isso não invalida a comparabilidade
da 4D, que usa as métricas versionadas e não exige SHA idêntico do OOF. A configuração
`random_state=42` e `n_jobs=-1` não foi alterada.

## Interpretação, limitações e próximo passo

A comparação abrange apenas três folds anuais, sem inferência estatística sobre as diferenças.
Não houve tuning, threshold, ensemble, stacking, refit ou uso de 2025. Os ranks apenas
organizam valores observados; não demonstram superioridade estatística, causalidade ou escolha
operacional definitiva.

A **Fase 4E — Seleção formal do modelo** avaliará os resultados consolidados e registrará a
decisão metodológica. Até lá, nenhum modelo está selecionado.
