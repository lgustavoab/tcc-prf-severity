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

## Fase 2B — Padrões temporais

### EDA005 — Distribuição mensal do volume de ocorrências registradas

**Data:** 18/08/2026.

**Fase:** 2B — Padrões temporais.

**Pergunta:** em quais meses houve maior e menor volume de ocorrências registradas?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025, sem
filtros.

**Categorias ausentes/ignoradas:** nenhuma; todas as 12 categorias mensais estavam presentes.

**Resultado absoluto:** dezembro apresentou 31.674 registros e fevereiro, 25.166. Após
normalização pela quantidade real de dias-calendário do período, dezembro permaneceu com o
maior valor (204,35 registros/dia), enquanto janeiro apresentou o menor (174,50 registros/dia).

**Proporção/taxa:** dezembro representou 9,2445% do dataset e fevereiro, 7,3451%. A medida por
dia-calendário é uma normalização descritiva, não uma taxa de risco ou exposição ao tráfego.

**Comparação:** dezembro teve 6.508 registros a mais que fevereiro e foi o mês de maior volume
em cada um dos cinco anos (5.847 em 2021; 5.838 em 2022; 6.614 em 2023; 6.587 em 2024; e
6.788 em 2025).

**Estabilidade entre anos:** a liderança de dezembro em volume foi recorrente nos cinco anos.

**Interpretação:** no período analisado, houve maior concentração de registros em dezembro,
inclusive após controlar apenas a duração dos meses.

**O que NÃO podemos concluir:** maior volume mensal não representa taxa por unidade de
exposição nem efeito causal do mês.

**Limitações:** meses têm durações diferentes e não há denominador de fluxo veicular mensal.

**Figura:** `../reports/figures/phase_2b_occurrences_by_month.png`.

**Tabela:** `../reports/tables/phase_2b_month_summary.csv` e
`../reports/tables/phase_2b_month_by_year.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/temporal.py`, dataset interim verificado de
2021–2025.

**Possível uso no TCC:** caracterização descritiva da sazonalidade do volume registrado.

**Status:** confirmado.

### EDA006 — Variação mensal da proporção de ocorrências graves

**Data:** 18/08/2026.

**Fase:** 2B — Padrões temporais.

**Pergunta:** a proporção de ocorrências graves varia entre os meses?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025, sem
filtros.

**Categorias ausentes/ignoradas:** nenhuma.

**Resultado absoluto:** maio reuniu 8.394 graves entre 28.914 registros; fevereiro reuniu
6.868 graves entre 25.166 registros.

**Proporção/taxa:** a maior proporção consolidada ocorreu em maio (29,0309%) e a menor em
fevereiro (27,2908%), diferença descritiva de 1,7401 ponto percentual.

**Comparação:** o mês com maior proporção não foi o mesmo em todos os anos: maio liderou em
2021 e 2025, setembro em 2022, junho em 2023 e agosto em 2024.

**Estabilidade entre anos:** as amplitudes anuais por mês variaram de 0,5552 ponto percentual
em agosto a 2,4980 em junho. A mudança da categoria líder recomenda cautela ao resumir a
dimensão por um único mês.

**Interpretação:** há diferenças descritivas moderadas entre os meses, mas o topo mensal não
foi recorrente nos cinco anos.

**O que NÃO podemos concluir:** as diferenças não demonstram efeito causal do mês nem
probabilidade individual de uma ocorrência grave.

**Limitações:** não há controle de exposição, composição das viagens ou outros fatores que
possam variar ao longo do ano.

**Figura:** `../reports/figures/phase_2b_severe_rate_by_month.png`.

**Tabela:** `../reports/tables/phase_2b_month_summary.csv`,
`../reports/tables/phase_2b_month_by_year.csv` e
`../reports/tables/phase_2b_temporal_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/temporal.py`, dataset interim verificado de
2021–2025.

**Possível uso no TCC:** descrição da associação temporal e justificativa para avaliar
estabilidade antes da modelagem.

**Status:** confirmado.

### EDA007 — Concentração no fim de semana e proporção de graves

**Data:** 18/08/2026.

**Fase:** 2B — Padrões temporais.

**Pergunta:** quais dias concentram mais registros e como dias úteis e fim de semana diferem
descritivamente na proporção de graves?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025, sem
filtros.

**Categorias ausentes/ignoradas:** nenhuma; os sete dias estavam presentes.

**Resultado absoluto:** domingo teve 56.278 registros e 17.093 graves, seguido por sábado com
56.111 registros e 16.840 graves. Terça-feira teve o menor volume, com 42.283 registros.
Agregados, os dias úteis reuniram 230.235 registros e 62.924 graves; o fim de semana, 112.389
registros e 33.933 graves.

**Proporção/taxa:** domingo apresentou 30,3724% de graves e quarta-feira, 26,9935%. A proporção
foi 30,1925% no fim de semana e 27,3303% nos dias úteis, diferença de 2,8621 pontos
percentuais.

**Comparação:** domingo liderou a proporção de graves de 2021 a 2024; em 2025, sábado foi a
categoria mais alta. Em volume, sábado ou domingo liderou em todos os anos.

**Estabilidade entre anos:** a taxa de domingo oscilou apenas 0,5406 ponto percentual entre
os anos; sábado variou 1,5028. O padrão consolidado de valores mais altos no fim de semana foi
recorrente, embora a liderança entre sábado e domingo tenha mudado.

**Interpretação:** entre as ocorrências registradas, houve maior concentração de registros e
maior fração de graves no fim de semana.

**O que NÃO podemos concluir:** o resultado não mostra que o fim de semana causa gravidade nem
estima uma probabilidade individual condicionada à exposição.

**Limitações:** não há quantidade de veículos, viagens ou veículo-quilômetro por dia da
semana; a composição das ocorrências pode diferir entre categorias.

**Figura:** `../reports/figures/phase_2b_occurrences_by_weekday.png` e
`../reports/figures/phase_2b_severe_rate_by_weekday.png`.

**Tabela:** `../reports/tables/phase_2b_weekday_summary.csv`,
`../reports/tables/phase_2b_weekday_by_year.csv` e
`../reports/tables/phase_2b_weekday_group_summary.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/temporal.py`, dataset interim verificado de
2021–2025.

**Possível uso no TCC:** caracterização temporal e avaliação futura de variáveis de calendário.

**Status:** confirmado.

### EDA008 — Padrão horário de volume e gravidade

**Data:** 18/08/2026.

**Fase:** 2B — Padrões temporais.

**Pergunta:** como volume e proporção de graves se distribuem pelas 24 horas?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025, sem
filtros.

**Categorias ausentes/ignoradas:** nenhuma; todas as horas de 0 a 23 estavam presentes.

**Resultado absoluto:** 18h concentrou 25.569 registros e 8.144 graves, maior volume entre as
24 horas. O menor volume ocorreu às 2h, com 5.798 registros. A maior proporção consolidada foi
às 19h, com 7.496 graves em 22.222 registros; a menor, às 8h, com 3.976 graves em 17.194.

