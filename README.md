# TCC — Gravidade de Acidentes em Rodovias Federais

Projeto de Ciência de Dados para analisar fatores associados à gravidade de acidentes registrados pela Polícia Rodoviária Federal (PRF) entre 2021 e 2025 e, posteriormente, avaliar modelos de aprendizado de máquina.

## Estado atual

**Fase 6D concluída — visualizações e comunicação científica integradas ao dashboard estático.**

Nesta fase o projeto:

- preserva os CSVs oficiais sem alteração;
- valida a presença e ordem das 30 colunas esperadas;
- padroniza apenas tipos técnicos;
- cria a definição operacional de `target_grave` (`mortos > 0` ou `feridos_graves > 0`), sem usar
  `classificacao_acidente`;
- valida tipos, nulabilidade, categorias estáveis e limites numéricos com Pandera;
- valida IDs, relações entre contagens, ano, target e dia da semana entre colunas;
- gera relatório de qualidade por ano;
- mantém divergências na decomposição de `pessoas` como métrica de auditoria, não como erro;
- consolida os cinco anos em um Parquet validado antes e depois da persistência;
- registra proveniência, hashes e versões em um manifesto;
- verifica o Parquet e sua proveniência sem reconstruir ou modificar os artefatos;
- caracteriza volume anual, estabilidade do target, nulidade e cardinalidade básica;
- caracteriza mês, dia da semana, hora e fase do dia, incluindo estabilidade descritiva anual;
- caracteriza macrorregião, UF, BR e município, separando volume de proporção grave;
- caracteriza tipo de pista, uso do solo, sentido, meteorologia e componentes multivalorados
  de traçado, separando volume, proporção grave, amostra e estabilidade anual;
- caracteriza tipo e causa registrados, mudanças de taxonomia e distribuições exatas de
  pessoas e veículos, sem decidir sua elegibilidade futura como features;
- consolida oito achados centrais e separa evidência descritiva de elegibilidade preditiva;
- encerra a EDA com uma síntese científica, uma matriz autoritativa de elegibilidade e um
  inventário de verificações temporais futuras;
- audita as 22 variáveis sinalizadas comparando 2021–2024 com 2025, com TVD descritiva,
  categorias não vistas, bins numéricos definidos somente no desenvolvimento e prevalências
  multilabel de traçado;
- congela o momento preditivo, 11 features/representações principais, quatro variáveis
  secundárias e as políticas anti-leakage, de redundância e categorias desconhecidas;
- materializa o dataset analítico principal com três metadados, o target preservado e 22
  predictors físicos, incluindo 12 indicadores multilabel de `tracado_via`;
- congela desenvolvimento em 2021–2024, avaliação final em 2025 e três folds internos
  expanding-window, sem duplicar o dataset em arquivos de treino/teste;
- define previamente Average Precision (AP), agregação entre folds, threshold por OOF e
  refit final;
- valida nos três folds uma receita train-only com nove categóricas em one-hot, `km`
  padronizado e 12 indicadores de traçado em passthrough;
- tolera e audita categorias desconhecidas sem aprender vocabulário da validação ou de 2025;
- executa a primeira baseline logística sem tuning: AP média não ponderada de 0,393508 e
  desvio padrão populacional de 0,004879;
- executa uma Random Forest de configuração fixa, também sem tuning: AP média não ponderada
  de 0,395984 e desvio padrão populacional de 0,005582, sem comparação formal entre modelos;
- executa XGBoost 3.3.0 com configuração fixa e 300 rounds por fold: AP média não ponderada
  de 0,400811 e desvio padrão populacional de 0,007430, sem seleção entre famílias;
- compara formalmente as três famílias nos mesmos folds: APs médias de 0,393508, 0,395984 e
  0,400811, com ranks apenas descritivos e sem selecionar o modelo final;
- seleciona formalmente XGBoost pela maior AP média não ponderada nos três folds internos,
  mantendo refit e avaliação de 2025 para fases posteriores;
- seleciona o threshold `0.23723246157169342` somente no OOF 2022–2024, elevando o F1 de
  `0,086164` no cutoff de referência 0,5 para `0,465309`, sem retreinar o XGBoost;
- refita uma única vez o pipeline 3E+4C nas 270.095 observações de 2021–2024, com 76.364
  graves, 22 predictors, 226 features transformadas e 300/300 rounds;
- persiste o pipeline congelado com SHA-256
  `c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351`;
- avalia uma única vez o pipeline congelado em 72.529 ocorrências de 2025, obtendo AP
  `0,397446`, ROC-AUC `0,628556` e Brier `0,193822`;
