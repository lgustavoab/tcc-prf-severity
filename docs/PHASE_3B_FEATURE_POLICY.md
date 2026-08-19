# Fase 3B — Momento preditivo e política final de features

## 1. Objetivo

A Fase 3B congela a política conceitual que deverá orientar a futura construção do dataset
analítico. Ela define o momento preditivo, resolve as pendências da matriz 2F, escolhe uma
representação principal sem redundâncias deliberadas e estabelece regras anti-leakage e de
generalização temporal. Nenhum valor de feature, split físico, encoder, scaler, pipeline ou
modelo foi criado.

## 2. Definição do momento preditivo

A unidade de predição é uma ocorrência registrada pela PRF. O target continua sendo
`target_grave`, verdadeiro quando a ocorrência possui ao menos um morto ou ferido grave.

O momento lógico escolhido é o **registro inicial da ocorrência**, depois de existir a
notificação de que uma ocorrência aconteceu, mas antes de conhecer seus desfechos humanos e
antes da consolidação investigativa ou da dinâmica final. A pergunta futura é: usando somente
contexto temporal, geográfico, rodoviário e ambiental conceitualmente compatível com esse
momento, é possível identificar ocorrências com maior potencial de serem graves?

A disponibilidade das features principais é uma premissa metodológica de compatibilidade
com o cenário preditivo definido. O dataset público não contém timestamps de preenchimento
por campo e esta fase não verificou o fluxo operacional interno da PRF; portanto, a política
não afirma que cada campo esteja comprovadamente preenchido no instante inicial do sistema.

São permitidas informações contextuais de data/hora, localização rodoviária, infraestrutura,
direção, meteorologia e uso do solo. São proibidos desfechos humanos, classificação do
desfecho, campos administrativos e informações cuja versão final dependa da dinâmica ou da
investigação posterior.

Associação com o target e baixa magnitude de drift não substituem a exigência de
disponibilidade temporal.

## 3. Princípio anti-leakage

Permanecem proibidos como predictors em qualquer conjunto futuro: `mortos`,
`feridos_graves`, `feridos_leves`, `feridos`, `ilesos`, `ignorados` e
`classificacao_acidente`. Os sete campos representam desfechos, componentes do target ou
proxies imediatos da gravidade. Não poderão reaparecer nem no experimento secundário.

`regional`, `delegacia` e `uop` também permanecem fora dos conjuntos principal e secundário.
São proxies administrativos, não características substantivas do cenário preditivo.

## 4. Decisões temporais

O conjunto principal usará:

- `month_name`, derivado de `data_inversa`;
- `dia_semana`;
- `hour`, derivado de `horario`.

`data_inversa` e `horario` serão usados somente como fontes para derivações e não como
predictors crus. `fase_dia` será excluída da versão principal por sobrepor a representação
horária escolhida. A política evita transformar datas ou horários completos em taxonomias de
alta cardinalidade e resolve a redundância `horario`/`hour`.

## 5. Decisões geográficas

A versão principal usará `uf`, `br` e `km`. Esse trio mantém contexto territorial agregado e
posição rodoviária interpretável. `br` e `km` entram com cautela: `br = 0` será preservada e o
encoder futuro deverá tolerar identificadores desconhecidos.

`municipio` não foi excluído automaticamente por ter a maior TVD. A decisão combina seu TVD
de 0,089805, alta cardinalidade, 49 categorias novas em 2025 e redundância com a localização
escolhida. `latitude` e `longitude` também ficam fora da versão principal porque exigiriam
representação geoespacial própria e duplicariam UF e BR/km. Reintroduzir município ou
coordenadas exigirá uma nova versão formal da política, não uma escolha durante avaliação do
modelo.

## 6. Via e ambiente

São autorizadas no conjunto principal:

- `sentido_via`, preservando `Não Informado` como ausência semântica;
- `condicao_metereologica`, preservando `Ignorado` como ausência semântica;
- `tipo_pista`;
- `uso_solo`, sem reinterpretá-lo automaticamente como urbano/rural.

Categorias de ausência continuam registradas, mas não devem ser apresentadas como evidência
substantiva sobre direção ou meteorologia.

## 7. Decisão sobre `tracado_via`

As combinações cruas de `tracado_via` ficam excluídas como representação redundante. Na 3A,
elas apresentaram TVD 0,082051, 1.046 combinações no desenvolvimento e 168 combinações novas
em 2025, embora com share unseen de apenas 0,272994%.

A representação autorizada é `tracado_via_components`. Todos os 12 componentes apareceram
nos cinco anos e suas mudanças de prevalência são semanticamente interpretáveis. Na Fase 3C,
cada componente deverá ser materializado como indicador binário multilabel, contando no
máximo uma vez por ocorrência. Essa materialização ainda não foi implementada.

## 8. Decisão sobre `tipo_acidente`

`tipo_acidente` fica **fora do conjunto principal** e reservado como `secondary_only`. O tipo
final descreve a dinâmica que efetivamente ocorreu e pode não estar determinado no registro
inicial. A TVD 0,032081, a ausência de categorias novas em 2025 e sua associação descritiva
não superam essa incompatibilidade temporal.

Um experimento secundário poderá avaliar um cenário explicitamente tardio. Seus resultados
não poderão ser misturados ou usados para substituir o modelo principal.

## 9. Decisão sobre `causa_acidente`

