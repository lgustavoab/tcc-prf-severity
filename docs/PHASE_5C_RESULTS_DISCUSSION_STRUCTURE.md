# Fase 5C — Estrutura de Resultados e Discussão

## 1. Objetivo

Converter as perguntas, evidências e decisões visuais já aprovadas em um roteiro acadêmico
detalhado para os capítulos de Resultados e Discussão. Esta fase define o lugar e a função de
cada evidência; não redige o manuscrito final, não produz figuras, não recalcula métricas e não
executa análises.

## 2. Princípios de redação

- **Resultados** apresenta população, contrastes, métricas, comparações e respostas objetivas
  às RQs, com interpretação limitada ao significado direto das medidas.
- **Discussão** integra os achados, confronta descrição e predição, examina escolhas
  metodológicas e limitações e explicita o que os resultados não permitem concluir.
- números não são repetidos integralmente quando já aparecem em tabela ou figura;
- associação, contribuição preditiva e causalidade permanecem conceitos distintos;
- volume de acidentes registrados não equivale a risco, pois não há denominador de exposição;
- 2025 é avaliação final de performance, mas não foi completamente cego para EDA e drift;
- referências externas serão inseridas somente depois de busca e verificação bibliográfica;
- os valores integrais continuam preservados nas tabelas-fonte, independentemente do
  arredondamento editorial.

## 3. Estrutura recomendada de Resultados

### 4.1 Caracterização da população analisada

- **Objetivo:** apresentar a população, o período e a definição operacional do desfecho.
- **RQ:** pergunta principal e contexto para RQ1.
- **Evidências:** `phase_2a_year_summary.csv` e síntese 5A.
- **Elemento previsto:** T1 — Caracterização anual da população.
- **Números:** 342.624 ocorrências, 96.857 graves, prevalência global de 28,2692%; prevalências
  anuais de 28,0608% a 28,4943%.
- **Mensagem:** a população cobre 2021–2025 e apresenta prevalência grave anual
  aproximadamente estável em termos descritivos.
- **Interpretação permitida:** descrever composição, volume e proporção do target.
- **Cautelas:** são acidentes registrados pela PRF; volume e prevalência não medem risco de
  ocorrência na malha rodoviária.
- **Transição:** após delimitar a população, examinar como a proporção grave varia entre
  contextos observados.

### 4.2 Associações descritivas com gravidade

Esta seção responde RQ1 e deve permanecer estritamente univariada e descritiva.

#### 4.2.1 Padrões temporais e de calendário

- **Objetivo:** apresentar os contrastes temporais selecionados sem fragmentá-los em vários
  gráficos.
- **RQ:** RQ1.
- **Evidências:** E001, E002 e o contraste de hora na matriz 2F.
- **Elemento previsto:** F1 — Contrastes temporais e de calendário.
- **Números:** Plena Noite 32,4726% versus Pleno dia 25,3047%; fim de semana 30,1925% versus
  dias úteis 27,3303%; 19h 33,7323% versus 8h 23,1243%.
- **Mensagem:** houve heterogeneidade temporal na proporção grave entre ocorrências
  registradas.
- **Interpretação permitida:** comparar proporções condicionais dentro de cada contraste.
- **Cautelas:** sem exposição horária, volume de circulação ou controle multivariado; painéis
  distintos não formam um ranking comum.
- **Transição:** ampliar a descrição para dimensões geográficas, viárias e meteorológicas.

#### 4.2.2 Padrões geográficos, viários e meteorológicos

- **Objetivo:** reunir dimensões substantivamente diferentes em facetas claramente separadas.
- **RQ:** RQ1.
- **Evidências:** E003–E006 da matriz 5A.
- **Elemento previsto:** F2 — Contrastes geográficos, viários e meteorológicos.
- **Números:** Nordeste 35,9171% versus Sul 24,8740%; MA 45,8117% versus SP 18,6394%; pista
  Simples 33,7115% versus Dupla 23,3513%; Nevoeiro/Neblina 31,5011% versus
  Garoa/Chuvisco 22,2644%.