- aplica sem alteração o threshold `0.23723246157169342`, com precision `0,331593`, recall
  `0,771825` e F1 `0,463889`, e persiste as predições finais sem retreinamento ou tuning.
- interpreta as predições finais com Tree SHAP nativo do XGBoost na escala de margem, com
  `uf`, `tipo_pista`, `hour`, `br` e `condicao_metereologica` nas cinco primeiras posições;
- reconcilia as contribuições com as probabilities 4H com erro máximo `4,0788e-07`, sem
  fit, novo threshold, seleção de features ou interpretação causal;
- consolida uma pergunta principal e cinco perguntas específicas em um mapa rastreável de
  métodos, evidências, respostas, cautelas e limitações, sem novo cálculo experimental.
- inventaria 19 candidatos visuais e recomenda para o corpo e os métodos três tabelas e oito
  figuras, separando itens de apêndice e de repositório sem recalcular resultados.
- organiza 18 subseções de Resultados e Discussão, com evidências, números, cautelas,
  transições e fronteiras interpretativas, sem redigir o manuscrito final ou gerar figuras.
- materializa nove figuras científicas em PNG/SVG e seis tabelas acadêmicas a partir de
  resultados congelados, sem executar análise, modelo, predição ou SHAP.
- verifica 19 referências candidatas e cobre os oito temas bibliográficos L1–L8 com inventário,
  mapas temático e de afirmações e limites de uso para a futura redação.
- redige a primeira versão dos capítulos de Resultados e Discussão, com auditorias numérica,
  bibliográfica e parágrafo–evidência, sem executar nova análise científica.
- revisa cientificamente e editorialmente esses capítulos, preservando todos os números e as
  19 referências verificadas, com auditorias de terminologia, números, citações e revisão.
- materializa 12 assets lógicos em 14 partes JSON, com manifesto, hashes, reconciliação e
  escopos temporal/contextual separados, sem inferência ou recomputação de ML;
- publica uma Home introdutória para público não especializado e preserva a Visão Geral
  analítica em `/visao-geral`, totalizando nove rotas estáticas.

