# Primeira redação acadêmica — Resultados e Discussão

> Versão de trabalho da Fase 5E.2. A redação organiza resultados científicos já congelados e
> literatura previamente verificada. Numeração, normalização bibliográfica e integração com os
> demais capítulos permanecem sujeitas à revisão da Fase 5F.

# 4. Resultados

## 4.1 Caracterização da população analisada

A população analisada reuniu 342.624 ocorrências registradas pela Polícia Rodoviária Federal
entre 2021 e 2025. O desfecho `target_grave` foi definido no nível da ocorrência pela presença
de ao menos uma morte ou de ao menos um ferido grave. Sob essa definição, foram identificadas
96.857 ocorrências graves e 245.767 não graves, correspondentes a uma prevalência global de
28,27%. Esses valores delimitam o universo empírico do estudo: acidentes efetivamente
registrados na base pública, e não o conjunto de deslocamentos realizados na malha federal.

A Tabela 1 [T1] mostra que as prevalências anuais ficaram entre 28,06% e 28,49%. A pequena
amplitude observada permite descrever a composição anual do desfecho como aproximadamente
constante no período, sem que essa constatação descritiva constitua teste de estabilidade
estatística. As contagens também evidenciam variação do volume anual de registros, razão pela
qual volume e prevalência são apresentados separadamente.

**Tabela 1 [T1] — Caracterização anual da população de ocorrências**

| Ano | Ocorrências | Graves | Não graves | Prevalência grave (%) |
|---|---:|---:|---:|---:|
| 2021 | 64.567 | 18.118 | 46.449 | 28,0608 |
| 2022 | 64.606 | 18.409 | 46.197 | 28,4943 |
| 2023 | 67.766 | 19.212 | 48.554 | 28,3505 |
| 2024 | 73.156 | 20.625 | 52.531 | 28,1932 |
| 2025 | 72.529 | 20.493 | 52.036 | 28,2549 |
| **Total** | **342.624** | **96.857** | **245.767** | **28,2692** |

*Fonte: elaboração própria a partir de `T1_population_characterization.csv`.*

## 4.2 Associações descritivas com gravidade

Definida a população, a RQ1 foi examinada por contrastes univariados entre categorias das
dimensões temporais, geográficas, viárias e meteorológicas. As comparações a seguir descrevem a
proporção de `target_grave` entre ocorrências registradas em cada contexto. Elas não incorporam
denominadores de circulação, controle multivariado ou identificação de mecanismos causais.

### 4.2.1 Padrões temporais e de calendário

Os contrastes temporais selecionados apresentaram diferenças na proporção de ocorrências
graves. Em Plena Noite, a prevalência foi de 32,47%, ante 25,30% em Pleno dia, diferença de
7,17 pontos percentuais. Nos fins de semana, observou-se 30,19%, em comparação com 27,33% nos
dias úteis. Na dimensão horária, 19h apresentou 33,73%, enquanto 8h apresentou 23,12%.

A Figura 1 [F1] preserva cada contraste em um painel próprio. Por isso, as seis categorias não
compõem uma ordenação conjunta: fase do dia, grupo de dias e hora registrada representam
recortes diferentes e parcialmente relacionados. Os resultados sustentam heterogeneidade
temporal entre os registros, mas não permitem atribuí-la ao volume de circulação nem isolar o
efeito de cada marcador de calendário.

![Figura 1 [F1] — Contrastes temporais observados na proporção de ocorrências graves](../reports/figures/tcc/F1_temporal_contrasts.png)

### 4.2.2 Padrões geográficos, viários e meteorológicos

Também foram observadas diferenças entre contextos geográficos, viários e meteorológicos. A
prevalência foi de 35,92% no Nordeste e de 24,87% no Sul. Entre os extremos estaduais
selecionados, Maranhão e São Paulo apresentaram, respectivamente, 45,81% e 18,64%. Quanto ao
tipo de pista, a categoria Simples registrou 33,71%, e a categoria Dupla, 23,35%. Entre
condições meteorológicas efetivamente informadas e com ao menos 500 ocorrências, os valores
foram de 31,50% para Nevoeiro/Neblina e 22,26% para Garoa/Chuvisco.

