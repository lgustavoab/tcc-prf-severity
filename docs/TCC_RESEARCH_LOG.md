# Memória científica do TCC

## Finalidade e governança

Este documento é a memória científica curada e versionada do projeto. Ele registra decisões
metodológicas, resultados confirmados, hipóteses, limitações e achados que sobreviveram à
revisão. Não é um histórico de comandos nem substitui os documentos técnicos da pipeline.

Os registros usam identificadores permanentes:

- `Dxxx`: decisão metodológica;
- `Rxxx`: resultado consolidado;
- `EDAxxx`: achado exploratório;
- `Hxxx`: hipótese;
- `Lxxx`: limitação.

Identificadores não devem ser reutilizados após descarte. Mudanças relevantes devem preservar
o registro anterior, atualizar o status e explicar a revisão.

## Relação com os demais documentos

- [EDA_FINDINGS.md](EDA_FINDINGS.md) recebe o registro detalhado das análises exploratórias,
  inclusive resultados provisórios, inconclusivos ou descartados.
- `TCC_RESEARCH_LOG.md` recebe a síntese curada das decisões e dos achados que sobreviveram à
  revisão.
- [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md) é a evidência congelada do encerramento da
  Fase 1 e não deve se transformar em diário de pesquisa.
- [PHASE_2_EDA_SYNTHESIS.md](PHASE_2_EDA_SYNTHESIS.md) e
  [PHASE_2_ACCEPTANCE.md](PHASE_2_ACCEPTANCE.md) registram a síntese e o aceite da EDA.

Detalhes técnicos permanecem no [contrato de dados](DATA_CONTRACT.md), na documentação do
[dataset intermediário](INTERIM_DATASET.md) e no [aceite da Fase 1](PHASE_1_ACCEPTANCE.md).

## Identificação da pesquisa

**Tema provisório:** Análise dos fatores associados à gravidade de acidentes em rodovias
federais brasileiras e avaliação de modelos de aprendizado de máquina.

**Fonte:** Polícia Rodoviária Federal — dados do Boletim de Acidente de Trânsito (BAT)
agrupados por ocorrência.

**Período:** 2021–2025.

**Unidade de análise:** uma ocorrência registrada pela PRF.

## Pergunta de pesquisa

**Quais fatores estão associados à gravidade dos acidentes registrados nas rodovias federais
brasileiras entre 2021 e 2025 e em que medida modelos de aprendizado de máquina são capazes de
identificar acidentes de maior gravidade?**

## Objetivo geral

Analisar fatores associados à gravidade das ocorrências registradas em rodovias federais
brasileiras entre 2021 e 2025 e avaliar o desempenho de modelos de aprendizado de máquina na
identificação de ocorrências graves.

## Objetivos específicos

1. Consolidar e validar os registros da PRF de 2021 a 2025. **Concluído na Fase 1.**
2. Caracterizar temporal e geograficamente as ocorrências. **Caracterizações temporal e
   geográfica concluídas nas Fases 2B e 2C.**
3. Investigar fatores associados à gravidade. **Síntese descritiva concluída na Fase 2F;
   avaliação multivariada ainda não executada.**
4. Definir operacionalmente uma variável-alvo de gravidade. **Concluído na Fase 1.**
5. Treinar e comparar modelos de classificação. **Ainda não executado.**
6. Avaliar os modelos com métricas adequadas ao problema. **Ainda não executado.**
7. Investigar quais variáveis mais influenciam os modelos. **Ainda não executado.**
8. Avaliar generalização temporal, reservando 2025 para teste final quando a modelagem for
   iniciada. **Estratégia planejada; ainda não executada.**

Nenhuma atividade de treinamento, comparação, avaliação ou interpretação de modelos foi
executada até o encerramento da Fase 2.

## Decisões metodológicas

### D001 — Unidade de análise

**Decisão:** uma linha representa uma ocorrência registrada pela PRF.

**Justificativa:** os arquivos utilizados são agrupados por ocorrência; pessoas e veículos
envolvidos aparecem como atributos agregados da ocorrência.