Consulte o [`contrato de dados`](docs/DATA_CONTRACT.md) e a documentação do
[`dataset intermediário`](docs/INTERIM_DATASET.md). O aceite formal da fundação está em
[`docs/PHASE_1_ACCEPTANCE.md`](docs/PHASE_1_ACCEPTANCE.md). A síntese e o aceite da EDA estão
em [`docs/PHASE_2_EDA_SYNTHESIS.md`](docs/PHASE_2_EDA_SYNTHESIS.md) e
[`docs/PHASE_2_ACCEPTANCE.md`](docs/PHASE_2_ACCEPTANCE.md).
Os métodos e resultados da auditoria temporal estão em
[`docs/PHASE_3A_TEMPORAL_DRIFT.md`](docs/PHASE_3A_TEMPORAL_DRIFT.md).
A política final de features está em
[`docs/PHASE_3B_FEATURE_POLICY.md`](docs/PHASE_3B_FEATURE_POLICY.md).
O contrato materializado do dataset principal está em
[`docs/PHASE_3C_ANALYTICAL_DATASET.md`](docs/PHASE_3C_ANALYTICAL_DATASET.md).
O desenho experimental temporal está em
[`docs/PHASE_3D_EXPERIMENTAL_DESIGN.md`](docs/PHASE_3D_EXPERIMENTAL_DESIGN.md).
O contrato e a auditoria do preprocessing estão em
[`docs/PHASE_3E_PREPROCESSING.md`](docs/PHASE_3E_PREPROCESSING.md).
A primeira baseline preditiva está documentada em
[`docs/PHASE_4A_LOGISTIC_BASELINE.md`](docs/PHASE_4A_LOGISTIC_BASELINE.md).
A Random Forest baseline está documentada em
[`docs/PHASE_4B_RANDOM_FOREST.md`](docs/PHASE_4B_RANDOM_FOREST.md).
O XGBoost baseline está documentado em
[`docs/PHASE_4C_XGBOOST.md`](docs/PHASE_4C_XGBOOST.md).
A comparação temporal está documentada em
[`docs/PHASE_4D_MODEL_COMPARISON.md`](docs/PHASE_4D_MODEL_COMPARISON.md).
A seleção formal está documentada em
[`docs/PHASE_4E_MODEL_SELECTION.md`](docs/PHASE_4E_MODEL_SELECTION.md).
A seleção do cutoff OOF está documentada em
[`docs/PHASE_4F_THRESHOLD_SELECTION.md`](docs/PHASE_4F_THRESHOLD_SELECTION.md).
O refit final está documentado em
[`docs/PHASE_4G_FINAL_REFIT.md`](docs/PHASE_4G_FINAL_REFIT.md).
A avaliação temporal final está documentada em
[`docs/PHASE_4H_FINAL_EVALUATION.md`](docs/PHASE_4H_FINAL_EVALUATION.md).
A interpretação final está documentada em
[`docs/PHASE_4I_FINAL_INTERPRETATION.md`](docs/PHASE_4I_FINAL_INTERPRETATION.md).
A consolidação das perguntas de pesquisa está documentada em
[`docs/PHASE_5A_RESEARCH_QUESTION_SYNTHESIS.md`](docs/PHASE_5A_RESEARCH_QUESTION_SYNTHESIS.md).
O plano congelado de tabelas e figuras está documentado em
[`docs/PHASE_5B_RESULTS_VISUAL_PLAN.md`](docs/PHASE_5B_RESULTS_VISUAL_PLAN.md).
A estrutura acadêmica de Resultados e Discussão está documentada em
[`docs/PHASE_5C_RESULTS_DISCUSSION_STRUCTURE.md`](docs/PHASE_5C_RESULTS_DISCUSSION_STRUCTURE.md).
Os critérios e outputs acadêmicos da Fase 5D estão documentados em
[`docs/PHASE_5D_ACADEMIC_VISUALS.md`](docs/PHASE_5D_ACADEMIC_VISUALS.md).
A fundamentação bibliográfica verificável está documentada em
[`docs/PHASE_5E1_BIBLIOGRAPHIC_GROUNDING.md`](docs/PHASE_5E1_BIBLIOGRAPHIC_GROUNDING.md).
A primeira redação acadêmica e seu relatório de rastreabilidade estão em
[`docs/PHASE_5E2_RESULTS_DISCUSSION_DRAFT.md`](docs/PHASE_5E2_RESULTS_DISCUSSION_DRAFT.md) e
[`docs/PHASE_5E2_WRITING_REPORT.md`](docs/PHASE_5E2_WRITING_REPORT.md).
A versão revisada e o relatório da Fase 5F estão em
[`docs/PHASE_5F_RESULTS_DISCUSSION_REVISED.md`](docs/PHASE_5F_RESULTS_DISCUSSION_REVISED.md) e
[`docs/PHASE_5F_SCIENTIFIC_REVISION.md`](docs/PHASE_5F_SCIENTIFIC_REVISION.md).
A arquitetura documental do dashboard está em
[`docs/PHASE_6A_DASHBOARD_ARCHITECTURE.md`](docs/PHASE_6A_DASHBOARD_ARCHITECTURE.md).
A exportação estática auditada está documentada em
[`docs/PHASE_6B_DASHBOARD_DATA_EXPORT.md`](docs/PHASE_6B_DASHBOARD_DATA_EXPORT.md).

## Requisitos

- Python 3.14
- uv

## Dados

Baixe os arquivos oficiais agrupados por ocorrência da PRF e coloque-os em `data/raw/`:

```text
datatran2021.csv
datatran2022.csv
datatran2023.csv
datatran2024.csv
datatran2025.csv
```

Os dados brutos não são versionados no Git.

## Instalação

```powershell
uv sync --locked
```

O `uv.lock` deve ser versionado no repositório. Ele é gerenciado pelo uv; não deve ser editado manualmente.

## Auditoria

```powershell
uv run prf-audit
```

Saídas esperadas:

```text
artifacts/audit/audit_2021_2025.json
artifacts/audit/audit_summary.csv
```

## Dataset intermediário

```powershell
uv run prf-build-interim
```

Saídas locais, derivadas e ignoradas pelo Git:

```text
data/interim/prf_accidents_2021_2025.parquet
artifacts/interim/interim_manifest.json
```

## Reprodução da fundação de dados

```powershell
uv sync --locked
uv run prf-audit
uv run prf-build-interim
uv run prf-verify-interim
```

- `uv sync --locked`: reproduz o ambiente definido no `uv.lock`.
- `prf-audit`: valida os RAW e reproduz as métricas de qualidade.
- `prf-build-interim`: reconstrói e publica o par Parquet + manifesto.
- `prf-verify-interim`: verifica, sem reconstruir, contrato, baseline, manifesto e hashes RAW.

## Qualidade

```powershell
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
```

## EDA — Caracterização geral

```powershell
uv run prf-eda-general
```