`causa_acidente` fica **fora do conjunto principal** e reservado como `secondary_only`. A
causa registrada depende de apuração posterior e pode incorporar conhecimento da ocorrência
e de seus desfechos. Sua forte associação descritiva não justifica autorização no momento
estrito. A 3A encontrou TVD 0,079368, nenhuma categoria nova e sete categorias ausentes em
2025, além da variação taxonômica anual já documentada.

Qualquer experimento secundário deverá preservar as strings originais e declarar que opera em
cenário tardio/investigativo.

## 10. Decisão sobre `pessoas`

`pessoas` fica **fora do conjunto principal** e reservado como `secondary_only`. A contagem
pode ser consolidada depois do registro inicial, possui divergências conhecidas na
decomposição e sua associação com `target_grave` é parcialmente mecânica: mais pessoas geram
mais oportunidades para ao menos uma satisfazer o target. A baixa TVD de 0,009196 não resolve
essas limitações.

## 11. Decisão sobre `veiculos`

`veiculos` fica **fora do conjunto principal** e reservado como `secondary_only`. Embora seja
uma informação contextual, a contagem final pode ser consolidada durante ou depois da
ocorrência e sua disponibilidade operacional no registro inicial não está garantida. A TVD de
0,013573 não é justificativa para assumir disponibilidade.

## 12. Política para categorias unseen

Qualquer encoder categórico futuro deverá:

1. ser ajustado somente no desenvolvimento 2021–2024;
2. aceitar categorias desconhecidas sem falhar;
3. registrar a ocorrência de unknown de forma auditável;
4. nunca aprender vocabulário usando 2025;
5. preservar `Ignorado`, `Não Informado` e `br = 0` como valores do contrato, com sua
   interpretação de qualidade.

A política deve ser compatível com tratamento explícito de categorias desconhecidas caso
OneHotEncoder seja escolhido futuramente, mas nenhuma biblioteca ou implementação de encoding
foi adicionada nesta fase.

## 13. Drift, numéricas e generalização

Para `km`, qualquer imputação, transformação ou escala futura será ajustada somente em
2021–2024. Os decis usados na 3A serviram apenas para auditoria de drift e não são bins
automaticamente autorizados para o modelo.

As magnitudes de TVD orientam monitoramento e cautela, não regras universais de inclusão. As
decisões desta política derivam primeiro do momento preditivo, leakage, semântica e
redundância, e não de uma otimização de performance.

## 14. Conjunto principal congelado

O contrato conceitual principal possui 11 features/representações:

1. `month_name`;
2. `dia_semana`;
3. `hour`;
4. `uf`;
5. `br`;
6. `km`;
7. `sentido_via`;
8. `condicao_metereologica`;
9. `tipo_pista`;
10. `uso_solo`;
11. `tracado_via_components`.

`br`, `km`, `sentido_via`, `condicao_metereologica` e `tracado_via_components` entram com
cautelas explicitadas na matriz, sem deixar de pertencer ao conjunto principal.

## 15. Conjunto secundário

O experimento secundário conceitual contém `tipo_acidente`, `causa_acidente`, `pessoas` e
`veiculos`. Ele representa um cenário tardio e não poderá ser apresentado como equivalente ao
momento preditivo estrito. A Fase 3B não criou dataset separado.

## 16. Variáveis proibidas e representações excluídas

- Leakage: `mortos`, `feridos_graves`, `feridos_leves`, `feridos`, `ilesos`, `ignorados`,
  `classificacao_acidente`.
- Administrativas: `regional`, `delegacia`, `uop`.
- Pós-ocorrência no modelo principal: `tipo_acidente`, `causa_acidente`, `pessoas`,
  `veiculos`.
- Redundantes na versão principal: `data_inversa`, `horario`, `fase_dia`, `municipio`,
  `latitude`, `longitude`, `tracado_via` bruto.

## 17. Fronteira metodológica e regras para a Fase 3C

O desenvolvimento planejado é 2021–2024 e o teste temporal final é 2025. Esse split ainda
não foi materializado.

Há uma limitação transparente: 2025 já foi explorado estruturalmente nas Fases 2 e 3A porque
o projeto começou como EDA de 2021–2025. Portanto, ele não é um holdout completamente cego no
sentido mais estrito. A 3A usou 2025 para diagnosticar generalização e congelar o desenho
experimental, não para otimizar desempenho de modelo.

A partir desta política:

- 2025 não poderá orientar novas seleções de features por performance;
- vocabulários, imputações, scalers, thresholds e hiperparâmetros deverão ser aprendidos
  somente em 2021–2024;
- 2025 será usado apenas uma vez na avaliação final após congelamento do pipeline;
- o conjunto principal deverá ser construído exatamente a partir da matriz 3B;
- o conjunto secundário, se materializado, deverá permanecer separado e identificado como
  cenário tardio;
- qualquer alteração na política exigirá nova decisão versionada, sem consultar performance
  do holdout para justificá-la.

## Artefatos

- `reports/tables/phase_3b_feature_policy.csv`: decisão completa para 32 variáveis e
  representações.
- `reports/tables/phase_3b_primary_feature_set.csv`: contrato das 11 features principais.
- `reports/tables/phase_3b_secondary_feature_set.csv`: contrato das quatro features do cenário
  tardio.

Esses arquivos contêm somente política e metadados; não contêm valores de features.
