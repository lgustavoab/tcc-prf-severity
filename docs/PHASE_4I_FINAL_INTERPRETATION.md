# Fase 4I — Interpretação final do modelo

## 1. Objetivo

A Fase 4I descreve quais informações o XGBoost final utilizou com maior intensidade para
formar suas predições de gravidade entre as ocorrências registradas pela PRF em 2025. Ela
também caracteriza os scores de verdadeiros positivos, falsos positivos, falsos negativos e
verdadeiros negativos. A fase não procura melhorar performance nem reabrir o experimento.

## 2. Posição após a avaliação final

A interpretação ocorre depois da avaliação temporal final da Fase 4H. A população contém as
72.529 ocorrências de 2025 já avaliadas, e as probabilidades e decisões oficiais continuam
sendo as materializadas em `phase_4h_final_2025_predictions.parquet`.

A análise de 2025 realizada nesta fase é pós-avaliação. Nenhuma informação obtida na
interpretação foi utilizada para modificar o modelo ou qualquer decisão experimental
previamente congelada.

## 3. Estado congelado do modelo

Foram preservados integralmente:

- modelo `phase_4c_xgboost_baseline`, da família `xgboost_gradient_boosted_trees`;
- pipeline treinado em 2021–2024, com SHA-256
  `c9379d5d150dde80615740de750a49b887869a5f56343ce9b967d51937033351`;
- 22 predictors físicos, 226 features transformadas e 300 boosting rounds;
- threshold `0.23723246157169342`;
- predictions 4H, com SHA-256
  `411b5113060b19c3cc9da5fe1a6cddcf8a7d7662fe73102a6f3fdb2b05b88375`.

Não houve fit, `fit_transform`, nova chamada a `predict_proba`, tuning, calibrador, seleção de
feature ou novo threshold.

## 4. Método de interpretação

Foi usada a implementação nativa do XGBoost:

`Booster.predict(DMatrix, pred_contribs=True)`

O resultado corresponde a contribuições do tipo Tree SHAP para cada feature transformada,
mais um termo de bias. A interpretação abrange todo o conjunto de 2025 e usa somente
`preprocessor.transform` no preprocessing já fitado.

## 5. Escala das contribuições

As contribuições são aditivas na escala de margem bruta do modelo. Para cada observação, o
bias somado às 226 contribuições reconstrói a margem; a função logística converte essa margem
em probabilidade. Portanto, os valores não são pontos percentuais, odds ratios, coeficientes
inferenciais ou efeitos causais.

A reconciliação com as probabilidades oficiais da 4H apresentou:

- erro absoluto máximo: `4.0788276994829786e-07`;
- erro absoluto médio: `8.79821110029995e-08`;
- tolerância máxima pré-definida: `1e-6`.

## 6. Mapeamento das 226 features

As categorias das nove variáveis one-hot foram derivadas diretamente de `categories_` do
`OneHotEncoder` fitado. O mapeamento não usa divisão ingênua por `_`, que seria ambígua para
nomes e categorias com underscores. `km` foi mapeada como numérica e os 12 indicadores de
`tracado_via` como binários. As 226 features reconciliaram exatamente com os 22 predictors.

Para cada predictor e observação, a contribuição absoluta global é a soma das magnitudes de
suas features transformadas. O ranking usa a média dessa soma em 2025; a média assinada é
mantida apenas como diagnóstico, pois sinais podem se cancelar.

## 7. Importância global por predictor