- **Mensagem:** as proporções observadas variaram entre contextos, sem que as diferenças
  identifiquem risco geográfico ou efeito causal.
- **Interpretação permitida:** registrar heterogeneidade descritiva entre categorias da mesma
  dimensão.
- **Cautelas:** ausência de exposição, composição distinta das populações e comparação
  univariada; `Ignorado` não é condição meteorológica física; não ordenar UFs ou rodovias por
  segurança.
- **Transição:** registrar separadamente tipo e causa, cujas maiores diferenças vêm com
  restrições adicionais de temporalidade e taxonomia.

#### 4.2.3 Tipo e causa registrados

- **Objetivo:** preservar um achado descritivo relevante sem lhe dar protagonismo preditivo.
- **RQ:** RQ1.
- **Evidência:** E007 e política 3B.
- **Elemento previsto:** resumo textual; detalhes permanecem em A4.
- **Números:** diferenças de 44,3469 p.p. para Atropelamento de Pedestre versus Colisão
  traseira e 51,4847 p.p. para Pedestre andava na pista versus Reação tardia ou ineficiente.
- **Mensagem:** tipo e causa registrados produziram contrastes grandes na EDA.
- **Interpretação permitida:** apresentar o achado como associação observada.
- **Cautelas:** taxonomias variaram e os campos podem ser conhecidos ou consolidados depois
  do momento preditivo; não foram incorporados ao conjunto principal.
- **Transição:** passar da descrição univariada ao experimento preditivo congelado.

### 4.3 Desenho preditivo e comparação dos modelos

- **Objetivo:** responder como as três famílias se compararam sob os mesmos folds.
- **RQ:** RQ3.
- **Evidência:** `phase_4d_model_comparison.csv`.
- **Elemento previsto:** F4 — AP média por família; M1 é apenas referenciado, pois já aparece
  na Metodologia.
- **Números:** Logística 0,393508; Random Forest 0,395984; XGBoost 0,400811. Deltas: RF−LR
  0,002476; XGB−LR 0,007303; XGB−RF 0,004827.
- **Mensagem:** XGBoost obteve a maior AP média, mas o ganho absoluto foi modesto.
- **Interpretação permitida:** relatar a ordenação sob este desenho experimental.
- **Cautelas:** somente três folds e nenhum teste post hoc; evitar “muito superior”, “grande
  ganho” ou “modelo excelente”.
- **Transição:** verificar se a ordenação e as magnitudes se mantêm nos anos de validação.

### 4.4 Consistência na validação temporal

- **Objetivo:** apresentar a AP de cada família em 2022, 2023 e 2024.
- **RQ:** RQ4.
- **Evidência:** `phase_4d_fold_comparison.csv`.
- **Elemento previsto:** F5 — AP por fold temporal.
- **Números:** o XGBoost variou de 0,390375 em 2022 a 0,407090 em 2024; os nove valores
  completos permanecem na figura e na fonte.
- **Mensagem:** as três famílias tiveram APs mais elevadas nos folds posteriores, sem queda
  abrupta ou colapso.
- **Interpretação permitida:** descrever a sequência observada e a dispersão.
- **Cautela obrigatória:** ano de validação e período/volume de treino mudam simultaneamente;
  a sequência não demonstra tendência temporal de melhora.
- **Transição:** levar o modelo selecionado ao único período final reservado para performance.

### 4.5 Capacidade preditiva e avaliação final em 2025

- **Objetivo:** responder a capacidade de distinção e a manutenção temporal final.
- **RQ:** RQ2 e RQ5.
- **Evidências:** `phase_4h_final_evaluation.csv` e
  `phase_4h_development_comparison.csv`.
