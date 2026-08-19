# Fase 5E.1 — Fundamentação bibliográfica

## 1. Objetivo

Esta fase substitui os oito placeholders conceituais da Fase 5C por um conjunto enxuto,
verificável e rastreável de referências reais para a futura redação de Resultados e Discussão.
Ela não escreve o manuscrito, não altera resultados internos e não executa EDA, modelagem,
predição, threshold, calibração ou SHAP.

O resultado contém 19 referências candidatas, todas `VERIFIED`, distribuídas entre literatura
aplicada à gravidade rodoviária e literatura metodológica. Não há referência `UNRESOLVED` sendo
usada como sustentação científica.

## 2. Protocolo de busca e verificação

A busca foi realizada em 19 de agosto de 2026 a partir dos oito temas L1–L8 congelados em
`PHASE_5C_RESULTS_DISCUSSION_STRUCTURE.md`. Foram consultados mecanismos de busca acadêmica e
web, seguidos de verificação individual em ao menos uma fonte bibliográfica confiável:

- página oficial do periódico ou proceedings;
- PubMed/PubMed Central, quando aplicável;
- DOI resolver e metadados editoriais;
- repositório institucional do autor ou da universidade, como apoio;
- PMLR ou NeurIPS para artigos cuja publicação original é proceedings sem DOI.

Snippets foram usados apenas para descoberta. A entrada no inventário exigiu confirmação de
autores, ano, título, veículo e DOI, quando existente. A ausência de DOI em REF016, REF018 e
REF019 foi mantida explicitamente; nenhum identificador foi inferido ou fabricado.

O inventário autoritativo é `phase_5e1_bibliography_inventory.csv`. O mapa temático registra
por que cada fonte é pertinente e seu limite de uso. O mapa de afirmações separa evidência
interna das Fases 2–4 e apoio externo.

## 3. Critérios de inclusão/exclusão

### Inclusão

- aderência direta a pelo menos um dos temas L1–L8;
- artigo revisado por pares, publicação metodológica original ou proceedings reconhecido;
- metadados verificáveis em fonte editorial, bibliográfica ou institucional;
- utilidade concreta para uma subseção 5.1–5.7;
- alcance compatível com as cautelas já congeladas no projeto.

### Exclusão

- blogs, páginas comerciais, Wikipedia, fóruns e textos sem autoria verificável;
- preprints redundantes quando havia versão final revisada por pares;
- artigos descobertos apenas por snippet sem metadados confirmáveis;
- estudos distantes do problema ou cuja inclusão apenas aumentaria a lista;
- fontes que exigiriam atribuir causalidade, superioridade universal ou equivalência de
  métricas além do que demonstram.

## 4. Literatura sobre gravidade rodoviária

Quatro referências compõem o núcleo aplicado:

- **REF001 — Iranitalab e Khattak (2017):** comparação de quatro métodos estatísticos e de ML
  para predição de gravidade. É útil para contextualizar comparações entre famílias, não para
  importar ranks ou métricas.
- **REF002 — Sameen e Pradhan (2017):** aplicação de rede recorrente à gravidade de acidentes.
  Demonstra diversidade de abordagens, com população e validação próprias.
- **REF003 — Komol et al. (2021):** comparação de RF, SVM e KNN para gravidade envolvendo
  usuários vulneráveis. A importância de variáveis permanece preditiva/associativa.
- **REF004 — Franceschi et al. (2022):** contexto brasileiro em rodovias federais, com modelo
  multinomial aplicado a dados de acidentes. É aproximação temática nacional, não benchmark de
  ML nem confirmação dos padrões deste TCC.

Esses estudos permitem escrever futuramente que a classificação de gravidade tem sido abordada
com famílias diversas e em diferentes populações. Não permitem afirmar que o presente estudo
“confirma” resultados externos. Comparações futuras devem usar “dialoga com”, “é consistente
com”, “apresenta padrão semelhante” ou “difere de” somente após confronto específico entre
definições, população, features e desenho de validação.

