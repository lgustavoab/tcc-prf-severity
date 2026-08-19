# Fase 5A — Consolidação científica

## 1. Objetivo

Esta fase organiza os resultados congelados do projeto na cadeia rastreável **pergunta →
método → evidência → resultado observado → resposta → limitações**. Não houve nova EDA,
modelagem, predição, interpretação computacional, teste estatístico ou ajuste experimental.
Os números foram lidos das tabelas versionadas das Fases 2–4; os documentos anteriores foram
usados para contexto metodológico e cautelas.

## 2. Pergunta principal

> Quais características temporais, geográficas, meteorológicas e viárias estão associadas à
> gravidade dos acidentes registrados em rodovias federais brasileiras e em que medida modelos
> de aprendizado de máquina conseguem identificar ocorrências graves?

A pergunta trata da gravidade entre acidentes registrados pela PRF. Ela não estima a
probabilidade de ocorrer um acidente, não ordena rodovias por risco de acidente e não identifica
fatores causais.

## 3. Perguntas específicas

- **RQ1:** Quais características estão associadas a maiores proporções de acidentes graves
  entre as ocorrências registradas pela PRF?
- **RQ2:** Em que medida características disponíveis no momento inicial da ocorrência
  permitem distinguir acidentes graves dos não graves?
- **RQ3:** Como Regressão Logística, Random Forest e XGBoost se comparam em validação temporal?
- **RQ4:** O desempenho preditivo permanece consistente entre diferentes anos de validação?
- **RQ5:** O modelo selecionado mantém desempenho em um período temporal posterior, reservado
  para avaliação final em 2025?

A Fase 4I fornece evidência complementar às perguntas existentes; nenhuma sexta pergunta foi
criada após a observação dos resultados.

## 4. Escopo interpretativo

### 4.1 Dataset condicionado a acidentes registrados

A população contém ocorrências registradas pela PRF entre 2021 e 2025. O target indica morte
ou ferimento grave em uma ocorrência registrada. Não há amostra de viagens sem acidente e o
modelo não prediz se um acidente ocorrerá.

### 4.2 Associação não implica causalidade

Diferenças de proporção observadas na EDA são associações descritivas. Elas podem refletir
composição geográfica, tráfego, registro, condições correlacionadas e outras variáveis não
controladas. Não identificam efeitos causais.

### 4.3 Predição não equivale a inferência causal

AP, ROC-AUC, Brier e métricas de threshold medem aspectos da capacidade preditiva no desenho
temporal adotado. Tree SHAP descreve como o XGBoost usou features em suas predições, não por
que a gravidade ocorreu.

### 4.4 Limitação de exposição

Não há denominadores como fluxo veicular, quilômetros percorridos, população exposta ou tempo
sob cada condição. Assim, volume e proporção de graves entre registros não medem risco absoluto
de acidente em uma região, rodovia, horário ou condição meteorológica.

## 5. RQ1 — Associações descritivas

**Método e evidências.** A resposta deriva da EDA das Fases 2A–2G, sobretudo da matriz de
evidências 2F e da síntese 2G. Frequência absoluta e proporção grave foram tratadas
separadamente, com estabilidade anual descritiva e cortes mínimos apenas para destaques.

**Principais resultados.** Temporalmente, Plena Noite apresentou 32,472550% de graves contra
25,304737% em Pleno dia; fim de semana, 30,192457% contra 27,330336% em dias úteis; e 19h,
33,732337% contra 23,124346% às 8h. Geograficamente, Nordeste e Sul apresentaram 35,917125% e
24,874032%, enquanto MA e SP formaram extremos estaduais de 45,811700% e 18,639426%. Entre
características viárias, pista Simples teve 33,711528% contra 23,351325% em Dupla. Entre
condições meteorológicas informadas com `n >= 500`, Nevoeiro/Neblina teve 31,501057% e
Garoa/Chuvisco 22,264400%. Tipo e causa registrados tiveram contrastes ainda maiores, mas
carregam cautelas de temporalidade e taxonomia.

**Resposta sintética.** As ocorrências registradas exibiram heterogeneidade temporal,
geográfica, meteorológica e viária consistente com associações descritivas relevantes. Noite,
fim de semana, certos contextos geográficos, pista Simples e algumas condições meteorológicas
informadas apresentaram maiores proporções graves nas comparações selecionadas. Isso não
significa maior frequência absoluta em todos os casos nem efeito causal.

**Limitações.** A natureza é observacional, não há exposição, as comparações são univariadas e
tipo/causa podem ser consolidados após a ocorrência. Categorias especiais como meteorologia
`Ignorado` caracterizam qualidade de informação, não condições substantivas.

## 6. RQ2 — Capacidade preditiva

