# Registro de achados exploratórios — Fase 2

## Finalidade

Este documento recebe o registro detalhado e auditável da Análise Exploratória de Dados. A
Fase 2A — Caracterização Geral foi executada sobre o Parquet interim validado; as demais
subfases ainda não foram iniciadas.

Os registros nascem aqui, inclusive quando provisórios, inconclusivos ou descartados. Achados
que sobreviverem à revisão metodológica podem ser sintetizados na
[memória científica](TCC_RESEARCH_LOG.md). O [aceite da Fase 1](PHASE_1_ACCEPTANCE.md)
permanece congelado como evidência da fundação de dados e não deve receber achados de EDA.

Figuras e tabelas associadas devem ser armazenadas, respectivamente, em
`../reports/figures/` e `../reports/tables/`.

## Regras editoriais

1. Sempre registrar o tamanho da amostra analisada.
2. Sempre distinguir contagem absoluta de proporção ou taxa.
3. Usar a expressão “entre as ocorrências registradas” quando aplicável.
4. Não usar linguagem causal sem um desenho de identificação causal.
5. Registrar categorias ignoradas, não informadas, ausentes ou excluídas da comparação.
6. Documentar todos os filtros e recortes aplicados.
7. Associar figuras e tabelas aos IDs dos achados correspondentes.
8. Registrar resultados inconclusivos ou descartados quando forem metodologicamente
   relevantes.

Resultados devem informar claramente denominadores, período, população, unidade de análise e
origem do código. Comparações entre grupos não devem ser interpretadas como risco absoluto de
acidente, pois a base contém apenas ocorrências registradas.

## 2A — Caracterização geral

### EDA001 — Distribuição anual do volume de ocorrências registradas

**Data:** 18/08/2026.

**Fase:** 2A — Caracterização geral.

**Pergunta:** quantas ocorrências existem em cada ano, quanto cada ano representa da base e
como o volume variou em relação ao ano anterior?

**População analisada:** 342.624 ocorrências registradas pela PRF entre 2021 e 2025, sem
filtros ou exclusões.

**Resultado absoluto:** 64.567 ocorrências em 2021; 64.606 em 2022; 67.766 em 2023; 73.156 em
2024; e 72.529 em 2025.

**Proporção/taxa:** cada ano representou, respectivamente, 18,8449%, 18,8562%, 19,7785%,
21,3517% e 21,1687% do dataset total.

**Comparação:** a variação anual do volume foi não aplicável em 2021, +0,0604% em 2022,
+4,8912% em 2023, +7,9538% em 2024 e -0,8571% em 2025. O maior volume foi observado em 2024;
2025 apresentou redução discreta em relação ao ano anterior.

**Interpretação:** o volume permaneceu praticamente inalterado entre 2021 e 2022, cresceu em
2023 e 2024 e apresentou pequena retração em 2025. Os anos de 2024 e 2025 têm as maiores
participações na população analisada.

**O que NÃO podemos concluir:** as diferenças não medem risco de acidente, não demonstram
mudança na exposição ao tráfego e não identificam causas para a variação anual.

**Limitações:** a base contém somente ocorrências registradas e não inclui denominadores como
fluxo de veículos ou veículo-quilômetro.

**Figura:** `../reports/figures/phase_2a_occurrences_by_year.png`.

**Tabela:** `../reports/tables/phase_2a_year_summary.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/general.py`, executado por
`uv run prf-eda-general` sobre `data/interim/prf_accidents_2021_2025.parquet` validado.

**Possível uso no TCC:** descrição da população e da composição anual da amostra.

**Status:** confirmado.

### EDA002 — Estabilidade descritiva da proporção anual de ocorrências graves

**Data:** 18/08/2026.

**Fase:** 2A — Caracterização geral.

**Pergunta:** a proporção de `target_grave` permaneceu estável entre 2021 e 2025?

**População analisada:** 342.624 ocorrências registradas, das quais 96.857 graves e 245.767
não graves, sem filtros ou exclusões.

**Resultado absoluto:** graves/não graves por ano: 18.118/46.449 em 2021;
18.409/46.197 em 2022; 19.212/48.554 em 2023; 20.625/52.531 em 2024; e 20.493/52.036 em
2025.

**Proporção/taxa:** a proporção anual de graves foi 28,0608% em 2021, 28,4943% em 2022,
28,3505% em 2023, 28,1932% em 2024 e 28,2549% em 2025.

**Comparação:** a menor taxa anual foi 28,0608%, a maior 28,4943% e a amplitude foi 0,4335
ponto percentual. A média simples das cinco taxas anuais foi 28,2707%; a taxa global,
ponderada pelos 342.624 registros, foi 28,2692%.

**Interpretação:** a proporção anual de ocorrências graves mostrou estabilidade descritiva no
período, com variação inferior a meio ponto percentual entre os extremos. A média anual simples
atribui o mesmo peso a cada ano; a taxa global pondera implicitamente pelos diferentes números
de ocorrências anuais.

**O que NÃO podemos concluir:** não foi realizado teste inferencial; portanto, o resultado não
prova igualdade estatística entre anos, não explica as diferenças e não expressa risco absoluto
de acidente.

**Limitações:** o target usa a definição operacional do projeto e a base não contém população
exposta ao tráfego.

**Figura:** `../reports/figures/phase_2a_severe_rate_by_year.png`.

**Tabela:** `../reports/tables/phase_2a_year_summary.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/general.py`, executado por
`uv run prf-eda-general` sobre o Parquet interim validado.

