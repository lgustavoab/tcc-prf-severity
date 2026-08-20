# Fase 6D — Visualizações científicas e integração funcional

## 1. Objetivo e escopo

A Fase 6D transforma a fundação estática da 6C em um dashboard científico funcional. Durante
a revisão da Fase 6D foi identificada a necessidade de uma camada introdutória de comunicação
científica para público não especializado. As nove rotas consomem exclusivamente os 15 JSONs
auditados da 6B. Nenhuma métrica de machine
learning, predição, explicação SHAP, faixa de calibração, matriz de confusão ou threshold é
recalculado no navegador.

## 2. Stack visual

A implementação usa Recharts `3.10.1`, release estável fixada exatamente, com `react-is`
`19.2.8`, alinhado ao React e React DOM `19.2.8`. Barras e linhas usam Recharts; KPIs,
tabelas, matriz de confusão e desenho metodológico usam HTML semântico e CSS nativo. Não foi
adicionada outra biblioteca de gráficos ou interface.

A paleta central preserva cores consistentes: Regressão Logística em azul, Random Forest em
ocre e XGBoost em verde-petróleo. Gravidade usa violeta, sem vermelho dominante ou semântica
automática de perigo. Séries também são identificadas por labels e, quando pertinente, traço.

## 3. Componentes

Os componentes de visualização ficam em `dashboard/src/components/charts/`:

- `ChartCard`: título, descrição e associação acessível do conteúdo;
- `AnnualOverviewChart`: composição anual de graves e não graves;
- `HourlyProportionChart`: proporção grave por hora registrada;
- `HorizontalProportionChart`: barras categóricas com eixo iniciado em zero e tabela;
- `ModelComparisonChart`: AP média congelada em escala 0–1;
- `CalibrationChart`: dez faixas publicadas e referência `y = x`;
- `TemporalValidationChart`: três modelos nos três folds publicados;
- `PredictorContributionChart`: variáveis de origem e top 15 transformadas.

`dashboard/src/lib/data/exploration.ts` centraliza a única derivação autorizada: filtragem de
células publicadas, soma das três contagens aditivas, agrupamento por dimensão de exibição e
`severe_occurrences / total_occurrences`. Não contém AP, ROC-AUC, Brier, F1, calibração,
threshold, SHAP ou estatística inferencial.

## 4. Integração por página

### Sobre o estudo (`/`)

A nova Home apresenta a pergunta central, RQ1–RQ5 com respostas em linguagem simples,
definição operacional de ocorrência grave, glossário, limites de interpretação e caminhos para
as páginas analíticas. Ela explica que resultados congelados são saídas já calculadas e fixadas
para preservar reprodutibilidade, distinguindo-os dos dados históricos de 2021–2025 e das
agregações interativas. As cinco perguntas adotam leitura progressiva: a resposta curta e a
ressalva permanecem visíveis, enquanto um `details` nativo oferece aprofundamento opcional dos
resultados, números e limites. Nenhuma resposta cria resultado científico novo.

### Visão Geral (`/visao-geral`)

A antiga Home analítica foi movida integralmente para `/visao-geral`. O filtro local `YEAR`
escolhe a linha total ou anual já publicada. Quatro KPIs mostram total,
graves, não graves e proporção grave. O gráfico empilhado apresenta a composição anual e uma
tabela mantém todos os valores acessíveis. O texto caracteriza a sequência como descritiva,
sem inferir tendência estatística.

### Exploração

TEMPORAL e CONTEXTUAL permanecem estados independentes. O primeiro controla ano, dia da
semana e hora e alimenta linha horária e barras por dia. O segundo controla ano, pista,
meteorologia e uso do solo e alimenta três gráficos categóricos. `Ignorado` permanece visível
e é identificado como informação ausente, não como condição meteorológica substantiva.

### Geografia

Ano, UF e BR mantêm a dependência UF → BR. Sem UF selecionada, a apresentação compara UFs;
com UF, compara as BRs compatíveis; com BRs selecionadas, restringe o subconjunto. A página
usa resumo, barras e tabela completa. Não existe mapa coroplético nem linguagem de rodovia
“mais perigosa” ou “mais segura”.

### Modelos

A comparação exibe a AP média das três famílias em eixo 0–1, com desvio padrão, ROC-AUC e
Brier na tabela. O XGBoost é identificado como selecionado sob a regra definida, com ressalva
de diferenças absolutas pequenas. A avaliação final mostra seis valores de 2025 e suas
referências publicadas. A calibração é descrita como diagnóstico, não prova categórica.

