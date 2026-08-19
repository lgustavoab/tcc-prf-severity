# Fase 3D — Desenho experimental e particionamento temporal

## Objetivo e população

A Fase 3D congela o protocolo experimental antes de qualquer modelagem. A população continua
sendo as 342.624 ocorrências de 2021–2025 materializadas no dataset analítico principal da
Fase 3C. Nenhuma linha foi copiada para arquivos separados, nenhum parâmetro foi ajustado e
nenhuma métrica preditiva foi calculada.

## Fronteira principal

- desenvolvimento: 2021–2024, com 270.095 ocorrências;
- avaliação temporal final: 2025, com 72.529 ocorrências.

`source_year`, em papel de metadata, determina a fronteira. As partições são disjuntas,
preservam todas as 342.624 linhas e não compartilham IDs.

2025 foi explorado estruturalmente nas Fases 2 e 3A e, portanto, não é um holdout totalmente
cego no sentido estrito. Após o congelamento da política 3B, porém, ele não poderá orientar
seleção de features, representação, modelo, hiperparâmetros, threshold, encoding, escala,
imputação, balanceamento ou calibração. O target de 2025 só será consultado na avaliação final
formal do pipeline congelado.

## Validação expanding-window

| Fold | Treino | Validação |
|---|---|---|
| 1 | 2021 | 2022 |
| 2 | 2021–2022 | 2023 |
| 3 | 2021–2023 | 2024 |

Treino sempre antecede validação. Não há shuffle, amostragem aleatória, `KFold`,
`StratifiedKFold` ou substituição da ordem temporal. Nenhuma ocorrência aparece ao mesmo
tempo no treino e na validação de um fold, e 2025 está ausente dos três folds internos.

2021 aparece somente como treino e não terá previsão out-of-fold. As futuras previsões OOF
usadas para decisões de desenvolvimento virão de 2022, 2023 e 2024.

## Preprocessing futuro e anti-leakage

Em cada fold, todo componente aprendido — encoder, scaler, imputer, calibração ou modelo —
deverá ser ajustado somente no subconjunto de treino. A validação será apenas transformada e
avaliada com os parâmetros já aprendidos. É proibido aplicar `fit_transform` ao conjunto
train + validation.

As derivações `month_name`, `hour` e `tracado_via_components` já foram materializadas na 3C.
Elas podem preceder o split porque são determinísticas e não aprendem estatísticas do dataset.
Essa permissão não se estende a transformações ajustáveis.

Após a seleção futura exclusivamente nos folds, o refit final poderá aprender parâmetros em
2021–2024 completos. O pipeline refitado será então aplicado a 2025; nenhuma etapa terá fit em
2025.

## Papéis e predictors

O esquema 3C é a única fonte da lista de predictors: entram colunas com `role = predictor` e
`included_in_model_matrix = true`. Atualmente são 22 predictors físicos.

Não entram em `X`:

- `id`: metadata de rastreabilidade;
- `source_year`: metadata do desenho temporal;
- `data_inversa`: metadata para auditoria cronológica;
- `target_grave`: target.

A classe positiva permanece `target_grave = True`; a negativa permanece `False`.

## Métricas previamente definidas

A métrica principal futura de seleção é **Average Precision (AP)** para
`target_grave=True`, usando a definição operacional correspondente a
`sklearn.metrics.average_precision_score`. AP é independente de threshold. A curva
Precision–Recall poderá ser apresentada como diagnóstico gráfico, mas não será tratada como
uma segunda métrica primária nem denominada de forma ambígua como se AP e área geométrica sob
a curva fossem necessariamente sinônimos. Nenhuma AP foi calculada nesta fase.

Relatórios futuros também deverão incluir:

- independente de threshold: ROC-AUC;
- dependentes de threshold: recall, precision e F1 da classe grave, além da matriz de
  confusão;
- calibração: avaliação gráfica/apropriada e Brier score, caso implementado.

Cada modelo/configuração terá AP calculada separadamente nos três folds. O valor principal de
ranking será a média aritmética **não ponderada** das três APs. Também serão registrados o
desvio padrão das três APs e o resultado do Fold 3, cuja validação é 2024. Nenhum modelo será
escolhido pelo melhor fold isolado, e uma AP única calculada sobre todas as validações OOF
concatenadas não será usada como critério principal de seleção.

A prevalência grave é um diagnóstico de partição e poderá servir como referência para uma
baseline trivial futura, mas não é performance de modelo. Nenhum classificador baseline foi
implementado na 3D.

## Política de threshold

O threshold não poderá ser escolhido com 2025. A política futura é:

1. produzir previsões OOF nos anos internos de validação;
2. garantir que cada previsão venha de um pipeline que não treinou naquela observação;
3. concatenar as previsões de 2022, 2023 e 2024;
4. escolher o threshold que maximize F1 da classe grave;
5. em empate, priorizar maior recall e, persistindo, menor threshold;
6. congelar o threshold;
7. refitar o pipeline em 2021–2024;
8. aplicar o threshold congelado em 2025.

Assim, a agregação de AP por fold para seleção de modelo é distinta do pool OOF concatenado
utilizado para selecionar um único threshold.

O threshold 0,5 poderá ser reportado como referência, mas não substitui essa política. Nenhum
threshold foi calculado nesta fase.

## Diagnóstico descritivo

| Partição | Linhas | Graves | Não graves | Prevalência grave |
|---|---:|---:|---:|---:|
| Desenvolvimento 2021–2024 | 270.095 | 76.364 | 193.731 | 28,273015% |
| Avaliação final 2025 | 72.529 | 20.493 | 52.036 | 28,254905% |

As contagens anuais e de cada lado dos folds estão nas tabelas, sem interpretação como
desempenho preditivo.

## Artefatos e reprodução

- `phase_3d_partition_summary.csv`: anos, partições principais e lados dos folds;
- `phase_3d_temporal_folds.csv`: definição e contagens dos três folds;
- `phase_3d_experimental_contract.csv`: regras congeladas de métricas, fitting, threshold,
  refit e holdout.

```powershell
uv run prf-verify-interim
uv run prf-verify-analytical
uv run prf-design-experiment
```

Não foi criado manifesto adicional nem Parquet de atribuição: `source_year` reproduz a
fronteira sem ambiguidade e as três tabelas versionadas são suficientes.

## Próximo passo

A próxima etapa poderá implementar preprocessing e modelos dentro dos folds congelados. Ela
deverá manter qualquer fit restrito ao treino do fold, agregar AP pela média não ponderada das
três validações, produzir previsões OOF concatenadas somente para threshold e preservar 2025
até a avaliação final. A Fase 3D não treinou modelos.
