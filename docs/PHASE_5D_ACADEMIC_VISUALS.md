# Fase 5D — Figuras e tabelas acadêmicas

## 1. Objetivo

Materializar os elementos selecionados nas Fases 5B e 5C em formatos acadêmicos reproduzíveis.
A fase produz apresentação e exportação; não executa EDA, modelagem, predição, SHAP,
recalibração, seleção de threshold ou nova avaliação.

Os outputs aguardam revisão visual humana antes de serem considerados aprovados para o
manuscrito.

## 2. Regra de não recálculo

O gerador lê somente CSVs científicos já versionados em `reports/tables/`. Parquet, pipeline
final e predictions individuais não são carregados. As únicas operações aplicadas são seleção
de linhas já ordenadas, posicionamento visual e formatação editorial. Quantis, bins, APs,
contribuições, deltas e matriz de confusão permanecem exatamente os publicados.

## 3. Ferramenta e reprodução

- Matplotlib, já presente como dependência direta;
- Polars para leitura, validação e escrita dos CSVs;
- backend não interativo `Agg`;
- fonte DejaVu Sans;
- PNG a 300 DPI e SVG vetorial;
- nenhum pacote ou fonte externa.

Regeneração no diretório oficial:

```powershell
uv run python scripts/generate_phase_5d_academic_visuals.py
```

Raiz alternativa, inclusive para testes:

```powershell
uv run python scripts/generate_phase_5d_academic_visuals.py `
    --output-root reports
```

O script valida existência, schema e não vacuidade das fontes antes de escrever. Os outputs
ficam exclusivamente abaixo de `--output-root`.

## 4. Padrão visual

- fundo branco, sem 3D, sombras, gradientes ou decoração;
- títulos e eixos em português, com notas metodológicas nas próprias figuras;
- escalas iniciadas em zero para F1, F2 e F4;
- F5 usa escala ampliada de 0,35 a 0,45, declarada explicitamente;
- F6 usa quatro caixas neutras, sem escala cromática de “bom” ou “ruim”;
- F7 apresenta os dez bins publicados e a referência `y = x`, sem suavização;
- F8 usa a participação relativa já publicada, sem nova normalização;
- A2 usa P10, P25, mediana, média, P75 e P90 já publicados, sem predictions individuais.

### Cores dos modelos

| Modelo | Cor |
|---|---|
| Regressão Logística | `#0072B2` |
| Random Forest | `#009E73` |
| XGBoost | `#D55E00` |

F4 e F5 reutilizam exatamente esse mapeamento. Cor não codifica qualidade.

### Arredondamento de apresentação

- percentuais: duas casas;
- AP, ROC-AUC, Brier, precision, recall e F1: quatro casas;
- threshold: seis casas no visual (`0,237232`);
- contagens: inteiros com separador de milhar;
- CSVs acadêmicos preservam valores numéricos integrais.

Nenhum dado é arredondado antes de construir marcas e linhas.

## 5. Figuras produzidas

| ID | Arquivos | Prioridade | Posição prevista | Decisão visual |
|---|---|---|---|---|
| M1 | `M1_temporal_design.{png,svg}` | ESSENTIAL_METHODS | Metodologia | Timeline expanding-window; 2025 isolado da otimização. |
| F1 | `F1_temporal_contrasts.{png,svg}` | ESSENTIAL | Resultados 4.2.1 | Três dumbbells, escala comum 0%–40%. |
| F2 | `F2_contextual_contrasts.{png,svg}` | ESSENTIAL | Resultados 4.2.2 | Quatro facetas, escala comum 0%–55%, sem mapa. |
| F4 | `F4_model_average_precision.{png,svg}` | ESSENTIAL | Resultados 4.3 | Lollipop horizontal, eixo 0–1. |
| F5 | `F5_temporal_fold_average_precision.{png,svg}` | ESSENTIAL | Resultados 4.4 | Linhas por modelo, escala 0,35–0,45 explicitada. |
| F6 | `F6_confusion_matrix_2025.{png,svg}` | ESSENTIAL | Resultados 4.6 | Real nas linhas, predito nas colunas. |
| F7 | `F7_calibration_2025.{png,svg}` | USEFUL | Resultados 4.7.1, se mantida | Diagnóstico condicional no manuscrito. |
| F8 | `F8_predictor_contributions.{png,svg}` | USEFUL | Fim de Resultados 4.7.2 | Top 8 do ranking publicado; nota não causal. |
| A2 | `A2_score_outcome_summary.{png,svg}` | APPENDIX | Apêndice | Quantile-range plot a partir do resumo 4I. |