Essas comparações são organizadas em facetas distintas na Figura 2 [F2], sem formar um ranking
comum entre macrorregião, unidade federativa, pista e meteorologia. A categoria meteorológica
`Ignorado` permanece registrada nas tabelas completas como aspecto de informação ausente, mas
não integra o contraste substantivo. A ausência de exposição e as diferenças de composição
entre categorias impedem transformar as proporções em medidas de segurança territorial,
viária ou meteorológica.

![Figura 2 [F2] — Heterogeneidade descritiva em contextos geográficos, viários e meteorológicos](../reports/figures/tcc/F2_contextual_contrasts.png)

### 4.2.3 Tipo e causa registrados

Tipo e causa registrados produziram os maiores contrastes selecionados na síntese descritiva.
Para tipo, Atropelamento de Pedestre versus Colisão traseira apresentou diferença de 44,35
pontos percentuais. Para causa, Pedestre andava na pista versus Reação tardia ou ineficiente do
condutor apresentou diferença de 51,48 pontos percentuais. Os valores integrais e as categorias
comparadas permanecem no Apêndice A4.

Embora relevantes para caracterizar o conjunto de dados, essas variáveis não foram
incorporadas ao conjunto preditivo principal. Seus campos podem ser conhecidos ou consolidados
após o momento preditivo assumido, e suas taxonomias apresentaram mudanças entre períodos. A
preservação dos achados na análise descritiva, portanto, não implica autorização automática
para uso no cenário preditivo definido.

## 4.3 Desenho preditivo e comparação dos modelos

Regressão Logística, Random Forest e XGBoost foram avaliados nos mesmos três folds temporais,
com Average Precision (AP) calculada separadamente em cada validação e agregada por média
aritmética não ponderada. As médias foram de 0,3935 para Regressão Logística, 0,3960 para
Random Forest e 0,4008 para XGBoost. A Figura 3 [F4] apresenta essa ordenação sob a regra
congelada de comparação.

As diferenças médias foram pequenas em termos absolutos: 0,0025 entre Random Forest e
Regressão Logística, 0,0073 entre XGBoost e Regressão Logística e 0,0048 entre XGBoost e
Random Forest. Assim, o XGBoost obteve a maior AP média e foi selecionado conforme a regra
pré-especificada, mas o incremento observado foi modesto. A comparação é descritiva para três
folds e não recebeu teste post hoc.

![Figura 3 [F4] — Average Precision média nos três folds temporais](../reports/figures/tcc/F4_model_average_precision.png)

## 4.4 Consistência na validação temporal

Nos folds expanding-window, as validações corresponderam sucessivamente a 2022, 2023 e 2024,
sempre com treinamento restrito aos anos anteriores. O XGBoost apresentou AP de 0,3904,
0,4050 e 0,4071 nesses três folds e ocupou a primeira posição em cada um deles. As três
famílias apresentaram APs mais elevadas nos folds posteriores, sem queda abrupta ou colapso de
generalização no intervalo observado.

Essa sequência não isola uma variação atribuível ao ano. O período e o volume de treinamento
crescem ao mesmo tempo que o ano de validação muda, de modo que os valores não demonstram uma
tendência temporal de melhora. A Figura 4 [F5] apresenta os nove resultados sem selecionar o
melhor fold isolado e permite observar tanto a ordenação quanto a dispersão entre as três
validações.

![Figura 4 [F5] — Average Precision por ano de validação](../reports/figures/tcc/F5_temporal_fold_average_precision.png)

## 4.5 Capacidade preditiva e avaliação final em 2025

Após a seleção interna e o refit em 2021–2024, o pipeline congelado foi avaliado nas
ocorrências de 2025. A AP foi de 0,3974, a ROC-AUC de 0,6286 e o Brier score de 0,1938. No
threshold previamente fixado, a precision foi de 0,3316, o recall de 0,7718 e o F1 de 0,4639.
Em conjunto, AP e ROC-AUC indicam capacidade discriminativa moderada, enquanto o Brier oferece
uma medida complementar do erro das probabilidades.

