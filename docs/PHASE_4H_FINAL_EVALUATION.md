# Fase 4H — Avaliação temporal final em 2025

## 1. Objetivo

A Fase 4H abre formalmente o holdout temporal de 2025 e avalia em que medida o pipeline
selecionado, refitado e congelado mantém capacidade preditiva em período posterior ao
desenvolvimento. O alvo é a gravidade entre ocorrências já registradas pela PRF, definida por
`target_grave = (mortos > 0) OR (feridos_graves > 0)`; o modelo não estima a probabilidade de
um acidente ocorrer.

## 2. Desenho temporal

O pipeline foi desenvolvido e refitado exclusivamente com 2021–2024. O ano de 2025 foi usado
somente como teste temporal final, sem participar da seleção da família, do threshold, dos
hiperparâmetros, das features ou do preprocessing. A avaliação materializou exclusivamente as
72.529 linhas de 2025, sem carregar 2021–2024 para predição.

## 3. Congelamento anterior à avaliação

Antes da abertura do holdout estavam congelados:

- modelo `phase_4c_xgboost_baseline`, da família `xgboost_gradient_boosted_trees`;
- pipeline 3E+4C refitado uma única vez em 2021–2024;
- 22 predictors físicos e 226 features transformadas;
- 300 boosting rounds;
- threshold `0.23723246157169342`, selecionado no OOF temporal 2022–2024.

Não houve novo treinamento, tuning, calibração, seleção de modelo ou seleção de threshold na
4H.

## 4. Pipeline e integridade SHA

O arquivo `artifacts/models/phase_4g_xgboost_final_pipeline.pkl` foi verificado antes da
desserialização. Seu SHA-256 coincidiu exatamente com o manifesto 4G:

`c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351`

Também foram validados o status do refit, o período de treinamento, a ausência de avaliação
anterior de 2025, o caminho do artefato, as versões registradas, o estado fitado, as classes
`[0, 1]`, os 300 rounds e as 226 features transformadas.

## 5. Holdout 2025

O teste final contém 72.529 IDs únicos, dos quais 20.493 são graves e 52.036 não graves. A
prevalência positiva é `0.2825490493457789` (28,2549%). O conjunto foi reconciliado com a
partição 3D e validado quanto a ano, IDs, target, predictors, nulidade e ausência de leakage.

## 6. Métricas primária e secundárias

A métrica primária, calculada para `target_grave=True` por
`sklearn.metrics.average_precision_score`, foi:

- Average Precision (AP): `0.3974456687131155`.

As métricas secundárias sobre as probabilidades foram:

- ROC-AUC: `0.6285562620583193`;
- Brier score: `0.19382199321256413`.

Nenhuma regra de aprovação ou reprovação foi criada a partir dos valores observados.

## 7. Threshold congelado

Aplicando a regra `predicted_probability_grave >= 0.23723246157169342`, foram obtidos:

| Métrica | Resultado |
|---|---:|
| Precision | 0.33159329140461213 |
| Recall | 0.7718245254477138 |
| F1 | 0.4638892554954321 |
| TN | 20.153 |
| FP | 31.883 |
| FN | 4.676 |
| TP | 15.817 |
| Preditos graves | 47.700 |
| Preditos não graves | 24.829 |

O cutoff permaneceu exatamente igual ao selecionado na Fase 4F.

## 8. Referência 0,5

O cutoff 0,5 foi calculado somente como referência descritiva, sem substituir o threshold
congelado:

| Métrica | Resultado |
|---|---:|
| Precision | 0.5587248322147651 |
| Recall | 0.048748353096179184 |
| F1 | 0.08967281540325839 |
| TN | 51.247 |
| FP | 789 |
| FN | 19.494 |
| TP | 999 |

## 9. Resultados finais