F3 não foi produzido, conforme exclusão por redundância definida na Fase 5B.

## 6. Tabelas produzidas

| ID | Arquivo | Prioridade | Posição prevista |
|---|---|---|---|
| M2 | `M2_features_preprocessing.csv` | ESSENTIAL_METHODS | Metodologia |
| T1 | `T1_population_characterization.csv` | ESSENTIAL | Resultados 4.1 |
| T2 | `T2_final_2025_evaluation.csv` | ESSENTIAL | Resultados 4.5 |
| A1 | `A1_top15_transformed_features.csv` | APPENDIX | Apêndice |
| A3 | `A3_fold_model_metrics.csv` | APPENDIX | Apêndice |
| A4 | `A4_selected_descriptive_contrasts.csv` | APPENDIX | Apêndice |

### Prévia M2 — features e preprocessing

| Grupo | Predictors físicos | Representações conceituais | Preprocessing | Política adicional |
|---|---:|---:|---|---|
| Categóricas | 9 | 9 | `OneHotEncoder(handle_unknown="ignore")` | Vocabulário somente no treino |
| Numérica | 1 | 1 | `StandardScaler` | Parâmetros somente no treino |
| Binárias de traçado | 12 | 1 | `passthrough` | Validação binária 0/1 |
| Total | 22 | 11 | `ColumnTransformer` | `remainder=drop` |

### Prévia T1 — caracterização da população

| Ano | Ocorrências | Graves | Não graves | Prevalência grave (%) |
|---|---:|---:|---:|---:|
| 2021 | 64.567 | 18.118 | 46.449 | 28,06 |
| 2022 | 64.606 | 18.409 | 46.197 | 28,49 |
| 2023 | 67.766 | 19.212 | 48.554 | 28,35 |
| 2024 | 73.156 | 20.625 | 52.531 | 28,19 |
| 2025 | 72.529 | 20.493 | 52.036 | 28,25 |
| **Total** | **342.624** | **96.857** | **245.767** | **28,27** |

### Prévia T2 — avaliação final de 2025

| Métrica | Referência | 2025 | Delta | Referência utilizada |
|---|---:|---:|---:|---|
| Average Precision | 0,4008 | 0,3974 | −0,0034 | Média interna dos folds |
| ROC-AUC | 0,6308 | 0,6286 | −0,0023 | Média interna dos folds |
| Brier score | 0,1939 | 0,1938 | −0,0001 | Média interna; menor é melhor |
| Precision | 0,3333 | 0,3316 | −0,0017 | OOF temporal no threshold congelado |
| Recall | 0,7705 | 0,7718 | +0,0014 | OOF temporal no threshold congelado |
| F1 | 0,4653 | 0,4639 | −0,0014 | OOF temporal no threshold congelado |

O delta negativo do Brier representa redução do erro médio quadrático probabilístico, não
deterioração.

## 7. Fontes e rastreabilidade

O manifesto `phase_5d_output_manifest.csv` registra, para cada formato, título, fonte,
prioridade, seção e dimensões. As fontes centrais são:

- tabelas 2A/2F para caracterização e contrastes;
- contratos 3B/3D/3E para M1/M2;
- tabelas 4D para comparação e folds;
- tabelas 4F/4H para threshold, avaliação e calibração;
- tabelas 4I para contribuições e scores resumidos;
- mapas 5A/5C para seleção, cautelas e apresentação.

## 8. QA e revisão humana

`phase_5d_visual_qa.csv` registra existência, tamanho e resolução de cada PNG/SVG. Todas as
figuras permanecem com `manual_review_required=true`.

A contact sheet está em
`reports/figures/tcc/review/phase_5d_contact_sheet.png`, marcada explicitamente como
“REVIEW ONLY — não usar no manuscrito”. Ela não é figura científica nem integra a lista final
do TCC.

A revisão local desta geração verificou eixos, notas, cores e legibilidade geral. F5 recebeu um
ajuste de espaçamento dos rótulos após a primeira inspeção. A aprovação visual editorial ainda
depende de revisão humana do conjunto final.

## 9. Outputs de controle

- `reports/tables/phase_5d_output_manifest.csv`;
- `reports/tables/phase_5d_visual_qa.csv`;
- `reports/tables/phase_5d_generation_checklist.csv`.

O checklist registra geração técnica concluída e revisão humana pendente. A Fase 5D não deve
ser declarada definitivamente aprovada antes dessa revisão.

## 10. Próxima etapa

Após aprovação visual humana: **Fase 5E — primeira redação de Resultados e Discussão**, usando
os artefatos aqui materializados sem alterar os resultados científicos congelados.
