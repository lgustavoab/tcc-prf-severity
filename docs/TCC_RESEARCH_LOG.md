# Memória científica do TCC

## Finalidade e governança

Este documento é a memória científica curada e versionada do projeto. Ele registra decisões
metodológicas, resultados confirmados, hipóteses, limitações e achados que sobreviveram à
revisão. Não é um histórico de comandos nem substitui os documentos técnicos da pipeline.

Os registros usam identificadores permanentes:

- `Dxxx`: decisão metodológica;
- `Rxxx`: resultado consolidado;
- `EDAxxx`: achado exploratório;
- `Hxxx`: hipótese;
- `Lxxx`: limitação.

Identificadores não devem ser reutilizados após descarte. Mudanças relevantes devem preservar
o registro anterior, atualizar o status e explicar a revisão.

## Relação com os demais documentos

- [EDA_FINDINGS.md](EDA_FINDINGS.md) recebe o registro detalhado das análises exploratórias,
  inclusive resultados provisórios, inconclusivos ou descartados.
- `TCC_RESEARCH_LOG.md` recebe a síntese curada das decisões e dos achados que sobreviveram à
  revisão.
- [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md) é a evidência congelada do encerramento da
  Fase 1 e não deve se transformar em diário de pesquisa.
- [PHASE_2_EDA_SYNTHESIS.md](PHASE_2_EDA_SYNTHESIS.md) e
  [PHASE_2_ACCEPTANCE.md](PHASE_2_ACCEPTANCE.md) registram a síntese e o aceite da EDA.

Detalhes técnicos permanecem no [contrato de dados](DATA_CONTRACT.md), na documentação do
[dataset intermediário](INTERIM_DATASET.md) e no [aceite da Fase 1](PHASE_1_ACCEPTANCE.md).

## Identificação da pesquisa

**Tema provisório:** Análise dos fatores associados à gravidade de acidentes em rodovias
federais brasileiras e avaliação de modelos de aprendizado de máquina.

**Fonte:** Polícia Rodoviária Federal — dados do Boletim de Acidente de Trânsito (BAT)
agrupados por ocorrência.

**Período:** 2021–2025.

**Unidade de análise:** uma ocorrência registrada pela PRF.

## Pergunta de pesquisa

**Quais fatores estão associados à gravidade dos acidentes registrados nas rodovias federais
brasileiras entre 2021 e 2025 e em que medida modelos de aprendizado de máquina são capazes de
identificar acidentes de maior gravidade?**

## Objetivo geral

Analisar fatores associados à gravidade das ocorrências registradas em rodovias federais
brasileiras entre 2021 e 2025 e avaliar o desempenho de modelos de aprendizado de máquina na
identificação de ocorrências graves.

## Objetivos específicos

1. Consolidar e validar os registros da PRF de 2021 a 2025. **Concluído na Fase 1.**
2. Caracterizar temporal e geograficamente as ocorrências. **Caracterizações temporal e
   geográfica concluídas nas Fases 2B e 2C.**
3. Investigar fatores associados à gravidade. **Síntese descritiva concluída na Fase 2F;
   avaliação multivariada ainda não executada.**
4. Definir operacionalmente uma variável-alvo de gravidade. **Concluído na Fase 1.**
5. Treinar e comparar modelos de classificação. **Ainda não executado.**
6. Avaliar os modelos com métricas adequadas ao problema. **Ainda não executado.**
7. Investigar quais variáveis mais influenciam os modelos. **Ainda não executado.**
8. Avaliar generalização temporal, reservando 2025 para teste final quando a modelagem for
   iniciada. **Estratégia planejada; ainda não executada.**

Nenhuma atividade de treinamento, comparação, avaliação ou interpretação de modelos foi
executada até o encerramento da Fase 2.

## Decisões metodológicas

### D001 — Unidade de análise

**Decisão:** uma linha representa uma ocorrência registrada pela PRF.

**Justificativa:** os arquivos utilizados são agrupados por ocorrência; pessoas e veículos
envolvidos aparecem como atributos agregados da ocorrência.

**Status:** confirmada.

**Origem:** [DATA_CONTRACT.md](DATA_CONTRACT.md).

### D002 — Período

**Decisão:** utilizar os cinco anos completos de 2021 a 2025.

**Justificativa:** o recorte oferece uma janela recente e contínua, com as cinco fontes
submetidas ao mesmo contrato e ao mesmo processo de auditoria.

**Status:** confirmada.