**Proporção/taxa:** as taxas variaram de 23,1243% às 8h a 33,7323% às 19h, amplitude
consolidada de 10,6080 pontos percentuais.

**Comparação:** 18h foi a hora de maior volume em cada um dos cinco anos. A maior taxa anual
alternou entre 19h (2022 e 2024) e 21h (2021, 2023 e 2025).

**Estabilidade entre anos:** as amplitudes anuais por hora variaram de 0,9785 ponto percentual
às 7h a 4,5926 às 5h. Apesar da variação pontual, os maiores valores anuais permaneceram na
faixa noturna de 19h–21h.

**Interpretação:** o volume apresenta picos às 7h e, de forma mais acentuada, entre 17h e 19h;
a fração de graves é menor no período diurno central e mais alta em várias horas noturnas.

**O que NÃO podemos concluir:** as taxas não permitem classificar comparativamente a segurança
das horas; são condicionadas aos registros e não ao total de veículos circulando.

**Limitações:** falta denominador horário de exposição; análises por hora não controlam outras
características das ocorrências.

**Figura:** `../reports/figures/phase_2b_occurrences_by_hour.png` e
`../reports/figures/phase_2b_severe_rate_by_hour.png`.

**Tabela:** `../reports/tables/phase_2b_hour_summary.csv`,
`../reports/tables/phase_2b_hour_by_year.csv` e
`../reports/tables/phase_2b_temporal_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/temporal.py`, dataset interim verificado de
2021–2025.

**Possível uso no TCC:** fundamentação descritiva para considerar hora como variável temporal
e avaliar sua estabilidade na modelagem futura.

**Status:** confirmado.

### EDA009 — Distribuição por fase do dia

**Data:** 18/08/2026.

**Fase:** 2B — Padrões temporais.

**Pergunta:** como as categorias existentes de `fase_dia` se comportam em volume e gravidade?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025, sem
filtros.

**Categorias ausentes/ignoradas:** nenhuma; as quatro categorias contratuais estavam presentes
e foram ordenadas semanticamente como Amanhecer, Pleno dia, Anoitecer e Plena Noite.

**Resultado absoluto:** `Pleno dia` reuniu 187.621 registros e 47.477 graves; `Plena Noite`,
119.581 registros e 38.831 graves; `Anoitecer`, 18.821 e 5.486; `Amanhecer`, 16.601 e 5.063.

**Proporção/taxa:** `Pleno dia` concentrou 54,7600% dos registros e apresentou 25,3047% de
graves. `Plena Noite` concentrou 34,9015% e apresentou a maior proporção de graves, 32,4726%.
A diferença entre essas taxas foi 7,1678 pontos percentuais.

**Comparação:** `Pleno dia` liderou o volume em todos os anos e `Plena Noite` liderou a
proporção de graves em todos.

**Estabilidade entre anos:** a taxa de `Pleno dia` variou 0,5931 ponto percentual e a de
`Plena Noite`, 1,2865. `Amanhecer` apresentou a maior amplitude entre as fases, 3,0377 pontos.

**Interpretação:** entre os registros, o período diurno concentrou mais ocorrências, enquanto
a categoria noturna apresentou maior fração de graves de forma recorrente.

**O que NÃO podemos concluir:** a noite não pode ser apresentada como causa de gravidade ou
como risco para quem trafega.

**Limitações:** não há fluxo veicular por fase do dia e a categoria não substitui a hora exata
nem controla outros atributos da ocorrência.

**Figura:** `../reports/figures/phase_2b_severe_rate_by_day_phase.png`.

**Tabela:** `../reports/tables/phase_2b_day_phase_summary.csv`,
`../reports/tables/phase_2b_day_phase_by_year.csv` e
`../reports/tables/phase_2b_temporal_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/temporal.py`, dataset interim verificado de
2021–2025.

**Possível uso no TCC:** discussão descritiva e avaliação futura da redundância entre hora e
fase do dia.

**Status:** confirmado.

### EDA010 — Recorrência e variação dos padrões temporais entre anos

**Data:** 18/08/2026.

**Fase:** 2B — Padrões temporais.

**Pergunta:** os principais padrões temporais foram recorrentes entre 2021 e 2025?

**População analisada:** todas as 342.624 ocorrências registradas, estratificadas pelos cinco
anos e por mês, dia da semana, hora e fase do dia.

**Categorias ausentes/ignoradas:** nenhuma; cada categoria foi observada nos cinco anos.

**Resultado absoluto:** dezembro liderou o volume mensal nos cinco anos; 18h liderou o volume
horário nos cinco; `Pleno dia` liderou o volume por fase nos cinco; e `Plena Noite` liderou a
proporção grave por fase nos cinco.

**Proporção/taxa:** as menores amplitudes anuais observadas foram 0,5406 ponto percentual para
domingo, 0,5552 para agosto, 0,5931 para `Pleno dia` e 0,9785 para 7h. As maiores amplitudes em
cada dimensão foram 2,4980 para junho, 2,1092 para sexta-feira, 4,5926 para 5h e 3,0377 para
`Amanhecer`.

**Comparação:** mês com maior taxa variou entre quatro categorias; dia com maior taxa foi
domingo em quatro anos e sábado em um; hora com maior taxa alternou entre 19h e 21h; fase com
maior taxa permaneceu `Plena Noite`.

**Estabilidade entre anos:** há forte recorrência descritiva nos líderes de volume e na
hierarquia das fases do dia, mas maior variação na identidade do mês e da hora com maior taxa.
Não foi aplicada classificação automática de estabilidade.

**Interpretação:** os resultados sustentam a análise temporal descritiva, mas também indicam
que a estabilidade deve ser examinada por feature antes de qualquer modelagem temporal.

**O que NÃO podemos concluir:** amplitudes pequenas não demonstram invariância estatística, e
amplitudes maiores não provam drift estrutural ou causalidade.

**Limitações:** a comparação é descritiva, sem testes inferenciais, ajuste por composição ou
denominadores de exposição.

**Figura:** não aplicável; as figuras consolidadas EDA005–EDA009 complementam a evidência.

**Tabela:** `../reports/tables/phase_2b_temporal_stability.csv` e tabelas ano × categoria da
Fase 2B.

**Código/origem:** `src/tcc_prf_severity/analysis/temporal.py`, dataset interim verificado de
2021–2025.

**Possível uso no TCC:** seção metodológica sobre validação temporal e motivação para análise
futura de drift.

**Status:** confirmado.

## Fase 2C — Padrões geográficos

### EDA011 — Distribuição e gravidade por macrorregião

**Data:** 18/08/2026.

**Fase:** 2C — Padrões geográficos.

**Pergunta:** como volume e proporção de ocorrências graves se distribuem pelas macrorregiões
brasileiras?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025, sem
filtros.

**Categorias ausentes/ignoradas:** nenhuma; as cinco macrorregiões foram derivadas em memória
a partir de `uf`. `macroregion` representa a divisão geográfica brasileira e não a coluna
`regional`, ligada à estrutura administrativa da PRF.

