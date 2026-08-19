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

**O que NÃO podemos concluir:** maior volume mensal não significa maior risco de acidente ou
efeito causal do mês.

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

**O que NÃO podemos concluir:** o resultado não mostra que o fim de semana causa gravidade ou
que trafegar nesses dias tenha maior risco individual.

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

**O que NÃO podemos concluir:** nenhuma hora pode ser descrita como mais perigosa; as taxas
são condicionadas às ocorrências registradas e não ao total de veículos circulando.

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