Em relação às referências de desenvolvimento, os deltas foram de −0,0034 para AP, −0,0023
para ROC-AUC e aproximadamente −0,00008 para Brier. A Tabela 2 [T2] mostra ainda que as
métricas do threshold ficaram próximas das observadas no OOF temporal. O ano de 2025 não foi
usado para selecionar modelo, threshold ou configuração de refit, nem motivou ajuste posterior;
contudo, havia participado de EDA e auditoria de drift, razão pela qual não é descrito como
completamente cego em sentido estrutural.

**Tabela 2 [T2] — Avaliação temporal final em 2025**

| Métrica | Referência de desenvolvimento | 2025 | Δ 2025 − referência | Referência utilizada |
|---|---:|---:|---:|---|
| Average Precision | 0,4008 | 0,3974 | −0,0034 | Média interna dos folds |
| ROC-AUC | 0,6308 | 0,6286 | −0,0023 | Média interna dos folds |
| Brier score | 0,1939 | 0,1938 | −0,0001 | Média interna; menor é melhor |
| Precision | 0,3333 | 0,3316 | −0,0017 | OOF temporal no threshold congelado |
| Recall | 0,7705 | 0,7718 | +0,0014 | OOF temporal no threshold congelado |
| F1 | 0,4653 | 0,4639 | −0,0014 | OOF temporal no threshold congelado |

*Fonte: elaboração própria a partir de `T2_final_2025_evaluation.csv`.*

## 4.6 Comportamento do threshold congelado

O threshold de 0,237232 foi selecionado exclusivamente nas previsões OOF temporais de 2022,
2023 e 2024, mediante maximização de F1 para a classe grave. Aplicado sem alteração em 2025,
produziu 20.153 verdadeiros negativos, 31.883 falsos positivos, 4.676 falsos negativos e
15.817 verdadeiros positivos. A Figura 5 [F6] apresenta a distribuição das decisões resultante
desse ponto de operação.

O recall de 77,18% indica que a maior parte das ocorrências graves foi classificada como
positiva, enquanto a precision de 33,16% e o F1 de 0,4639 mostram que uma parcela substancial
dos alertas positivos correspondeu a ocorrências não graves. Esse resultado descreve o
compromisso produzido pela regra matemática de seleção. Não foram avaliados custos de erro,
capacidade de atendimento ou utilidade institucional, e o cutoff não constitui recomendação de
uso.

![Figura 5 [F6] — Matriz de confusão em 2025 no threshold congelado](../reports/figures/tcc/F6_confusion_matrix_2025.png)

## 4.7 Diagnósticos complementares

### 4.7.1 Calibração descritiva em 2025

As probabilidades de 2025 foram organizadas em dez faixas quantílicas e, em cada uma, a média
predita foi comparada à proporção grave observada. A Figura 6 [F7] apresenta essas relações e a
referência `y = x`, complementando as métricas globais sem alterar as previsões produzidas pelo
pipeline.

O diagnóstico permanece descritivo: nenhum calibrador foi ajustado e as faixas não constituem
um novo teste de desempenho. A figura registra como previsão média e frequência observada se
relacionaram nos agrupamentos publicados, sem sustentar um julgamento categórico de calibração
nem reabrir a avaliação final.

![Figura 6 [F7] — Calibração descritiva das probabilidades em 2025](../reports/figures/tcc/F7_calibration_2025.png)

### 4.7.2 Contribuição agregada dos predictors

A interpretação pós-avaliação por Tree SHAP, calculada na escala de margem bruta do XGBoost,
colocou UF, Tipo de pista, Hora, BR e Condição meteorológica nas cinco primeiras posições do
ranking agregado. A Figura 7 [F8] apresenta os oito predictors líderes por contribuição
absoluta média, preservando a ordenação publicada.