O comando verifica o interim e gera quatro tabelas em `reports/tables/` e duas figuras
científicas em `reports/figures/`. A lógica numérica oficial está em
`src/tcc_prf_severity/analysis/general.py`.

## EDA — Padrões temporais

```powershell
uv run prf-eda-temporal
```

O comando verifica o interim sem reconstruí-lo e gera dez tabelas temporais em
`reports/tables/` e sete figuras científicas em `reports/figures/`. As derivações de mês e hora
existem somente em memória; nenhum dataset processed é criado.

## EDA — Padrões geográficos

```powershell
uv run prf-eda-geographic
```

O comando verifica o interim, deriva macrorregião somente em memória e gera 15 tabelas e seis
figuras geográficas. As tabelas completas preservam `br = 0` e todas as categorias; rankings
de taxa de BR e município usam `n >= 500` apenas como critério editorial de destaque.

## EDA — Via e ambiente

```powershell
uv run prf-eda-road-environment
```

O comando verifica o interim sem reconstruí-lo e gera 14 tabelas e quatro figuras sobre tipo
de pista, uso do solo, sentido, meteorologia e componentes de `tracado_via`. A separação dos
componentes ocorre somente em memória; suas contagens não são mutuamente exclusivas. O corte
`n >= 500` é apenas um critério editorial para destaques de taxa em meteorologia e traçado;
`Ignorado` permanece nas tabelas completas, mas não é tratado como condição meteorológica
informada nesses destaques.

## EDA — Dinâmica das ocorrências

```powershell
uv run prf-eda-occurrence-dynamics
```

O comando verifica o interim sem reconstruí-lo e gera 17 tabelas e seis figuras sobre tipo de
acidente, causa registrada pela PRF, mudanças de taxonomia e contagens exatas de pessoas e
veículos. Não há harmonização, bins, remoção de outliers ou dataset processed. Essas variáveis
são permitidas na EDA associativa, mas sua elegibilidade para ML será decidida separadamente
devido à disponibilidade temporal e ao risco de leakage.

## EDA — Associação com gravidade

```powershell
uv run prf-eda-severity-associations
```

O comando verifica o interim e recalcula uma síntese das associações descritivas das Fases
2A–2E com `target_grave`. Ele gera quatro tabelas consolidadas e uma figura, incluindo uma
matriz conceitual de elegibilidade para modelagem futura. Não cria features, divisão
treino/teste, modelos ou dataset processed.

## Auditoria temporal das features

```powershell
uv run prf-audit-temporal-drift
```

O comando verifica o interim, lê o inventário autoritativo da Fase 2F e compara as 22
variáveis sinalizadas entre 2021–2024 e 2025. Gera sete tabelas e até três figuras sem criar
split, dataset processed, encoding, seleção definitiva de features ou modelo.

## Dataset analítico principal

```powershell
uv run prf-build-analytical
uv run prf-verify-analytical
```

`prf-build-analytical` verifica o interim e o contrato 3B, aplica apenas derivações
determinísticas e publica com rollback o Parquet, o esquema e o manifesto da Fase 3C.
`prf-verify-analytical` confere o artefato existente e sua proveniência sem reconstruí-lo.

Saídas locais e reproduzíveis:

```text
data/processed/prf_primary_analytical_2021_2025.parquet
reports/tables/phase_3c_analytical_schema.csv
artifacts/processed/phase_3c_primary_analytical_manifest.json
```

O Parquet contém 342.624 ocorrências e 26 colunas: três metadados, um target e 22 predictors
físicos. Nenhum encoder, scaler, imputação, split ou modelo é criado.

## Desenho experimental temporal

```powershell
uv run prf-design-experiment
```

O comando verifica o interim e o dataset analítico, obtém os 22 predictors pelo esquema 3C e
materializa três tabelas pequenas. O desenvolvimento cobre 2021–2024; 2025 fica reservado à
avaliação final. Os folds internos são `2021 -> 2022`, `2021–2022 -> 2023` e
`2021–2023 -> 2024`. Não há split aleatório, cópia completa do dataset, fitting ou cálculo de
performance.

## Validação do preprocessing

```powershell
uv run prf-validate-preprocessing
```

O comando verifica o dataset analítico e os folds da 3D, cria um `ColumnTransformer` novo por
fold e ajusta cada encoder/scaler somente no respectivo treino. As nove categóricas usam
one-hot com categorias desconhecidas toleradas e auditadas, somente `km` usa
`StandardScaler`, e os 12 indicadores `tracado_*` seguem por passthrough. As matrizes ficam
esparsas; 2025 não é transformado e nenhum modelo ou transformer fitado é persistido.