**Resultado absoluto:** Sudeste concentrou 107.259 registros e 27.127 graves; Sul, 101.415 e
25.226; Nordeste, 74.232 e 26.662; Centro-Oeste, 41.178 e 11.446; Norte, 18.540 e 6.396.

**Proporção/taxa:** Sudeste reuniu 31,3052% do dataset e Sul, 29,5995%. A proporção de graves
foi maior no Nordeste (35,9171%) e menor no Sul (24,8740%), diferença descritiva de 11,0431
pontos percentuais.

**Comparação:** maior concentração de registros e maior proporção de graves não ocorreram na
mesma macrorregião.

**Estabilidade entre anos:** Nordeste teve a maior taxa em quatro anos e Norte em 2023. As
amplitudes anuais foram 0,8891 ponto percentual no Sudeste, 1,0513 no Centro-Oeste, 1,2394 no
Sul, 2,4035 no Nordeste e 4,1118 no Norte.

**Interpretação:** há desigualdade geográfica descritiva tanto no volume registrado quanto na
composição de gravidade, e essas dimensões devem ser analisadas separadamente.

**O que NÃO podemos concluir:** as diferenças não estimam risco rodoviário nem efeito causal
da macrorregião.

**Limitações:** não há fluxo veicular, veículos-quilômetro, extensão usada como exposição ou
quantidade de viagens por região.

**Figura:** `../reports/figures/phase_2c_occurrences_by_macroregion.png` e
`../reports/figures/phase_2c_severe_rate_by_macroregion.png`.

**Tabela:** `../reports/tables/phase_2c_macroregion_summary.csv`,
`../reports/tables/phase_2c_macroregion_by_year.csv` e
`../reports/tables/phase_2c_macroregion_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/geographic.py`, dataset interim verificado
de 2021–2025.

**Possível uso no TCC:** caracterização da desigualdade geográfica descritiva e planejamento
da validação de features geográficas.

**Status:** confirmado.

### EDA012 — Concentração e proporção de graves por UF

**Data:** 18/08/2026.

**Fase:** 2C — Padrões geográficos.

**Pergunta:** quais UFs concentram maior volume e quais apresentam maior proporção de graves
entre as ocorrências registradas?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025, sem
filtros; as 27 UFs foram preservadas.

**Categorias ausentes/ignoradas:** nenhuma.

**Resultado absoluto:** MG concentrou 44.502 registros e 13.025 graves, seguido por SC com
39.849 e 9.942 e PR com 37.055 e 9.850. MA apresentou 2.647 graves entre 5.778 registros; PA,
2.037 entre 4.666; SP, 4.288 entre 23.005.

**Proporção/taxa:** MG representou 12,9886% do dataset. A maior proporção grave ocorreu no MA
(45,8117%), seguido por PA (43,6562%); a menor ocorreu em SP (18,6394%). A amplitude
consolidada entre MA e SP foi 27,1723 pontos percentuais.

**Comparação:** MG liderou o volume nos cinco anos. MA teve a maior proporção em 2021 e de
2023 a 2025; PA liderou em 2022.

**Estabilidade entre anos:** o padrão de volume de MG foi recorrente, enquanto a liderança de
taxa alternou uma vez entre MA e PA.

**Interpretação:** volume e fração grave apresentam distribuições estaduais distintas e não
devem ser condensados em uma única noção de desempenho geográfico.

**O que NÃO podemos concluir:** não é possível ordenar a segurança das UFs; faltam
denominadores de exposição e controle da composição das ocorrências.

**Limitações:** as UFs diferem em malha rodoviária, tráfego, população, registro e composição
das ocorrências, dimensões não ajustadas nesta fase.

**Figura:** `../reports/figures/phase_2c_occurrences_by_uf.png` e
`../reports/figures/phase_2c_severe_rate_by_uf.png`.

**Tabela:** `../reports/tables/phase_2c_uf_summary.csv`,
`../reports/tables/phase_2c_uf_volume_top15.csv` e
`../reports/tables/phase_2c_uf_by_year.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/geographic.py`, dataset interim verificado
de 2021–2025.

**Possível uso no TCC:** discussão da heterogeneidade estadual e futura avaliação de UF como
feature categórica.

**Status:** confirmado.

### EDA013 — Amplitude anual da proporção de graves por UF

**Data:** 18/08/2026.

**Fase:** 2C — Padrões geográficos.

**Pergunta:** as taxas estaduais permanecem numericamente semelhantes entre 2021 e 2025?

**População analisada:** todas as 342.624 ocorrências, estratificadas por 27 UFs e cinco anos.

**Categorias ausentes/ignoradas:** nenhuma; todas as UFs foram observadas nos cinco anos.

**Resultado absoluto:** as menores amplitudes anuais ocorreram em RS (0,9389 ponto
percentual), MG (1,0856), RN (1,1202) e GO (1,2421). As maiores ocorreram em RR (17,9409), SE
(9,5196), MA (8,0007), AM (7,2431) e PA (7,1917).

**Proporção/taxa:** em MA, as taxas anuais variaram de 42,1751% a 50,1757%; em MG, de 28,8726%
a 29,9582%; em RR, de 27,9851% a 45,9259%.

**Comparação:** amplitudes maiores apareceram em várias UFs com volumes consolidados menores,
o que exige considerar conjuntamente taxa, tamanho amostral e ano.

**Estabilidade entre anos:** foram reportados mínimo, máximo e amplitude, sem transformar
qualquer valor automaticamente em classe “estável” ou “instável”.

**Interpretação:** a estabilidade anual varia entre UFs e deverá ser avaliada antes de usar
geografia em validação temporal futura.

**O que NÃO podemos concluir:** pequena amplitude não prova invariância; grande amplitude não
prova drift estrutural nem mudança causal.

**Limitações:** a análise é descritiva e não ajusta composição, exposição ou incerteza de
amostras anuais menores.

**Figura:** não aplicável; as figuras consolidadas por UF complementam a evidência.

**Tabela:** `../reports/tables/phase_2c_uf_stability.csv` e
`../reports/tables/phase_2c_uf_by_year.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/geographic.py`, dataset interim verificado
de 2021–2025.

**Possível uso no TCC:** seção metodológica sobre drift e validação temporal das features.

**Status:** confirmado.

### EDA014 — Concentração de registros por BR e preservação de BR 0

**Data:** 18/08/2026.

**Fase:** 2C — Padrões geográficos.

**Pergunta:** quais BRs concentram mais ocorrências e como a categoria `br = 0` foi tratada?

**População analisada:** todas as 342.624 ocorrências nas tabelas completas; apenas o destaque
de volume excluiu `br = 0`.

**Categorias ausentes/ignoradas:** `br = 0` foi preservada e rotulada como “Não identificada
(BR 0)”; não foi tratada como rodovia válida no ranking.