O agrupamento foi realizado pelo predictor de origem, de modo que BR agrega 125 colunas
one-hot. Os valores representam participação no comportamento preditivo do modelo e dependem
da representação, da cardinalidade, das interações e das redundâncias existentes. Por isso, o
ranking não identifica mecanismos causais nem determina a seleção futura de variáveis.

![Figura 7 [F8] — Principais contribuições agregadas nas predições do XGBoost](../reports/figures/tcc/F8_predictor_contributions.png)

# 5. Discussão

## 5.1 Heterogeneidade da gravidade entre ocorrências registradas

Os resultados respondem à RQ1 ao mostrar que a prevalência de `target_grave` não se distribuiu
uniformemente entre os contextos registrados. Contrastes temporais, geográficos, viários e
meteorológicos apresentaram magnitudes distintas, enquanto tipo e causa exibiram diferenças
ainda maiores sob cautelas adicionais. Esse conjunto de achados pode ser contextualizado por
uma literatura que estuda a gravidade rodoviária em populações e formulações diversas, com
métodos estatísticos e de aprendizado de máquina variados (Iranitalab e Khattak, 2017; Sameen
e Pradhan, 2017; Komol et al., 2021).

No contexto brasileiro, Franceschi et al. (2022) também analisaram severidade em rodovias
federais com uma definição, um período e um modelo próprios. A proximidade temática permite
estabelecer diálogo com uma aplicação nacional, mas não torna seus coeficientes ou conclusões
diretamente comparáveis aos contrastes deste estudo. Aqui, as diferenças derivam de análises
univariadas da população registrada e não de uma estimativa ajustada de mecanismos que
produzem gravidade.

A interpretação exige ainda separar volume, proporção condicional e oportunidade de exposição.
Chapman (1973) mostra que medidas de segurança viária dependem da definição das oportunidades
relevantes de exposição. Como a base utilizada não inclui fluxo veicular, veículo-quilômetro,
número de viagens, população exposta ou tempo sob cada condição, as prevalências descrevem a
composição dos acidentes registrados. Elas não quantificam a ocorrência de acidentes fora
desse conjunto condicionado de registros.

## 5.2 O que as características conseguem prever

A RQ2 foi respondida pela presença de sinal preditivo moderado. Em 2025, a AP ficou
acima da prevalência da classe positiva e a ROC-AUC permaneceu próxima de 0,63, indicando que
as características autorizadas contêm informação para ordenar parcialmente ocorrências graves
e não graves. A separação, entretanto, é imperfeita, como também evidencia a combinação de
precision mais baixa e recall mais alto no threshold congelado.

A escolha de AP como métrica primária dirige a atenção à classe positiva em um problema no
qual ela é menos frequente. Curvas ROC e Precision–Recall ocupam espaços relacionados, mas
distintos (Davis e Goadrich, 2006), e a visualização Precision–Recall pode ser especialmente
informativa em dados desbalanceados (Saito e Rehmsmeier, 2015). Neste estudo, a definição
operacional de AP permanece a do contrato experimental; seu uso não implica que a métrica
seja universalmente preferível à ROC-AUC.

Discriminação e calibração são propriedades diferentes de previsões probabilísticas (Van
Calster et al., 2019). O Brier score complementa as métricas de ordenação ao quantificar erro
quadrático probabilístico (Brier, 1950), enquanto a Figura 6 oferece uma inspeção agrupada da
relação entre probabilidades e frequências observadas. A leitura conjunta desses diagnósticos
não elimina outra premissa do desenho: a compatibilidade das features com o momento preditivo
foi adotada metodologicamente, mas o dataset público não comprova quando cada campo é preenchido
no fluxo interno da PRF.

## 5.3 Complexidade dos modelos e ganhos modestos

A comparação da RQ3 mostra que a complexidade adicional não produziu uma mudança ampla de
capacidade discriminativa. Random Forest combina árvores por agregação (Breiman, 2001),
enquanto XGBoost implementa boosting de árvores de forma regularizada e escalável (Chen e
Guestrin, 2016). Esses mecanismos oferecem recursos para representar não linearidades e
interações ausentes em uma especificação linear simples, mas as referências fundadoras
explicam os métodos e não antecipam qual família deveria liderar neste conjunto de dados.