## Regressão Logística baseline

```powershell
uv run prf-run-logistic-baseline
```

O comando executa a configuração logística fixa nos três folds temporais e publica métricas,
calibração diagnóstica e previsões OOF de 2022–2024. As APs foram 0,386681, 0,396058 e
0,397786; a média não ponderada foi 0,393508. O corte 0,5 é somente referência: nenhum
threshold foi selecionado, nenhum refit foi feito e 2025 permaneceu fora da execução.

## Random Forest baseline

```powershell
uv run prf-run-random-forest-baseline
```

O comando executa uma Random Forest fixa com 300 árvores nos mesmos três folds e com o mesmo
preprocessing train-only. As APs foram 0,388096, 0,399673 e 0,400183; a média não ponderada
foi 0,395984. Métricas no corte 0,5, calibração e estrutura das árvores são apenas
diagnósticos: não houve tuning, seleção de threshold, refit, uso de 2025 ou escolha de modelo.

## XGBoost baseline

```powershell
uv run prf-run-xgboost-baseline
```

O comando executa XGBoost 3.3.0 com configuração fixa, o mesmo preprocessing train-only e
exatamente 300 rounds nos três folds. As APs foram 0,390375, 0,404968 e 0,407090; a média não
ponderada foi 0,400811. Não houve tuning, early stopping, seleção de threshold, refit, uso de
2025 ou escolha de modelo.

## Comparação temporal dos modelos

```powershell
uv run prf-compare-models
```

O comando lê somente as tabelas publicadas das Fases 4A–4C, valida que folds, populações,
prevalências, dimensões e contratos são comparáveis e gera quatro tabelas consolidadas. A
comparação registra AP por fold, média, dispersão, Fold 3, métricas secundárias e deltas, sem
treinar modelos, usar 2025, calcular threshold ou realizar a seleção final.

## Seleção formal do modelo

```powershell
uv run prf-select-model
```

O comando lê somente os resultados consolidados da 4D e os contratos versionados, reconcilia
rank e maior AP média e publica a seleção após 13 verificações substantivas. XGBoost foi
selecionado exclusivamente pela maior AP média não ponderada (`0,400811`). Nenhum OOF,
threshold, refit, tuning posterior ou resultado de 2025 participa desta fase.

## Seleção do threshold OOF

```powershell
uv run prf-select-threshold
```

O comando valida a seleção 4E e o OOF do XGBoost 4C, usa como candidatos exatamente os
scores únicos observados em 2022–2024 e maximiza F1 da classe grave. AP continua sendo a
métrica que selecionou o modelo; F1 seleciona apenas o cutoff binário. O threshold congelado
é `0.23723246157169342`, com precision `0,333301`, recall `0,770456` e F1 `0,465309` no pool
OOF. No cutoff de referência 0,5, os valores são `0,571368`, `0,046595` e `0,086164`. Nenhum
modelo é treinado, nenhum threshold anual é criado e 2025 não é acessado.

## Refit final 2021–2024

```powershell
uv run prf-refit-final-model
```

O comando valida as seleções 4E/4F e os contratos 3C–4C, filtra somente 2021–2024 e executa
um único fit da factory oficial `build_xgboost_pipeline`. Foram usadas 270.095 observações,
76.364 graves e 22 predictors; o preprocessing produziu 226 features e o XGBoost completou
300/300 rounds. O threshold 4F foi apenas registrado, sem recálculo. O pipeline local ignorado
pelo Git possui SHA-256
`c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351`. Nenhuma métrica de
treino ou resultado de 2025 foi produzido.

## Avaliação temporal final em 2025

```powershell
uv run prf-evaluate-final-2025
```

O comando valida o SHA do pipeline antes de carregá-lo e avalia exclusivamente as 72.529
ocorrências de 2025. A AP final foi `0,3974456687131155`, a ROC-AUC
`0,6285562620583193` e o Brier `0,19382199321256413`. No threshold congelado pela 4F,
precision, recall e F1 foram `0,33159329140461213`, `0,7718245254477138` e
`0,4638892554954321`. As predições locais têm SHA-256
`411b5113060b19c3cc9da5fe1a6cddcf8a7d7662fe73102a6f3fdb2b05b88375`. A comparação com o
desenvolvimento é descritiva; nenhum modelo, hiperparâmetro, predictor, preprocessing ou
threshold foi alterado após a observação do holdout.

## Interpretação final pós-avaliação

```powershell
uv run prf-interpret-final-model
```