**Resultado absoluto:** BR 101 concentrou 59.370 registros e 15.468 graves; BR 116, 52.837 e
12.309; BR 40, 16.390 e 4.015. A categoria BR 0 preservou 883 registros, dos quais 81 graves.

**Proporção/taxa:** BR 101 representou 17,3280% do dataset e apresentou 26,0536% de graves;
BR 116 representou 15,4213% e apresentou 23,2962%. BR 0 representou 0,2577% do dataset.

**Comparação:** as duas primeiras BRs concentraram volumes muito superiores às demais, mas
essa contagem não foi normalizada por extensão ou tráfego.

**Estabilidade entre anos:** não avaliada por BR nesta fase, em favor de parcimônia.

**Interpretação:** o resultado descreve concentração de registros por código de BR e preserva
explicitamente a anomalia conhecida sem contaminar os destaques de rodovias identificadas.

**O que NÃO podemos concluir:** o ranking não ordena segurança rodoviária e não estima taxas
por quilômetro ou por veículo.

**Limitações:** não há extensão percorrida, fluxo veicular ou segmentação da rodovia; códigos
agregam trechos heterogêneos.

**Figura:** `../reports/figures/phase_2c_br_volume_top15.png`.

**Tabela:** `../reports/tables/phase_2c_br_summary.csv` e
`../reports/tables/phase_2c_br_volume_top15.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/geographic.py`, dataset interim verificado
de 2021–2025.

**Possível uso no TCC:** descrição da concentração por rodovia e advertência metodológica
sobre exposição e `br = 0`.

**Status:** confirmado.

### EDA015 — Concentração municipal com chave UF + município

**Data:** 18/08/2026.

**Fase:** 2C — Padrões geográficos.

**Pergunta:** quais pares município/UF concentram maior volume de registros?

**População analisada:** todas as 342.624 ocorrências, agrupadas em 2.098 pares `uf +
municipio`.

**Categorias ausentes/ignoradas:** nenhuma. Os 2.098 pares correspondem a 2.050 nomes
municipais distintos; as 48 combinações excedentes demonstram por que o nome isolado não foi
usado como chave.

**Resultado absoluto:** Brasília/DF concentrou 4.948 registros e 948 graves; Guarulhos/SP,
3.914 e 571; Curitiba/PR, 3.774 e 720; São José/SC, 3.629 e 707; Duque de Caxias/RJ, 3.508 e
544.

**Proporção/taxa:** Brasília representou 1,4441% do dataset e apresentou 19,1593% de graves.
Entre os cinco maiores volumes, as proporções variaram de 14,5887% em Guarulhos a 19,4820% em
São José.

**Comparação:** o município/UF de maior volume não coincide com os destaques de maior taxa
entre grupos elegíveis.

**Estabilidade entre anos:** não foi criada tabela município × ano devido à alta cardinalidade
e à ausência de necessidade científica nesta fase.

**Interpretação:** os registros apresentam concentração municipal, mas o agrupamento correto
depende da composição de UF e nome do município.

**O que NÃO podemos concluir:** maior contagem não significa maior insegurança ou risco para
moradores e viajantes.

**Limitações:** não há população exposta, fluxo, viagens ou extensão rodoviária municipal como
denominador.

**Figura:** `../reports/figures/phase_2c_municipality_volume_top15.png`.

**Tabela:** `../reports/tables/phase_2c_municipality_summary.csv` e
`../reports/tables/phase_2c_municipality_volume_top15.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/geographic.py`, dataset interim verificado
de 2021–2025.

**Possível uso no TCC:** caracterização da alta cardinalidade municipal e justificativa da
chave geográfica composta.

**Status:** confirmado.

### EDA016 — Destaques de taxa com critério editorial de amostra

**Data:** 18/08/2026.

**Fase:** 2C — Padrões geográficos.

**Pergunta:** entre BRs e municípios com amostra suficiente para destaque descritivo, quais
apresentam maiores proporções de graves?

**População analisada:** tabelas completas com 126 categorias de BR e 2.098 pares
município/UF; destaques restritos a BRs identificadas e categorias com pelo menos 500
ocorrências.

**Categorias ausentes/ignoradas:** nenhuma foi removida das tabelas completas. BR 0 foi
excluída somente do ranking; categorias abaixo de 500 permaneceram disponíveis nos resumos.

**Resultado absoluto:** entre BRs elegíveis, BR 10 apresentou 992 graves em 2.139 registros,
BR 423 teve 463 em 999 e BR 316, 2.652 em 5.889. Entre municípios/UF elegíveis, Barreiras/BA
teve 236 graves em 500 registros, Picos/PI 240 em 572 e Sabará/MG 248 em 592.

**Proporção/taxa:** as taxas foram 46,3768% na BR 10, 46,3463% na BR 423 e 45,0331% na BR
316; 47,2000% em Barreiras, 41,9580% em Picos e 41,8919% em Sabará.

**Comparação:** com n≥100 seriam elegíveis 99 BRs e 763 municípios; com n≥500, 62 e 157; com
n≥1000, 47 e 59. No corte municipal de 1000, o primeiro destaque passaria a Governador
Valadares/MG, com 408 graves em 1.112 registros (36,6906%).

**Critério n>=500:** o limite foi adotado apenas para evitar destacar proporções extremamente
instáveis em grupos muito pequenos. Não é limiar científico universal nem filtro do dataset.

**Estabilidade entre anos:** não avaliada para BR e município nesta fase.

**Interpretação:** os destaques dependem do critério editorial de tamanho amostral; por isso,
taxa, numerador e total foram apresentados conjuntamente.

**O que NÃO podemos concluir:** as categorias destacadas não constituem uma classificação de
segurança, e a taxa não estima probabilidade individual de acidente grave.

**Limitações:** o corte de 500 é convencional e os resultados não controlam exposição ou
composição das ocorrências.

**Figura:** não aplicável; tabelas evitam ênfase visual indevida em rankings de taxa.

**Tabela:** `../reports/tables/phase_2c_br_severe_rate_top15_n500.csv`,
`../reports/tables/phase_2c_municipality_severe_rate_top15_n500.csv` e
`../reports/tables/phase_2c_ranking_threshold_diagnostics.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/geographic.py`, dataset interim verificado
de 2021–2025.

**Possível uso no TCC:** justificativa metodológica para controle editorial de pequenas
amostras e discussão de alta cardinalidade.

**Status:** confirmado.

### EDA017 — Cobertura mínima das coordenadas

**Data:** 18/08/2026.

**Fase:** 2C — Padrões geográficos.

**Pergunta:** qual é a cobertura básica das coordenadas no dataset interim?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025.

**Categorias ausentes/ignoradas:** não aplicável.

**Resultado absoluto:** latitude apresentou zero nulos; longitude, zero nulos; foram
observados 166.502 pares distintos de coordenadas.

**Proporção/taxa:** cobertura não nula de 100% em ambas as colunas.

**Comparação:** não aplicável; esta foi somente uma caracterização de cobertura.

**Estabilidade entre anos:** não avaliada.