- **Elemento previsto:** T2 — Avaliação temporal final e comparação com desenvolvimento.
- **Números:** AP 0,397446; ROC-AUC 0,628556; Brier 0,193822; precision 0,331593; recall
  0,771825; F1 0,463889. AP versus média interna −0,003365; ROC-AUC −0,002294; Brier
  −0,000075.
- **Mensagem:** o desempenho em 2025 permaneceu aproximadamente próximo das referências
  internas e a capacidade discriminativa foi moderada.
- **Interpretação permitida:** comparar descritivamente métricas congeladas.
- **Cautelas:** 2025 é um único ano; não houve teste de hipótese; não chamar a capacidade de
  excelente.
- **Transição:** separar o desempenho de ranking das decisões produzidas pelo cutoff.

### 4.6 Comportamento do threshold congelado

- **Objetivo:** mostrar como o cutoff transforma probabilities em decisões.
- **RQ:** RQ2 e RQ5.
- **Evidências:** `phase_4f_threshold_selection.csv` e
  `phase_4h_threshold_evaluation.csv`.
- **Elemento previsto:** F6 — Matriz de confusão em 2025.
- **Números:** threshold 0,23723246157169342; TN 20.153, FP 31.883, FN 4.676 e TP 15.817;
  recall 77,1825% e precision 33,1593%.
- **Mensagem:** o cutoff selecionado por F1 no OOF priorizou recall e produziu muitos falsos
  positivos.
- **Interpretação permitida:** distinguir ranking probabilístico de classificação binária.
- **Cautelas:** custos de FP/FN não foram estudados; o cutoff não é recomendação operacional
  para a PRF e nunca usou 2025 em sua seleção.
- **Transição:** encerrar Resultados com diagnósticos complementares, sem criar novas decisões.

### 4.7 Diagnósticos complementares

#### 4.7.1 Calibração descritiva em 2025

- **Objetivo:** complementar AP e Brier com a relação descritiva entre probability média e
  frequência observada.
- **RQ:** apoio a RQ2 e RQ5.
- **Evidência:** `phase_4h_calibration.csv`.
- **Elemento previsto:** F7, somente se houver espaço editorial.
- **Números:** dez bins quantis; valores completos permanecem na fonte e na figura futura.
- **Mensagem:** calibração é diagnóstico complementar; nenhum calibrador foi ajustado.
- **Cautelas:** não afirmar calibração perfeita e não reinterpretar os bins como novo teste.
- **Transição:** apresentar, também de forma complementar, quais predictors mais participaram
  das predições.

#### 4.7.2 Contribuição agregada dos predictors

- **Objetivo:** apresentar o ranking 4I sem convertê-lo em explicação causal.
- **RQ:** complemento de RQ2.
- **Evidência:** `phase_4i_global_feature_contributions.csv`.
- **Elemento previsto:** F8 — Top predictors por contribuição absoluta agregada.
- **Números:** `uf`, `tipo_pista`, `hour`, `br` e `condicao_metereologica` ocupam as cinco
  primeiras posições; `br` agrega 125 features OHE.
- **Mensagem:** features derivadas desses predictors tiveram maior participação absoluta
  agregada nas predições em margem bruta.
- **Interpretação permitida:** relatar ranking, escala e cardinalidade.
- **Cautelas:** Tree SHAP não mede causa, efeito ou fator de risco; cardinalidades diferentes
  influenciam agregações.
- **Transição:** abrir a Discussão retomando o significado conjunto dos resultados, sem repetir
  o ranking.

**Decisão sobre F8:** posicioná-la no fim de Resultados, onde valores e ranking são
apresentados. A subseção 5.6 retoma apenas seu significado e sua convergência parcial com a
EDA. Essa separação evita inserir interpretação extensa em Resultados e evita repetir a figura
na Discussão.

## 4. Estrutura recomendada de Discussão

### 5.1 Heterogeneidade da gravidade entre ocorrências registradas