**Método e evidências.** A política 3B definiu compatibilidade conceitual com o momento
preditivo, a 3D congelou validação temporal, as Fases 4A–4C treinaram três famílias e a 4H
avaliou o XGBoost final em 2025. A disponibilidade operacional por campo não foi comprovada.

**Resultados probabilísticos.** Em 2025, o XGBoost obteve AP `0.3974456687131155`, acima da
prevalência positiva `0.2825490493457789`; ROC-AUC `0.6285562620583193`; e Brier
`0.19382199321256413`. Esses valores indicam sinal preditivo e capacidade discriminativa
moderada, não performance excepcional.

**Threshold.** O cutoff `0.23723246157169342`, selecionado somente no OOF temporal, produziu
precision `0.33159329140461213`, recall `0.7718245254477138` e F1
`0.4638892554954321` em 2025, com 31.883 FP e 15.817 TP. O ranking probabilístico e a decisão
binária são objetos distintos: o threshold prioriza recall e aceita precision relativamente
baixa.

**Resposta.** As características autorizadas distinguem parcialmente ocorrências graves das
não graves. Existe informação preditiva útil, porém limitada/moderada; a configuração de
decisão alcança recall alto ao custo de muitos falsos positivos.

**Limitações.** A compatibilidade temporal das features é uma premissa metodológica, não uma
auditoria do fluxo operacional da PRF. Custos reais de FP/FN não foram incorporados e o
modelo não substitui julgamento operacional.

## 7. RQ3 — Comparação dos modelos

| Modelo | AP média não ponderada | Desvio padrão populacional | Rank |
|---|---:|---:|---:|
| Regressão Logística | 0.3935082935577437 | 0.004878870165386994 | 3 |
| Random Forest | 0.3959839275865431 | 0.00558166427201829 | 2 |
| XGBoost | 0.40081097458169895 | 0.007430307892479644 | 1 |

Os deltas médios foram `0.0024756340287994116` de Logística para Random Forest,
`0.00730268102395526` de Logística para XGBoost e `0.004827046995155848` de Random Forest
para XGBoost.

**Resposta.** XGBoost apresentou a maior AP média nos três folds temporais e foi selecionado
pela regra pré-especificada; Random Forest ficou em segundo e Regressão Logística em terceiro.
A maior complexidade trouxe ganho incremental, não transformação radical da capacidade
discriminativa.

**Cautela.** Os ranks e deltas são descritivos para três folds. Não foram realizados p-values,
bootstrap, intervalos retrospectivos ou testes post hoc; a seleção não prova superioridade
universal.

## 8. RQ4 — Consistência temporal

Os folds expanding-window validaram 2022, 2023 e 2024, sempre com treino anterior ao ano de
validação.

| Modelo | AP 2022 | AP 2023 | AP 2024 | Amplitude |
|---|---:|---:|---:|---:|
| Regressão Logística | 0.3866809762501382 | 0.3960583174959361 | 0.3977855869271569 | 0.011104610677018678 |
| Random Forest | 0.3880957692713414 | 0.3996726973944841 | 0.4001833160938038 | 0.012087546822462436 |
| XGBoost | 0.390374557377428 | 0.40496847114969603 | 0.4070898952179728 | 0.016715337840544797 |

**Resposta.** As três famílias apresentaram APs mais elevadas nos folds posteriores, sem queda
abrupta ou colapso de generalização. XGBoost manteve a maior AP em cada fold, embora também
tenha apresentado a maior amplitude e dispersão.

**Limitações.** São apenas três folds; o período e o volume de treino crescem simultaneamente à
mudança do ano de validação. A sequência não permite atribuir a diferença exclusivamente ao
tempo, inferir tendência de melhora ou sustentar afirmação de diferença significativa.

## 9. RQ5 — Generalização em 2025

**Congelamento prévio.** A Fase 4G materializou o pipeline treinado em 2021–2024 com 22
predictors, 226 features transformadas e 300 rounds. Modelo, hiperparâmetros, preprocessing e
threshold foram fixados antes da avaliação 4H.

**Resultados e deltas.** Em 2025, AP foi `0.3974456687131155`, ROC-AUC
`0.6285562620583193` e Brier `0.19382199321256413`. A AP ficou
`-0.003365305868583468` em relação à média interna e `-0.0096442265048573` em relação ao
Fold 3. ROC-AUC diferiu `-0.0022936789354663922` da média e Brier,
`-0.00007547537507013313`. No threshold congelado, os deltas contra OOF foram
`-0.0017078575767531246` em precision, `+0.0013681850981619448` em recall e
`-0.0014194485644579147` em F1.

**Resposta.** O modelo manteve desempenho aproximadamente consistente no período posterior.
Os deltas foram pequenos, e não houve colapso de AP, ROC-AUC, Brier ou comportamento do
threshold em 2025.

**Ressalva de blindagem.** 2025 não foi completamente cego a análises estruturais porque
participou de EDA e drift. Sua performance preditiva, entretanto, não selecionou modelo ou
threshold, não participou do refit e não motivou alteração posterior.