**Interpretação:** as coordenadas estão preenchidas no interim, mas isso não valida precisão,
exatidão ou adequação para análise espacial.

**O que NÃO podemos concluir:** preenchimento completo não garante georreferenciamento
correto nem autoriza inferência espacial.

**Limitações:** não foram criados mapas, clusters, testes espaciais ou validação externa de
coordenadas.

**Figura:** não aplicável.

**Tabela:** `../reports/tables/phase_2c_coordinate_coverage.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/geographic.py`, dataset interim verificado
de 2021–2025.

**Possível uso no TCC:** avaliação futura da viabilidade de visualizações espaciais simples.

**Status:** confirmado.

## Fase 2D — Via e ambiente

### EDA018 — Tipo de pista e proporção de ocorrências graves

**Data:** 18/08/2026.

**Fase:** 2D — Via e ambiente.

**Pergunta:** como volume e proporção de graves se distribuem entre os tipos de pista?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025.

**Categorias ausentes/ignoradas:** nenhuma; foram preservadas Simples, Dupla e Múltipla.

**Resultado absoluto:** pista Simples concentrou 167.198 registros e 56.365 graves; Dupla,
143.585 e 33.529; Múltipla, 31.841 e 6.963.

**Proporção/taxa:** as proporções graves foram 33,7115%, 23,3513% e 21,8680%,
respectivamente. As participações no dataset foram 48,7993%, 41,9075% e 9,2933%.

**Comparação:** pista Simples reuniu o maior volume e a maior proporção de graves entre as
três categorias.

**Estabilidade entre anos:** Simples apresentou a maior proporção em todos os anos, variando
de 33,2019% a 34,0765% (amplitude de 0,8746 ponto percentual). As amplitudes de Dupla e
Múltipla foram 0,8383 e 0,8273 ponto.

**Interpretação:** existe contraste descritivo persistente entre os tipos de pista nas
ocorrências registradas.

**O que NÃO podemos concluir:** o contraste não demonstra efeito causal do tipo de pista nem
estima risco absoluto de acidente ou de gravidade ao trafegar.

**Limitações:** não há denominador de exposição rodoviária nem controle por região, fluxo,
velocidade, composição dos veículos ou outros fatores.

**Figura:** `../reports/figures/phase_2d_severe_rate_by_road_type.png`.

**Tabela:** `../reports/tables/phase_2d_road_type_summary.csv`,
`../reports/tables/phase_2d_road_type_by_year.csv` e
`../reports/tables/phase_2d_environment_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/road_environment.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** motivar análise associativa posterior com controle das demais
variáveis e validação temporal.

**Status:** confirmado.

### EDA019 — Uso do solo conforme o campo da PRF

**Data:** 18/08/2026.

**Fase:** 2D — Via e ambiente.

**Pergunta:** como o campo `uso_solo` se relaciona descritivamente com a gravidade?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025.

**Categorias ausentes/ignoradas:** nenhuma; foram preservadas as categorias `Não` e `Sim`.

**Resultado absoluto:** `Não` reuniu 194.181 registros, dos quais 57.900 graves; `Sim`
reuniu 148.443, dos quais 38.957 graves.

**Proporção/taxa:** as proporções graves foram 29,8175% em `Não` e 26,2437% em `Sim`; as
participações no dataset foram 56,6747% e 43,3253%.

**Comparação:** `Não` apresentou proporção 3,5738 pontos percentuais maior que `Sim`.

**Estabilidade entre anos:** `Não` manteve a maior proporção em todos os anos; sua amplitude
foi 0,3614 ponto percentual, ante 0,6360 em `Sim`.

**Interpretação:** as duas categorias do campo apresentam diferença descritiva pequena e
recorrente no período.

**O que NÃO podemos concluir:** `Sim` e `Não` não foram reinterpretados automaticamente como
urbano e rural, e a diferença não demonstra causalidade nem risco absoluto.

**Limitações:** a semântica é a registrada pela PRF e não há denominador de exposição ou
ajuste por fatores de confusão.

**Figura:** `../reports/figures/phase_2d_severe_rate_by_land_use.png`.

**Tabela:** `../reports/tables/phase_2d_land_use_summary.csv`,
`../reports/tables/phase_2d_land_use_by_year.csv` e
`../reports/tables/phase_2d_environment_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/road_environment.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** variável contextual a ser avaliada com sua codificação original.

**Status:** confirmado.

### EDA020 — Sentido da via e preservação de Não Informado

**Data:** 18/08/2026.

**Fase:** 2D — Via e ambiente.

**Pergunta:** qual é a distribuição de volume e gravidade por sentido da via?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025.

**Categorias ausentes/ignoradas:** `Não Informado` foi preservado como categoria explícita.

**Resultado absoluto:** Crescente reuniu 183.409 registros e 53.013 graves; Decrescente,
158.332 e 43.763; Não Informado, 883 e 81.

**Proporção/taxa:** as proporções graves foram 28,9043%, 27,6400% e 9,1733%; Não Informado
representou 0,2577% do dataset.

**Comparação:** Crescente e Decrescente diferiram 1,2642 ponto percentual; Não Informado teve
volume muito menor.

**Estabilidade entre anos:** as amplitudes anuais foram 0,7490 ponto em Crescente, 0,7309 em
Decrescente e 8,1683 em Não Informado; a última deve ser lida junto de seu baixo volume.

**Interpretação:** a direção nominal apresenta pequena diferença descritiva entre as duas
categorias informadas.

**O que NÃO podemos concluir:** Crescente ou Decrescente não possuem significado causal para
gravidade e não representam, isoladamente, condições de segurança.

**Limitações:** Não Informado é pouco frequente; não há exposição por sentido nem controle de
características da via e do tráfego.

**Figura:** não aplicável; a tabela é suficiente para o contraste.