O comando valida os hashes do pipeline e das predictions 4H, transforma os 22 predictors sem
novo fit e calcula contribuições Tree SHAP nativas para as 226 features. As contribuições são
aditivas na margem bruta, não em pontos percentuais de probabilidade. Os cinco predictors de
maior contribuição absoluta média em 2025 foram `uf`, `tipo_pista`, `hour`, `br` e
`condicao_metereologica`. TP/FP/FN/TN permaneceram em 15.817/31.883/4.676/20.153. O ranking
explica o uso de informações pelo modelo e não representa causalidade, feature selection ou
nova decisão experimental.

## Consolidação das perguntas de pesquisa

A Fase 5A organiza os resultados publicados das Fases 2–4 em cinco perguntas específicas:
associações descritivas, capacidade preditiva, comparação entre famílias, consistência temporal
e generalização em 2025. A síntese preserva AP como métrica principal, distingue ranking
probabilístico de decisão por threshold e usa a interpretação 4I apenas como evidência
complementar não causal. Nenhum modelo, predição, threshold ou teste estatístico foi executado.

## Plano de tabelas e figuras finais

A Fase 5B rastreia 19 candidatos e congela uma recomendação para o corpo e os métodos de três
tabelas e oito figuras, além de quatro itens de apêndice. A seleção privilegia cobertura das
cinco perguntas de pesquisa, legibilidade, parcimônia, separação entre volume e proporção e
interpretação não causal. Artefatos técnicos, tabelas completas e redundâncias permanecem no
repositório ou no apêndice. Nenhuma figura foi gerada e nenhum resultado foi recalculado.

Para uma eventual Fase 6, o plano reserva um dashboard 100% estático em Next.js, React e
TypeScript, alimentado por JSON exportado pelo pipeline Python e com filtros executados no
cliente. Métricas congeladas de modelagem serão apenas exibidas, sem recálculo; a hospedagem
prevista é a Vercel. Essa arquitetura é somente uma decisão futura e não adiciona dependências
nesta fase.

## Estrutura de Resultados e Discussão

A Fase 5C separa explicitamente apresentação e interpretação em 10 subseções planejadas de
Resultados e oito de Discussão. Cada seção possui RQ, evidência versionada, elemento visual,
mensagem, cautela e transição. F8 foi posicionada no fim de Resultados para apresentar o
ranking e será retomada na Discussão apenas para interpretação; F7 permanece opcional e M1/M2
continuam na Metodologia. Nenhuma figura, referência bibliográfica ou redação final completa
foi produzida.

## Figuras e tabelas acadêmicas

A Fase 5D gerou nove figuras científicas, cada uma em PNG a 300 DPI e SVG, e seis tabelas CSV
em `reports/figures/tcc/` e `reports/tables/tcc/`. A geração lê somente tabelas científicas
versionadas; não carrega Parquet, pipeline ou predictions individuais. O contact sheet e o QA
foram produzidos, e a aprovação visual humana foi concluída antes da Fase 5E.1.

```powershell
uv run python scripts/generate_phase_5d_academic_visuals.py
```

## Fundamentação bibliográfica

A Fase 5E.1 verificou 19 referências candidatas — 19 `VERIFIED` e nenhuma `UNRESOLVED` — e
cobriu os oito temas L1–L8 definidos na Fase 5C. O inventário e os mapas de tema e afirmação
registram fontes de verificação, uso planejado e fronteiras interpretativas, separando
literatura aplicada de referências metodológicas. Nenhuma citação foi inserida no roteiro 5C e
nenhuma análise foi reexecutada.

## Primeira redação de Resultados e Discussão

A Fase 5E.2 redigiu os capítulos 4 e 5 com a estrutura congelada na Fase 5C, os elementos
acadêmicos da Fase 5D e somente as referências verificadas na Fase 5E.1. Os 45 parágrafos de
prosa possuem mapa de evidência; afirmações numéricas e citações externas têm auditorias
próprias, ambas sem `FAIL`. O texto é uma primeira versão para revisão na Fase 5F, não o
manuscrito final. Nenhuma análise, métrica, figura ou resultado científico foi recalculado.

## Revisão científica de Resultados e Discussão

A Fase 5F produziu uma versão revisada dos capítulos 4 e 5, com terminologia acadêmica,
transições e redundâncias revistas. Os 41 grupos numéricos e as 19 referências verificadas
foram preservados, e as auditorias de terminologia, números, citações e revisão não registraram
falhas. Nenhuma nova análise foi executada. A leitura e a aprovação humanas ainda são
necessárias antes da integração definitiva ao manuscrito.

## Arquitetura do dashboard estático