No experimento congelado, o XGBoost alcançou a maior AP em cada fold e a maior média, seguido
por Random Forest e Regressão Logística. A pequena distância entre as três famílias indica que,
sob este desenho, a flexibilidade adicional dos modelos de árvores produziu incremento limitado
em AP. Estudos comparativos de gravidade também mostram que a ordenação entre famílias depende
da população, do desfecho, das variáveis e da validação adotada (Iranitalab e Khattak, 2017;
Komol et al., 2021).

Desse modo, a seleção do XGBoost é válida para a regra previamente definida, mas não constitui
uma afirmação geral sobre ensembles. O resultado está condicionado aos períodos de 2021–2024,
às 22 variáveis físicas, ao preprocessing, às configurações fixas e à AP média não ponderada.
Sem busca ampla de hiperparâmetros ou inferência sobre os deltas, a interpretação adequada é a
de liderança interna com ganho modesto.

## 5.4 Consistência temporal e generalização

A validação temporal foi desenhada para respeitar a direção do tempo: cada conjunto de
validação ocorreu depois dos dados usados no respectivo treinamento. Esse princípio é
importante quando observações têm dependência temporal e o interesse recai sobre desempenho
futuro (Roberts et al., 2017). Nos resultados, não houve queda abrupta entre os três folds, e o
XGBoost preservou a primeira posição em 2022, 2023 e 2024.

As APs mais elevadas nos folds posteriores não isolam uma evolução temporal. A janela de
treinamento cresce entre as validações, enquanto o próprio ano avaliado também muda. Logo, a
sequência é compatível com diferentes combinações de quantidade de treino e composição anual,
sem permitir atribuição exclusiva a qualquer uma delas. Três folds oferecem evidência
descritiva limitada e não demonstram invariância do desempenho.

Em 2025, AP, ROC-AUC, Brier e as métricas no threshold permaneceram próximas das referências
internas, o que responde à RQ5 por manutenção aproximada em um período posterior. Ainda assim,
mudanças entre distribuições de desenvolvimento e aplicação podem afetar generalização
(Moreno-Torres et al., 2012), e um único ano final não cobre variações futuras. Além disso,
2025 foi protegido da seleção preditiva, mas já havia sido observado em EDA e drift estrutural;
essa distinção impede tratá-lo como um período inteiramente desconhecido para o projeto.

## 5.5 Threshold, recall e falsos positivos

O threshold traduz scores contínuos em decisões binárias e, por isso, responde a uma questão
distinta da ordenação probabilística. Diferentes pontos de operação alteram a relação entre
precision e recall e podem implicar custos de erro distintos (Davis e Goadrich, 2006; Fawcett,
2006). No ponto congelado, o recall de aproximadamente 77% foi acompanhado de precision de
aproximadamente 33% e de 31.883 falsos positivos.

A maximização de F1 possui uma regra matemática própria para selecionar o cutoff (Lipton,
Elkan e Naryanaswamy, 2014). No presente desenho, essa regra foi aplicada somente ao OOF
temporal, com critérios de desempate definidos antes da avaliação final. O comportamento
semelhante em 2025 mostra reprodução descritiva do compromisso, mas não converte a escolha em
ótimo institucional.

Uma decisão de implantação exigiria informações que não fazem parte deste estudo, como custos
relativos de falsos positivos e falsos negativos, capacidade de resposta, benefício
operacional e impacto institucional. Sem esses elementos, não é possível concluir que o ponto
selecionado maximize utilidade para a PRF. O resultado informa o volume de erros associado à
regra experimental e explicita por que recall elevado não deve ser interpretado isoladamente.

## 5.6 Relação entre EDA e interpretação do XGBoost

Há convergência parcial entre os contrastes descritivos e o ranking pós-avaliação. Unidade
federativa, tipo de pista, hora e condição meteorológica mostraram heterogeneidade na EDA e
também figuraram entre os predictors de maior contribuição absoluta agregada. Essa aproximação
indica que o XGBoost utilizou informações pertencentes às mesmas dimensões empíricas, mas não
significa que repetiu diretamente os contrastes univariados.

