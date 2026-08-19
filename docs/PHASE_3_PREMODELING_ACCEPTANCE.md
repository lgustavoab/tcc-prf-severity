# Aceite pré-modelagem da Fase 3

## 1. Escopo da Fase 3

A Fase 3 transformou as conclusões da EDA em um contrato experimental auditável, sem treinar
modelos. A sequência cobriu drift temporal (3A), política final de features (3B), dataset
analítico principal (3C), desenho temporal (3D), preprocessing train-only (3E) e o presente
aceite pré-modelagem (3F).

## 2. Artefatos congelados

O aceite usa como fontes autoritativas os documentos `PHASE_3A_TEMPORAL_DRIFT.md` a
`PHASE_3E_PREPROCESSING.md` e os contratos versionados das Fases 3B–3E. Permanecem congelados:

- o Parquet analítico, seu esquema e manifesto da 3C;
- as 11 representações principais e suas 22 colunas físicas;
- as partições e os três folds da 3D;
- a métrica, a agregação, o threshold e o refit futuros;
- a receita de preprocessing 9 categóricas / 1 numérica / 12 binárias da 3E.

Este aceite não altera nenhum desses artefatos.

## 3. População

As verificações existentes confirmam 342.624 ocorrências, 342.624 IDs únicos e 96.857 casos
com `target_grave=True`. O desenvolvimento de 2021–2024 contém 270.095 ocorrências e 76.364
graves. A avaliação temporal final de 2025 contém 72.529 ocorrências e 20.493 graves.

## 4. Contrato de features

O conjunto principal possui 11 representações conceituais e 22 predictors físicos. `id`,
`source_year`, `data_inversa` e `target_grave` estão fora de X. Também estão ausentes:

- leakage: `mortos`, `feridos_graves`, `feridos_leves`, `feridos`, `ilesos`, `ignorados` e
  `classificacao_acidente`;
- administrativas: `regional`, `delegacia` e `uop`;
- secondary only: `tipo_acidente`, `causa_acidente`, `pessoas` e `veiculos`;
- redundantes: `horario`, `fase_dia`, `municipio`, `latitude`, `longitude` e `tracado_via`
  bruto.

As quatro variáveis secondary only não participarão da primeira modelagem principal. Um
experimento futuro com elas deverá ser materializado e interpretado separadamente.

## 5. Desenho temporal

Os folds expanding-window permanecem:

1. fit em 2021 e validação em 2022;
2. fit em 2021–2022 e validação em 2023;
3. fit em 2021–2023 e validação em 2024.

Treino e validação são disjuntos, o treino sempre antecede a validação e 2025 não aparece nos
folds internos. Nenhuma observação de validação participa de fit.

## 6. Preprocessing

As nove categóricas usam `OneHotEncoder(handle_unknown="ignore")`, sem drop ou agrupamento
automático de categorias raras. Somente `km` usa `StandardScaler`. Os 12 indicadores
`tracado_*` seguem por passthrough. Encoder e scaler são ajustados somente no treino de cada
fold.

Não existem imputer, target encoding, feature selection, PCA ou balanceamento. As entradas
têm zero nulls; as três validações produziram matrizes CSR esparsas e finitas. Nenhum
preprocessor fitado foi persistido.

## 7. Métrica primária

A futura métrica principal é Average Precision (AP) para `target_grave=True`, pela definição
operacional de `sklearn.metrics.average_precision_score`. A seleção comparará a média
aritmética não ponderada das três APs, acompanhada do desvio padrão e do resultado do Fold 3.
Nenhuma AP foi calculada na Fase 3.

## 8. Threshold e refit

O threshold futuro será escolhido sobre previsões OOF temporais concatenadas de 2022, 2023 e
2024, maximizando F1 da classe grave. Empates priorizam maior recall e depois menor threshold;
0,5 é apenas referência. O threshold não foi calculado neste aceite.

Depois da seleção exclusiva no desenvolvimento, um preprocessor novo e o modelo escolhido
serão ajustados em 2021–2024 completos. Pipeline e threshold serão congelados antes de uma
única avaliação em 2025.

## 9. Política de 2025

2025 já foi explorado estruturalmente nas fases anteriores e não constitui holdout
completamente cego. Após o congelamento metodológico, porém, ele não pode orientar seleção de
features, preprocessing, modelos, hiperparâmetros, threshold, calibração, balanceamento ou
qualquer escolha baseada em performance. A primeira consulta à performance preditiva de 2025
ocorrerá somente após o pipeline final estar congelado.

## 10. Limitações

- O dataset público não contém timestamps de preenchimento por campo; a disponibilidade das
  features principais é uma premissa metodológica de compatibilidade com o cenário, não uma
  comprovação do fluxo operacional interno da PRF.
- A base contém ocorrências registradas, não a população exposta ao risco de acidente.
- O desenho é observacional e associações não devem ser interpretadas como efeitos causais.
- Como 2025 foi explorado estruturalmente, sua avaliação final deve ser descrita como temporal,
  mas não como teste em holdout totalmente cego.

## 11. Resultado do checklist

O arquivo `reports/tables/phase_3f_premodeling_checklist.csv` contém 26 verificações
substantivas. O resultado consolidado é **26 PASS e 0 FAIL**. As verificações cobrem fundação,
população, features, folds, preprocessing, métrica, threshold, refit e ausência de modelagem
antes do aceite.

## 12. Autorização para a Fase 4

Todos os critérios pré-modelagem foram atendidos sem alterar features, folds, preprocessing ou
políticas experimentais e sem consultar performance de 2025.

**Fase 3 aprovada para início da modelagem principal.**