**Tabela:** `../reports/tables/phase_2d_direction_summary.csv`,
`../reports/tables/phase_2d_direction_by_year.csv` e
`../reports/tables/phase_2d_environment_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/road_environment.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** documentação de qualidade e avaliação contextual posterior.

**Status:** confirmado.

### EDA021 — Condição meteorológica, tamanho amostral e categorias raras

**Data:** 18/08/2026.

**Fase:** 2D — Via e ambiente.

**Pergunta:** como volume e proporção grave variam entre as categorias meteorológicas?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025; todas as
dez categorias do contrato foram mantidas na tabela completa.

**Categorias ausentes/ignoradas:** `Ignorado` foi preservado com 4.492 registros. Granizo
(n=11) e Neve (n=8) foram preservados, mas não destacados por taxa. `Ignorado` também foi
excluído somente dos destaques por não representar uma condição meteorológica observada.

**Resultado absoluto:** Céu Claro concentrou 214.012 registros e 62.867 graves; Nublado,
54.014 e 14.971; Chuva, 34.396 e 8.285. Como aspecto de qualidade, `Ignorado` teve 1.552
graves em 4.492 registros. Entre condições informadas com n≥500, Nevoeiro/Neblina teve 894
graves em 2.838 e Vento, 186 em 593.

**Proporção/taxa:** `Ignorado` apresentou 34,5503%, registrada como métrica de ausência
semântica, não como efeito meteorológico. Entre condições informadas elegíveis ao destaque,
as maiores proporções foram 31,5011% em Nevoeiro/Neblina e 31,3659% em Vento. Céu Claro teve
29,3755%; Nublado, 27,7169%; Sol, 26,8196%; Chuva, 24,0871%; Garoa/Chuvisco, 22,2644%.

**Comparação:** o corte editorial `n >= 500` evitou destacar Granizo e Neve, cujas taxas se
baseiam em apenas 11 e 8 observações. `Ignorado` foi excluído por ausência de conteúdo
meteorológico. Nenhuma dessas regras removeu categorias da análise completa, anual ou de
estabilidade.

**Estabilidade entre anos:** amplitudes foram pequenas nas categorias volumosas Céu Claro
(0,5941 ponto), Nublado (0,9225), Sol (0,9768) e Chuva (1,3658); categorias menores foram
mais variáveis, incluindo Vento (7,5321) e Ignorado (6,7986).

**Interpretação:** tamanho amostral e qualidade de registro são indispensáveis para ler as
diferenças meteorológicas observadas. A taxa de `Ignorado` caracteriza informação ausente e
não recebe interpretação substantiva como condição meteorológica.

**O que NÃO podemos concluir:** as proporções não medem o risco de acidente sob cada condição
nem demonstram que a meteorologia causou a gravidade.

**Limitações:** não há exposição por condição meteorológica; `Ignorado` não é condição física;
categorias raras geram taxas instáveis. O limiar de 500 é editorial, não científico universal.

**Figura:** `../reports/figures/phase_2d_severe_rate_by_weather.png`.

**Tabela:** `../reports/tables/phase_2d_weather_summary.csv`,
`../reports/tables/phase_2d_weather_by_year.csv`,
`../reports/tables/phase_2d_weather_severe_rate_n500.csv` e
`../reports/tables/phase_2d_environment_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/road_environment.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** fundamentar critérios de amostra e tratamento explícito de categorias
raras ou desconhecidas.

**Status:** confirmado.

### EDA022 — Componentes multivalorados de traçado da via

**Data:** 18/08/2026.

**Fase:** 2D — Via e ambiente.

**Pergunta:** quais componentes básicos aparecem em `tracado_via` e como se distribuem volume
e proporção grave?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025, com
separação analítica em memória pelo delimitador `;`.

**Categorias ausentes/ignoradas:** nenhum token desconhecido foi encontrado. Foram confirmados
Aclive, Curva, Declive, Desvio Temporário, Em Obras, Interseção de Vias, Ponte, Reta, Retorno
Regulamentado, Rotatória, Túnel e Viaduto.

**Resultado absoluto:** Reta apareceu em 241.869 ocorrências, Curva em 62.755, Declive em
32.735, Aclive em 25.085 e Interseção de Vias em 22.802. A soma das contagens foi 418.561,
75.937 acima do total do dataset, pois uma ocorrência pode conter vários componentes.

**Proporção/taxa:** Reta esteve em 70,5931% das ocorrências; Curva, 18,3160%; Declive, 9,5542%.
Entre componentes com n≥500, Ponte apresentou 31,7514% de graves (1.124/3.540), Declive
31,3487% (10.262/32.735) e Aclive 29,7668% (7.467/25.085).

**Comparação:** os componentes foram ordenados por volume na tabela completa; `n >= 500` foi
usado somente nos destaques de taxa. Túnel (n=190) permaneceu na tabela, mas não no destaque.

**Estabilidade entre anos:** entre componentes volumosos, as amplitudes foram 0,8387 ponto em
Reta, 1,3939 em Curva, 2,0138 em Declive e 1,9174 em Aclive. Categorias menores foram mais
instáveis, como Desvio Temporário (7,9765) e Túnel (21,0221).

**Interpretação:** `tracado_via` representa combinações multivaloradas, não aproximadamente
1.214 tipos independentes. As contagens de componentes não são mutuamente exclusivas; o
percentual significa ocorrências que contêm o componente, não participação exclusiva.

**O que NÃO podemos concluir:** os contrastes não demonstram efeito causal do traçado nem
estimam risco absoluto de acidente ou gravidade.

**Limitações:** não há denominador de exposição por componente, e combinações entre componentes
podem refletir contextos distintos não controlados nesta análise.

**Figura:** `../reports/figures/phase_2d_severe_rate_by_road_layout_component.png`.

**Tabela:** `../reports/tables/phase_2d_road_layout_component_summary.csv`,
`../reports/tables/phase_2d_road_layout_component_by_year.csv`,
`../reports/tables/phase_2d_road_layout_component_severe_rate_n500.csv` e
`../reports/tables/phase_2d_road_layout_tokens.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/road_environment.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** definir representação multirrótulo adequada antes de qualquer análise
associativa ou preparação de features.

**Status:** confirmado.

### EDA023 — Estabilidade descritiva das dimensões de via e ambiente

**Data:** 18/08/2026.

**Fase:** 2D — Via e ambiente.

**Pergunta:** os contrastes consolidados de via e ambiente se repetem entre 2021 e 2025?

**População analisada:** todas as 342.624 ocorrências, estratificadas por ano e pelas
categorias da Fase 2D.

**Categorias ausentes/ignoradas:** categorias raras e especiais foram mantidas; seus volumes
devem acompanhar as amplitudes.

**Resultado absoluto:** foram calculados mínimo, máximo, amplitude e número de anos observados
para cada categoria de tipo de pista, uso do solo, sentido, meteorologia e componente de
traçado.

**Proporção/taxa:** Simples liderou tipo de pista e `Não` liderou uso do solo nos cinco anos,
com amplitudes de 0,8746 e 0,3614 ponto percentual. Nas categorias meteorológicas volumosas,
as amplitudes ficaram entre 0,5941 e 1,3658 ponto; Reta variou 0,8387 ponto.

**Comparação:** categorias volumosas tenderam a variações anuais menores que categorias raras;
por exemplo, Túnel variou 21,0221 pontos e Neve, 33,3333, com amostras muito pequenas.

**Estabilidade entre anos:** a tabela registra diretamente mínimo, máximo e amplitude, sem
criar índice composto ou classificar automaticamente categorias como estáveis.

**Interpretação:** os padrões mais volumosos foram descritivamente recorrentes, enquanto
amplitudes de grupos raros não devem ser separadas de seus tamanhos amostrais.

**O que NÃO podemos concluir:** recorrência temporal não elimina confundimento, não demonstra
causalidade e não garante estabilidade futura ou ausência de drift.

**Limitações:** cinco pontos anuais oferecem caracterização simples; não foram feitos testes
inferenciais, ajuste de composição ou validação de exposição.

**Figura:** não aplicável; a tabela preserva todas as categorias e medidas.

**Tabela:** `../reports/tables/phase_2d_environment_stability.csv` e tabelas `*_by_year.csv`
da Fase 2D.

**Código/origem:** `src/tcc_prf_severity/analysis/road_environment.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** orientar validação temporal futura sem antecipar decisões de ML.