## 5. Validação temporal e generalização

- **REF006 — Moreno-Torres et al. (2012)** fornece uma taxonomia de dataset shift e sustenta a
  cautela de que treino e aplicação podem seguir distribuições distintas.
- **REF007 — Roberts et al. (2017)** discute validação quando os dados têm estrutura temporal,
  espacial ou hierárquica e apoia o bloqueio compatível com o objetivo de generalização.

Essas referências sustentam o desenho temporal, mas não transformam os três folds do projeto em
prova de estabilidade estatística. A interpretação interna permanece: não houve colapso
observado, as APs foram mais elevadas nos folds posteriores e 2025 ficou aproximadamente
próximo às referências de desenvolvimento. Como treino e ano de validação mudam juntos, não há
tendência demonstrada de melhora.

## 6. Modelos e complexidade

- **REF008 — Breiman (2001)** é a referência original de Random Forest.
- **REF009 — Chen e Guestrin (2016)** é a referência original do XGBoost.
- **REF001 e REF003** mostram aplicações comparativas em gravidade rodoviária.

Os artigos fundadores explicam os métodos; não constituem evidência de superioridade. A futura
Discussão poderá registrar que ensembles em árvores modelam relações não lineares e interações,
mas deverá atribuir a liderança do XGBoost exclusivamente aos resultados internos congelados.
O ganho pequeno sobre as demais famílias é específico às features, períodos, configurações e
métrica deste estudo.

## 7. Average Precision e desbalanceamento

- **REF010 — Davis e Goadrich (2006)** formaliza relações e diferenças entre curvas ROC e PR.
- **REF011 — Saito e Rehmsmeier (2015)** mostra por que a visualização precision-recall pode ser
  informativa quando a classe positiva é menos frequente.

Essas fontes apoiam a pertinência condicional de métricas PR. Elas não sustentam que AP seja
sempre melhor que ROC-AUC. A métrica congelada neste projeto continua sendo Average Precision
calculada por `sklearn.metrics.average_precision_score`; AP não será chamada genericamente de
PR-AUC, nem confundida com integração trapezoidal da curva.

## 8. Calibração e Brier

- **REF012 — Brier (1950)** é a referência original do escore quadrático para previsões
  probabilísticas.
- **REF013 — Van Calster et al. (2019)** distingue calibração de discriminação e discute sua
  avaliação em modelos preditivos.

O Brier complementa AP e ROC-AUC, mas não prova calibração perfeita. F7 continua sendo um
diagnóstico descritivo em faixas quantílicas de 2025; não houve recalibração nem novo teste.

## 9. Threshold e custos de decisão

- **REF014 — Fawcett (2006)** relaciona pontos de operação, distribuição de classes e custos de
  erro.
- **REF015 — Lipton, Elkan e Naryanaswamy (2014)** formaliza threshold para maximização de F1.
- **REF010** apoia a leitura conjunta de precision e recall.

Essas fontes ajudam a explicar o compromisso observado no cutoff congelado, mas não fornecem
custos, capacidade ou utilidade operacional da PRF. Maximizar F1 no OOF é uma decisão matemática
do desenho experimental; não equivale ao threshold operacionalmente ótimo.

## 10. SHAP e interpretação

- **REF016 — Lundberg e Lee (2017)** apresenta o framework SHAP.
- **REF017 — Lundberg et al. (2020)** fundamenta Tree SHAP e a passagem de explicações locais a
  resumos globais em modelos de árvore.
- **REF018 — Janzing, Minorics e Blöbaum (2020)** explicita a fronteira entre relevância de
  features e causalidade.
- **REF019 — Kumar et al. (2020)** registra limites conceituais de importâncias baseadas em
  valores de Shapley.

No TCC, SHAP descreve o comportamento preditivo do XGBoost em margem bruta. A soma das colunas
one-hot por predictor é uma escolha de apresentação que depende da representação e da
cardinalidade; ela não identifica fatores de risco, determinantes ou efeitos causais. A
literatura crítica limita o alcance interpretativo sem invalidar o uso descritivo já congelado.

