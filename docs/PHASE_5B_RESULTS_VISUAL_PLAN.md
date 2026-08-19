# Fase 5B — Plano de tabelas e figuras

## 1. Objetivo

Selecionar um conjunto enxuto de tabelas e figuras que sustente a pergunta principal e as
cinco RQs consolidadas na Fase 5A. Esta fase organiza evidências publicadas; não recalcula
métricas, não executa análises e não cria figuras.

## 2. Princípios de seleção

- cada elemento deve responder uma RQ, esclarecer método ou apoiar uma limitação relevante;
- o corpo privilegia evidência científica, legibilidade e economia visual;
- detalhes necessários à auditoria, mas não à argumentação, permanecem no repositório;
- uma informação não recebe múltiplos gráficos sem ganho claro de compreensão;
- contagem, proporção, score probabilístico e decisão por threshold permanecem distintos;
- associação descritiva e contribuição preditiva não são causalidade;
- nenhuma figura deve sugerir risco de acidente, pois não há denominadores de exposição;
- tabelas com muitas categorias ou detalhes técnicos migram para apêndice ou repositório.

As prioridades usadas são `ESSENTIAL`, `USEFUL`, `APPENDIX`, `REPOSITORY_ONLY` e
`ESSENTIAL_METHODS`.

## 3. Relação com as perguntas de pesquisa

- **RQ1:** F1 e F2 sintetizam associações descritivas; T1 contextualiza população e target.
- **RQ2:** T2 resume capacidade preditiva; F6 mostra o efeito do threshold; F7 e F8 são apoio.
- **RQ3:** F4 compara a AP média; M1 mostra o desenho que sustenta a comparação.
- **RQ4:** F5 apresenta AP por fold; M1 explicita que treino e ano mudam simultaneamente.
- **RQ5:** T2 compara 2025 com desenvolvimento; F6 e F7 complementam decisão e calibração.
- **Pergunta principal:** a sequência T1 → F1/F2 → F4/F5 → T2/F6 integra descrição,
  capacidade preditiva, validação temporal e generalização final.

A interpretação 4I aparece somente como apoio à RQ2 e à Discussão; não constitui RQ6.

## 4. Tabelas essenciais

### T1 — Caracterização anual da população de ocorrências

- **RQ:** pergunta principal e RQ1.
- **Fonte:** `phase_2a_year_summary.csv`.
- **Campos:** ano, ocorrências, graves, não graves, prevalência grave e participação anual;
  incluir uma linha total 2021–2025 no layout futuro usando os valores já publicados.
- **Mensagem:** contextualizar 342.624 ocorrências e 96.857 graves, separando volume e taxa.
- **Localização:** início de Resultados.
- **Observação:** substitui um gráfico exclusivo da prevalência anual; deve indicar que se trata
  apenas de acidentes registrados.

### T2 — Avaliação temporal final em 2025 e comparação com desenvolvimento

- **RQ:** RQ2 e RQ5.
- **Fontes:** `phase_4h_final_evaluation.csv` e `phase_4h_development_comparison.csv`.
- **Campos:** AP, ROC-AUC, Brier, precision, recall, F1, referência de desenvolvimento e delta.
- **Mensagem:** o desempenho 2025 ficou próximo das referências internas; o threshold prioriza
  recall.
- **Localização:** Resultados — avaliação final.
- **Observação:** não incluir todas as chaves do manifesto 4H nem duplicar a matriz de confusão.

O corpo de Resultados fica, portanto, com duas tabelas essenciais. A terceira tabela do núcleo
do manuscrito é metodológica (M2), descrita na seção 9.

## 5. Figuras essenciais

### F1 — Contrastes temporais e de calendário associados à gravidade