**Status:** confirmado.

## Fase 2E — Dinâmica das ocorrências

As quatro variáveis desta seção podem ser conhecidas ou consolidadas apenas durante ou após a
ocorrência. Seu uso aqui é exclusivamente descritivo/associativo e não implica elegibilidade
automática como features de modelos futuros. Essa elegibilidade será decidida separadamente,
considerando disponibilidade temporal e risco de leakage. Não foram usados `mortos`,
`feridos`, `feridos_graves`, `feridos_leves`, `ilesos`, `ignorados` ou
`classificacao_acidente` como variáveis explicativas.

### EDA024 — Volume e gravidade por tipo de acidente registrado

**Data:** 18/08/2026.

**Fase:** 2E — Dinâmica das ocorrências.

**Pergunta:** quais tipos de acidente registrados concentram volume e quais apresentam maior
proporção de graves?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025.

**Categorias ausentes/ignoradas:** nenhuma categoria foi harmonizada, combinada ou removida;
as 18 strings observadas foram preservadas.

**Resultado absoluto:** Colisão traseira teve 65.634 registros e 15.538 graves; Saída de leito
carroçável, 52.394 e 11.565; Colisão transversal, 43.190 e 14.238. Entre tipos com n≥500,
Atropelamento de Pedestre teve 10.416 graves em 15.313 registros e Colisão frontal, 14.532 em
23.045.

**Proporção/taxa:** entre os tipos elegíveis ao destaque, Atropelamento de Pedestre apresentou
68,0206% de graves, Colisão frontal 63,0592%, Colisão lateral sentido oposto 35,4728% e
Colisão transversal 32,9660%.

**Comparação:** o maior volume não coincidiu com a maior proporção. O corte `n >= 500` foi
aplicado apenas ao destaque de taxa, sem retirar categorias da tabela completa.

**Estabilidade entre anos:** Atropelamento de Pedestre esteve nos cinco anos e variou de
67,1573% a 68,7717% (amplitude 1,6144 ponto percentual); Colisão frontal variou de 62,2785%
a 63,5335% (1,2550 ponto). A estabilidade foi calculada somente para categorias presentes em
pelo menos três anos.

**Interpretação:** existem diferenças descritivas persistentes entre os tipos registrados nas
ocorrências, com separação clara entre volume e proporção grave.

**O que NÃO podemos concluir:** o tipo registrado não demonstra causalidade, não mede risco
absoluto e não é automaticamente uma feature disponível antes ou no momento de uma previsão.

**Limitações:** tipo de acidente pode depender da dinâmica e da classificação posterior da
ocorrência; não houve controle por exposição ou pelas demais características.

**Figura:** `../reports/figures/phase_2e_accident_type_volume_top15.png` e
`../reports/figures/phase_2e_accident_type_severe_rate_top15_n500.png`.

**Tabela:** `../reports/tables/phase_2e_accident_type_summary.csv`,
`../reports/tables/phase_2e_accident_type_by_year.csv` e tabelas top 15 correspondentes.

**Código/origem:** `src/tcc_prf_severity/analysis/occurrence_dynamics.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** caracterização associativa da dinâmica, sujeita à avaliação futura de
disponibilidade temporal e leakage.

**Status:** confirmado.

### EDA025 — Volume e gravidade por causa registrada pela PRF

**Data:** 18/08/2026.

**Fase:** 2E — Dinâmica das ocorrências.

**Pergunta:** quais categorias registradas em `causa_acidente` concentram volume e quais
apresentam maior proporção de graves?

**População analisada:** todas as 342.624 ocorrências registradas entre 2021 e 2025.

**Categorias ausentes/ignoradas:** nenhuma das 76 strings foi harmonizada, combinada ou
removida; a análise trata o campo como causa registrada pela PRF, não como causalidade
científica demonstrada.

**Resultado absoluto:** Reação tardia ou ineficiente do condutor teve 46.901 registros e
11.223 graves; Ausência de reação do condutor, 44.630 e 11.912; Acessar a via sem observar a
presença dos outros veículos, 31.168 e 10.244. Entre categorias com n≥500, Pedestre andava na
pista teve 2.460 graves em 3.262 registros.

**Proporção/taxa:** Pedestre andava na pista apresentou 75,4139% de graves; Entrada inopinada
do pedestre, 68,7312%; Pedestre cruzava a pista fora da faixa, 66,4806%; Transitar na
contramão, 60,2333%.

**Comparação:** as categorias de maior volume não foram as mesmas com maiores proporções. O
threshold editorial foi aplicado somente ao ranking de taxa.

**Estabilidade entre anos:** Pedestre andava na pista esteve nos cinco anos e variou de
74,2574% a 77,7946% (amplitude 3,5371 pontos); Transitar na contramão variou de 58,8663% a
60,8291% (1,9628 ponto). Algumas categorias com menor volume apresentaram amplitudes maiores.

**Interpretação:** as categorias registradas apresentam associações descritivas marcantes com
gravidade, mas representam a classificação registrada no boletim.

**O que NÃO podemos concluir:** a causa registrada não prova que a categoria provocou a
gravidade e não deve ser chamada de classificação de perigo ou de risco individual.

**Limitações:** o campo pode incorporar conhecimento posterior à ocorrência, pode variar com
práticas de registro e exige avaliação específica de leakage antes de eventual modelagem.

**Figura:** `../reports/figures/phase_2e_cause_volume_top15.png` e
`../reports/figures/phase_2e_cause_severe_rate_top15_n500.png`.

**Tabela:** `../reports/tables/phase_2e_cause_summary.csv`,
`../reports/tables/phase_2e_cause_by_year.csv` e tabelas top 15 correspondentes.

**Código/origem:** `src/tcc_prf_severity/analysis/occurrence_dynamics.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** discutir associação descritiva e a separação entre campo registrado e
inferência causal.

**Status:** confirmado.

### EDA026 — Mudanças observadas nas taxonomias de tipo e causa

**Data:** 18/08/2026.

**Fase:** 2E — Dinâmica das ocorrências.

**Pergunta:** as taxonomias observadas de `tipo_acidente` e `causa_acidente` permaneceram
iguais entre 2021 e 2025?

**População analisada:** todas as categorias observadas nas 342.624 ocorrências, sem
harmonização textual.

**Categorias ausentes/ignoradas:** ausência em um ano foi tratada como não observação daquela
string no ano, sem concluir equivalência com outra categoria semelhante.

**Resultado absoluto:** `tipo_acidente` apresentou 17, 16, 16, 17 e 17 categorias por ano; a
união teve 18, sendo 16 presentes nos cinco anos e uma exclusiva de um ano. Colisão lateral
apareceu somente em 2021 (676 registros), enquanto Sinistro pessoal de trânsito apareceu em
2024–2025 (19). `causa_acidente` apresentou 71, 71, 75, 69 e 69 categorias; a união teve 76,
65 presentes nos cinco anos e uma exclusiva de um ano.