- **Objetivo:** integrar as dimensões temporal, geográfica, viária e meteorológica de RQ1.
- **Base:** F1, F2 e T1; tipo e causa entram como ressalva.
- **Argumento:** a heterogeneidade é real no dataset, mas condicionada à população de
  ocorrências registradas.
- **Interpretação:** distinguir maior volume de maior proporção grave e discutir composição.
- **Limites:** sem exposição não há estimativa de risco de acidente; dados observacionais não
  sustentam causalidade.
- **Literatura futura:** [LITERATURA NECESSÁRIA: estudos observacionais sobre gravidade em
  acidentes rodoviários e denominadores de exposição].
- **Transição:** perguntar se essas heterogeneidades contêm sinal útil para ordenar casos.

### 5.2 O que as características conseguem prever

- **Objetivo:** interpretar RQ2 sem transformar predição em explicação.
- **Base:** T2, F6 e, se mantida, F7.
- **Argumento:** AP acima da prevalência e ROC-AUC próxima de 0,63 indicam sinal, mas a
  discriminação é moderada e há sobreposição relevante entre classes.
- **Limites:** disponibilidade operacional das features é premissa metodológica e não foi
  comprovada no fluxo interno da PRF.
- **Literatura futura:** [LITERATURA NECESSÁRIA: avaliação de modelos de gravidade e uso de AP
  em classes desbalanceadas].
- **Transição:** discutir quanto a complexidade adicional alterou esse sinal.

### 5.3 Complexidade dos modelos e ganhos modestos

- **Objetivo:** interpretar RQ3 e a pequena distância entre as famílias.
- **Base:** F4 e A3.
- **Argumento:** não linearidades e interações podem favorecer o XGBoost, mas o ganho pequeno
  mostra que maior complexidade não produziu salto substancial sob este desenho.
- **Limites:** a liderança é específica aos dados, features, períodos e configurações
  congeladas; não demonstra superioridade universal.
- **Literatura futura:** [LITERATURA NECESSÁRIA: comparação entre modelos lineares, florestas
  e boosting em dados tabulares].
- **Transição:** avaliar as famílias ao longo dos folds, em vez de olhar somente a média.

### 5.4 Consistência temporal e generalização

- **Objetivo:** integrar RQ4 e RQ5.
- **Base:** M1, F5 e T2.
- **Argumento:** não houve colapso nos folds e a performance de 2025 ficou próxima da média
  interna, o que sustenta manutenção aproximada, não invariância temporal.
- **Limites:** existem apenas três folds e um ano final; treino e validação mudam juntos; 2025
  foi final para performance, mas já havia sido usado em EDA e drift estrutural.
- **Proteções:** 2025 não selecionou modelo ou threshold, não alterou o refit e não motivou
  ajuste posterior.
- **Literatura futura:** [LITERATURA NECESSÁRIA: validação temporal e mudança de distribuição
  em modelos preditivos].
- **Transição:** passar da generalização probabilística ao compromisso decisório do cutoff.

### 5.5 Threshold, recall e falsos positivos

- **Objetivo:** interpretar o compromisso entre sensibilidade e carga de alertas.
- **Base:** F6 e evidências 4F/4H.
- **Argumento:** recall próximo de 77% veio acompanhado de precision próxima de 33% e 31.883
  falsos positivos; o threshold otimiza F1 matematicamente no OOF.
- **Limites:** não há estudo de custo, capacidade de atendimento, benefício operacional ou impacto
  institucional; não recomendar implantação operacional.
- **Literatura futura:** [LITERATURA NECESSÁRIA: trade-off precision–recall, seleção de cutoff
  e custos de decisão].
- **Transição:** examinar se as informações usadas pelo modelo dialogam com a EDA.

### 5.6 Relação entre EDA e interpretação do XGBoost