**Status:** confirmada.

**Origem:** [DATA_CONTRACT.md](DATA_CONTRACT.md).

### D002 — Período

**Decisão:** utilizar os cinco anos completos de 2021 a 2025.

**Justificativa:** o recorte oferece uma janela recente e contínua, com as cinco fontes
submetidas ao mesmo contrato e ao mesmo processo de auditoria.

**Status:** confirmada.

**Origem:** [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### D003 — Definição operacional do target

**Decisão:**

```text
target_grave = (mortos > 0) OR (feridos_graves > 0)
```

**Justificativa:** `classificacao_acidente` não é usada na construção do target porque a
categoria `Com Vítimas Feridas` não diferencia feridos leves de feridos graves. A definição
adotada usa diretamente as contagens dos estados físicos relevantes ao problema.

**Status:** confirmada.

**Origem:** [DATA_CONTRACT.md](DATA_CONTRACT.md).

### D004 — Camadas de dados

**Decisão:**

- `RAW`: arquivos oficiais de origem, imutáveis;
- `INTERIM`: dados consolidados, tipados e validados, preservando o conteúdo analítico;
- `PROCESSED`: ainda não criado e reservado para transformações analíticas futuras.

**Status:** confirmada para `RAW` e `INTERIM`; planejada para `PROCESSED`.

**Origem:** [INTERIM_DATASET.md](INTERIM_DATASET.md).

### D005 — Separação entre EDA e modelagem

**Decisão:** na EDA associativa poderão ser examinadas variáveis como `causa_acidente`,
`tipo_acidente`, `pessoas` e `veiculos`. Isso não implica sua inclusão em modelos preditivos.

**Justificativa:** a seleção de features de ML deverá considerar a disponibilidade da
informação no momento relevante para a previsão e o risco de leakage.

**Status:** confirmada como princípio; seleção de features ainda não executada.

### D006 — Validação temporal futura

**Estratégia planejada:** usar 2021–2024 para desenvolvimento e reservar 2025 para teste
temporal final.

**Justificativa:** avaliar generalização em um período posterior e não utilizado no
desenvolvimento.

**Status:** planejada; nenhuma divisão ou modelagem foi executada.

### D007 — Fechamento da EDA e autoridade da matriz de elegibilidade

**Data:** 19/08/2026.

**Decisão:** encerrar formalmente a Fase 2 após a síntese 2G e adotar
`phase_2f_modeling_eligibility_matrix.csv` como fonte autoritativa para a triagem conceitual
de features.

**Justificativa:** relevância descritiva não garante disponibilidade no momento preditivo nem
ausência de leakage. A matriz separa candidatas, cautelas, decisões pendentes e exclusões sem
criar dataset de modelagem.

**Consequências:** antes de qualquer preparação ou ML, devem ser definidos o momento
preditivo, o tratamento das quatro variáveis pendentes e as verificações de drift previstas
por H001. Os sete campos de leakage permanecem bloqueados.

**Origem:** [PHASE_2_EDA_SYNTHESIS.md](PHASE_2_EDA_SYNTHESIS.md) e
`reports/tables/phase_2f_modeling_eligibility_matrix.csv`.

**Status:** confirmada; Fase 2 encerrada e modelagem não iniciada.

## Resultados consolidados

### R001 — Dimensão do dataset

**Resultado:** 342.624 ocorrências entre 2021 e 2025, com 30 colunas nas fontes RAW e 32
colunas no dataset interim.

**Status:** confirmado.

**Origem:** [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### R002 — Distribuição do target

**Resultado:** 96.857 ocorrências graves e 245.767 não graves, correspondendo a uma taxa de
graves de 28,2692%.

**Derivação:** a quantidade de não graves é a diferença já conhecida
`342.624 - 96.857 = 245.767`.

**Status:** confirmado.

**Origem:** auditoria e [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### R003 — Integridade

**Resultado:** zero IDs duplicados, zero falhas em
`feridos = feridos_leves + feridos_graves` e cinco fontes RAW verificadas contra o baseline de
referência do projeto.

**Status:** confirmado.

**Origem:** auditoria e comando `prf-verify-interim`, documentados em
[PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

### R004 — Anomalias preservadas

**Resultado:** 18.538 divergências na decomposição de `pessoas`, 883 registros com `br = 0` e
1.652 registros com `km = 0`.

**Interpretação metodológica:** são métricas de qualidade não bloqueantes. Nenhum desses
registros foi corrigido ou removido na fundação de dados.

**Status:** confirmado.

**Origem:** auditoria e [PHASE_1_ACCEPTANCE.md](PHASE_1_ACCEPTANCE.md).

## Achados exploratórios

### EDA001 — Distribuição anual do volume

Entre as 342.624 ocorrências registradas, os totais anuais variaram de 64.567 em 2021 a 73.156
em 2024. O volume ficou praticamente estável em 2022 (+0,0604%), cresceu em 2023 (+4,8912%) e
2024 (+7,9538%) e recuou discretamente em 2025 (-0,8571%). O resultado descreve a composição
da base e não mede exposição ao tráfego ou risco de acidente.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA001](EDA_FINDINGS.md#eda001--distribuição-anual-do-volume-de-ocorrências-registradas).

### EDA002 — Estabilidade descritiva do target

A proporção anual de ocorrências graves permaneceu entre 28,0608% e 28,4943%, com amplitude
de 0,4335 ponto percentual. A média anual simples foi 28,2707%, enquanto a taxa global
ponderada pelos registros foi 28,2692%. A proximidade é descritiva e não substitui avaliação
inferencial futura.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA002](EDA_FINDINGS.md#eda002--estabilidade-descritiva-da-proporção-anual-de-ocorrências-graves).

### EDA003 — Qualidade analítica básica

Somente `classificacao_acidente`, `regional`, `delegacia` e `uop` apresentaram nulos, todos
com proporções inferiores a 0,1% por coluna. Foram preservados 883 registros `Não Informado`
em `sentido_via` e 4.492 registros `Ignorado` em `condicao_metereologica`; essas categorias
não foram convertidas para nulo.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA003](EDA_FINDINGS.md#eda003--nulidade-e-categorias-especiais-preservadas).

### EDA004 — Cardinalidade categórica

As maiores cardinalidades entre as variáveis categóricas avaliadas ocorreram em `municipio`
(2.050), `tracado_via` (1.214), `uop` (408), `delegacia` (155) e `causa_acidente` (76). Esse
resultado orienta decisões futuras de apresentação e codificação, mas não mede relevância ou
capacidade preditiva.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA004](EDA_FINDINGS.md#eda004--cardinalidade-das-principais-variáveis-categóricas).

### EDA007 — Concentração temporal no fim de semana

Sábado e domingo reuniram 112.389 ocorrências, das quais 33.933 foram graves (30,1925%),
enquanto os dias úteis reuniram 230.235 ocorrências e 62.924 graves (27,3303%). Domingo
liderou a proporção grave em quatro dos cinco anos e sábado em 2025. A diferença é descritiva,
condicionada às ocorrências registradas, e não mede exposição ou causalidade.

**Relevância:** caracteriza uma associação temporal diretamente ligada à pergunta da pesquisa
e recomenda avaliar calendário e estabilidade anual na modelagem futura.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA007](EDA_FINDINGS.md#eda007--concentração-no-fim-de-semana-e-proporção-de-graves).

### EDA008 — Padrão horário de volume e gravidade

18h concentrou o maior volume em todos os cinco anos (25.569 registros no consolidado). A
proporção de graves variou de 23,1243% às 8h a 33,7323% às 19h; a maior taxa anual alternou
entre 19h e 21h. Cada destaque de taxa foi examinado com seu tamanho amostral, sem usar fluxo
veicular como denominador.

**Relevância:** a recorrência do padrão e a variação anual apoiam a avaliação futura de hora
como feature, sujeita a análise de drift e disponibilidade.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA008](EDA_FINDINGS.md#eda008--padrão-horário-de-volume-e-gravidade).

### EDA009 — Fase do dia e proporção de graves

`Pleno dia` concentrou 187.621 registros e apresentou 25,3047% de graves. `Plena Noite`
reuniu 119.581 registros e apresentou 32,4726% de graves, liderando essa proporção em cada um
dos cinco anos. O resultado é uma associação descritiva e não demonstra efeito causal da
fase do dia.

**Relevância:** é pertinente à discussão da pesquisa e à futura avaliação de redundância entre
`fase_dia` e hora.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA009](EDA_FINDINGS.md#eda009--distribuição-por-fase-do-dia).

### EDA010 — Estabilidade descritiva dos padrões temporais

Dezembro liderou o volume mensal, 18h o volume horário, `Pleno dia` o volume por fase e
`Plena Noite` a proporção grave por fase nos cinco anos. Em contraste, o mês de maior taxa
variou entre quatro categorias e a hora de maior taxa alternou entre 19h e 21h. As amplitudes
anuais foram registradas sem limiar arbitrário de classificação.

**Relevância:** fornece evidência metodológica para preservar validação temporal e avaliar
drift por variável antes da modelagem.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA010](EDA_FINDINGS.md#eda010--recorrência-e-variação-dos-padrões-temporais-entre-anos).

### EDA011 — Desigualdade geográfica descritiva por macrorregião

Sudeste concentrou 107.259 ocorrências registradas (31,3052% do dataset), enquanto Nordeste
apresentou a maior proporção grave, 26.662 em 74.232 registros (35,9171%). Sul apresentou
24,8740%. Nordeste liderou a taxa em quatro anos e Norte em 2023. Volume e composição de
gravidade são dimensões distintas e não representam exposição rodoviária.

**Relevância:** o contraste macrorregional se relaciona diretamente à pergunta da pesquisa e
indica que geografia deverá ser considerada com validação temporal e linguagem não causal.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA011](EDA_FINDINGS.md#eda011--distribuição-e-gravidade-por-macrorregião).

### EDA012 — Heterogeneidade estadual de volume e gravidade

MG liderou o volume nos cinco anos e somou 44.502 registros. MA apresentou 2.647 graves em
5.778 registros (45,8117%), a maior taxa consolidada, e liderou em quatro anos; PA liderou em
2022. SP apresentou 4.288 graves em 23.005 registros (18,6394%). As diferenças são
condicionadas às ocorrências registradas e não permitem classificar risco estadual.

**Relevância:** UF é uma candidata importante para análise associativa e eventual modelagem,
mas exigirá tratamento categórico e avaliação de generalização temporal.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA012](EDA_FINDINGS.md#eda012--concentração-e-proporção-de-graves-por-uf).

### EDA013 — Variação anual das taxas estaduais

As amplitudes anuais variaram de 0,9389 ponto percentual no RS a 17,9409 em RR. MG, líder de
volume, variou 1,0856 ponto, enquanto MA variou 8,0007. Não foi aplicado limiar automático de
estabilidade, e tamanho amostral deverá acompanhar qualquer interpretação de taxa estadual.

**Relevância:** o resultado reforça H001 e afeta a futura estratégia de validação temporal de
features geográficas.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA013](EDA_FINDINGS.md#eda013--amplitude-anual-da-proporção-de-graves-por-uf).

### EDA015 — Alta cardinalidade e chave municipal composta

Foram observados 2.098 pares `uf + municipio` para 2.050 nomes municipais distintos. As 48
combinações excedentes mostram que município isolado não é uma chave geográfica suficiente.
Brasília/DF concentrou o maior volume, com 4.948 registros, mas nenhuma tabela município × ano
foi criada por parcimônia.

**Relevância:** a cardinalidade e a necessidade da chave composta afetam preparação,
codificação e validação de variáveis em fases futuras.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA015](EDA_FINDINGS.md#eda015--concentração-municipal-com-chave-uf--município).

### EDA016 — Controle editorial de pequenas amostras geográficas

Os rankings de taxa de BR e município foram restritos a categorias com pelo menos 500
registros, sem excluir categorias das tabelas completas. Seriam elegíveis 99/62/47 BRs e
763/157/59 municípios nos cortes 100/500/1000, respectivamente. A categoria municipal líder
muda quando o corte passa de 500 para 1000, evidenciando sensibilidade ao critério.

**Relevância:** documenta uma salvaguarda contra destaques de taxas em grupos muito pequenos e
mostra que o limiar é editorial, não universal ou científico.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA016](EDA_FINDINGS.md#eda016--destaques-de-taxa-com-critério-editorial-de-amostra).

### EDA018 — Contraste persistente por tipo de pista

Pista Simples concentrou 167.198 registros e apresentou 56.365 graves (33,7115%), ante
23,3513% em Dupla e 21,8680% em Múltipla. Simples manteve a maior proporção nos cinco anos,
com amplitude de 0,8746 ponto percentual.

**Relevância:** o contraste é recorrente e diretamente relacionado às características da via,
mas exige futura análise multivariada, sem interpretação causal ou de risco absoluto.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA018](EDA_FINDINGS.md#eda018--tipo-de-pista-e-proporção-de-ocorrências-graves).

### EDA021 — Meteorologia requer leitura conjunta de taxa e amostra

`Ignorado` apresentou 34,5503% de graves em 4.492 registros, mas caracteriza ausência
semântica e não uma condição meteorológica observada. Entre condições informadas com pelo
menos 500 registros, Nevoeiro/Neblina apresentou 31,5011% e Vento 31,3659%. Granizo (n=11)
e Neve (n=8) foram mantidos na tabela completa, mas excluídos dos destaques pelo tamanho.

**Relevância:** documenta que categorias raras e desconhecidas exigem cautela, separa ausência
de informação de condições observadas e exige tamanho amostral em toda comparação.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA021](EDA_FINDINGS.md#eda021--condição-meteorológica-tamanho-amostral-e-categorias-raras).

### EDA022 — Representação multivalorada de traçado da via

Foram confirmados 12 componentes básicos em `tracado_via`. Reta ocorreu em 241.869 registros,
Curva em 62.755 e Declive em 32.735. As contagens somaram 418.561 porque uma ocorrência pode
conter vários componentes; portanto, elas não são mutuamente exclusivas.

**Relevância:** o campo não deve ser tratado como aproximadamente 1.214 categorias completas
independentes. Sua eventual preparação deverá preservar a natureza multirrótulo e evitar
chamar o percentual de cada componente de participação exclusiva.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA022](EDA_FINDINGS.md#eda022--componentes-multivalorados-de-traçado-da-via).

### EDA023 — Recorrência temporal em categorias volumosas de via e ambiente

Simples liderou tipo de pista e `Não` liderou uso do solo em todos os anos. Categorias
volumosas como Céu Claro, Nublado, Chuva e Reta apresentaram amplitudes anuais entre 0,5941 e
1,3658 ponto percentual, enquanto categorias raras foram substancialmente mais variáveis.

**Relevância:** reforça que estabilidade temporal e tamanho amostral deverão ser avaliados
conjuntamente; recorrência descritiva não garante ausência de drift nem estabilidade futura.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA023](EDA_FINDINGS.md#eda023--estabilidade-descritiva-das-dimensões-de-via-e-ambiente).

### EDA024 — Tipo de acidente separa volume e proporção grave

Colisão traseira concentrou 65.634 registros, enquanto Atropelamento de Pedestre apresentou a
maior proporção entre tipos com n≥500: 10.416 graves em 15.313 registros (68,0206%), seguido
de Colisão frontal (63,0592%). Ambos estiveram nos cinco anos e tiveram amplitudes anuais de
1,6144 e 1,2550 ponto percentual.

**Relevância:** os contrastes são persistentes e relacionados à dinâmica, mas o tipo pode ser
conhecido ou consolidado após a ocorrência; aplica-se a separação EDA/modelagem da D005.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA024](EDA_FINDINGS.md#eda024--volume-e-gravidade-por-tipo-de-acidente-registrado).

### EDA025 — Causa registrada apresenta contrastes descritivos marcantes

Reação tardia ou ineficiente do condutor teve o maior volume (46.901). Entre categorias com
n≥500, Pedestre andava na pista apresentou 2.460 graves em 3.262 registros (75,4139%), e
Transitar na contramão, 6.713 em 11.145 (60,2333%). Essas categorias estiveram nos cinco anos.

**Relevância:** o campo possui associação descritiva forte com gravidade, mas é uma causa
registrada pela PRF, não causalidade científica demonstrada, e exige avaliação de leakage.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA025](EDA_FINDINGS.md#eda025--volume-e-gravidade-por-causa-registrada-pela-prf).

### EDA026 — Taxonomias variam no período

`tipo_acidente` teve 18 categorias na união, 16 presentes nos cinco anos e uma exclusiva de
um ano. `causa_acidente` teve 76 na união, 65 presentes nos cinco anos, uma exclusiva de um
ano, cinco com primeiro registro após 2021 e sete com último registro antes de 2025.

**Relevância:** comparações temporais e preparação futura deverão preservar ou tratar
explicitamente mudanças de rótulo; nenhuma harmonização foi feita nesta fase.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA026](EDA_FINDINGS.md#eda026--mudanças-observadas-nas-taxonomias-de-tipo-e-causa).

### EDA029 — Síntese das associações descritivas centrais

A Fase 2F consolidou oito comparações centrais. Os maiores contrastes foram Pedestre andava
na pista versus Reação tardia ou ineficiente do condutor (51,4847 pontos percentuais),
Atropelamento de Pedestre versus Colisão traseira (44,3469), Colisão frontal versus Colisão
traseira (39,3855) e Transitar na contramão versus Reação tardia ou ineficiente do condutor
(36,3042). Também foram centrais os contrastes de macrorregião, tipo de pista, fase do dia e
fim de semana. Todas as categorias focais foram observadas nos cinco anos. A comparação de
nove pessoas versus uma permaneceu como achado secundário, com os números preservados e a
ressalva de associação parcialmente mecânica com a definição do target.

**Relevância:** a síntese prioriza resultados para a escrita sem criar score, inferência
causal ou medida de risco absoluto. As diferenças permanecem condicionadas às ocorrências
registradas e sem denominador de exposição.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA029](EDA_FINDINGS.md#eda029--síntese-das-associações-descritivas-centrais-com-gravidade).

### EDA030 — Separação entre evidência descritiva e elegibilidade preditiva

A matriz conceitual classificou 13 variáveis como candidatas, cinco como candidatas com
cautela, quatro como dependentes de decisão metodológica, três como exclusões administrativas
e sete como exclusões por leakage. Tipo, causa, pessoas e veículos não foram automaticamente
promovidos; as mudanças taxonômicas do EDA026 e a relação mecânica de `pessoas` com o target
permanecem alertas explícitos. As 22 variáveis não excluídas foram inventariadas para futura
verificação de drift. Tanto `tracado_via` quanto seus componentes derivados exigem cautela; a
matriz de elegibilidade é a fonte autoritativa dos status, enquanto derivações puramente
analíticas e categorias de qualidade não recebem elegibilidade independente.

**Relevância:** relevância associativa e admissibilidade no momento preditivo são decisões
distintas. A matriz planeja uma etapa futura; nenhum dataset processed, feature, split ou
modelo foi criado.

**Status:** confirmado. **Origem:** [EDA_FINDINGS.md — EDA030](EDA_FINDINGS.md#eda030--achado-descritivo-e-elegibilidade-preditiva-são-decisões-separadas).

## Hipóteses

### H001 — Estabilidade temporal das features

**Data:** 18/08/2026.

**Hipótese metodológica:** a estabilidade da prevalência de `target_grave` observada na Fase
2A não implica estabilidade das distribuições das variáveis explicativas.

**Fundamentação:** a Fase 2B encontrou recorrência em alguns resumos temporais e variação em
outros. Isso não avalia as demais features nem demonstra ausência de drift.

**Como avaliar:** antes da modelagem temporal, comparar as distribuições das features entre
2021–2024 e 2025, com métricas adequadas ao tipo de variável e sem usar o teste final para
decisões de desenvolvimento.

**Status:** proposta; pendência futura, não apresentada como resultado.

## Limitações

### L001 — Ausência de população exposta

**Limitação:** a base contém somente ocorrências registradas. Não contém o total de viagens,
veículos que trafegaram sem acidente ou veículo-quilômetro.

**Consequência:** o estudo não estima diretamente a probabilidade de ocorrer um acidente e não
deve interpretar proporções de gravidade como risco absoluto de trafegar em uma rodovia.

**Status:** ativa.

### L002 — Associação não implica causalidade

**Limitação:** diferenças observadas entre grupos não demonstram causalidade.

**Consequência:** resultados associativos devem usar linguagem compatível com o desenho
observacional e não causal.

**Status:** ativa.

### L003 — Variáveis determinadas após a ocorrência

**Limitação:** variáveis como `causa_acidente`, `tipo_acidente` e `pessoas` podem ser definidas
ou consolidadas durante ou após a ocorrência. Além disso, como `target_grave` vale verdadeiro
quando há ao menos um morto ou ferido grave na ocorrência, um número maior de pessoas oferece
mais oportunidades para satisfazer mecanicamente a definição do target.

**Consequência:** essas variáveis são úteis para EDA, mas exigirão avaliação específica de
disponibilidade temporal e leakage antes de eventual uso em ML. `pessoas` requer cautela
adicional: sua associação crescente com o target não deve ser tomada diretamente como efeito
causal nem como evidência suficiente para selecioná-la como feature.

**Status:** ativa.

### L004 — Qualidade dos registros

**Limitação:** existem categorias como `Ignorado` e `Não Informado`, além das inconsistências
conhecidas na decomposição de `pessoas`.

**Consequência:** categorias ausentes ou desconhecidas e inconsistências preservadas devem ser
explicitamente quantificadas e consideradas nas análises.

**Status:** ativa.

## Figuras e tabelas associadas

As Fases 2A a 2F produziram figuras e tabelas versionadas em `reports/`. A Fase 2G consolidou
esses resultados em [PHASE_2_EDA_SYNTHESIS.md](PHASE_2_EDA_SYNTHESIS.md), no aceite formal e
em uma tabela editorial de decisões, sem executar nova EDA. Os artefatos científicos estão
associados aos IDs correspondentes em [EDA_FINDINGS.md](EDA_FINDINGS.md).

## Templates para registros futuros

### EDAxxx — Título

**Data:**

**Fase:**

**Pergunta:**

**População analisada:**

**Resultado absoluto:**

**Proporção/taxa:**

**Comparação:**

**Interpretação:**

**O que NÃO podemos concluir:**

**Limitações:**

**Figura:**

**Tabela:**

**Código/origem:**

**Possível uso no TCC:**

**Status:** provisório / confirmado / descartado.

### Dxxx — Título da decisão

**Data:**

**Decisão:**

**Justificativa:**

**Alternativas consideradas:**

**Consequências:**

**Origem:**

**Status:** proposta / confirmada / substituída.

### Hxxx — Título da hipótese

**Data:**

**Hipótese:**

**Fundamentação:**

**Como avaliar:**

**Status:** proposta / apoiada / não apoiada / inconclusiva.

### Lxxx — Título da limitação

**Descrição:**

**Consequência:**

**Mitigação possível:**

**Status:** ativa / mitigada / encerrada.

### Rxxx — Título do resultado consolidado

**Data:**

**População e período:**

**Resultado:**

**Método/origem:**

**Limitações:**

**Possível uso no TCC:**

**Status:** provisório / confirmado / substituído.