| Rank | Predictor | Grupo | Features transformadas | Contribuição absoluta média | Participação |
|---:|---|---|---:|---:|---:|
| 1 | `uf` | categórica | 27 | 0.30914061427705003 | 26,6226% |
| 2 | `tipo_pista` | categórica | 3 | 0.2156401333022573 | 18,5705% |
| 3 | `hour` | categórica | 24 | 0.21537897879567514 | 18,5480% |
| 4 | `br` | categórica | 125 | 0.11535052497091844 | 9,9338% |
| 5 | `condicao_metereologica` | categórica | 10 | 0.06993538475580058 | 6,0227% |
| 6 | `km` | numérica | 1 | 0.05342911061350782 | 4,6012% |
| 7 | `dia_semana` | categórica | 7 | 0.04208529200467867 | 3,6243% |
| 8 | `tracado_reta` | binária | 1 | 0.03534370390834038 | 3,0437% |
| 9 | `tracado_declive` | binária | 1 | 0.026401786513688824 | 2,2737% |
| 10 | `tracado_rotatoria` | binária | 1 | 0.015050987950956999 | 1,2962% |

Os 22 shares somam aproximadamente 1. O número de níveis varia entre predictors; em especial,
`br` possui 125 colunas one-hot. O ranking agregado descreve o uso multivariado do modelo e
não deve ser lido isoladamente como uma escala substantiva entre conceitos.

## 8. Principais features transformadas

As 15 maiores magnitudes médias foram:

| Rank | Feature transformada | Predictor | Nível | Contribuição absoluta média |
|---:|---|---|---|---:|
| 1 | `categorical__tipo_pista_Simples` | `tipo_pista` | Simples | 0.16333748430331746 |
| 2 | `numeric__km` | `km` | — | 0.05342911061350782 |
| 3 | `categorical__uf_RJ` | `uf` | RJ | 0.049295763042818096 |
| 4 | `categorical__uf_RS` | `uf` | RS | 0.04558408870262294 |
| 5 | `categorical__uf_SP` | `uf` | SP | 0.039741662093391916 |
| 6 | `categorical__tipo_pista_Dupla` | `tipo_pista` | Dupla | 0.03763496880374983 |
| 7 | `categorical__uf_SC` | `uf` | SC | 0.037616869136038206 |
| 8 | `binary__tracado_reta` | `tracado_reta` | — | 0.03534370390834038 |
| 9 | `categorical__condicao_metereologica_Chuva` | `condicao_metereologica` | Chuva | 0.0273973269826363 |
| 10 | `binary__tracado_declive` | `tracado_declive` | — | 0.026401786513688824 |
| 11 | `categorical__hour_19` | `hour` | 19 | 0.024655146976092217 |
| 12 | `categorical__hour_18` | `hour` | 18 | 0.02037337809631397 |
| 13 | `categorical__br_116` | `br` | 116 | 0.020146821814230047 |
| 14 | `categorical__uf_PE` | `uf` | PE | 0.018949463187857958 |
| 15 | `categorical__condicao_metereologica_Céu Claro` | `condicao_metereologica` | Céu Claro | 0.01884140629201051 |

A magnitude informa quanto a feature participou das predições em média. O sinal médio de uma
coluna one-hot não deve ser transformado em uma afirmação causal ou em um efeito simples de
presença da categoria, pois as contribuições dependem do restante do perfil e da estrutura de
interações da árvore.

## 9. Análise TP/FP/FN/TN

As decisões já persistidas pela 4H reconciliaram exatamente: TP=15.817, FP=31.883, FN=4.676
e TN=20.153.

| Outcome | Linhas | Participação | Média | Mediana | P10 | P90 | Mínimo | Máximo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TP | 15.817 | 21,8078% | 0.349405 | 0.331816 | 0.256113 | 0.469000 | 0.237236 | 0.756967 |
| FP | 31.883 | 43,9590% | 0.323297 | 0.307983 | 0.249482 | 0.418579 | 0.237236 | 0.753018 |
| FN | 4.676 | 6,4471% | 0.197795 | 0.204486 | 0.152974 | 0.231860 | 0.079039 | 0.237216 |
| TN | 20.153 | 27,7861% | 0.190062 | 0.195533 | 0.142256 | 0.229577 | 0.055196 | 0.237232 |

## 10. Interpretação dos erros

