# Fase 5E.2 — Relatório da primeira redação acadêmica

## 1. Objetivo e escopo

A Fase 5E.2 produziu a primeira redação acadêmica dos capítulos de Resultados e Discussão a
partir de evidências científicas, elementos visuais e referências já congelados. Não houve
nova EDA, modelagem, predição, seleção de threshold, calibração, SHAP ou recálculo de métricas.
O texto é uma versão de trabalho para revisão científica e editorial na Fase 5F, não uma versão
final do manuscrito.

## 2. Fontes utilizadas

A redação seguiu a prioridade **artefato científico original → mapa intermediário → documento
de síntese**. As fontes estruturais foram as Fases 5A–5E.1, especialmente o mapa de seções, o
mapa texto–evidência e o inventário de números da Fase 5C. Os valores foram reconciliados com
as tabelas originais das Fases 2–4 e com T1/T2. A literatura foi limitada às 19 referências
`VERIFIED` de `phase_5e1_bibliography_inventory.csv`; nenhuma referência foi acrescentada,
removida ou pesquisada nesta fase.

## 3. Estrutura e extensão

O arquivo principal preserva integralmente a estrutura aprovada na Fase 5C:

- Capítulo 4 — Resultados: 1.704 palavras;
- Capítulo 5 — Discussão: 1.724 palavras;
- total entre os dois capítulos: 3.428 palavras;
- parágrafos de prosa: 45, sendo 21 em Resultados e 24 em Discussão.

A contagem considera tokens alfanuméricos no conteúdo Markdown entre os títulos de cada
capítulo, incluindo legendas e conteúdo das tabelas. Títulos de arquivo e a nota editorial
anterior ao Capítulo 4 não integram o total dos capítulos.

## 4. Evidências e elementos acadêmicos

Resultados incorpora T1, F1, F2, F4, F5, T2, F6, F7 e F8 nas posições previstas. M1 e M2
permanecem elementos da Metodologia e não foram apresentados como resultados. F7 foi mantida
como diagnóstico descritivo complementar, ainda sujeito à decisão editorial final. Tipo e causa
registrados permanecem no texto como achados descritivos secundários, com remissão ao Apêndice
A4 e sem ingresso no conjunto preditivo principal.

## 5. Uso bibliográfico

Foram usadas as 19 referências verificadas, REF001–REF019; nenhuma referência verificada ficou
sem uso nesta primeira versão. As citações externas aparecem somente no Capítulo 5, em formato
autor–data e sem URLs no corpo do manuscrito. As fontes aplicadas contextualizam a diversidade
do problema, enquanto as metodológicas fundamentam exposição, validação temporal, ensembles,
avaliação probabilística, threshold e SHAP. Nenhuma fonte externa substitui ou confirma
automaticamente os resultados internos.

## 6. Política numérica

As contagens usam separador de milhar; percentuais descritivos usam duas casas no texto e até
quatro nas tabelas; AP, ROC-AUC, Brier, precision, recall e F1 usam quatro casas; deltas
preservam o sinal; e o threshold aparece com seis casas, mantendo o valor integral na fonte.
As tabelas científicas anteriores não foram modificadas. Cada afirmação numérica substantiva
do rascunho foi reconciliada em `phase_5e2_numeric_audit.csv`.

## 7. Cautelas preservadas

A redação mantém população restrita a acidentes registrados, ausência de denominadores de
exposição, natureza observacional, temporalidade e taxonomia cautelosas para tipo e causa,
compatibilidade temporal de features como premissa metodológica, apenas três folds e um ano
final, mudança simultânea de treino e ano de validação, 2025 não completamente cego para
EDA/drift, capacidade moderada, muitos falsos positivos, ausência de custos operacionais e
interpretação SHAP não causal e sensível à representação. Não há recomendação de implantação.

## 8. Auditorias de rastreabilidade

- auditoria numérica: 41 registros, 41 `PASS` e 0 `FAIL`;
- auditoria de citações: 16 afirmações, 16 `PASS` e 0 `FAIL`;
- mapa parágrafo–evidência: 45 parágrafos mapeados;
- checklist do rascunho: 50 verificações, 50 `PASS` e 0 `FAIL`;
- busca de expressões proibidas: 0 ocorrências.

Os IDs dos controles são locais à Fase 5E.2 e não alteram identificadores científicos de fases
anteriores.

A forma de auditoria combina `Import-Csv` para conferir schemas, contagens e status,
`Test-Path` para validar fontes e figuras, busca textual com `rg -n -i` para as expressões
proibidas e importação, inspeção e renderização dos quatro CSVs com `@oai/artifact-tool`. A
validação do repositório usa os comandos congelados no escopo desta fase.

## 9. Pontos para a Fase 5F

A revisão seguinte deverá avaliar fluidez entre subseções, equilíbrio entre Resultados e
Discussão, redundâncias, consistência terminológica, normalização ABNT, numeração final de
tabelas e figuras, integração com Introdução/Metodologia/Conclusão, permanência editorial de F7
e conferência final das referências. Esses pontos não autorizam recalcular resultados nem
reabrir decisões experimentais.

## 10. Artefatos produzidos

- `docs/PHASE_5E2_RESULTS_DISCUSSION_DRAFT.md`;
- `docs/PHASE_5E2_WRITING_REPORT.md`;
- `reports/tables/phase_5e2_numeric_audit.csv`;
- `reports/tables/phase_5e2_citation_audit.csv`;
- `reports/tables/phase_5e2_paragraph_evidence_map.csv`;
- `reports/tables/phase_5e2_draft_checklist.csv`.

## 11. Próxima etapa

Fase 5F — revisão científica, editorial e de integração do manuscrito, preservando as fontes e
os resultados congelados.