- **Objetivo:** relacionar F8 a F1/F2 sem validar causalidade por repetição.
- **Base:** F8, A1 e evidências descritivas.
- **Argumento:** `uf`, `tipo_pista`, `hour` e meteorologia mostram convergência parcial entre
  heterogeneidade univariada e uso multivariado pelo modelo.
- **Explicações para diferenças:** interações, não linearidade, redundância, composição,
  cardinalidade e representação OHE.
- **Limites:** Tree SHAP está em raw margin, é pós-avaliação e não confirma fatores de risco.
- **Literatura futura:** [LITERATURA NECESSÁRIA: interpretação SHAP, agregação de one-hot e
  limites causais de explicações preditivas].
- **Transição:** consolidar as limitações transversais do estudo.

### 5.7 Limitações

Organizar a seção em quatro blocos conectados:

- **Dados e população:** somente acidentes registrados, ausência de exposição e natureza
  observacional.
- **Desenho preditivo:** disponibilidade operacional como premissa, três folds, um único ano
  final e 2025 não completamente cego para EDA/drift.
- **Modelo e decisão:** discriminação moderada, muitos falsos positivos, ausência de custos e
  threshold sem validação operacional.
- **Interpretação:** Tree SHAP não causal, efeito da cardinalidade e possíveis mudanças futuras
  de taxonomia e população.

A limitação mecânica de `pessoas` também deve ser lembrada se a variável for mencionada: mais
pessoas oferecem mais oportunidades para que o target no nível da ocorrência seja satisfeito.

- **Transição:** responder de forma integrada à pergunta principal, sem antecipar a Conclusão.

### 5.8 Síntese da discussão

- **Objetivo:** conectar RQ1–RQ5 à pergunta principal.
- **Síntese:** houve heterogeneidade descritiva e sinal preditivo moderado; XGBoost liderou por
  margem pequena, não houve colapso temporal e 2025 permaneceu próximo das referências, mas o
  threshold implicou muitos falsos positivos e nenhuma evidência autoriza leitura causal ou
  implantação.
- **Fronteira:** encerrar a Discussão sem escrever a Conclusão formal do TCC.

## 5. Mapa RQ → subseção

| Pergunta | Resultados | Discussão | Resposta sustentada |
|---|---|---|---|
| Principal | 4.1–4.7 | 5.8 | Integra heterogeneidade e capacidade preditiva entre ocorrências registradas. |
| RQ1 | 4.2.1–4.2.3 | 5.1 e 5.6 | Contrastes descritivos existem, sem exposição ou causalidade. |
| RQ2 | 4.5–4.7 | 5.2, 5.5 e 5.6 | Há sinal moderado; o threshold prioriza recall. |
| RQ3 | 4.3 | 5.3 | XGBoost lidera por ganho absoluto modesto. |
| RQ4 | 4.4 | 5.4 | Não há colapso, mas os folds não demonstram tendência de melhora. |
| RQ5 | 4.5–4.6 | 5.4–5.5 | 2025 fica próximo das referências sem otimização posterior. |

## 6. Mapa visual → subseção

| Elemento | Posição | Função |
|---|---|---|
| M1 | Metodologia — desenho experimental | Mostrar folds expanding-window e separação de 2025. |
| M2 | Metodologia — features/preprocessing | Resumir 22 predictors e transformações. |
| T1 | 4.1 | Caracterizar população e target. |
| F1 | 4.2.1 | Apresentar contrastes temporais. |
| F2 | 4.2.2 | Apresentar contrastes geográficos, viários e meteorológicos. |
| F4 | 4.3 | Comparar AP média das famílias. |
| F5 | 4.4 | Mostrar AP por fold temporal. |
| T2 | 4.5 | Sintetizar avaliação 2025 e deltas. |
| F6 | 4.6 | Mostrar decisões no threshold congelado. |
| F7 | 4.7.1 e retomada breve em 5.2/5.4 | Diagnóstico opcional de calibração. |
| F8 | 4.7.2 e interpretação em 5.6 | Apresentar ranking; discutir convergência parcial. |
| A1 | Apêndice — interpretação detalhada | Preservar top 15 features transformadas. |
| A2 | Apêndice — diagnóstico do threshold | Preservar distribuição dos scores por outcome. |
| A3 | Apêndice — resultados completos | Preservar métricas completas por fold e modelo. |
| A4 | Apêndice — evidências descritivas | Preservar contrastes e cautelas de RQ1. |