### Validação Temporal

O gráfico apresenta AP de Regressão Logística, Random Forest e XGBoost em 2022, 2023 e 2024.
A tabela conserva AP, ROC-AUC e Brier para os nove pares modelo/fold. A página explicita que
período/volume de treinamento e ano de validação mudam simultaneamente e que a sequência não
demonstra tendência temporal de melhora.

### Limiar

O threshold, precisão positiva, sensibilidade e F1 permanecem somente leitura. A matriz de
confusão é um grid HTML/CSS responsivo com TN, FP, FN e TP exatos do JSON, acompanhado por
descrição textual. Não há slider, simulação de ponto de operação ou recomendação de uso.

### Interpretação

O controle alterna apenas entre as duas visões publicadas. Barras horizontais preservam a
ordem por variável de origem e o top 15 transformado. Labels amigáveis coexistem com nomes
técnicos para rastreabilidade. O caveat esclarece que SHAP descreve o modelo, não causalidade,
e que OHE e cardinalidade — inclusive as 125 colunas de BR publicadas — afetam a leitura.

### Metodologia

O desenho temporal usa os três folds e os períodos do contrato JSON, seguido do ajuste
2021–2024 e avaliação 2025. Tabelas e cards apresentam as 11 representações autorizadas, 22
preditores físicos e três grupos de preprocessing. Campos excluídos por leakage não são
reapresentados como candidatos.

## 5. Responsividade

Os breakpoints finais são: mobile abaixo de `640px`, tablet entre `640px` e `1023px`, e
desktop a partir de `1024px`. KPI grids passam de até quatro colunas para duas e uma; filtros
empilham no mobile; timeline usa quatro, duas e uma colunas. Gráficos usam a prop `responsive`
do Recharts e containers CSS com largura integral. Barras horizontais recebem altura derivada
da quantidade de categorias. Tabelas usam overflow horizontal sem ocultar valores essenciais.
Na Home introdutória, perguntas, glossário, limites e chamadas passam de duas ou quatro colunas
para duas no tablet e uma no mobile, sem overflow horizontal. A Home e `/visao-geral` foram
inspecionadas estruturalmente em 390px, 768px e viewport desktop durante a revisão.

A matriz `phase_6d_responsive_matrix.csv` registra revisão estrutural/manual guiada por código
e build. Ela não representa teste visual em dispositivo real, reservado ao fechamento 6E.

## 6. Acessibilidade

Os charts usam `accessibilityLayer`, título visível, descrição e conteúdo textual ou tabular
associado. Tooltips pt-BR complementam, mas nunca substituem os valores essenciais. Filtros
continuam controles nativos com áreas adequadas a touch; foco visível, skip link, headings,
landmarks e `aria-current` da 6C foram preservados. A matriz possui `aria-label` com os quatro
valores e explicações abaixo.

## 7. Fontes e fronteira científica

As fontes são `overview/summary.json`, os dois assets de `exploration/`, `geography.json`, os
três assets de `models/`, `temporal_validation.json`, `threshold_2025.json`, as duas partes de
`interpretation/`, `meta.json` e as duas partes de `methodology/`. Seus hashes e o manifesto
permanecem inalterados.

Resultados `FROZEN_RESULT` são somente apresentados. Agregações exploratórias operam apenas
sobre células publicadas e mantêm o aviso de que proporções entre acidentes registrados não
representam risco de ocorrência sem denominador de exposição ao tráfego.

## 8. Validação e artefatos de aceite

O aceite compreende lint, TypeScript, build, verificação das nove rotas estáticas, check npm,
árvore de dependências, suíte Python, hashes JSON e inspeção do diff. Os relatórios são:

- `phase_6d_route_implementation.csv`;
- `phase_6d_responsive_matrix.csv`;
- `phase_6d_visualization_inventory.csv`;
- `phase_6d_scientific_visual_audit.csv`;
- `phase_6d_visualization_checklist.csv`.

## 9. Limitações e Fase 6E

A 6D não executa automação de browser nem alega teste visual em dispositivo físico. Polimento
final, auditoria visual real, otimização de bundle, cache, validação em ambiente limpo e deploy
continuam reservados à Fase 6E. Nenhum deploy foi executado nesta fase.