## 11. Exposição e limites de risco

**REF005 — Chapman (1973)** sustenta que segurança viária requer uma definição das
oportunidades de exposição. O dataset deste projeto contém acidentes registrados, mas não
contém fluxo veicular, veículo-quilômetro, distância percorrida, número de viagens, população
exposta ou tempo sob cada condição.

Por isso, volumes e proporções de `target_grave` podem descrever composição entre ocorrências
registradas, mas não risco absoluto de ocorrer acidente ao trafegar em determinada rodovia,
horário, UF ou condição. Nenhum denominador novo é criado nesta fase.

## 12. Mapa para a Discussão

| Seção | Uso planejado | Referências principais | Fronteira obrigatória |
|---|---|---|---|
| 5.1 | Contextualizar heterogeneidade aplicada e ausência de exposição. | REF001–REF005 | Associação e proporção entre registros não são causalidade nem risco de acidente. |
| 5.2 | Situar capacidade preditiva, AP, discriminação, calibração e Brier. | REF001–REF003; REF010–REF013 | Não importar métricas externas nem declarar AP universalmente superior ou calibração perfeita. |
| 5.3 | Explicar RF/XGBoost e interpretar o ganho modesto. | REF001; REF003; REF008–REF009 | Referências de método não provam superioridade; rank é interno. |
| 5.4 | Fundamentar validação temporal, shift e avaliação em período posterior. | REF006–REF007; REF012–REF013 | Três folds não demonstram estabilidade nem tendência de melhora. |
| 5.5 | Interpretar precision, recall, F1, threshold e falsos positivos. | REF010; REF014–REF015 | Threshold por F1 não é decisão operacional ótima sem custos. |
| 5.6 | Explicar Tree SHAP, agregação e convergência parcial com EDA. | REF016–REF019 | Contribuição preditiva e associação descritiva não identificam causalidade. |
| 5.7 | Consolidar população, exposição, shift, decisão e interpretação. | REF005–REF007; REF013–REF019 | Preservar 2025 não completamente cego e todas as limitações internas. |

O detalhamento afirmação → referência está em `phase_5e1_claim_reference_map.csv`. O documento
5C não foi editado e ainda não recebeu citações.

## 13. Referências excluídas ou não verificadas

Não há referência `UNRESOLVED` no inventário final. Foram excluídos sem atribuição bibliográfica
no projeto:

- resultados encontrados somente em snippets ou agregadores sem confirmação editorial;
- preprints de gravidade rodoviária quando fontes revisadas por pares já cobriam a função;
- estudos recentes redundantes com o núcleo aplicado selecionado;
- páginas comerciais, blogs, fóruns e enciclopédias;
- fontes cuja utilidade dependeria de extrapolar causalidade, superioridade ou implantação.

Uma referência futura que não possa ser confirmada deverá entrar como `UNRESOLVED` e não poderá
sustentar o manuscrito até nova verificação.

## 14. Limites da busca

- A busca é dirigida pelos oito temas congelados, não uma revisão sistemática exaustiva.
- Não houve protocolo PRISMA, dupla triagem independente ou avaliação formal de risco de viés.
- Metadados e resumos verificados foram suficientes para o planejamento; PDFs protegidos não
  foram armazenados nem textos integrais reproduzidos.
- A proximidade entre populações, targets e estratégias de validação varia entre estudos.
- O estudo brasileiro selecionado fornece contexto aplicado, mas usa modelo, período e
  definição de severidade próprios.
- A adequação final de cada citação dependerá da frase exata redigida na Fase 5E.2.

## 15. Próxima etapa

A Fase 5E.2 poderá redigir a primeira versão de Resultados e Discussão usando apenas referências
`VERIFIED` e os mapas desta fase. A redação deverá preservar a separação entre evidência interna
e literatura externa, manter todas as cautelas científicas e não reabrir métricas, figuras,
modelos ou decisões experimentais.