**Origem:** [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### D003 — Definição operacional do target

**Decisão:**

```text
target_grave = (mortos > 0) OR (feridos_graves > 0)
```

**Justificativa:** `classificacao_acidente` não é usada na construção do target porque a
categoria `Com Vítimas Feridas` não diferencia feridos leves de feridos graves. A definição
adotada usa diretamente as contagens dos estados físicos relevantes ao problema.

**Status:** confirmada.

**Origem:** [DATA_CONTRACT.md](DATA_CONTRACT.md).

### D004 — Camadas de dados

**Decisão:**

- `RAW`: arquivos oficiais de origem, imutáveis;
- `INTERIM`: dados consolidados, tipados e validados, preservando o conteúdo analítico;
- `PROCESSED`: dataset analítico principal materializado a partir do interim por derivações
  determinísticas autorizadas e seleção explícita de colunas.

**Status:** confirmada para `RAW`, `INTERIM` e o artefato principal `PROCESSED` da Fase 3C.

**Origem:** [INTERIM_DATASET.md](INTERIM_DATASET.md).

### D005 — Separação entre EDA e modelagem

**Decisão:** na EDA associativa poderão ser examinadas variáveis como `causa_acidente`,
`tipo_acidente`, `pessoas` e `veiculos`. Isso não implica sua inclusão em modelos preditivos.

**Justificativa:** a seleção de features de ML deverá considerar a disponibilidade da
informação no momento relevante para a previsão e o risco de leakage.

**Status:** confirmada como princípio; seleção de features ainda não executada.

### D006 — Validação temporal futura

**Estratégia planejada:** usar 2021–2024 para desenvolvimento e reservar 2025 para teste
temporal final.

**Justificativa:** avaliar generalização em um período posterior e não utilizado no
desenvolvimento.

**Status:** planejada; nenhuma divisão ou modelagem foi executada.

### D007 — Fechamento da EDA e autoridade da matriz de elegibilidade

**Data:** 19/08/2026.

**Decisão:** encerrar formalmente a Fase 2 após a síntese 2G e adotar
`phase_2f_modeling_eligibility_matrix.csv` como fonte autoritativa para a triagem conceitual
de features.

**Justificativa:** relevância descritiva não garante disponibilidade no momento preditivo nem
ausência de leakage. A matriz separa candidatas, cautelas, decisões pendentes e exclusões sem
criar dataset de modelagem.

**Consequências:** antes de qualquer preparação ou ML, devem ser definidos o momento
preditivo, o tratamento das quatro variáveis pendentes e as verificações de drift previstas
por H001. Os sete campos de leakage permanecem bloqueados.

**Origem:** [PHASE_2_EDA_SYNTHESIS.md](PHASE_2_EDA_SYNTHESIS.md) e
`reports/tables/phase_2f_modeling_eligibility_matrix.csv`.

**Status:** confirmada; Fase 2 encerrada e modelagem não iniciada.

### D008 — Auditoria de drift antes da preparação de dados

**Data:** 19/08/2026.

**Decisão:** comparar descritivamente 2021–2024 com 2025 para todas as variáveis sinalizadas
na matriz 2F, aprendendo bins numéricos somente em 2021–2024 e sem criar split físico,
dataset processed ou seleção final.

**Justificativa:** a estabilidade do target não responde se as distribuições das features,
seus suportes ou suas taxonomias permanecem comparáveis no holdout planejado.

**Consequências:** a Fase 3B deverá definir política para categorias desconhecidas,
representações redundantes e disponibilidade preditiva. TVD permanece magnitude descritiva,
sem thresholds universais ou rótulos automáticos.

**Origem:** [PHASE_3A_TEMPORAL_DRIFT.md](PHASE_3A_TEMPORAL_DRIFT.md).

**Status:** confirmada.

### D009 — Momento preditivo e política final de features

**Data:** 19/08/2026.

**Decisão:** definir o registro inicial da ocorrência como momento preditivo, antes dos
desfechos humanos e da consolidação investigativa/dinâmica. O conjunto principal fica
congelado em `month_name`, `dia_semana`, `hour`, `uf`, `br`, `km`, `sentido_via`,
`condicao_metereologica`, `tipo_pista`, `uso_solo` e `tracado_via_components`.

**Justificativa:** disponibilidade temporal, anti-leakage e semântica prevalecem sobre força
associativa ou baixa magnitude de drift. As combinações cruas de `tracado_via` são
substituídas por componentes multilabel; data/horário crus, `fase_dia`, município e
coordenadas ficam fora por redundância da versão escolhida.

**Consequências:** `tipo_acidente`, `causa_acidente`, `pessoas` e `veiculos` ficam somente em
experimento secundário tardio. Encoders e transformações serão ajustados em 2021–2024,
tolerarão categorias unknown e nunca aprenderão vocabulário ou estatísticas usando 2025. Os
sete campos de leakage e três administrativos permanecem proibidos.

**Fronteira temporal:** a 3A já usou 2025 para diagnóstico estrutural e desenho experimental.
A partir do congelamento 3B, 2025 será reservado à avaliação final e não poderá orientar
seleção por performance, thresholds, hiperparâmetros ou transformações.

**Origem:** [PHASE_3B_FEATURE_POLICY.md](PHASE_3B_FEATURE_POLICY.md) e
`reports/tables/phase_3b_feature_policy.csv`.

**Status:** confirmada; nenhuma feature foi materializada e nenhum modelo foi iniciado.

### D010 — Materialização determinística do dataset analítico principal

**Data:** 19/08/2026.

**Decisão:** materializar o conjunto principal congelado na 3B em um Parquet com `id`,
`source_year` e `data_inversa` como metadata, `target_grave` como target e 22 predictors
físicos. As 11 representações conceituais incluem 12 indicadores binários para os componentes
de `tracado_via`.

**Justificativa:** separar metadata, target e matriz futura de predictors torna as exclusões
de leakage auditáveis e preserva rastreabilidade para o desenho temporal. Mês, hora e
componentes de traçado são derivações determinísticas; nenhuma estatística é aprendida.

**Consequências:** o cenário secundário não foi materializado. O artefato mantém as 342.624
ocorrências, 96.857 graves e os anos 2021–2025, sem imputação, encoding, escala ou split. A
Fase 3D poderá criar o desenho temporal sem redefinir a população ou a política de features.

**Origem:** [PHASE_3C_ANALYTICAL_DATASET.md](PHASE_3C_ANALYTICAL_DATASET.md),
`reports/tables/phase_3c_analytical_schema.csv` e
`artifacts/processed/phase_3c_primary_analytical_manifest.json`.

**Status:** confirmada; dataset principal materializado e machine learning não iniciado.

### D011 — Desenho experimental temporal anterior à modelagem

**Data:** 19/08/2026.

**Decisão:** usar 2021–2024 como desenvolvimento e 2025 exclusivamente como avaliação
temporal final. A validação interna será expanding-window: 2021 valida em 2022, 2021–2022
valida em 2023 e 2021–2023 valida em 2024.

**Justificativa:** a separação cronológica representa generalização futura e impede que
observações posteriores participem do fitting. Average Precision (AP), calculada futuramente
para `target_grave=True` pela definição operacional de
`sklearn.metrics.average_precision_score`, é congelada como métrica principal antes de
qualquer modelo. O ranking usará a média aritmética não ponderada das APs dos três folds,
acompanhada do desvio padrão e do resultado do Fold 3; não usará o melhor fold isolado nem uma
AP única sobre validações OOF concatenadas.

**Política de threshold e refit:** o threshold futuro maximizará F1 da classe grave usando
somente previsões OOF temporais concatenadas de 2022–2024; empates priorizam maior recall e
depois menor threshold. Esse pool OOF serve ao threshold, não ao ranking de modelos. Após a
seleção pelos folds, o pipeline será refitado em 2021–2024 e aplicado uma única vez a 2025 com
threshold congelado.

**Consequências:** transformações aprendidas serão ajustadas somente no treino de cada fold.
2025 não poderá selecionar features, representação, modelo, hiperparâmetros, threshold,
calibração ou preprocessing. A exploração estrutural anterior de 2025 permanece registrada
como limitação; nenhum modelo ou performance foi produzido na 3D.

**Origem:** [PHASE_3D_EXPERIMENTAL_DESIGN.md](PHASE_3D_EXPERIMENTAL_DESIGN.md) e tabelas
`phase_3d_*` em `reports/tables/`.

**Status:** confirmada; desenho congelado antes da primeira modelagem.

### D012 — Preprocessing train-only por fold temporal

**Data:** 19/08/2026.

**Decisão:** construir uma instância independente de `ColumnTransformer` por fold, ajustada
somente no treino. As nove variáveis categóricas — incluindo `hour` e `br` por sua semântica
— usam `OneHotEncoder(handle_unknown="ignore")`; somente `km` usa `StandardScaler`; os 12
indicadores `tracado_*` seguem por passthrough.

**Justificativa:** vocabulários e estatísticas aprendidos globalmente introduziriam informação
da validação no treino. A política train-only preserva a ordem temporal, tolera mudança de
categorias sem escondê-la da auditoria e mantém uma representação comum para futuros modelos
lineares e de árvore.

**Consequências:** cada fold pode ter dimensionalidade diferente. Os três folds produziram
matrizes CSR esparsas com 215, 220 e 223 features, respectivamente, e nenhum valor não finito.
Categorias desconhecidas ocorreram somente em `br`, afetando 12, 3 e 3 linhas das validações.
Não há imputer, vocabulário global, uso de target ou transformação de 2025. Nenhum preprocessor
fitado foi persistido e nenhum modelo ou métrica preditiva foi produzido.

**Origem:** [PHASE_3E_PREPROCESSING.md](PHASE_3E_PREPROCESSING.md) e tabelas
`phase_3e_*` em `reports/tables/`.

**Status:** confirmada; receita validada antes da primeira modelagem.

### D013 — Fechamento pré-modelagem da Fase 3

**Data:** 19/08/2026.

**Decisão:** encerrar a Fase 3 com o contrato pré-modelagem congelado e autorizar o início da
modelagem principal na Fase 4. A autorização depende do checklist 3F integralmente aprovado e
preserva população, features, folds, preprocessing, AP, threshold OOF, refit e fronteira de
2025 definidos nas Fases 3A–3E.

**Consequências:** a primeira modelagem deverá usar somente o conjunto principal e os folds de
2021–2024. Nenhuma performance de 2025 poderá orientar decisões; o cenário secondary only
continuará separado da conclusão principal.

**Origem:** [PHASE_3_PREMODELING_ACCEPTANCE.md](PHASE_3_PREMODELING_ACCEPTANCE.md) e
`reports/tables/phase_3f_premodeling_checklist.csv`.

**Status:** confirmada; Fase 3 encerrada e Fase 4 autorizada.

### D014 — Seleção formal do XGBoost

**Data:** 19/08/2026.

**Decisão:** selecionar `phase_4c_xgboost_baseline`, família
`xgboost_gradient_boosted_trees`, exclusivamente por apresentar a maior AP média aritmética
não ponderada nos três folds internos: 0,400811, frente a 0,395984 da Random Forest e
0,393508 da Logistic Regression. O `primary_metric_rank=1` é único e coincide com o argmax
recalculado da AP média.

**Justificativa:** Average Precision e sua média não ponderada foram congeladas antes da
modelagem como métrica e agregação principais. AP std, Fold 3, ROC-AUC e Brier são
complementares e não causam a seleção. Os deltas médios descritivos do XGBoost são
0,00730268102395526 contra Logistic Regression e 0,004827046995155848 contra Random Forest;
não houve teste de significância ou score composto.

**Consequências:** família, configuração 4C, preprocessing 3E, features 3B/3C e desenho 3D
ficam congelados sem tuning posterior. 2025 permanece reservado; nenhum OOF foi carregado,
nenhum threshold foi selecionado e nenhum refit foi realizado. O próximo passo é a Fase 4F.

**Origem:** [PHASE_4E_MODEL_SELECTION.md](PHASE_4E_MODEL_SELECTION.md),
`phase_4e_model_selection.csv` e `phase_4e_selection_checklist.csv`.

**Status:** confirmada; 13 checks PASS e 0 FAIL.

### D015 — Threshold OOF temporal do XGBoost

**Data:** 19/08/2026.

**Decisão:** congelar o threshold `0.23723246157169342` para transformar a probabilidade do
XGBoost 4C em decisão `target_grave=True`. A busca usou os 202.207 scores únicos do OOF
concatenado de 2022–2024 e a regra `probabilidade >= threshold`.

**Justificativa:** conforme o contrato 3D, o objetivo foi maximizar o F1 positivo, comparado
exatamente como `2TP / (2TP + FP + FN)`. Empates seriam resolvidos por maior recall e depois
menor threshold; o máximo observado teve um único candidato. AP permanece a métrica que
selecionou o modelo, enquanto F1 seleciona somente o cutoff.

**Consequências:** no OOF pooled, precision, recall e F1 são 0,333301, 0,770456 e 0,465309,
contra 0,571368, 0,046595 e 0,086164 no cutoff de referência 0,5. O mesmo threshold foi
aplicado apenas como diagnóstico em 2022, 2023 e 2024. O XGBoost/configuração 4C,
preprocessing e features permanecem congelados; não houve treinamento, tuning, refit ou uso
de 2025. O próximo passo é a Fase 4G.

**Origem:** [PHASE_4F_THRESHOLD_SELECTION.md](PHASE_4F_THRESHOLD_SELECTION.md) e tabelas
`phase_4f_*` em `reports/tables/`.

**Status:** confirmada; 17 checks PASS e 0 FAIL.

### D016 — Materialização final antes da abertura de 2025

**Data:** 19/08/2026.

**Decisão:** refitar uma única vez o pipeline oficial 3E+4C em todo o desenvolvimento
2021–2024 e congelar a materialização resultante para a Fase 4H. O fit usou 270.095
ocorrências, 76.364 graves, 22 predictors e produziu 226 features transformadas; o XGBoost
completou 300/300 rounds.

**Justificativa:** modelo, hiperparâmetros, preprocessing, features e threshold já estavam
selecionados. O refit integral incorpora todo o desenvolvimento sem reabrir decisões e impede
novo treinamento após a futura abertura do holdout. O threshold `0.23723246157169342` foi
somente lido e registrado.

**Consequências:** o pipeline está em
`artifacts/models/phase_4g_xgboost_final_pipeline.pkl`, com 1.204.426 bytes e SHA-256
`c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351`. O binário é local e
ignorado pelo Git. A 4H deverá verificar esse SHA antes de desserializar e usar o mesmo objeto
sem fit adicional. Não houve tuning, early stopping, métrica in-sample, transformação,
predição ou avaliação de 2025.

**Origem:** [PHASE_4G_FINAL_REFIT.md](PHASE_4G_FINAL_REFIT.md) e tabelas `phase_4g_*` em
`reports/tables/`.

**Status:** confirmada; 16 checks PASS e 0 FAIL.

### D017 — Abertura única do holdout temporal de 2025

**Data:** 19/08/2026.

**Decisão:** avaliar uma única vez o pipeline 4G congelado sobre 2025, depois de validar seu
SHA-256, sem fit, tuning, calibração, alteração de predictors, preprocessing, modelo ou
threshold. O cutoff `0.23723246157169342` permaneceu o operacional; 0,5 foi calculado apenas
como referência descritiva.

**Justificativa:** 2025 é o teste temporal final e não participou da seleção do modelo, do
threshold ou do refit. Embora já tivesse sido usado em EDA e drift estrutural, sua performance
preditiva permaneceu fora de todas as decisões congeladas em 4E–4G.

**Consequências:** a avaliação contém 72.529 IDs, 20.493 graves e 52.036 não graves. A AP foi
`0.3974456687131155`, a ROC-AUC `0.6285562620583193` e o Brier
`0.19382199321256413`. No threshold congelado, precision, recall e F1 foram
`0.33159329140461213`, `0.7718245254477138` e `0.4638892554954321`. O desempenho observado
em 2025 foi utilizado exclusivamente para avaliação temporal final e não motivou alteração do
modelo, hiperparâmetros, conjunto de atributos, pré-processamento ou limiar de decisão.

**Origem:** [PHASE_4H_FINAL_EVALUATION.md](PHASE_4H_FINAL_EVALUATION.md) e tabelas
`phase_4h_*` em `reports/tables/`.

**Status:** confirmada; 25 checks PASS e 0 FAIL. Próximo passo: Fase 4I.

### D018 — Interpretação pós-avaliação sem reabertura experimental

**Data:** 19/08/2026.

**Decisão:** interpretar o pipeline final sobre as 72.529 ocorrências de 2025 por contribuições
Tree SHAP nativas do XGBoost (`pred_contribs=True`), na escala de margem bruta, agregando as
226 features em 22 predictors e reutilizando as decisões congeladas da 4H para TP/FP/FN/TN.

**Justificativa:** a avaliação final já estava concluída. A interpretação deve explicar quais
informações o modelo utilizou sem produzir nova avaliação, fit, tuning, calibrador, threshold
ou seleção de features. A identidade aditiva foi reconciliada com as probabilities 4H com erro
máximo `4.0788276994829786e-07`, abaixo da tolerância explícita de `1e-6`.

**Consequências:** `uf`, `tipo_pista`, `hour`, `br` e `condicao_metereologica` foram os cinco
predictors de maior contribuição absoluta média. O ranking é interpretativo, multivariado e
não causal. Modelo, preprocessing, features, hiperparâmetros, threshold e predictions 4H
permaneceram inalterados.

**Origem:** [PHASE_4I_FINAL_INTERPRETATION.md](PHASE_4I_FINAL_INTERPRETATION.md) e tabelas
`phase_4i_*` em `reports/tables/`.

**Status:** confirmada; 25 checks PASS e 0 FAIL. Próximo passo: consolidar as perguntas de
pesquisa e mapear cada pergunta às evidências produzidas nas Fases 2–4.

### D019 — Congelamento das perguntas de pesquisa e de seu mapa de evidências

**Data:** 19/08/2026.

**Decisão:** consolidar uma pergunta principal e exatamente cinco perguntas específicas,
definindo para cada uma método, evidências versionadas, resposta curta e limitações. A Fase 2
responde primariamente RQ1; as Fases 3–4 respondem RQ2–RQ5; a interpretação 4I é suporte e não
origina uma pergunta post hoc.

**Justificativa:** a modelagem e a avaliação final já estavam encerradas. A redação científica
precisa de rastreabilidade entre perguntas e resultados sem recalcular o experimento ou
selecionar evidências apenas por conveniência narrativa.

**Consequências:** foram materializadas cinco respostas, 22 evidências selecionadas, 12
achados centrais e dez limitações mínimas. Evidência descritiva, preditiva, temporal, final e
interpretativa permanecem semanticamente separadas. Nenhum modelo, score, threshold, teste
estatístico ou artefato das Fases 2–4 foi alterado.

**Origem:** [PHASE_5A_RESEARCH_QUESTION_SYNTHESIS.md](PHASE_5A_RESEARCH_QUESTION_SYNTHESIS.md)
e tabelas `phase_5a_*` em `reports/tables/`.

**Status:** confirmada; 20 checks PASS e 0 FAIL. Próximo passo: selecionar evidências, tabelas
e figuras para os capítulos de Resultados e Discussão.

### D020 — Congelamento do plano de tabelas e figuras finais

**Data:** 19/08/2026.

**Decisão:** inventariar 19 candidatos e classificá-los em sete `ESSENTIAL`, dois `USEFUL`,
quatro `APPENDIX`, quatro `REPOSITORY_ONLY` e dois `ESSENTIAL_METHODS`. Para o corpo e os
métodos, recomendar três tabelas e oito figuras; sob restrição de espaço, a figura de
calibração pode ser removida, reduzindo o núcleo a sete figuras. Quatro itens permanecem
planejados para o apêndice.

**Justificativa:** a apresentação final deve responder às cinco perguntas com rastreabilidade,
sem multiplicar gráficos redundantes nem transportar artefatos técnicos para o texto
científico. O plano separa volume de proporção, métodos de resultados, evidência descritiva de
interpretação causal e corpo principal de material suplementar.

**Consequências:** cada item selecionado recebeu fonte, seção, mensagem, cautela e especificação
de produção futura. Nenhuma figura foi criada e nenhum resultado das Fases 2–4 foi recalculado.
Para uma eventual Fase 6, ficam registrados Next.js, React e TypeScript, arquitetura 100%
estática com JSON produzido pelo pipeline Python, filtros no cliente e hospedagem na Vercel;
resultados congelados de modelagem serão apenas apresentados, nunca recalculados no dashboard.

**Origem:** [PHASE_5B_RESULTS_VISUAL_PLAN.md](PHASE_5B_RESULTS_VISUAL_PLAN.md) e tabelas
`phase_5b_*` em `reports/tables/`.

**Status:** confirmada; 23 checks PASS e 0 FAIL. Próximo passo: Fase 5C — estruturar os
capítulos de Resultados e Discussão conforme o plano congelado.

### D021 — Separação estrutural entre Resultados e Discussão

**Data:** 19/08/2026.

**Decisão:** organizar o roteiro acadêmico em dez subseções planejadas de Resultados e oito de
Discussão. Resultados apresenta observações, métricas e comparações; Discussão integra os
achados, examina limites e trata significado metodológico sem repetir tabelas e figuras.

**Justificativa:** as cinco RQs e o plano visual já estavam congelados, mas a redação final
precisa de fronteiras explícitas entre evidência e interpretação. Cada subseção recebeu
objetivo, RQ, fonte, visual, números, mensagem, cautela e transição. F8 fica no final de
Resultados para apresentar o ranking e é retomada em Discussão somente para interpretar sua
convergência parcial com a EDA; F7 permanece opcional e M1/M2 continuam na Metodologia.

**Consequências:** foram materializados um mapa de 18 subseções, 27 vínculos de evidência, 66
números publicados e uma política editorial de arredondamento. Pontos que exigem literatura
foram marcados sem inventar referências. Nenhuma análise, figura ou redação integral do
manuscrito foi produzida; a arquitetura estática planejada para a Fase 6 permanece inalterada.

**Origem:** [PHASE_5C_RESULTS_DISCUSSION_STRUCTURE.md](PHASE_5C_RESULTS_DISCUSSION_STRUCTURE.md)
e tabelas `phase_5c_*` em `reports/tables/`.

**Status:** confirmada; 26 checks PASS e 0 FAIL. Próximo passo: Fase 5D — gerar as figuras e
tabelas acadêmicas selecionadas.

## Resultados consolidados

### R001 — Dimensão do dataset

**Resultado:** 342.624 ocorrências entre 2021 e 2025, com 30 colunas nas fontes RAW e 32
colunas no dataset interim.

**Status:** confirmado.

**Origem:** [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### R002 — Distribuição do target

**Resultado:** 96.857 ocorrências graves e 245.767 não graves, correspondendo a uma taxa de
graves de 28,2692%.

**Derivação:** a quantidade de não graves é a diferença já conhecida
`342.624 - 96.857 = 245.767`.

**Status:** confirmado.

**Origem:** auditoria e [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### R003 — Integridade

**Resultado:** zero IDs duplicados, zero falhas em
`feridos = feridos_leves + feridos_graves` e cinco fontes RAW verificadas contra o baseline de
referência do projeto.

**Status:** confirmado.

**Origem:** auditoria e comando `prf-verify-interim`, documentados em
[PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### R004 — Anomalias preservadas

**Resultado:** 18.538 divergências na decomposição de `pessoas`, 883 registros com `br = 0` e
1.652 registros com `km = 0`.

**Interpretação metodológica:** são métricas de qualidade não bloqueantes. Nenhum desses
registros foi corrigido ou removido na fundação de dados.

**Status:** confirmado.

**Origem:** auditoria e [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### R005 — Drift descritivo das features

**Data:** 19/08/2026.

**População e período:** 342.624 ocorrências; desenvolvimento planejado 2021–2024 comparado a
2025, sem criação física de split.

**Resultado:** as maiores TVDs categóricas foram observadas em `municipio` (0,089805),
`tracado_via` (0,082051) e `causa_acidente` (0,079368). Entre as contínuas, com decis
definidos apenas no desenvolvimento, `longitude` apresentou a maior TVD (0,019970). Cinco
variáveis tiveram categorias não vistas em 2025, sempre com participação agregada inferior a
0,3% por variável.

**Método/origem:** [PHASE_3A_TEMPORAL_DRIFT.md](PHASE_3A_TEMPORAL_DRIFT.md) e tabelas
`phase_3a_*` em `reports/tables/`.

**Limitações:** magnitudes descritivas não medem causalidade, relevância preditiva ou impacto
em desempenho de modelo; taxonomias não foram harmonizadas.

**Possível uso no TCC:** justificar políticas de categorias desconhecidas e decisões de
representação antes da preparação de dados.

**Status:** confirmado.

### R006 — Primeira modelagem: Regressão Logística baseline

**Data:** 19/08/2026.

**População e período:** três folds temporais internos, com fit progressivo em 2021–2023 e
validações separadas em 2022, 2023 e 2024. Nenhuma predição ou métrica de 2025 foi consultada.

**Método:** pipeline train-only da Fase 3E seguido por `LogisticRegression` com
`solver="newton-cholesky"`, `C=1.0`, `l1_ratio=0.0`, `class_weight=None`, intercepto, tolerância
`1e-4` e `max_iter=500`. A configuração foi única, sem tuning.

**Resultado:** as APs foram 0,386681, 0,396058 e 0,397786. A média aritmética não ponderada foi
0,393508 e o desvio padrão populacional, 0,004879. Os três folds convergiram em três iterações.
ROC-AUC, Brier, métricas no corte fixo 0,5 e calibração foram registrados como diagnósticos;
nenhum threshold foi selecionado.

**Limitações:** trata-se de uma baseline linear e não de modelo vencedor. O corte 0,5 é apenas
referência, o resultado não é causal e 2025 continua reservado ao pipeline final congelado.

**Origem:** [PHASE_4A_LOGISTIC_BASELINE.md](PHASE_4A_LOGISTIC_BASELINE.md) e tabelas
`phase_4a_logistic_*` em `reports/tables/`.

**Status:** confirmado; primeira baseline executada sem refit final ou consulta a 2025.

### R007 — Random Forest baseline

**Data:** 19/08/2026.

**População e período:** três folds temporais internos, com fit progressivo em 2021–2023 e
validações separadas em 2022, 2023 e 2024. Nenhuma transformação, predição ou métrica de 2025
foi realizada.

**Método:** pipeline train-only da Fase 3E seguido por `RandomForestClassifier` com 300
árvores, Gini, profundidade máxima 20, `min_samples_leaf=5`, `max_features="sqrt"`, bootstrap,
`random_state=42`, `n_jobs=-1`, sem pesos de classe e sem OOB. A configuração foi única e
congelada, sem tuning.

**Resultado:** as APs foram 0,388096, 0,399673 e 0,400183. A média aritmética não ponderada foi
0,395984 e o desvio padrão populacional, 0,005582. As 300 árvores de cada fold atingiram
profundidade máxima 20; as médias de nós foram 1.862,927, 2.775,713 e 3.592,353. ROC-AUC,
Brier, métricas no corte fixo 0,5 e calibração foram registrados como diagnósticos; nenhum
threshold foi selecionado.

**Auditoria de reprodutibilidade:** duas reexecuções preservaram exatamente IDs, targets,
folds e anos. Entre 205.528 probabilidades, 89.588 não foram bitwise idênticas;
`max_abs_difference=3.3306690738754696e-16`,
`mean_abs_difference=2.4697206337636872e-17`, percentil 99 absoluto de
`1.1102230246251565e-16` e `RMSE=4.0536620258397663e-17`. AP, ROC-AUC e Brier foram
exatamente iguais em todos os folds, a AP média foi exatamente igual e zero decisões no
corte 0,5 mudaram.

**Limitações:** trata-se de uma baseline não otimizada, não de modelo vencedor. A estrutura
das árvores é diagnóstico, não regra de seleção; não houve interpretação de importância de
features, refit final ou consulta a 2025. A variação observada é compatível com ruído numérico
de ponto flutuante na execução paralela, não com divergência preditiva substantiva. O SHA-256
identifica uma materialização específica do OOF; equivalência científica entre reexecuções
paralelas não exige Parquets bitwise idênticos e deve considerar estrutura, targets,
probabilidades numericamente equivalentes e métricas reproduzidas. Os hashes históricos não
são substituídos.

**Origem:** [PHASE_4B_RANDOM_FOREST.md](PHASE_4B_RANDOM_FOREST.md) e tabelas
`phase_4b_random_forest_*` em `reports/tables/`.

**Status:** confirmado; segunda baseline executada sem comparação formal entre modelos.

### R008 — XGBoost baseline

**Data:** 19/08/2026.

**População e período:** três folds temporais internos, com fit progressivo em 2021–2023 e
validações separadas em 2022, 2023 e 2024. Nenhuma transformação, predição ou métrica de 2025
foi realizada.

**Método:** pipeline train-only da Fase 3E seguido por XGBoost 3.3.0 com 300 árvores,
`learning_rate=0.05`, profundidade máxima 6, subamostragem de linhas e colunas em 0,8,
regularização L2 baseline, `tree_method="hist"` e CPU. A configuração foi única e congelada,
sem tuning, reponderação de classe ou early stopping.

**Resultado:** as APs foram 0,390375, 0,404968 e 0,407090. A média aritmética não ponderada foi
0,400811 e o desvio padrão populacional, 0,007430. Os três Boosters completaram exatamente
300 rounds. ROC-AUC, Brier, métricas no corte fixo 0,5 e calibração foram registrados como
diagnósticos; nenhum threshold foi selecionado.

**Limitações:** trata-se de uma baseline não otimizada, não de modelo vencedor. Não houve
interpretação de importância de features, refit final ou consulta a 2025.

**Origem:** [PHASE_4C_XGBOOST.md](PHASE_4C_XGBOOST.md) e tabelas `phase_4c_xgboost_*` em
`reports/tables/`.

**Status:** confirmado; terceira família executada sem comparação formal entre modelos.

### R009 — Comparação temporal formal das três famílias

**Data:** 19/08/2026.

**População e período:** resultados publicados dos três folds internos, com validações em
2022, 2023 e 2024. Nenhum dataset, OOF ou resultado de 2025 foi consultado.

**Método:** consolidação das tabelas versionadas de Logistic Regression, Random Forest e
XGBoost após validar folds, anos, tamanhos, prevalências, dimensões transformadas, métrica,
agregação e ausência de teste final ou threshold selecionado. Não houve retreinamento, teste
estatístico, score composto ou nova decisão baseada em OOF.

**Resultado:** as APs médias não ponderadas foram 0,393508 para Logistic Regression, 0,395984
para Random Forest e 0,400811 para XGBoost. Descritivamente, XGBoost apresentou a maior média
e a maior AP no Fold 3; Logistic Regression apresentou o menor desvio padrão populacional
(0,004879); Random Forest ficou intermediária em AP média. Os deltas médios foram 0,002476
de Logistic para Random Forest, 0,007303 de Logistic para XGBoost e 0,004827 de Random Forest
para XGBoost.

**Limitações:** os ranks e deltas organizam três folds observados e não demonstram
significância estatística, causalidade ou superioridade definitiva. A variação bitwise do OOF
paralelo da Random Forest não afeta as métricas reproduzidas nem esta comparabilidade.

**Origem:** [PHASE_4D_MODEL_COMPARISON.md](PHASE_4D_MODEL_COMPARISON.md) e tabelas
`phase_4d_*` em `reports/tables/`.

**Status:** confirmado; comparação descritiva concluída. A seleção posterior está registrada
na decisão D014.

### R010 — Threshold OOF do modelo selecionado

**Data:** 19/08/2026.

**População e período:** 205.528 previsões OOF e IDs únicos do XGBoost, exclusivamente das
validações temporais de 2022, 2023 e 2024. A materialização usada possui SHA-256
`28925211b1542c2c7965b8b45cd6b5f360389f200ea197de57f9068f777a6bdb`.

**Método:** busca `O(n log n)` sobre 202.207 probabilidades únicas, agrupando scores iguais e
acumulando a matriz de confusão. F1 foi comparado por frações inteiras, sem grid, tolerância
de empate ou inclusão especial do cutoff 0,5.

**Resultado:** o threshold `0.23723246157169342` obteve precision 0,33330114898136526,
recall 0,7704563403495519 e F1 0,46530870405989, com TN=57.517, FP=89.765, FN=13.370 e
TP=44.876. Em 0,5, precision=0,5713684210526315, recall=0,04659547436733853 e
F1=0,08616420090164455. Os F1 anuais no cutoff congelado foram 0,463337 em 2022, 0,466830
em 2023 e 0,465596 em 2024.

**Limitações:** o cutoff é ótimo apenas segundo F1 no OOF temporal de desenvolvimento e não
incorpora custos operacionais nem garante validade universal. A perda de precision e o aumento
de falsos positivos devem ser considerados na interpretação futura. Nenhum resultado de 2025
participou da decisão.

**Origem:** [PHASE_4F_THRESHOLD_SELECTION.md](PHASE_4F_THRESHOLD_SELECTION.md) e tabelas
`phase_4f_*` em `reports/tables/`.

**Status:** confirmado; threshold congelado para a próxima etapa.

### R011 — Refit final do pipeline selecionado

**Data:** 19/08/2026.

**População e período:** desenvolvimento completo 2021–2024, com 270.095 IDs únicos, 76.364
graves e 193.731 não graves; prevalência positiva de 0,2827301505026009. O conjunto entregue
ao fit não continha linhas de 2025.

**Método:** um único `fit` do pipeline formado pelo preprocessing 3E e pela factory XGBoost
4C, usando os 22 predictors físicos congelados. O preprocessor derivou 226 features e o
classifier completou 300/300 rounds, sem tuning, early stopping ou mudança de configuração.

**Resultado estrutural:** pipeline persistido com 1.204.426 bytes e SHA-256
`c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351`, sob Python 3.14.6,
scikit-learn 1.9.0, XGBoost 3.3.0 e Polars 1.43.2. O threshold 4F permaneceu exatamente
`0.23723246157169342`.

**Limitações:** a Fase 4G não avaliou capacidade preditiva e não calculou métricas no treino.
O pickle deve ser carregado apenas se produzido pelo projeto, considerado confiável e validado
pelo SHA registrado. O hash identifica esta materialização, não equivalência universal entre
resserializações.

**Origem:** [PHASE_4G_FINAL_REFIT.md](PHASE_4G_FINAL_REFIT.md) e tabelas `phase_4g_*` em
`reports/tables/`.

**Status:** confirmado; pipeline congelado para a avaliação final 4H, sem uso de 2025.

### R012 — Avaliação temporal final em 2025

**Data:** 19/08/2026.

**População e período:** 72.529 ocorrências e IDs únicos de 2025, sendo 20.493 graves e
52.036 não graves, com prevalência positiva de `0.2825490493457789`.

**Método:** carregamento do pipeline 4G somente após confirmação do SHA-256
`c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351`; uma única coleção de
probabilidades, sem fit, tuning ou calibrador. AP foi a métrica primária, ROC-AUC e Brier foram
secundárias, e o threshold 4F foi aplicado sem alteração.

**Resultado:** AP=`0.3974456687131155`, ROC-AUC=`0.6285562620583193` e
Brier=`0.19382199321256413`. No threshold congelado, precision=`0.33159329140461213`,
recall=`0.7718245254477138` e F1=`0.4638892554954321`, com TN=20.153, FP=31.883, FN=4.676 e
TP=15.817. Os deltas contra a média interna foram -0,003365 em AP, -0,002294 em ROC-AUC e
-0,000075 em Brier; o delta de F1 contra o OOF foi -0,001419. São comparações descritivas.

**Limitações:** 2025 não foi estruturalmente cego à EDA e ao drift, cobre apenas um ano
posterior e não sustenta inferência causal. O modelo estima gravidade entre ocorrências já
registradas, não risco de ocorrência de acidente. Nenhuma decisão foi reaberta após o
resultado.

**Origem:** [PHASE_4H_FINAL_EVALUATION.md](PHASE_4H_FINAL_EVALUATION.md),
`phase_4h_final_evaluation.csv` e demais tabelas `phase_4h_*`.

**Status:** confirmado; avaliação final concluída e predições congeladas para a Fase 4I.

### R013 — Contribuições do modelo e distribuição dos erros em 2025

**Data:** 19/08/2026.

**População e método:** 72.529 ocorrências de 2025, após a avaliação final, interpretadas com
Tree SHAP nativo para 226 features transformadas e agregadas em 22 predictors. As contribuições
são aditivas na margem bruta e reconciliaram com as probabilidades oficiais com erro absoluto
máximo de `4.0788276994829786e-07` e médio de `8.79821110029995e-08`.

**Resultado:** as contribuições absolutas médias foram 0,309141 para `uf`, 0,215640 para
`tipo_pista`, 0,215379 para `hour`, 0,115351 para `br` e 0,069935 para
`condicao_metereologica`. Entre features transformadas, destacaram-se `tipo_pista_Simples`,
`km`, `uf_RJ`, `uf_RS` e `uf_SP`. As decisões congeladas mantiveram TP=15.817, FP=31.883,
FN=4.676 e TN=20.153; as medianas de score foram 0,331816, 0,307983, 0,204486 e 0,195533,
respectivamente.

**Interpretação e limitações:** `uf`, `tipo_pista` e `hour` também haviam apresentado variação
descritiva na EDA, mas a convergência não confirma causalidade. O ranking pode diferir de
associações univariadas por interações, não linearidades, redundância, cardinalidade e
composição da população. A base contém somente ocorrências registradas e não estima risco de
ocorrência de acidente.

**Origem:** [PHASE_4I_FINAL_INTERPRETATION.md](PHASE_4I_FINAL_INTERPRETATION.md),
`phase_4i_global_feature_contributions.csv`, `phase_4i_transformed_feature_contributions.csv`
e `phase_4i_error_analysis.csv`.

**Status:** confirmado; interpretação pós-avaliação concluída sem alteração retrospectiva.

## Perguntas de pesquisa consolidadas

**Pergunta principal:** Quais características temporais, geográficas, meteorológicas e viárias
estão associadas à gravidade dos acidentes registrados em rodovias federais brasileiras e em
que medida modelos de aprendizado de máquina conseguem identificar ocorrências graves?

| Pergunta | Fase principal | Resposta curta |
|---|---|---|
| RQ1 — Quais características estão associadas a maiores proporções de acidentes graves entre as ocorrências registradas pela PRF? | Fase 2 — EDA | Houve heterogeneidade temporal, geográfica, meteorológica e viária, incluindo noite/fim de semana, Nordeste/UFs, condições informadas e pista Simples; são associações não causais e sem denominador de exposição. |
| RQ2 — Em que medida características disponíveis no momento inicial da ocorrência permitem distinguir acidentes graves dos não graves? | 3B e 4A–4C/4H | Existe sinal preditivo moderado; em 2025, AP foi 0,397446 e ROC-AUC 0,628556, enquanto o threshold priorizou recall 0,771825 com precision 0,331593. |
| RQ3 — Como Regressão Logística, Random Forest e XGBoost se comparam em validação temporal? | 4A–4E | XGBoost apresentou a maior AP média, seguido por Random Forest e Logística, mas os ganhos absolutos foram pequenos e incrementais. |
| RQ4 — O desempenho preditivo permanece consistente entre diferentes anos de validação? | 3D e 4D | As três famílias apresentaram APs mais elevadas nos folds posteriores, sem queda abrupta ou colapso; como o período de treino também cresce, a sequência não demonstra tendência de melhora. |
| RQ5 — O modelo selecionado mantém desempenho em um período temporal posterior, reservado para avaliação final em 2025? | 4G e 4H | Sim, aproximadamente: AP, ROC-AUC, Brier e métricas do threshold ficaram próximas das referências internas, sem ajuste baseado em 2025. |

O mapeamento integral de métodos, evidências, resultados e limitações está em
[PHASE_5A_RESEARCH_QUESTION_SYNTHESIS.md](PHASE_5A_RESEARCH_QUESTION_SYNTHESIS.md). A Fase 4I
permanece evidência complementar para compreender o XGBoost e não constitui RQ6.

## Achados exploratórios

### EDA001 — Distribuição anual do volume

Entre as 342.624 ocorrências registradas, os totais anuais variaram de 64.567 em 2021 a 73.156
em 2024. O volume ficou praticamente estável em 2022 (+0,0604%), cresceu em 2023 (+4,8912%) e
2024 (+7,9538%) e recuou discretamente em 2025 (-0,8571%). O resultado descreve a composição
da base e não mede exposição ao tráfego ou risco de acidente.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA001](EDA_FINDINGS.md#eda001--distribuição-anual-do-volume-de-ocorrências-registradas).

### EDA002 — Estabilidade descritiva do target

A proporção anual de ocorrências graves permaneceu entre 28,0608% e 28,4943%, com amplitude
de 0,4335 ponto percentual. A média anual simples foi 28,2707%, enquanto a taxa global
ponderada pelos registros foi 28,2692%. A proximidade é descritiva e não substitui avaliação
inferencial futura.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA002](EDA_FINDINGS.md#eda002--estabilidade-descritiva-da-proporção-anual-de-ocorrências-graves).

### EDA003 — Qualidade analítica básica

Somente `classificacao_acidente`, `regional`, `delegacia` e `uop` apresentaram nulos, todos
com proporções inferiores a 0,1% por coluna. Foram preservados 883 registros `Não Informado`
em `sentido_via` e 4.492 registros `Ignorado` em `condicao_metereologica`; essas categorias
não foram convertidas para nulo.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA003](EDA_FINDINGS.md#eda003--nulidade-e-categorias-especiais-preservadas).

### EDA004 — Cardinalidade categórica

As maiores cardinalidades entre as variáveis categóricas avaliadas ocorreram em `municipio`
(2.050), `tracado_via` (1.214), `uop` (408), `delegacia` (155) e `causa_acidente` (76). Esse
resultado orienta decisões futuras de apresentação e codificação, mas não mede relevância ou
capacidade preditiva.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA004](EDA_FINDINGS.md#eda004--cardinalidade-das-principais-variáveis-categóricas).

### EDA007 — Concentração temporal no fim de semana

Sábado e domingo reuniram 112.389 ocorrências, das quais 33.933 foram graves (30,1925%),
enquanto os dias úteis reuniram 230.235 ocorrências e 62.924 graves (27,3303%). Domingo
liderou a proporção grave em quatro dos cinco anos e sábado em 2025. A diferença é descritiva,
condicionada às ocorrências registradas, e não mede exposição ou causalidade.

**Relevância:** caracteriza uma associação temporal diretamente ligada à pergunta da pesquisa
e recomenda avaliar calendário e estabilidade anual na modelagem futura.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA007](EDA_FINDINGS.md#eda007--concentração-no-fim-de-semana-e-proporção-de-graves).

### EDA008 — Padrão horário de volume e gravidade

18h concentrou o maior volume em todos os cinco anos (25.569 registros no consolidado). A
proporção de graves variou de 23,1243% às 8h a 33,7323% às 19h; a maior taxa anual alternou
entre 19h e 21h. Cada destaque de taxa foi examinado com seu tamanho amostral, sem usar fluxo
veicular como denominador.

**Relevância:** a recorrência do padrão e a variação anual apoiam a avaliação futura de hora
como feature, sujeita a análise de drift e disponibilidade.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA008](EDA_FINDINGS.md#eda008--padrão-horário-de-volume-e-gravidade).

### EDA009 — Fase do dia e proporção de graves

`Pleno dia` concentrou 187.621 registros e apresentou 25,3047% de graves. `Plena Noite`
reuniu 119.581 registros e apresentou 32,4726% de graves, liderando essa proporção em cada um
dos cinco anos. O resultado é uma associação descritiva e não demonstra efeito causal da
fase do dia.

**Relevância:** é pertinente à discussão da pesquisa e à futura avaliação de redundância entre
`fase_dia` e hora.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA009](EDA_FINDINGS.md#eda009--distribuição-por-fase-do-dia).

### EDA010 — Estabilidade descritiva dos padrões temporais

Dezembro liderou o volume mensal, 18h o volume horário, `Pleno dia` o volume por fase e
`Plena Noite` a proporção grave por fase nos cinco anos. Em contraste, o mês de maior taxa
variou entre quatro categorias e a hora de maior taxa alternou entre 19h e 21h. As amplitudes
anuais foram registradas sem limiar arbitrário de classificação.

**Relevância:** fornece evidência metodológica para preservar validação temporal e avaliar
drift por variável antes da modelagem.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA010](EDA_FINDINGS.md#eda010--recorrência-e-variação-dos-padrões-temporais-entre-anos).

### EDA011 — Desigualdade geográfica descritiva por macrorregião

Sudeste concentrou 107.259 ocorrências registradas (31,3052% do dataset), enquanto Nordeste
apresentou a maior proporção grave, 26.662 em 74.232 registros (35,9171%). Sul apresentou
24,8740%. Nordeste liderou a taxa em quatro anos e Norte em 2023. Volume e composição de
gravidade são dimensões distintas e não representam exposição rodoviária.

**Relevância:** o contraste macrorregional se relaciona diretamente à pergunta da pesquisa e
indica que geografia deverá ser considerada com validação temporal e linguagem não causal.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA011](EDA_FINDINGS.md#eda011--distribuição-e-gravidade-por-macrorregião).

### EDA012 — Heterogeneidade estadual de volume e gravidade

MG liderou o volume nos cinco anos e somou 44.502 registros. MA apresentou 2.647 graves em
5.778 registros (45,8117%), a maior taxa consolidada, e liderou em quatro anos; PA liderou em
2022. SP apresentou 4.288 graves em 23.005 registros (18,6394%). As diferenças são
condicionadas às ocorrências registradas e não permitem classificar risco estadual.

**Relevância:** UF é uma candidata importante para análise associativa e eventual modelagem,
mas exigirá tratamento categórico e avaliação de generalização temporal.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA012](EDA_FINDINGS.md#eda012--concentração-e-proporção-de-graves-por-uf).

### EDA013 — Variação anual das taxas estaduais

As amplitudes anuais variaram de 0,9389 ponto percentual no RS a 17,9409 em RR. MG, líder de
volume, variou 1,0856 ponto, enquanto MA variou 8,0007. Não foi aplicado limiar automático de
estabilidade, e tamanho amostral deverá acompanhar qualquer interpretação de taxa estadual.

**Relevância:** o resultado reforça H001 e afeta a futura estratégia de validação temporal de
features geográficas.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA013](EDA_FINDINGS.md#eda013--amplitude-anual-da-proporção-de-graves-por-uf).

### EDA015 — Alta cardinalidade e chave municipal composta

Foram observados 2.098 pares `uf + municipio` para 2.050 nomes municipais distintos. As 48
combinações excedentes mostram que município isolado não é uma chave geográfica suficiente.
Brasília/DF concentrou o maior volume, com 4.948 registros, mas nenhuma tabela município × ano
foi criada por parcimônia.

**Relevância:** a cardinalidade e a necessidade da chave composta afetam preparação,
codificação e validação de variáveis em fases futuras.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA015](EDA_FINDINGS.md#eda015--concentração-municipal-com-chave-uf--município).

### EDA016 — Controle editorial de pequenas amostras geográficas

Os rankings de taxa de BR e município foram restritos a categorias com pelo menos 500
registros, sem excluir categorias das tabelas completas. Seriam elegíveis 99/62/47 BRs e
763/157/59 municípios nos cortes 100/500/1000, respectivamente. A categoria municipal líder
muda quando o corte passa de 500 para 1000, evidenciando sensibilidade ao critério.

**Relevância:** documenta uma salvaguarda contra destaques de taxas em grupos muito pequenos e
mostra que o limiar é editorial, não universal ou científico.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA016](EDA_FINDINGS.md#eda016--destaques-de-taxa-com-critério-editorial-de-amostra).

### EDA018 — Contraste persistente por tipo de pista

Pista Simples concentrou 167.198 registros e apresentou 56.365 graves (33,7115%), ante
23,3513% em Dupla e 21,8680% em Múltipla. Simples manteve a maior proporção nos cinco anos,
com amplitude de 0,8746 ponto percentual.

**Relevância:** o contraste é recorrente e diretamente relacionado às características da via,
mas exige futura análise multivariada, sem interpretação causal ou de risco absoluto.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA018](EDA_FINDINGS.md#eda018--tipo-de-pista-e-proporção-de-ocorrências-graves).

### EDA021 — Meteorologia requer leitura conjunta de taxa e amostra

`Ignorado` apresentou 34,5503% de graves em 4.492 registros, mas caracteriza ausência
semântica e não uma condição meteorológica observada. Entre condições informadas com pelo
menos 500 registros, Nevoeiro/Neblina apresentou 31,5011% e Vento 31,3659%. Granizo (n=11)
e Neve (n=8) foram mantidos na tabela completa, mas excluídos dos destaques pelo tamanho.

**Relevância:** documenta que categorias raras e desconhecidas exigem cautela, separa ausência
de informação de condições observadas e exige tamanho amostral em toda comparação.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA021](EDA_FINDINGS.md#eda021--condição-meteorológica-tamanho-amostral-e-categorias-raras).

### EDA022 — Representação multivalorada de traçado da via

Foram confirmados 12 componentes básicos em `tracado_via`. Reta ocorreu em 241.869 registros,
Curva em 62.755 e Declive em 32.735. As contagens somaram 418.561 porque uma ocorrência pode
conter vários componentes; portanto, elas não são mutuamente exclusivas.

**Relevância:** o campo não deve ser tratado como aproximadamente 1.214 categorias completas
independentes. Sua eventual preparação deverá preservar a natureza multirrótulo e evitar
chamar o percentual de cada componente de participação exclusiva.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA022](EDA_FINDINGS.md#eda022--componentes-multivalorados-de-traçado-da-via).

### EDA023 — Recorrência temporal em categorias volumosas de via e ambiente

Simples liderou tipo de pista e `Não` liderou uso do solo em todos os anos. Categorias
volumosas como Céu Claro, Nublado, Chuva e Reta apresentaram amplitudes anuais entre 0,5941 e
1,3658 ponto percentual, enquanto categorias raras foram substancialmente mais variáveis.

**Relevância:** reforça que estabilidade temporal e tamanho amostral deverão ser avaliados
conjuntamente; recorrência descritiva não garante ausência de drift nem estabilidade futura.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA023](EDA_FINDINGS.md#eda023--estabilidade-descritiva-das-dimensões-de-via-e-ambiente).

### EDA024 — Tipo de acidente separa volume e proporção grave

Colisão traseira concentrou 65.634 registros, enquanto Atropelamento de Pedestre apresentou a
maior proporção entre tipos com n≥500: 10.416 graves em 15.313 registros (68,0206%), seguido
de Colisão frontal (63,0592%). Ambos estiveram nos cinco anos e tiveram amplitudes anuais de
1,6144 e 1,2550 ponto percentual.

**Relevância:** os contrastes são persistentes e relacionados à dinâmica, mas o tipo pode ser
conhecido ou consolidado após a ocorrência; aplica-se a separação EDA/modelagem da D005.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA024](EDA_FINDINGS.md#eda024--volume-e-gravidade-por-tipo-de-acidente-registrado).

### EDA025 — Causa registrada apresenta contrastes descritivos marcantes

Reação tardia ou ineficiente do condutor teve o maior volume (46.901). Entre categorias com
n≥500, Pedestre andava na pista apresentou 2.460 graves em 3.262 registros (75,4139%), e
Transitar na contramão, 6.713 em 11.145 (60,2333%). Essas categorias estiveram nos cinco anos.

**Relevância:** o campo possui associação descritiva forte com gravidade, mas é uma causa
registrada pela PRF, não causalidade científica demonstrada, e exige avaliação de leakage.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA025](EDA_FINDINGS.md#eda025--volume-e-gravidade-por-causa-registrada-pela-prf).

### EDA026 — Taxonomias variam no período

`tipo_acidente` teve 18 categorias na união, 16 presentes nos cinco anos e uma exclusiva de
um ano. `causa_acidente` teve 76 na união, 65 presentes nos cinco anos, uma exclusiva de um
ano, cinco com primeiro registro após 2021 e sete com último registro antes de 2025.

**Relevância:** comparações temporais e preparação futura deverão preservar ou tratar
explicitamente mudanças de rótulo; nenhuma harmonização foi feita nesta fase.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA026](EDA_FINDINGS.md#eda026--mudanças-observadas-nas-taxonomias-de-tipo-e-causa).

### EDA029 — Síntese das associações descritivas centrais

A Fase 2F consolidou oito comparações centrais. Os maiores contrastes foram Pedestre andava
na pista versus Reação tardia ou ineficiente do condutor (51,4847 pontos percentuais),
Atropelamento de Pedestre versus Colisão traseira (44,3469), Colisão frontal versus Colisão
traseira (39,3855) e Transitar na contramão versus Reação tardia ou ineficiente do condutor
(36,3042). Também foram centrais os contrastes de macrorregião, tipo de pista, fase do dia e
fim de semana. Todas as categorias focais foram observadas nos cinco anos. A comparação de
nove pessoas versus uma permaneceu como achado secundário, com os números preservados e a
ressalva de associação parcialmente mecânica com a definição do target.

**Relevância:** a síntese prioriza resultados para a escrita sem criar score, inferência
causal ou medida de risco absoluto. As diferenças permanecem condicionadas às ocorrências
registradas e sem denominador de exposição.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA029](EDA_FINDINGS.md#eda029--síntese-das-associações-descritivas-centrais-com-gravidade).

### EDA030 — Separação entre evidência descritiva e elegibilidade preditiva

A matriz conceitual classificou 13 variáveis como candidatas, cinco como candidatas com
cautela, quatro como dependentes de decisão metodológica, três como exclusões administrativas
e sete como exclusões por leakage. Tipo, causa, pessoas e veículos não foram automaticamente
promovidos; as mudanças taxonômicas do EDA026 e a relação mecânica de `pessoas` com o target
permanecem alertas explícitos. As 22 variáveis não excluídas foram inventariadas para futura
verificação de drift. Tanto `tracado_via` quanto seus componentes derivados exigem cautela; a
matriz de elegibilidade é a fonte autoritativa dos status, enquanto derivações puramente
analíticas e categorias de qualidade não recebem elegibilidade independente.

**Relevância:** relevância associativa e admissibilidade no momento preditivo são decisões
distintas. A matriz planeja uma etapa futura; nenhum dataset processed, feature, split ou
modelo foi criado.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA030](EDA_FINDINGS.md#eda030--achado-descritivo-e-elegibilidade-preditiva-são-decisões-separadas).

## Hipóteses

### H001 — Estabilidade temporal das features

**Data:** 18/08/2026.

**Hipótese metodológica:** a estabilidade da prevalência de `target_grave` observada na Fase
2A não implica estabilidade das distribuições das variáveis explicativas.

**Fundamentação:** a Fase 2B encontrou recorrência em alguns resumos temporais e variação em
outros. Isso não avalia as demais features nem demonstra ausência de drift.

**Como foi avaliada:** a Fase 3A comparou 2021–2024 com 2025 usando TVD categórica, bins
numéricos definidos somente no desenvolvimento, categorias não vistas, cobertura de
data/horário e prevalências multilabel. Foram observadas distribuições, cardinalidades e
suportes diferentes, sobretudo em município, traçado e causa, apesar da baixa variação anual
do target.

**Status:** apoiada por evidência descritiva; não submetida a teste inferencial e não
apresentada como hipótese estatística provada.

## Limitações

### L001 — Ausência de população exposta

**Limitação:** a base contém somente ocorrências registradas. Não contém o total de viagens,
veículos que trafegaram sem acidente ou veículo-quilômetro.

**Consequência:** o estudo não estima diretamente a probabilidade de ocorrer um acidente e não
deve interpretar proporções de gravidade como risco absoluto de trafegar em uma rodovia.

**Status:** ativa.

### L002 — Associação não implica causalidade

**Limitação:** diferenças observadas entre grupos não demonstram causalidade.

**Consequência:** resultados associativos devem usar linguagem compatível com o desenho
observacional e não causal.

**Status:** ativa.

### L003 — Variáveis determinadas após a ocorrência

**Limitação:** variáveis como `causa_acidente`, `tipo_acidente` e `pessoas` podem ser definidas
ou consolidadas durante ou após a ocorrência. Além disso, como `target_grave` vale verdadeiro
quando há ao menos um morto ou ferido grave na ocorrência, um número maior de pessoas oferece
mais oportunidades para satisfazer mecanicamente a definição do target.

**Consequência:** essas variáveis são úteis para EDA, mas exigirão avaliação específica de
disponibilidade temporal e leakage antes de eventual uso em ML. `pessoas` requer cautela
adicional: sua associação crescente com o target não deve ser tomada diretamente como efeito
causal nem como evidência suficiente para selecioná-la como feature.

**Status:** ativa.

### L004 — Qualidade dos registros

**Limitação:** existem categorias como `Ignorado` e `Não Informado`, além das inconsistências
conhecidas na decomposição de `pessoas`.

**Consequência:** categorias ausentes ou desconhecidas e inconsistências preservadas devem ser
explicitamente quantificadas e consideradas nas análises.

**Status:** ativa.

### L005 — Holdout temporal previamente explorado

**Limitação:** 2025 foi incluído na EDA 2021–2025 e na auditoria estrutural de drift da Fase
3A. Portanto, não constitui holdout completamente cego no sentido experimental mais estrito.

**Consequência:** a partir do congelamento da política 3B, nenhuma decisão poderá ser
otimizada por performance em 2025. Seleção posterior, vocabulários, imputações, scalers,
thresholds e hiperparâmetros deverão usar somente 2021–2024; 2025 ficará reservado à
avaliação final do pipeline congelado.

**Status:** ativa e explicitamente mitigada pelo protocolo temporal da Fase 3B.

## Figuras e tabelas associadas

As Fases 2A a 2F produziram figuras e tabelas versionadas em `reports/`. A Fase 2G consolidou
esses resultados em [PHASE_2_EDA_SYNTHESIS.md](PHASE_2_EDA_SYNTHESIS.md), no aceite formal e
em uma tabela editorial de decisões, sem executar nova EDA. Os artefatos científicos estão
associados aos IDs correspondentes em [EDA_FINDINGS.md](EDA_FINDINGS.md).

## Templates para registros futuros

### EDAxxx — Título

**Data:**

**Fase:**

**Pergunta:**

**População analisada:**

**Resultado absoluto:**

**Proporção/taxa:**

**Comparação:**

**Interpretação:**

**O que NÃO podemos concluir:**

**Limitações:**

**Figura:**

**Tabela:**

**Código/origem:**

**Possível uso no TCC:**

**Status:** provisório / confirmado / descartado.

### Dxxx — Título da decisão

**Data:**

**Decisão:**

**Justificativa:**

**Alternativas consideradas:**

**Consequências:**

**Origem:**

**Status:** proposta / confirmada / substituída.

### Hxxx — Título da hipótese

**Data:**

**Hipótese:**

**Fundamentação:**

**Como avaliar:**

**Status:** proposta / apoiada / não apoiada / inconclusiva.

### Lxxx — Título da limitação

**Descrição:**

**Consequência:**

**Mitigação possível:**

**Status:** ativa / mitigada / encerrada.

### Rxxx — Título do resultado consolidado

**Data:**

**População e período:**

**Resultado:**

**Método/origem:**

**Limitações:**

**Possível uso no TCC:**

**Status:** provisório / confirmado / substituído.