## 7. Resultados vs interpretação

| Elemento | Resultado apresenta | Discussão interpreta |
|---|---|---|
| População | 342.624 registros, 96.857 graves e 28,2692%. | População condicionada a acidentes registrados, sem exposição. |
| Contrastes RQ1 | Proporções e diferenças de F1/F2. | Heterogeneidade não equivale a efeito ou risco. |
| AP dos modelos | 0,393508; 0,395984; 0,400811. | Complexidade adicionou ganho modesto neste desenho. |
| Folds temporais | Nove APs de 2022–2024. | Sem colapso, mas sem tendência demonstrada de melhora. |
| Avaliação 2025 | AP 0,397446, ROC-AUC 0,628556 e Brier 0,193822. | Sinal moderado e manutenção aproximada em um único ano final. |
| Matriz de confusão | 31.883 FP e 4.676 FN. | Cutoff favorece recall sem validação de custo operacional. |
| F8 | Ranking por contribuição absoluta em margem. | Convergência parcial com EDA, não confirmação causal. |

## 8. Números essenciais que devem aparecer no texto

- população: 342.624 ocorrências, 96.857 graves e prevalência de 28,2692%;
- limites anuais da prevalência: 28,0608%–28,4943%;
- contrastes selecionados de F1/F2, preferencialmente resumidos no texto e completos nos
  visuais;
- AP média das três famílias e os deltas que qualificam o ganho como modesto;
- intervalo observado do XGBoost nos folds: 0,3904–0,4071;
- AP, ROC-AUC, Brier, precision, recall e F1 de 2025;
- threshold editorialmente arredondado e valor exato preservado na fonte;
- TN, FP, FN e TP da matriz de confusão;
- nomes dos cinco predictors líderes, se F8 permanecer.

O inventário exato está em `phase_5c_key_numbers.csv`.

### Política de arredondamento

- contagens: inteiros com separador de milhar;
- percentuais descritivos: duas casas no texto, até quatro quando a diferença pequena exigir;
- AP, ROC-AUC, Brier, precision, recall e F1: quatro casas no texto;
- deltas: quatro casas, mantendo sinal;
- threshold: `0,237232` no texto e valor exato `0,23723246157169342` no repositório;
- tabelas técnicas: quatro a seis casas quando necessário;
- tabelas-fonte: nenhuma perda de precisão.

Essa política é somente editorial e não altera valores computados.

## 9. Resultados que NÃO precisam ser repetidos no corpo

- todos os cinco totais anuais e todas as prevalências de T1 no parágrafo;
- os nove valores de AP de F5; o texto pode informar apenas o intervalo do XGBoost;
- todos os bins de calibração de F7;
- as 226 contribuições transformadas ou o top 15 de A1;
- todas as métricas secundárias por fold de A3;
- hashes, manifestos, checklists e parâmetros de engenharia;
- rankings extensos de categorias ou resultados de drift que não respondem diretamente às RQs.

## 10. Pontos que exigirão literatura

Usar os placeholders abaixo até uma busca bibliográfica posterior e verificável:

- [LITERATURA NECESSÁRIA: estudos de ML para gravidade de acidentes rodoviários];
- [LITERATURA NECESSÁRIA: exposição ao tráfego e interpretação de proporções condicionais];
- [LITERATURA NECESSÁRIA: validação temporal e drift em aprendizado de máquina];
- [LITERATURA NECESSÁRIA: modelos ensemble e ganhos em dados tabulares];
- [LITERATURA NECESSÁRIA: Average Precision em desbalanceamento de classes];
- [LITERATURA NECESSÁRIA: calibração probabilística e Brier score];
- [LITERATURA NECESSÁRIA: trade-off precision–recall e custos de decisão];
- [LITERATURA NECESSÁRIA: SHAP, agregação de categorias OHE e limites causais].