**Possível uso no TCC:** caracterização do desfecho e justificativa descritiva para acompanhar
estabilidade temporal em etapas futuras.

**Status:** confirmado.

### EDA003 — Nulidade e categorias especiais preservadas

**Data:** 18/08/2026.

**Fase:** 2A — Caracterização geral.

**Pergunta:** qual é o panorama básico de valores nulos e categorias especiais relevantes?

**População analisada:** todas as 342.624 ocorrências e as 32 colunas do dataset interim.

**Resultado absoluto:** foram encontrados 5 nulos em `classificacao_acidente`, 27 em
`regional`, 127 em `delegacia` e 282 em `uop`; as demais 28 colunas não apresentaram nulos.
Entre as categorias especiais, `sentido_via` contém 883 registros `Não Informado` e
`condicao_metereologica` contém 4.492 registros `Ignorado`. Não foram observadas as duas
categorias especiais nas outras combinações verificadas de `classificacao_acidente`,
`regional`, `delegacia` e `uop`.

**Proporção/taxa:** a nulidade corresponde a 0,0015% em `classificacao_acidente`, 0,0079% em
`regional`, 0,0371% em `delegacia` e 0,0823% em `uop`. `Não Informado` em `sentido_via`
representa 0,2577% da base e `Ignorado` em `condicao_metereologica`, 1,3111%.

**Comparação:** `uop` possui a maior contagem e proporção de nulos entre as colunas; entre as
categorias especiais verificadas, `Ignorado` em `condicao_metereologica` é a mais frequente.

**Interpretação:** a nulidade é concentrada em quatro campos e permanece abaixo de 0,1% em
cada um. Categorias especiais foram mantidas como valores informativos, sem conversão para
nulo.

**O que NÃO podemos concluir:** baixa nulidade não garante ausência de erro de registro nem
autoriza assumir que categorias especiais ocorram aleatoriamente.

**Limitações:** a análise mede presença e frequência, mas não avalia mecanismos de ausência ou
associação dessas categorias com gravidade.

**Figura:** não aplicável.

**Tabela:** `../reports/tables/phase_2a_data_quality.csv` e
`../reports/tables/phase_2a_special_categories.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/general.py`, executado por
`uv run prf-eda-general`.

**Possível uso no TCC:** seção de qualidade dos dados e ressalvas metodológicas.

**Status:** confirmado.

### EDA004 — Cardinalidade das principais variáveis categóricas

**Data:** 18/08/2026.

**Fase:** 2A — Caracterização geral.

**Pergunta:** qual é a cardinalidade não nula básica das principais variáveis categóricas?

**População analisada:** todas as 342.624 ocorrências, sem transformação das categorias.

**Resultado absoluto:** `dia_semana` 7; `uf` 27; `municipio` 2.050; `causa_acidente` 76;
`tipo_acidente` 18; `classificacao_acidente` 3; `fase_dia` 4; `sentido_via` 3;
`condicao_metereologica` 10; `tipo_pista` 3; `tracado_via` 1.214; `uso_solo` 2; `regional`
28; `delegacia` 155; e `uop` 408 valores distintos não nulos.

**Proporção/taxa:** não aplicável; cardinalidade é uma contagem de valores distintos.

**Comparação:** `municipio` e `tracado_via` apresentam as maiores cardinalidades entre as
variáveis avaliadas, seguidas por `uop`, `delegacia` e `causa_acidente`.

**Interpretação:** a heterogeneidade de cardinalidade deverá orientar escolhas de apresentação
na EDA e avaliação futura de codificação, sem transformar variáveis nesta fase.

**O que NÃO podemos concluir:** cardinalidade não mede relevância substantiva, associação com
gravidade ou utilidade preditiva.

**Limitações:** `tracado_via` preserva composições textuais e não foi expandido; nenhuma
taxonomia foi harmonizada.

**Figura:** não aplicável.

**Tabela:** `../reports/tables/phase_2a_cardinality.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/general.py`, executado por
`uv run prf-eda-general`.

**Possível uso no TCC:** planejamento das tabelas exploratórias e discussão de preparação de
variáveis em fases posteriores.

**Status:** confirmado.

## 2B — Padrões temporais

Nenhum achado registrado.

## 2C — Padrões geográficos

Nenhum achado registrado.

## 2D — Via e ambiente

Nenhum achado registrado.

## 2E — Dinâmica das ocorrências

Nenhum achado registrado.

## 2F — Associação com gravidade

Nenhum achado registrado.

## 2G — Síntese

Nenhum achado registrado.

## Template de achado EDA

Copiar o bloco abaixo para a subseção apropriada. Substituir `EDAxxx` por um identificador
permanente e sequencial.

### EDAxxx — Título

**Data:**

**Fase:** 2A / 2B / 2C / 2D / 2E / 2F / 2G.

**Pergunta:**

**População analisada:** incluir período, filtros e tamanho da amostra.

**Categorias ausentes/ignoradas:**

**Resultado absoluto:**

**Proporção/taxa:** informar numerador e denominador.

**Comparação:**

**Interpretação:**

**O que NÃO podemos concluir:**

**Limitações:**

**Figura:** `../reports/figures/<arquivo>` ou “não aplicável”.

**Tabela:** `../reports/tables/<arquivo>` ou “não aplicável”.

**Código/origem:** caminho do script/notebook e versão do dataset.

**Possível uso no TCC:** seção, argumento ou “não utilizar”.

**Status:** provisório / confirmado / descartado.