O threshold baixo congelado na 4F produz muitos casos classificados como graves e, por
consequência, muitos falsos positivos, coerente com o recall final de 0,771825. TP e FP ficam
acima do cutoff por definição e suas distribuições se sobrepõem; FN e TN permanecem abaixo e
também apresentam sobreposição. As medianas de TP e FP são maiores que as de FN e TN, mas a
distribuição não fornece um novo cutoff e não foi usada para reotimização.

A tabela secundária por outcome registra 88 combinações predictor × outcome. Ela serve para
comparar como as magnitudes e sinais médios se distribuem entre acertos e erros, sem criar
políticas de subgroup, thresholds locais ou seleção de features.

## 11. Relação com a EDA

Há convergências cautelosas entre os resultados:

- `uf`, primeiro no ranking do modelo, já apresentava heterogeneidade descritiva de gravidade
  na EDA; isso mostra que o modelo usou informação estadual, não que UF cause gravidade ou que
  permita ordenar segurança entre estados;
- `tipo_pista`, segundo predictor, tinha contraste persistente entre Simples, Dupla e Múltipla,
  e `tipo_pista_Simples` foi a feature transformada de maior magnitude;
- `hour`, terceiro predictor, havia mostrado diferenças entre horas, incluindo 19h versus 8h;
  os níveis 19 e 18 aparecem entre as 15 maiores contribuições transformadas;
- meteorologia também apresentou variação descritiva na EDA e foi usada pelo modelo, mas
  categorias informadas, qualidade do registro e ausência de exposição continuam limitando a
  interpretação;
- `br` e `km` aparecem com contribuição relevante, mas dependem fortemente do contexto
  geográfico e rodoviário e não autorizam classificar rodovias como mais perigosas.

O ranking multivariado não precisa reproduzir contrastes univariados. Redundância entre
features, interações, não linearidades, cardinalidade e composição do conjunto podem alterar
a intensidade com que o XGBoost usa cada informação.

## 12. Associação, predição e causalidade

A EDA descreve associações e proporções observadas entre acidentes registrados. A
interpretação do XGBoost descreve informações usadas para discriminar a gravidade dessas
ocorrências. Nenhuma das duas, isoladamente, identifica efeitos causais.

Valores de contribuição do modelo descrevem a participação dos atributos nas predições do
XGBoost e não devem ser interpretados como efeitos causais.

## 13. Limitações

- Tree SHAP explica o modelo e a população analisada, não o processo causal real;
- contribuições estão em margem bruta, não em variação absoluta de probabilidade;
- o ranking depende da representação, inclusive da quantidade de níveis one-hot;
- predictors correlacionados ou redundantes podem compartilhar ou redistribuir contribuição;
- a análise cobre 2025 e pode não generalizar a outros períodos ou sistemas de registro;
- a base contém somente ocorrências registradas e não fornece denominadores de exposição.

## 14. Proibição de ajuste retrospectivo

Nenhum resultado da interpretação modificou modelo, threshold, features, preprocessing,
hiperparâmetros ou predictions 4H. Não foram criados thresholds por subgrupo, recalibração ou
seleção baseada em importância.

Na primeira tentativa de execução, uma validação excessivamente estrita exigiu ordem física
idêntica entre o dataset analítico e as predictions. A tentativa parou antes da transformação e
de `pred_contribs`, sem produzir tabelas ou resultados. O alinhamento foi corrigido para usar
ID com reconciliação de ano e target, validado por testes, e a segunda tentativa produziu os
artefatos reportados nesta fase.

## 15. Síntese

Em 2025, o XGBoost usou principalmente informações geográficas (`uf`), viárias
(`tipo_pista`), temporais (`hour`) e contextuais (`br`, meteorologia e `km`). A interpretação
reconstruiu as probabilidades 4H dentro da tolerância numérica e preservou integralmente o
experimento. Esses resultados ajudam a explicar o comportamento preditivo, sem converter o
ranking em causalidade ou em uma nova etapa de seleção.

## 16. Próximo passo

O próximo passo é consolidar as perguntas de pesquisa e mapear cada uma às evidências
produzidas nas Fases 2–4, preparando a apresentação científica dos resultados no TCC.