Nenhum autor, título ou artigo é atribuído nesta fase.

## 11. Transições narrativas

- **Caracterização → EDA:** “Definida a população analisada, examinam-se a seguir as variações
  da proporção grave entre os contextos registrados.”
- **EDA → modelagem:** “As heterogeneidades descritivas motivam a avaliação de quanto esse
  conjunto de informações permite distinguir ocorrências graves sob validação temporal.”
- **Comparação → validação temporal:** “A média resume a ordenação geral, mas a leitura por
  fold é necessária para verificar seu comportamento entre anos de validação.”
- **Validação → avaliação final:** “Após a comparação interna, o pipeline congelado foi
  avaliado no período final de 2025.”
- **Avaliação → threshold:** “As métricas probabilísticas descrevem ranking e calibração; a
  decisão binária exige examinar separadamente o cutoff congelado.”
- **Resultados → Discussão:** “Os resultados estabelecem heterogeneidade e sinal preditivo;
  sua relevância e seus limites metodológicos são discutidos no capítulo seguinte.”

## 12. Limitações e cautelas obrigatórias

- população formada somente por acidentes registrados e sem denominadores de exposição;
- desenho observacional e associações não causais;
- tipo e causa com temporalidade e taxonomia cautelosas;
- compatibilidade temporal das features como premissa, não comprovação operacional;
- somente três folds e um ano final;
- treino e ano de validação mudam simultaneamente nos folds;
- 2025 reservado para performance, mas não totalmente cego para EDA/drift;
- capacidade discriminativa moderada e muitos falsos positivos;
- threshold selecionado por F1, sem custos operacionais;
- SHAP em margem, não causal e sensível à representação/cardinalidade;
- ausência de recomendação de implantação;
- possíveis mudanças futuras de taxonomia e população.

## 13. Estrutura final recomendada

```text
4. Resultados
  4.1 Caracterização da população analisada
  4.2 Associações descritivas com gravidade
    4.2.1 Padrões temporais e de calendário
    4.2.2 Padrões geográficos, viários e meteorológicos
    4.2.3 Tipo e causa registrados
  4.3 Desenho preditivo e comparação dos modelos
  4.4 Consistência na validação temporal
  4.5 Capacidade preditiva e avaliação final em 2025
  4.6 Comportamento do threshold congelado
  4.7 Diagnósticos complementares
    4.7.1 Calibração descritiva em 2025
    4.7.2 Contribuição agregada dos predictors

5. Discussão
  5.1 Heterogeneidade da gravidade entre ocorrências registradas
  5.2 O que as características conseguem prever
  5.3 Complexidade dos modelos e ganhos modestos
  5.4 Consistência temporal e generalização
  5.5 Threshold, recall e falsos positivos
  5.6 Relação entre EDA e interpretação do XGBoost
  5.7 Limitações
  5.8 Síntese da discussão
```

Introdução, Referencial Teórico, Metodologia completa e Conclusão não são escritos nesta fase.
M1 e M2 permanecem planejados na Metodologia. A arquitetura futura da Fase 6 continua sendo
Next.js, React e TypeScript, 100% estática, com JSON científico, filtros no cliente, nenhum
backend e hospedagem pretendida na Vercel; nenhum código web é iniciado agora.

## 14. Próxima etapa

1. **Fase 5D:** gerar as figuras e tabelas acadêmicas selecionadas.
2. **Fase 5E:** redigir a primeira versão de Resultados e Discussão.
3. **Fase 5F:** revisar cientificamente e integrar o manuscrito.
4. **Fase 6:** desenvolver o dashboard web estático.