A Fase 6A definiu a arquitetura, a Fase 6B materializou os JSONs determinísticos, a Fase 6C
criou a aplicação Next.js/React/TypeScript e a Fase 6D integrou gráficos Recharts, tabelas,
KPIs, matriz de confusão e desenho metodológico. O frontend lê somente
`dashboard/public/data/`, mantém filtros locais e resultados científicos congelados e se
reorganiza em desktop, tablet e mobile. Não existe backend, inferência ou recálculo de
métricas científicas.

Durante a revisão da Fase 6D foi identificada a necessidade de uma camada introdutória de
comunicação científica para público não especializado. A nova Home `/` explica a pergunta
central, as cinco perguntas de pesquisa, resultados congelados, glossário e limites de
interpretação. A Visão Geral analítica foi movida sem perda para `/visao-geral`; o site possui
nove rotas estáticas.

## Documentação científica

- [`PHASE_2_EDA_SYNTHESIS.md`](docs/PHASE_2_EDA_SYNTHESIS.md): síntese científica e resposta
  provisória da EDA à pergunta de pesquisa.
- [`PHASE_2_ACCEPTANCE.md`](docs/PHASE_2_ACCEPTANCE.md): aceite formal das Fases 2A–2G.
- [`PHASE_3A_TEMPORAL_DRIFT.md`](docs/PHASE_3A_TEMPORAL_DRIFT.md): auditoria de drift entre
  desenvolvimento e 2025.
- [`PHASE_3B_FEATURE_POLICY.md`](docs/PHASE_3B_FEATURE_POLICY.md): momento preditivo e contrato
  conceitual dos conjuntos principal e secundário.
- [`PHASE_3C_ANALYTICAL_DATASET.md`](docs/PHASE_3C_ANALYTICAL_DATASET.md): materialização
  determinística do conjunto principal, esquema, manifesto e verificações.
- [`PHASE_3D_EXPERIMENTAL_DESIGN.md`](docs/PHASE_3D_EXPERIMENTAL_DESIGN.md): fronteira
  temporal, folds internos e políticas futuras de seleção, threshold e refit.
- [`PHASE_3E_PREPROCESSING.md`](docs/PHASE_3E_PREPROCESSING.md): receita train-only,
  auditoria de categorias desconhecidas e validação real dos três folds internos.
- [`PHASE_4A_LOGISTIC_BASELINE.md`](docs/PHASE_4A_LOGISTIC_BASELINE.md): primeira baseline,
  resultados por fold, calibração diagnóstica e OOF temporal.
- [`PHASE_4B_RANDOM_FOREST.md`](docs/PHASE_4B_RANDOM_FOREST.md): configuração fixa da floresta,
  resultados por fold, estrutura das árvores, calibração diagnóstica e OOF temporal.
- [`PHASE_4C_XGBOOST.md`](docs/PHASE_4C_XGBOOST.md): versão e configuração fixas do boosting,
  rounds completos, resultados por fold, calibração diagnóstica e OOF temporal.
- [`PHASE_4D_MODEL_COMPARISON.md`](docs/PHASE_4D_MODEL_COMPARISON.md): comparabilidade,
  resultados consolidados, estabilidade e deltas descritivos das três famílias.
- [`PHASE_4E_MODEL_SELECTION.md`](docs/PHASE_4E_MODEL_SELECTION.md): regra pré-especificada,
  modelo selecionado, checklist e congelamento pós-seleção.
- [`PHASE_4F_THRESHOLD_SELECTION.md`](docs/PHASE_4F_THRESHOLD_SELECTION.md): OOF auditado,
  busca exata, cutoff congelado e diagnósticos pooled e anuais.
- [`PHASE_4G_FINAL_REFIT.md`](docs/PHASE_4G_FINAL_REFIT.md): refit único, auditoria estrutural,
  persistência, SHA e proteção do holdout final.
- [`PHASE_4H_FINAL_EVALUATION.md`](docs/PHASE_4H_FINAL_EVALUATION.md): abertura do holdout,
  métricas finais, threshold congelado, calibração e comparação temporal descritiva.
- [`PHASE_4I_FINAL_INTERPRETATION.md`](docs/PHASE_4I_FINAL_INTERPRETATION.md): Tree SHAP
  nativo, contribuições globais e transformadas, análise dos erros e relação cautelosa com a EDA.
- [`PHASE_5A_RESEARCH_QUESTION_SYNTHESIS.md`](docs/PHASE_5A_RESEARCH_QUESTION_SYNTHESIS.md):
  perguntas consolidadas, evidências rastreáveis, respostas curtas e limitações integradas.