## 10. Interpretação complementar do XGBoost

A Fase 4I aplicou Tree SHAP nativo sobre 2025, em escala de margem bruta. Os cinco predictors
com maior contribuição absoluta agregada foram:

| Rank | Predictor | Contribuição absoluta média | Features transformadas |
|---:|---|---:|---:|
| 1 | `uf` | 0.30914061427705003 | 27 |
| 2 | `tipo_pista` | 0.2156401333022573 | 3 |
| 3 | `hour` | 0.21537897879567514 | 24 |
| 4 | `br` | 0.11535052497091844 | 125 |
| 5 | `condicao_metereologica` | 0.06993538475580058 | 10 |

`uf`, `tipo_pista`, `hour` e meteorologia também apresentaram heterogeneidade descritiva na
EDA, e suas features derivadas tiveram participação relevante nas predições. Isso não confirma
causalidade. O ranking representa uso pelo modelo, é pós-avaliação e depende de interações,
redundância, representação e cardinalidade; `br`, em particular, agrega 125 colunas OHE.

## 11. Resposta à pergunta principal

Entre as ocorrências registradas pela PRF, a gravidade apresentou heterogeneidade temporal,
geográfica, meteorológica e viária. Noite e fim de semana tiveram proporções maiores nas
comparações adotadas; macrorregiões e UFs diferiram; pista Simples se destacou frente a Dupla;
e condições meteorológicas informadas também variaram. Tipo e causa registrados mostraram
contrastes elevados, mas possuem limitações adicionais de temporalidade e taxonomia. Esses
resultados descrevem associações na população registrada, sem demonstrar causalidade ou risco
absoluto de acidente.

As features conceitualmente compatíveis com o cenário preditivo forneceram sinal para
distinguir gravidade, mas com capacidade moderada. XGBoost teve a maior AP média temporal, com
ganhos modestos sobre Random Forest e Regressão Logística. O desempenho não colapsou nos folds
e permaneceu próximo das referências internas em 2025. No threshold congelado, o modelo
priorizou recall e gerou muitos falsos positivos, deixando explícito o compromisso operacional.

A interpretação pós-avaliação mostrou uso relevante de informação estadual, tipo de pista,
hora, BR e meteorologia. Essa convergência parcial com a EDA ajuda a compreender o modelo, mas
não converte contribuição preditiva em efeito causal. A síntese sustenta as cinco perguntas
congeladas sem reabrir decisões experimentais.

## 12. Limitações consolidadas

1. A base contém somente acidentes registrados pela PRF.
2. Não há denominadores de exposição ao tráfego, distância, população ou condição.
3. O estudo é observacional.
4. Associações descritivas não identificam causalidade.
5. Disponibilidade no momento inicial é premissa metodológica, não validação operacional do
   fluxo interno da PRF.
6. 2025 não foi completamente cego para EDA e drift estrutural.
7. A capacidade discriminativa observada é limitada/moderada.
8. O threshold prioriza recall e produz muitos falsos positivos.
9. Tree SHAP descreve contribuição preditiva na margem e não efeito causal.
10. Cardinalidade e representação podem influenciar agregações de contribuição.
11. Há somente três folds internos e um ano de avaliação final.
12. Mudanças futuras de população, taxonomia e processo de registro podem afetar generalização.

## 13. Implicações para a redação do TCC

A seção de Resultados deve separar evidência descritiva, comparação preditiva, generalização
final e interpretação do modelo. A Discussão deve tratar ganhos modestos, compromisso do
threshold, ausência de exposição e limites não causais. As tabelas 5A funcionam como índice de
rastreabilidade para selecionar evidências sem repetir todo o inventário analítico.

### Candidatos a figuras

| Candidato | Prioridade | Uso proposto |
|---|---|---|
| Prevalência grave por ano | útil | Contextualizar estabilidade do target. |
| Principais associações descritivas da Fase 2 | essencial | Responder RQ1 com poucos contrastes centrais. |
| AP média dos três modelos | essencial | Responder RQ3 e mostrar ganhos incrementais. |
| AP por fold temporal | essencial | Responder RQ4 sem ocultar variação anual. |
| Calibração de 2025 | útil | Complementar AP/ROC-AUC/Brier na RQ5. |
| Top predictors por contribuição absoluta | útil | Explicar o comportamento pós-avaliação. |
| Matriz de confusão no threshold congelado | essencial | Evidenciar recall alto e falsos positivos. |
| Distribuições completas de scores por outcome | dispensável | Manter em tabela se houver excesso de figuras. |

Nenhuma figura foi criada nesta fase.

## 14. Próxima etapa

Selecionar as evidências, tabelas e figuras que integrarão os capítulos de Resultados e
Discussão, preservando a distinção entre descrição, predição e interpretação não causal.