- **Tipo:** dot plot ou barras horizontais em três painéis independentes.
- **Eixo X:** proporção de ocorrências graves (%), escala comum de 0% a 100%.
- **Eixo Y:** categorias dentro de cada painel.
- **Unidade/séries:** Plena Noite/Pleno dia; fim de semana/dias úteis; 19h/8h.
- **Fonte:** `phase_2f_association_evidence_matrix.csv`.
- **Título provisório:** “Contrastes temporais observados na proporção de ocorrências graves”.
- **Legenda necessária:** proporções condicionadas aos registros; comparações descritivas.
- **Cautela:** painéis não devem ser lidos como categorias mutuamente comparáveis ou causais.
- **Anotação:** percentuais e `n` focal, sem estrelas de significância.

### F2 — Contrastes geográficos, viários e meteorológicos

- **Tipo:** dot plot em quatro facetas, não um ranking único.
- **Eixo X:** proporção grave (%), 0% a 100%.
- **Eixo Y:** duas categorias por faceta.
- **Facetas:** Nordeste/Sul; MA/SP; Simples/Dupla; Nevoeiro-Neblina/Garoa-Chuvisco.
- **Fonte:** `phase_2f_association_evidence_matrix.csv`.
- **Título provisório:** “Heterogeneidade descritiva em contextos geográficos, viários e
  meteorológicos”.
- **Legenda necessária:** facetas representam dimensões distintas; meteorologia usa condições
  informadas com `n >= 500`.
- **Cautela:** não usar mapa nem linguagem de risco; ausência de denominadores de exposição.
- **Anotação:** percentuais e tamanho focal.

### F4 — AP média por família de modelo

- **Tipo:** pontos ou barras simples.
- **Eixo X:** família do modelo.
- **Eixo Y:** AP média não ponderada, preferencialmente 0 a 1.
- **Séries:** Regressão Logística, Random Forest e XGBoost, com cores fixas reutilizadas.
- **Fonte:** `phase_4d_model_comparison.csv`.
- **Título provisório:** “Average Precision média nos três folds temporais”.
- **Legenda necessária:** média aritmética não ponderada; AP é a métrica primária.
- **Cautela:** diferenças são pequenas e não receberam teste post hoc.
- **Anotação:** valor exato com três ou quatro casas no gráfico e valor integral na tabela-fonte.

### F5 — AP por fold temporal e família

- **Tipo:** linhas e pontos por ano de validação.
- **Eixo X:** 2022, 2023 e 2024.
- **Eixo Y:** AP, escala coerente e não truncada de modo enganoso.
- **Séries:** as três famílias com as mesmas cores de F4.
- **Fonte:** `phase_4d_fold_comparison.csv`.
- **Título provisório:** “Average Precision por fold temporal”.
- **Legenda necessária:** janelas de treino crescem de 2021 até o ano anterior à validação.
- **Cautela:** APs mais elevadas nos folds posteriores não demonstram tendência temporal de
  melhora, pois período de treino e ano de validação mudam juntos.
- **Anotação:** valores por ponto, se mantida legibilidade.

### F6 — Matriz de confusão em 2025

- **Tipo:** matriz 2×2 textual/visual, com fundo claro e escala de cores discreta.
- **Eixos:** classe observada × classe predita.
- **Unidade:** contagens; TN=20.153, FP=31.883, FN=4.676 e TP=15.817.
- **Fonte:** `phase_4h_threshold_evaluation.csv`.
- **Título provisório:** “Decisões em 2025 no threshold congelado de 0,237232”.
- **Legenda necessária:** regra `probabilidade >= threshold`; threshold selecionado no OOF.
- **Cautela:** volumes absolutos não devem sugerir qualidade elevada; destacar recall alto e
  muitos falsos positivos.
- **Anotação:** quatro contagens e, fora da matriz, precision/recall/F1 publicados.

## 6. Figuras úteis

### F7 — Calibração descritiva em 2025