**Proporção/taxa:** não aplicável; este é um diagnóstico de taxonomia.

**Comparação:** em causa, cinco categorias tiveram primeiro registro após 2021 e sete tiveram
último registro antes de 2025. Exemplos preservados incluem `Transitar no acostamento`
(2021–2022) e `Transitar no Acostamento` (2023–2025), sem decidir que sejam equivalentes.

**Estabilidade entre anos:** o lifecycle registra primeiro ano, último ano e número de anos
observados; a tabela de taxas inclui somente categorias presentes em pelo menos três anos.

**Interpretação:** as taxonomias observadas mudaram ao longo do período, sobretudo em causa.
Essa mudança precisa ser considerada antes de comparações longitudinais ou preparação futura.

**O que NÃO podemos concluir:** sem referência externa, não se pode atribuir automaticamente
as mudanças a revisão formal de taxonomia, erro, mera grafia ou mudança substantiva.

**Limitações:** o diagnóstico usa igualdade exata das strings e deliberadamente não harmoniza
rótulos semelhantes.

**Figura:** não aplicável; tabelas preservam detalhes sem simplificação visual.

**Tabela:** `../reports/tables/phase_2e_taxonomy_diagnostics.csv`,
`../reports/tables/phase_2e_category_lifecycle.csv` e
`../reports/tables/phase_2e_category_stability.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/occurrence_dynamics.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** justificar tratamento temporal explícito das categorias e impedir
harmonização não documentada.

**Status:** confirmado.

### EDA027 — Pessoas envolvidas, cauda e proporção grave

**Data:** 18/08/2026.

**Fase:** 2E — Dinâmica das ocorrências.

**Pergunta:** como a contagem registrada de pessoas envolvidas se relaciona descritivamente
com gravidade?

**População analisada:** todas as 342.624 ocorrências; 75 valores exatos observados, sem bins,
remoção ou winsorização.

**Categorias ausentes/ignoradas:** não aplicável; `pessoas` é não nula e ≥1 pelo contrato. As
métricas não foram derivadas dos campos de vítimas.

**Resultado absoluto:** mínimo 1, P25 2, mediana 2, média 2,5733, P75 3, P90 4, P95 5, P99 8 e
máximo 95. Houve 2.993 registros acima de P99. Os valores de 1 a 9 tiveram pelo menos 500
ocorrências cada.

**Proporção/taxa:** entre valores elegíveis, a proporção grave foi 18,7820% com uma pessoa
(14.048/74.795), 27,1340% com duas (37.605/138.590), 32,7845% com três
(22.858/69.722) e chegou a 49,0286% com nove (429/875).

**Comparação:** a associação observada é real no dataset: entre os valores exatos elegíveis,
as proporções cresceram monotonicamente de 18,7820% com uma pessoa até 49,0286% com nove. A
tabela completa preserva toda a cauda, inclusive valores com amostras pequenas.

**Estabilidade entre anos:** não avaliada para cada contagem nesta fase.

**Interpretação:** há associação descritiva entre maior número registrado de pessoas e maior
proporção grave entre os valores com amostra suficiente. Como `target_grave` é definido no
nível da ocorrência por `(mortos > 0) OR (feridos_graves > 0)`, ocorrências com mais pessoas
possuem, por construção, mais oportunidades para que ao menos uma satisfaça a condição do
target. Parte da associação pode, portanto, ser mecanicamente influenciada por essa definição.

**O que NÃO podemos concluir:** o crescimento observado não deve ser interpretado diretamente
como efeito causal do número de pessoas sobre a gravidade. `pessoas` pode ser consolidada após
a ocorrência e exige cautela adicional antes de qualquer seleção futura de features.

**Limitações:** a relação mecânica com a definição do target e o conhecimento potencialmente
pós-ocorrência tornam `pessoas` especialmente suscetível a leakage e endogeneidade. Existem
18.538 divergências conhecidas na decomposição de pessoas, preservadas como métrica de
qualidade.

**Figura:** `../reports/figures/phase_2e_people_distribution.png`.

**Tabela:** `../reports/tables/phase_2e_people_distribution.csv`,
`../reports/tables/phase_2e_people_summary_statistics.csv` e
`../reports/tables/phase_2e_people_severe_rate_n500.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/occurrence_dynamics.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** caracterização da dinâmica e alerta de disponibilidade/leakage.

**Status:** confirmado.

### EDA028 — Veículos envolvidos, cauda e proporção grave

**Data:** 18/08/2026.

**Fase:** 2E — Dinâmica das ocorrências.

**Pergunta:** como a contagem registrada de veículos envolvidos se relaciona descritivamente
com gravidade?

**População analisada:** todas as 342.624 ocorrências; 30 valores exatos observados, sem bins,
remoção ou winsorização.

**Categorias ausentes/ignoradas:** não aplicável; `veiculos` é não nula e ≥1 pelo contrato.

**Resultado absoluto:** mínimo 1, P25 1, mediana 2, média 1,9865, P75 2, P90 3, P95 4, P99 6 e
máximo 131. Houve 2.230 registros acima de P99. Os valores de 1 a 7 tiveram pelo menos 500
ocorrências cada.

**Proporção/taxa:** entre valores elegíveis, uma unidade apresentou 20,4720% de graves
(23.493/114.757), duas 30,9446% (50.294/162.529), três 33,8377% (13.798/40.777), quatro
35,8181% (5.199/14.515) e cinco 40,3329% (2.326/5.767); seis e sete tiveram 39,0434% e 39,9%.

**Comparação:** houve aumento de uma a cinco unidades, mas os valores elegíveis de cinco a
sete não formam sequência estritamente crescente. A distribuição exata preserva a cauda.

**Estabilidade entre anos:** não avaliada para cada contagem nesta fase.

**Interpretação:** existe associação descritiva entre a contagem de veículos e gravidade, sem
supor forma linear.

**O que NÃO podemos concluir:** a contagem não demonstra causalidade e não está aprovada como
feature; valores máximos não foram classificados automaticamente como erros.

**Limitações:** `veiculos` integra a dinâmica da ocorrência e pode não estar disponível no
momento relevante para uma previsão futura; valores raros têm taxas instáveis.

**Figura:** `../reports/figures/phase_2e_vehicle_distribution.png`.

**Tabela:** `../reports/tables/phase_2e_vehicle_distribution.csv`,
`../reports/tables/phase_2e_vehicle_summary_statistics.csv` e
`../reports/tables/phase_2e_vehicle_severe_rate_n500.csv`.

**Código/origem:** `src/tcc_prf_severity/analysis/occurrence_dynamics.py`, dataset interim
verificado de 2021–2025.

**Possível uso no TCC:** caracterização da dinâmica e alerta de disponibilidade/leakage.

**Status:** confirmado.

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