- [`PHASE_5B_RESULTS_VISUAL_PLAN.md`](docs/PHASE_5B_RESULTS_VISUAL_PLAN.md): inventário,
  priorização, especificações e redundâncias do plano final de tabelas e figuras.
- [`PHASE_5C_RESULTS_DISCUSSION_STRUCTURE.md`](docs/PHASE_5C_RESULTS_DISCUSSION_STRUCTURE.md):
  roteiro de subseções, evidências, números, transições e limites interpretativos.
- [`PHASE_5D_ACADEMIC_VISUALS.md`](docs/PHASE_5D_ACADEMIC_VISUALS.md): geração reproduzível,
  padrão visual, outputs, prévias tabulares, QA e revisão humana posteriormente concluída.
- [`PHASE_5E1_BIBLIOGRAPHIC_GROUNDING.md`](docs/PHASE_5E1_BIBLIOGRAPHIC_GROUNDING.md): protocolo
  de verificação, inventário, mapas bibliográficos e limites de uso para L1–L8.
- [`PHASE_5E2_RESULTS_DISCUSSION_DRAFT.md`](docs/PHASE_5E2_RESULTS_DISCUSSION_DRAFT.md): primeira
  redação acadêmica dos capítulos 4 e 5.
- [`PHASE_5E2_WRITING_REPORT.md`](docs/PHASE_5E2_WRITING_REPORT.md): fontes, extensão, cautelas,
  auditorias e pontos para revisão editorial.
- [`PHASE_5F_RESULTS_DISCUSSION_REVISED.md`](docs/PHASE_5F_RESULTS_DISCUSSION_REVISED.md): versão
  revisada dos capítulos de Resultados e Discussão.
- [`PHASE_5F_SCIENTIFIC_REVISION.md`](docs/PHASE_5F_SCIENTIFIC_REVISION.md): escopo, política
  terminológica, preservação científica, auditorias e pendências de revisão humana.
- [`PHASE_6A_DASHBOARD_ARCHITECTURE.md`](docs/PHASE_6A_DASHBOARD_ARCHITECTURE.md): arquitetura
  estática, contratos de dados, rotas, filtros, fronteiras científicas e plano das Fases 6B–6E.
- [`PHASE_6B_DASHBOARD_DATA_EXPORT.md`](docs/PHASE_6B_DASHBOARD_DATA_EXPORT.md): exportador,
  JSONs, manifesto, hashes, reconciliação, determinismo e limites da camada estática de dados.
- [`PHASE_6C_DASHBOARD_SHELL.md`](docs/PHASE_6C_DASHBOARD_SHELL.md): aplicação Next.js,
  rotas, componentes, dados tipados, filtros locais, acessibilidade e static export.
- [`PHASE_6D_DASHBOARD_VISUALIZATIONS.md`](docs/PHASE_6D_DASHBOARD_VISUALIZATIONS.md):
  integração dos gráficos, tabelas, matriz de confusão, responsividade e fronteira científica.
- [`TCC_RESEARCH_LOG.md`](docs/TCC_RESEARCH_LOG.md): memória científica curada de decisões,
  resultados confirmados, hipóteses e limitações.
- [`EDA_FINDINGS.md`](docs/EDA_FINDINGS.md): registro detalhado dos achados da Fase 2,
  inclusive resultados provisórios ou inconclusivos.
- [`PHASE_1_ACCEPTANCE.md`](docs/PHASE_1_ACCEPTANCE.md): evidência congelada do encerramento e
  aceite da fundação de dados.

## Grupos planejados

As dependências estão organizadas no `pyproject.toml`:

- principal: scikit-learn e XGBoost 3.3.0, usados no preprocessing e nas três baselines;
- `ml`: Optuna, MLflow e SHAP, ainda reservados para fases futuras;
- `viz`: JupyterLab, Plotly e Streamlit.

Matplotlib é uma dependência principal da geração das figuras científicas das Fases 2 e 5D. Os
grupos `ml` e `viz` permanecem reservados para fases futuras.

## Próximo passo

A próxima etapa é a Fase 6E, dedicada ao polimento visual, auditoria final de acessibilidade e
responsividade, otimização do build estático e deploy. Nenhum deploy foi concluído na 6D.

## Princípio metodológico

O projeto não pretende prever **se** um acidente ocorrerá. A base contém somente ocorrências registradas. A futura modelagem avaliará, dado que uma ocorrência aconteceu, a capacidade de características contextuais ajudarem a identificar ocorrências com ferido grave ou morte.