- **Tipo:** linha/pontos com diagonal de calibração perfeita como referência.
- **Eixo X:** probabilidade média por bin.
- **Eixo Y:** proporção observada de graves.
- **Unidade:** proporção de 0 a 1; dez bins quantis.
- **Fonte:** `phase_4h_calibration.csv`.
- **Título provisório:** “Calibração descritiva das probabilidades em 2025”.
- **Legenda:** bins quantis; nenhum calibrador foi ajustado.
- **Cautela:** diagnóstico pós-avaliação, sem modificar as probabilities.
- **Anotação:** dispensável se pontos e diagonal forem legíveis.

### F8 — Top predictors por contribuição absoluta agregada

- **Tipo:** barras horizontais ordenadas.
- **Eixo X:** `mean_abs_margin_contribution`.
- **Eixo Y:** top 8 predictors de origem.
- **Unidade:** contribuição absoluta média em margem bruta.
- **Fonte:** `phase_4i_global_feature_contributions.csv`.
- **Título provisório:** “Contribuição absoluta agregada para as predições do XGBoost”.
- **Legenda:** Tree SHAP nativo, população 2025, pós-avaliação.
- **Cautela:** não usar “fatores de risco”; cardinalidade varia e `br` agrega 125 colunas OHE.
- **Anotação:** magnitude ou share, usando somente um deles como eixo principal.

F7 e F8 entram se a extensão permitir sete figuras no corpo de Resultados/Discussão. Se houver
restrição severa, F8 tem prioridade narrativa sobre F7, enquanto a calibração permanece em
tabela técnica no repositório.

## 7. Apêndices

- **A1 — Top 15 features transformadas:** tabela curta derivada da tabela 4I já publicada;
  preserva detalhes sem expor 226 linhas.
- **A2 — Distribuição de scores por outcome:** figura diagnóstica de TP/FP/FN/TN, sem sugerir
  novo threshold.
- **A3 — Métricas completas por fold:** tabela com os nove pares modelo-fold e métricas
  secundárias.
- **A4 — Contrastes descritivos e cautelas:** tabela rastreável dos valores usados em F1/F2.

## 8. Elementos somente do repositório

- gráfico isolado de prevalência anual, por redundância com T1;
- inventário completo das 226 features transformadas;
- tabela exata dos dez bins de calibração;
- manifestos, hashes, checklists e relatórios de auditoria;
- gráficos técnicos de drift que sustentaram decisões metodológicas, mas não respondem
  diretamente às RQs finais.

Esses elementos continuam versionados ou preservados conforme sua política atual; apenas não
integram o texto acadêmico principal.

## 9. Elementos de metodologia

### M1 — Desenho temporal expanding-window

- **Tipo:** timeline/diagrama horizontal simples.
- **Eixo:** anos 2021–2025, sem eixo quantitativo.
- **Fluxos:** 2021→2022; 2021–2022→2023; 2021–2023→2024; refit 2021–2024→2025.
- **Fonte:** `phase_3d_temporal_folds.csv` e `phase_3d_partition_summary.csv`.
- **Título:** “Desenho temporal de desenvolvimento, validação e avaliação final”.
- **Legenda:** AP por fold; threshold apenas no OOF 2022–2024; 2025 somente teste final.
- **Cautela:** não apresentar 2025 como fold interno nem como fonte de otimização.
- **Anotação:** anos de treino/validação e número de observações, se legível.

### M2 — Conjunto principal de features e preprocessing

- **Tipo:** tabela metodológica compacta.
- **Campos:** grupo conceitual, representações, quantidade física, transformação e cautela.
- **Fonte:** `phase_3b_primary_feature_set.csv` e `phase_3e_preprocessing_contract.csv`.
- **Mensagem:** nove categóricas one-hot, `km` padronizado e 12 binárias de traçado, totalizando
  22 predictors físicos.
- **Cautela:** compatibilidade com o momento preditivo é premissa do estudo, não comprovação do
  instante operacional de preenchimento na PRF.

## 10. Redundâncias removidas

Não serão produzidos para o corpo principal:

- um gráfico independente para cada contraste da RQ1;
- gráfico anual de prevalência além de T1;
- mapas de UF/BR que possam sugerir risco sem exposição;
- tabela extensa de todas as associações;
- ranking integral das 226 features ou top níveis transformados no corpo;
- distribuição de scores competindo com a matriz de confusão;
- tabela dos bins de calibração ao lado da curva;
- tabela completa de métricas por fold ao lado de F4/F5;
- manifestos, hashes, checklists e detalhes de engenharia.

As decisões e substituições estão rastreadas em `phase_5b_excluded_visuals.csv`.

## 11. Regras de construção visual

- estilo acadêmico limpo, fundo claro, fontes legíveis e alta resolução;
- não truncar eixos de barras para amplificar diferenças pequenas;
- escalas percentuais coerentes e denominadores explicitados;
- nenhuma visualização 3D e preferência por barras/pontos sobre pizza;
- paleta curta, acessível a daltonismo e consistente entre figuras;
- mesma cor para cada família de modelo em F4 e F5;
- títulos informativos e legendas metodológicas sem redundância;
- distinguir sempre contagem, proporção, probabilidade e classificação;
- indicar “entre acidentes registrados pela PRF” nas figuras descritivas;
- não usar mapa ou cor para sugerir risco geográfico;
- exportar preferencialmente PNG em alta resolução e SVG quando compatível.

## 12. Plano RQ → evidência visual

| Pergunta | Núcleo | Apoio/apêndice |
|---|---|---|
| Principal | T1, F1, F2, F4, F5, T2, F6 | F7 e F8 |
| RQ1 | F1 e F2 | T1 e A4 |
| RQ2 | T2 e F6 | F7, F8, A1 e A2 |
| RQ3 | F4 e M1 | A3 |
| RQ4 | F5 e M1 | A3 |
| RQ5 | T2, F6 e M1 | F7 e A2 |
| Interpretação 4I | nenhuma pergunta nova | F8 e A1 |

Cada RQ possui pelo menos um elemento essencial. O plano evita exigir uma figura exclusiva
quando tabela ou elemento metodológico já comunica a evidência.

## 13. Candidatos para o dashboard da Fase 6

O dashboard futuro poderá reaproveitar T1, F1/F2, F4/F5, T2, F6/F7, F8 e A2. A arquitetura
planejada é:

- **frontend:** Next.js, React e TypeScript;
- **arquitetura:** 100% estática;
- **dados:** JSON gerado pelo Python a partir dos artefatos científicos;
- **backend:** nenhum;
- **hospedagem pretendida:** Vercel;
- **filtros descritivos no cliente:** ano, UF, BR, tipo de pista, condição meteorológica, dia
  da semana, horário/faixa, uso do solo e, eventualmente, traçado.

Filtros podem recombinar análises descritivas. APs, folds, threshold, avaliação 2025 e Tree
SHAP final são resultados congelados: o frontend apenas apresenta seus JSONs e nunca os
recalcula dinamicamente. Nenhum código de dashboard é iniciado nesta fase.

## 14. Conjunto recomendado final

- **Corpo de Resultados:** 2 tabelas essenciais (T1, T2), 5 figuras essenciais (F1, F2, F4,
  F5, F6) e até 2 úteis (F7, F8).
- **Metodologia:** 1 tabela (M2) e 1 figura (M1).
- **Apêndice selecionado:** 3 tabelas (A1, A3, A4) e 1 figura (A2).
- **Repositório apenas:** 4 candidatos do inventário, além dos artefatos técnicos já existentes.

Recomendação para o núcleo do manuscrito: **3 tabelas e 8 figuras** incluindo Metodologia e as
duas figuras úteis. Se houver restrição de espaço, remover primeiro F7, resultando em 3 tabelas
e 7 figuras, sem perda da resposta principal. O apêndice mantém quatro elementos.

## 15. Próxima etapa

Fase 5C — estruturar os capítulos de Resultados e Discussão usando este plano, antes de gerar
as figuras finais.