O pipeline congelado produziu uma única coleção de probabilidades para 2025. A AP final foi
0,397446, acompanhada de ROC-AUC 0,628556 e Brier 0,193822. No threshold operacional
congelado, o modelo priorizou recall (0,771825), com precision 0,331593 e F1 0,463889. Esses
resultados descrevem desempenho fora do período de desenvolvimento e não autorizam ajuste
retrospectivo.

## 10. Comparação com a validação interna

Os deltas abaixo são exclusivamente descritivos:

| Métrica | Referência de desenvolvimento | Valor de desenvolvimento | 2025 | Delta 2025 − desenvolvimento |
|---|---|---:|---:|---:|
| AP | média dos folds internos | 0.40081097458169895 | 0.3974456687131155 | -0.003365305868583468 |
| AP | Fold 3 (2024) | 0.4070898952179728 | 0.3974456687131155 | -0.0096442265048573 |
| ROC-AUC | média dos folds internos | 0.6308499409937857 | 0.6285562620583193 | -0.0022936789354663922 |
| Brier | média dos folds internos | 0.19389746858763426 | 0.19382199321256413 | -0.00007547537507013313 |
| Precision no threshold congelado | OOF temporal pooled | 0.33330114898136526 | 0.33159329140461213 | -0.0017078575767531246 |
| Recall no threshold congelado | OOF temporal pooled | 0.7704563403495519 | 0.7718245254477138 | 0.0013681850981619448 |
| F1 no threshold congelado | OOF temporal pooled | 0.46530870405989 | 0.4638892554954321 | -0.0014194485644579147 |

Não foram aplicados testes de significância, p-values ou critérios retroativos de aceitação.

## 11. Calibração descritiva

A calibração foi resumida em dez bins por quantis, sem treinamento de calibrador. Os bins
têm 7.252 ou 7.253 observações. A probabilidade média cresce de `0.14931416648929158` no
primeiro bin, cuja taxa observada é `0.14338894250654902`, até `0.4708657106925221` no
décimo, cuja taxa observada é `0.47787122569971047`. A tabela completa está em
`reports/tables/phase_4h_calibration.csv`.

## 12. Interpretação cautelosa

Os resultados indicam que a capacidade preditiva observada em 2025 ficou próxima das
referências temporais internas, mas os deltas são apenas descritivos. Não constituem evidência
causal, não medem risco de ocorrência de acidente e não demonstram validade operacional fora
da população e do período estudados.

## 13. Limitações

O teste cobre um único ano posterior e reflete a população de ocorrências registradas na base
pública. O threshold maximiza F1 no OOF de desenvolvimento e não incorpora custos
operacionais. A análise de calibração é diagnóstica e não corrige probabilidades. Mudanças
futuras na população, no registro ou nas taxonomias podem alterar o desempenho.

## 14. Ressalva sobre a cegueira estrutural de 2025

2025 não foi completamente cego para análises estruturais anteriores, pois participou da EDA
e da auditoria de drift. Sua performance preditiva, entretanto, não participou da seleção do
modelo, da seleção do threshold nem do refit, e não foi usada para modificar decisões
congeladas.

## 15. Proibição de ajuste retrospectivo

O desempenho observado em 2025 foi utilizado exclusivamente para avaliação temporal final e
não motivou alteração do modelo, hiperparâmetros, conjunto de atributos, pré-processamento ou
limiar de decisão.

## 16. Predições finais persistidas

As predições foram persistidas localmente em
`data/processed/phase_4h_final_2025_predictions.parquet`, arquivo ignorado pelo Git, com cinco
colunas, 72.529 linhas e 394.330 bytes. Seu SHA-256 é:

`411b5113060b19c3cc9da5fe1a6cddcf8a7d7662fe73102a6f3fdb2b05b88375`

Essa materialização permite que a Fase 4I reutilize as probabilidades e decisões finais sem
reconstruir ou alterar o modelo.

## 17. Próximo passo

A próxima etapa é a Fase 4I — interpretação e análise final, usando os resultados e as
predições congeladas pela 4H sem reabrir seleção, treinamento ou threshold.