SHAP representa predições por atribuições aditivas de contribuição (Lundberg e Lee, 2017), e
Tree SHAP permite resumir explicações locais em descrições globais de modelos de árvore
(Lundberg et al., 2020). No presente estudo, as contribuições foram calculadas em margem bruta
e agregadas por predictor de origem. Interações, não linearidades, redundância, composição,
codificação one-hot e cardinalidades distintas ajudam a explicar por que a ordenação
multivariada não precisa coincidir com a amplitude dos contrastes descritivos.

As atribuições permanecem vinculadas ao comportamento do modelo, não ao processo que gerou os
dados. A quantificação de relevância por valores de Shapley envolve escolhas distributivas e
questões causais que não são resolvidas pela explicação preditiva (Janzing, Minorics e Blöbaum,
2020), e seu uso como medida geral de importância possui limitações conceituais (Kumar et al.,
2020). Assim, a Figura 7 sustenta interpretação do XGBoost avaliado, sem transformar as
contribuições agregadas em determinantes da gravidade.

## 5.7 Limitações

A primeira limitação decorre da população e da mensuração. O estudo cobre somente acidentes
registrados pela PRF e não dispõe de denominadores de exposição; portanto, volumes e
prevalências permanecem condicionados aos registros. O desenho observacional também impede
separar efeitos de composição, contexto, registro e variáveis omitidas. A literatura aplicada
serve para contextualizar o problema, não para substituir essa evidência interna nem para
atribuir mecanismos às associações observadas.

A segunda limitação pertence ao desenho preditivo. A disponibilidade das features no momento
definido é uma premissa de compatibilidade conceitual, pois não há timestamps de preenchimento
por campo nem auditoria do fluxo operacional da PRF. Há somente três folds internos e um ano de
avaliação final; além disso, o período de treino e o ano de validação mudam simultaneamente.
Mudanças futuras de população, taxonomia ou processo de registro podem deslocar as
distribuições encontradas, e 2025 não foi completamente cego às análises estruturais.

A terceira limitação envolve modelo e decisão. A discriminação observada foi moderada, o ganho
do XGBoost foi pequeno e o threshold produziu muitos falsos positivos. Não foram incorporados
custos de erro, capacidade institucional ou avaliação prospectiva. O pipeline, portanto,
constitui evidência experimental sobre distinção entre ocorrências registradas e não uma
ferramenta validada para uso operacional.

A quarta limitação diz respeito à interpretação. Tree SHAP foi aplicado após a avaliação, em
escala de margem, e a agregação por predictor depende da representação e da cardinalidade. A
contribuição de BR, por exemplo, resume 125 colunas one-hot e não é diretamente comparável a
uma variável numérica representada por uma única coluna. Esses resumos descrevem o modelo
congelado e não fornecem identificação causal, mesmo quando dialogam com heterogeneidades da
EDA.

## 5.8 Síntese da discussão

Em conjunto, os resultados respondem à pergunta principal e às cinco RQs. Entre acidentes
registrados, houve heterogeneidade temporal, geográfica, viária e meteorológica; as
características selecionadas forneceram sinal preditivo moderado; e o XGBoost obteve a maior AP
sob validação temporal, com vantagem absoluta pequena sobre Random Forest e Regressão
Logística. Não se observou colapso nos folds, e a avaliação de 2025 permaneceu próxima das
referências internas sem participar da seleção ou do ajuste do pipeline.

O alcance dessas respostas é deliberadamente limitado. O threshold favoreceu recall ao custo
de muitos falsos positivos, a interpretação por SHAP descreveu contribuições preditivas e a
base não forneceu exposição nem suporte para inferência causal. A evidência sustenta a
utilidade científica do experimento para compreender associações e capacidade de
classificação entre registros, mas não autoriza recomendação operacional nem antecipa a
Conclusão formal do trabalho.
