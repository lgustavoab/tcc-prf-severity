# Fase 5F — Revisão científica, editorial e integração

## 1. Objetivo

A Fase 5F revisou os capítulos de Resultados e Discussão para aumentar precisão científica,
coesão e consistência terminológica, sem produzir nova evidência. O trabalho incidiu somente
sobre redação, apresentação acadêmica, transições, redundâncias e rastreabilidade.

## 2. Documento de origem e documento revisado

O documento histórico e imutável de origem é
`docs/PHASE_5E2_RESULTS_DISCUSSION_DRAFT.md`. A versão produzida nesta fase é
`docs/PHASE_5F_RESULTS_DISCUSSION_REVISED.md`. O SHA-256 do documento 5E.2 foi conferido antes
e depois da revisão, e nenhuma alteração foi aplicada ao arquivo original.

## 3. Escopo da revisão

A estrutura científica aprovada na Fase 5C foi mantida: 11 subseções em Resultados e oito em
Discussão, sem novos blocos analíticos. Permaneceram as respostas às cinco perguntas
específicas, a distinção entre associação, predição e interpretação, e as cautelas relativas a
exposição, causalidade, desenho temporal, ponto de operação e Tree SHAP.

Não houve carregamento de dados, predições ou modelos; não foram executados EDA, treinamento,
inferência, SHAP, calibração, seleção de limiar ou recálculo de métricas. Código, testes,
dependências e artefatos científicos das fases anteriores ficaram fora do escopo.

## 4. Política terminológica

O nome técnico `target_grave` foi reservado à primeira definição do desfecho. Os termos
`features` e `predictors` deram lugar a variáveis preditoras; `threshold`, a limiar de decisão;
`pipeline`, a modelo ou procedimento; e `refit`, a ajuste final. Predições out-of-fold foram
apresentadas por extenso antes da sigla OOF. A primeira menção relevante às métricas passou a
usar precisão positiva (precision) e sensibilidade (recall), com preferência posterior pelas
formas em português. Tree SHAP foi descrito inicialmente em escala de margem bruta
(`raw margin`).

Nas comparações entre categorias, adotou-se proporção de ocorrências graves. Prevalência foi
reservada à classe grave ou à composição global do desfecho, evitando linguagem que sugira
risco de ocorrência de acidente sem denominador de exposição.

## 5. Principais refinamentos

O Capítulo 4 ficou mais factual e sem literatura externa. A abertura foi aproximada da
linguagem de manuscrito; a transição entre caracterização descritiva e modelagem foi tornada
explícita; e a avaliação de 2025 passou a usar terminologia acadêmica consistente. A cautela de
que treino e ano de validação mudam simultaneamente foi preservada em formulação mais direta.

O Capítulo 5 concentrou a interpretação substantiva e o diálogo com a literatura. A discussão
da complexidade conduz à validação temporal, a análise do limiar distingue ordenação e decisão,
e a relação entre análise descritiva e Tree SHAP permanece uma convergência parcial. Os quatro
blocos de limitações foram mantidos em prosa.

## 6. Reduções de redundância

As cautelas sobre ausência de exposição e causalidade foram estabelecidas nas seções em que
definem o alcance e retomadas apenas quando necessárias. A ausência de tendência temporal, o
caráter não operacional do limiar, os falsos positivos e os limites de SHAP foram discutidos
substantivamente em suas seções e sintetizados em Limitações, sem repetir argumentos inteiros.

## 7. Preservação numérica

A auditoria reconciliou os 41 grupos numéricos da Fase 5E.2. Todos receberam `PRESERVED` e
`PASS`: contagens, percentuais, APs, ROC-AUC, Brier, deltas, limiar, matriz de confusão,
cardinalidades, anos e ranking permaneceram inalterados. Não existe `NEW_VALUE`,
`SCIENTIFIC_CHANGE` ou número substantivo sem fonte anterior.

## 8. Preservação bibliográfica

Foram mantidas as 19 referências `VERIFIED`, REF001–REF019. Nenhuma referência foi removida,
acrescentada ou pesquisada. A auditoria preservou as 16 unidades de citação da Fase 5E.2 e
registrou apenas ajustes de formulação ou estilo. As fontes externas continuam a contextualizar
resultados e métodos, sem confirmar automaticamente a evidência interna.

## 9. Figuras e tabelas

Continuam referenciadas T1, F1, F2, F4, F5, T2, F6, F7 e F8; M1 e M2 permanecem na
Metodologia. F7 continua como diagnóstico complementar e potencialmente removível na edição
final. IDs internos foram movidos para comentários HTML, e as fontes visíveis de T1 e T2 foram
apresentadas como elaboração própria com base nos dados da PRF.

Nenhuma figura ou tabela científica foi modificada. A numeração usada nos capítulos é
provisória e deverá ser ajustada na montagem completa do manuscrito.

## 10. Extensão antes e depois

O relatório histórico da Fase 5E.2 registrou 1.704 palavras em Resultados e 1.724 em Discussão.
Uma recontagem determinística dos arquivos atuais, por tokens alfanuméricos no conteúdo
Markdown dos capítulos, encontrou 1.712 e 1.732 no arquivo 5E.2 e 1.695 e 1.620 na versão 5F,
respectivamente. A pequena diferença entre o registro histórico e a recontagem atual é
documental e não altera a comparação: ambos os capítulos revisados não cresceram, e a redução
foi maior na Discussão. Foram preservados 45 parágrafos de prosa, 21 em Resultados e 24 em
Discussão.

## 11. Auditorias

- terminologia: 12 registros, 12 `PASS` e 0 `FAIL`;
- preservação numérica: 41 registros, 41 `PASS` e 0 `FAIL`;
- citações: 16 registros, 16 `PASS` e 0 `FAIL`;
- log de revisão: 25 registros, todos sem mudança científica e com `PASS`;
- checklist: 50 verificações, 50 `PASS` e 0 `FAIL`;
- expressões problemáticas: zero ocorrências das 19 formulações pesquisadas.

Os CSVs foram importados, inspecionados e renderizados com a ferramenta de artefatos tabulares
para verificar schema, legibilidade e integridade de células.

## 12. Limitações preservadas

Permanecem explícitos: população restrita aos registros da PRF; ausência de denominadores de
exposição; desenho observacional; disponibilidade operacional das variáveis como premissa;
três folds e um único ano final; mudança simultânea de treino e validação; observação
estrutural prévia de 2025; discriminação moderada; ganho modesto do XGBoost; falsos positivos;
ausência de custos operacionais; limiar não validado para implantação; e interpretação SHAP
não causal, dependente de representação e cardinalidade.

## 13. Itens para integração completa

A integração futura deverá normalizar definitivamente citações e referências segundo o padrão
institucional, ajustar a numeração global de tabelas e figuras, decidir editorialmente a
permanência de F7 e harmonizar estes capítulos com Introdução, Metodologia e Conclusão. Esses
itens não autorizam reabrir resultados congelados.

## 14. Situação de aceite

A revisão automatizada e de rastreabilidade foi concluída, mas a aprovação humana permanece
pendente. A versão 5F não deve ser tratada como manuscrito final antes dessa leitura.
