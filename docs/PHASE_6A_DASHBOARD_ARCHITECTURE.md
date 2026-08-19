# Fase 6A — Arquitetura do Dashboard

## 1. Objetivo

A Fase 6A congela a arquitetura e os contratos lógicos do futuro dashboard web estático do
TCC antes de qualquer implementação. Ela define localização, fluxo de dados, rotas, filtros,
assets, fronteiras científicas, acessibilidade, deploy e responsabilidades das Fases 6B–6E.

Esta fase é exclusivamente documental. Não cria a pasta `dashboard/`, não exporta JSON, não
instala dependências Node, não implementa frontend e não executa análise, inferência ou novo
cálculo científico.

## 2. Princípios científicos

O dashboard apresentará somente acidentes registrados pela Polícia Rodoviária Federal. Sua
métrica descritiva principal será a **proporção de ocorrências graves entre ocorrências
registradas**, calculada a partir das contagens de graves e total. Ela não representa risco de
acidente, probabilidade de o acidente ocorrer ou probabilidade de uma pessoa sofrer acidente.
Sem denominador de exposição, também não autoriza classificar rodovia, UF, BR, horário ou
condição como “mais perigosa”.

O componente reutilizável de cautela científica a ser criado futuramente deverá apresentar,
quando pertinente, o seguinte texto-base:

> Os percentuais representam a proporção de ocorrências graves entre acidentes registrados
> pela PRF. Sem denominador de exposição ao tráfego, esses valores não representam risco de
> ocorrência de acidente.

O dashboard distinguirá associação descritiva, desempenho preditivo e contribuição para as
predições do modelo. Nenhuma visualização transforma associação em causalidade, resultado
exploratório em resultado formal ou contribuição Tree SHAP em efeito causal.

## 3. Arquitetura geral

A aplicação ficará futuramente em `dashboard/`, na raiz do repositório. A arquitetura alvo é
um site estático em Next.js, React e TypeScript, sem backend de produção, banco de dados, API
de inferência, Python em runtime ou modelo de machine learning em produção.

O navegador consumirá exclusivamente JSONs versionados e auditados. Parquets, modelos,
pickles, predições individuais e ambiente científico não integrarão o build nem o runtime do
site. A hospedagem principal planejada é a Vercel, mantendo compatibilidade com qualquer
serviço capaz de publicar conteúdo estático.

## 4. Estrutura futura do repositório

A estrutura planejada é:

```text
tcc-prf-severity/
├─ data/
├─ artifacts/
├─ docs/
├─ reports/
├─ scripts/
├─ src/
├─ tests/
├─ dashboard/
│  ├─ src/
│  │  ├─ app/
│  │  ├─ components/
│  │  │  ├─ charts/
│  │  │  ├─ filters/
│  │  │  ├─ layout/
│  │  │  └─ ui/
│  │  ├─ lib/
│  │  │  ├─ data/
│  │  │  ├─ formatting/
│  │  │  └─ constants/
│  │  └─ types/
│  ├─ public/
│  │  └─ data/
│  ├─ package.json
│  ├─ tsconfig.json
│  └─ next.config.*
└─ README.md
```

A futura Fase 6B criará apenas os caminhos necessários à exportação versionada dos dados. A
estrutura da aplicação será materializada na Fase 6C. O contrato completo de caminhos está em
`reports/tables/phase_6a_repository_layout.csv`; nenhum deles foi criado na Fase 6A.

## 5. Stack planejada

A stack congelada conceitualmente é:

- Next.js com App Router;
- React;
- TypeScript;
- geração/exportação estática;
- execução do frontend no navegador;
- Vercel como destino primário planejado.

Versões, gerenciador de pacotes e bibliotecas auxiliares serão verificados na implementação.
Nenhuma versão ou dependência é fixada nesta fase. O site não terá backend, banco em runtime,
API de inferência, Python em runtime ou modelo implantado.

## 6. Fluxo Python → JSON → Next.js

O fluxo obrigatório será:

```text
artefatos científicos congelados
        ↓
Python + Polars
        ↓
exportação determinística e auditada
        ↓
dashboard/public/data/*.json
        ↓
Next.js / React
        ↓
visualização no navegador
```

A Fase 6B deverá criar `scripts/export_dashboard_data.py`, com lógica reutilizável em
`src/tcc_prf_severity/dashboard/`, e testes em `tests/test_dashboard_export.py`. Esse pipeline
será o único responsável por transformar fontes científicas em JSON. O frontend não abrirá
Parquet ou SQLite, não carregará modelo, não executará Python, SHAP ou inferência e não
recalculará AP, ROC-AUC, Brier, calibração, limiar ou matriz de confusão.

Os JSONs ficarão em `dashboard/public/data/` e serão versionados. Assim, build e deploy não
dependerão de Python, `uv`, Parquets, modelos ou acesso ao ambiente científico.

## 7. Contrato dos dados

### 7.1 Versão e forma lógica

A versão inicial do schema dos dados do dashboard é a string `"1"`. Cada JSON terá contrato
explícito e, quando adequado, os blocos `metadata`, `filters` e `data`. Assets simples podem
adotar forma menor, desde que seus campos sejam documentados e o manifesto permaneça como
ponto comum de proveniência.

Números serão armazenados como números. Percentuais científicos não serão serializados como
strings formatadas, como `"28,27%"`; serão frações numéricas ou percentuais numéricos com
unidade documentada. A apresentação pt-BR pertence ao frontend. Anos serão inteiros e datas,
quando necessárias, strings ISO previsíveis.

Campos JSON, IDs e nomes de arquivos usarão inglês técnico em `snake_case`, sem acentos. As
rotas e todos os textos visíveis ao usuário serão em português brasileiro. Essa convenção
evita misturar padrões arbitrariamente.

### 7.2 Manifesto

O arquivo comum será `dashboard/public/data/manifest.json`, com no mínimo:

- `schema_version`;
- `generated_at`;
- `data_period`;
- `source_scope`;
- `target_definition`;
- `assets`.

Cada item de `assets` registrará `asset_id`, `path`, `purpose`, `source_artifacts`,
`row_count`, `sha256` e `generation_status`. A Fase 6B definirá o formato determinístico de
`generated_at`, validará todos os hashes e rejeitará asset sem fonte ou status válido.

### 7.3 Granularidade e tamanho

É proibido publicar uma linha por ocorrência ou arquivos equivalentes a `all_accidents.json`,
`raw_dataset.json` ou `occurrences.json`. Somente agregações necessárias à interface,
resultados científicos congelados e metadados serão exportados.

O pipeline não produzirá o produto cartesiano de todas as dimensões. Serão usadas agregações
específicas por página e, em `/exploracao`, por escopo de seção. A Fase 6B medirá tamanho e contagem de linhas de cada asset; se um
arquivo for excessivo, poderá dividi-lo por finalidade ou ano, ou reduzir dimensões. Nunca
recorrerá ao dataset linha a linha no navegador.

### 7.4 Assets lógicos

Os IDs lógicos congelados são `META`, `OVERVIEW`, `EXPLORATION`, `GEOGRAPHY`,
`MODEL_COMPARISON`, `TEMPORAL_VALIDATION`, `FINAL_2025`, `CALIBRATION_2025`,
`THRESHOLD_2025`, `INTERPRETATION`, `METHODOLOGY_DESIGN` e `METHODOLOGY_FEATURES`.

Um ID lógico não implica um único arquivo. `EXPLORATION` permanece um único asset lógico, mas
poderá ser materializado em `dashboard/public/data/exploration/temporal.json` e
`dashboard/public/data/exploration/contextual.json`, desde que o manifesto e o contrato
lógico permaneçam íntegros. O primeiro arquivo admitirá apenas `source_year`, `dia_semana` e
`hour`; o segundo, apenas `source_year`, `tipo_pista`, `condicao_metereologica` e `uso_solo`.
Os caminhos futuros incluem `meta.json` e os diretórios
`overview/`, `exploration/`, `geography/`, `models/`, `validation/`, `threshold/`,
`interpretation/` e `methodology/` sob `dashboard/public/data/`.

## 8. Dados congelados vs agregações exploratórias

### 8.1 FROZEN_RESULT

`FROZEN_RESULT` representa resultados científicos já aprovados: comparação de modelos,
validação temporal, avaliação final de 2025, matriz de confusão, calibração, Tree SHAP e
desenho metodológico. Esses dados serão copiados ou estruturados a partir das tabelas e
figuras científicas publicadas, sem carregar predições para reconstruir métricas. O frontend
somente apresenta, filtra a apresentação quando expressamente permitido e formata valores; não
recalcula o experimento.

As fontes de verdade incluem `reports/tables/tcc/`, `reports/tables/phase_4d_*`,
`reports/tables/phase_4f_*`, `reports/tables/phase_4h_*`, `reports/tables/phase_4i_*` e
`reports/figures/tcc/`.

### 8.2 EXPLORATORY_AGGREGATE

`EXPLORATORY_AGGREGATE` representa agregações descritivas geradas na Fase 6B a partir do
dataset analítico congelado da Fase 3C. Elas podem conter apenas:

- contagem de ocorrências;
- contagem de graves;
- contagem de não graves;
- proporção de graves entre ocorrências registradas.

Não podem conter p-values, intervalos de confiança, testes, correlações novas, rankings
científicos, causalidade ou novas métricas de ML. Esses dados serão identificados na interface
como exploratórios. Sua presença no dashboard não os transforma em resultados formais do TCC;
qualquer conclusão científica nova exigirá análise e revisão separadas.

## 9. Rotas

As únicas rotas planejadas nesta fase são:

| Rota | Página | Status científico | Filtros exploratórios |
|---|---|---|---|
| `/` | Visão Geral | `MIXED` | ano |
| `/exploracao` | Exploração | `EXPLORATORY` | temporal: ano, dia da semana e hora; contextual: ano, pista, meteorologia e uso do solo |
| `/geografia` | Geografia | `EXPLORATORY` | ano, UF e BR |
| `/modelos` | Modelos | `FROZEN_RESULT` | nenhum |
| `/validacao-temporal` | Validação Temporal | `FROZEN_RESULT` | nenhum |
| `/limiar` | Limiar de Decisão | `FROZEN_RESULT` | nenhum |
| `/interpretacao` | Interpretação | `FROZEN_RESULT` | nenhum |
| `/metodologia` | Metodologia | `DOCUMENTATION` | nenhum |

Não serão acrescentadas outras páginas sem revisão do contrato. A matriz detalhada de rotas,
fontes e caveats está em `reports/tables/phase_6a_route_matrix.csv`.

## 10. Filtros

Filtros pertencem às páginas exploratórias; não haverá estado global capaz de alterar todas
as rotas. A Visão Geral terá apenas ano. Em `/exploracao`, os controles serão locais à seção
e separados em dois escopos independentes:

- **TEMPORAL:** `YEAR`, `WEEKDAY` e `HOUR`;
- **CONTEXTUAL:** `YEAR`, `ROAD_TYPE`, `WEATHER` e `LAND_USE`.

Os filtros não atravessam esses escopos: `HOUR` não recorta a seção contextual;
`ROAD_TYPE` e `WEATHER` não recortam a seção temporal; `WEEKDAY` não recorta a seção
contextual. Portanto, os seis filtros de Exploração não formam um estado combinável em toda a
página nem autorizam um cubo de seis dimensões. `YEAR` existe nos dois escopos, mas cada
controle de ano afeta somente a seção correspondente.

Geografia terá ano, UF e BR combináveis, preservando a dependência UF→BR. Os campos físicos
confirmados no schema 3C são `source_year`, `dia_semana`, `hour`, `tipo_pista`,
`condicao_metereologica`, `uso_solo`, `uf` e `br`.

UF poderá restringir as opções de BR. Essa dependência é comportamento de interface; as
opções virão dos JSONs produzidos pelo Python. A seleção padrão será “todos”, seleção múltipla
será permitida apenas quando documentada no contrato e uma seleção vazia não significará zero
registros: retornará ao padrão ou será rejeitada pela interface.

O frontend poderá filtrar linhas já agregadas, somar contagens aditivas quando o asset declarar
essa operação e a agregação for compatível com o escopo da seção, formatar valores e ordenar para apresentação. Somente em páginas
`EXPLORATORY_AGGREGATE` poderá recomputar `graves / total` após um filtro, usando exclusivamente
as contagens exportadas pelo Python. Essa exceção não se aplica a métricas científicas.

As páginas `/modelos`, `/validacao-temporal`, `/limiar`, `/interpretacao` e `/metodologia` não
reagirão a ano, UF, BR, meteorologia, pista, hora ou qualquer filtro populacional.

## 11. Contrato por página

### Visão Geral (`/`)

Página `MIXED`, de resumo e exploração limitada. Apresentará total de ocorrências, graves, não
graves, proporção grave, período, visão temporal, destaques descritivos e navegação. Apenas os
cards e séries explicitamente exploratórios poderão reagir ao filtro de ano; resultados de ML
permanecerão congelados. O caveat de exposição será obrigatório.

### Exploração (`/exploracao`)

Página `EXPLORATORY` para associações descritivas entre ocorrências registradas. Usará apenas
as dimensões aprovadas no contrato de filtros, em seções temporal e contextual independentes.
Nenhum controle de uma seção recortará a outra. `tipo_acidente` e `causa_acidente` não serão
filtros nem variáveis principais; poderão ser discutidos futuramente apenas como conteúdo
descritivo secundário após decisão explícita. O caveat de exposição será obrigatório.

### Geografia (`/geografia`)

Página `EXPLORATORY` para contagens e proporção grave por UF e BR, com tabelas e barras e
filtros de ano, UF e BR. Mapa coroplético de gravidade é proibido por padrão, pois pode ser
interpretado como mapa de perigo. Qualquer mapa futuro exigirá revisão científica específica.
O caveat de exposição será obrigatório.

### Modelos (`/modelos`)

Página `FROZEN_RESULT`, sem filtros exploratórios. Apresentará Regressão Logística, Random
Forest e XGBoost, AP média, pequenas diferenças, seleção do XGBoost, avaliação final de 2025 e
calibração como diagnóstico complementar. As fontes principais serão F4, T2, F7 e tabelas
científicas correspondentes. Nenhuma métrica será recalculada no navegador.

### Validação Temporal (`/validacao-temporal`)

Página `FROZEN_RESULT`, sem filtros. Apresentará os folds com janela expansiva, AP por modelo e
fold, comportamento temporal e comparação com 2025. Preservará a cautela de que período de
treinamento e ano de validação mudam simultaneamente. `validation_year` é dimensão dos
resultados publicados, não filtro populacional: selecionar ou exibir um fold será apenas uma
operação de apresentação e não recalculará performance. O filtro `YEAR` permanece negado
nessa rota. As fontes serão F5, T2 e os contratos/resultados 3D, 4D e 4H.

### Limiar de Decisão (`/limiar`)

Página `FROZEN_RESULT`, sem filtros. Apresentará o limiar 0,237232, matriz de confusão,
precisão positiva, sensibilidade, F1, falsos positivos, falsos negativos e interpretação do
ponto de operação. Não haverá slider nem recálculo da matriz. As fontes serão F6 e as tabelas
das Fases 4F e 4H.

### Interpretação (`/interpretacao`)

Página `FROZEN_RESULT`, sem filtros populacionais. Apresentará F8, contribuições agregadas,
Tree SHAP em margem, cardinalidade, codificação one-hot e fronteira não causal. Uma futura
alternância de apresentação entre variável de origem e top features transformadas já
publicadas em A1 poderá ser aceita, desde que apenas selecione resultados congelados.

### Metodologia (`/metodologia`)

Página `DOCUMENTATION`, sem filtros. Resumirá definição do desfecho, período, população, M1,
M2, separação temporal, conjunto preditivo, pré-processamento, política de leakage, seleção e
avaliação de 2025. Não reproduzirá necessariamente todo o capítulo metodológico.

## 12. Limites científicos

São proibidos em qualquer página: inferência de modelo, recomputação de AP, ROC-AUC, Brier,
SHAP ou matriz de confusão, seleção de novo limiar, novo teste estatístico e transformação de
proporção em risco. O slider de limiar é proibido. Páginas congeladas não recebem filtros
exploratórios.

O frontend não duplicará lógica científica em TypeScript. A única derivação numérica permitida
é a soma de contagens explicitamente aditivas e o cálculo de `graves / total` em páginas
exploratórias, a partir de contagens produzidas pelo exportador. Ordenação visual não poderá
ser apresentada como novo ranking científico.

A matriz completa de ações `ALLOW`, `LIMITED` e `DENY` está em
`reports/tables/phase_6a_scientific_boundary_matrix.csv`.

## 13. Acessibilidade e UX

A implementação deverá ser responsiva, funcionar em desktop e mobile e oferecer navegação por
teclado, foco visível e contraste adequado. Gráficos não dependerão somente de cor; tooltips
não serão a única forma de obter valores, e informações essenciais terão labels, descrições ou
tabelas acessíveis. Nenhuma animação será necessária para compreender os dados.

A identidade visual poderá ser moderna e própria, mantendo coerência conceitual com as figuras
5D. Cores de Regressão Logística, Random Forest e XGBoost serão consistentes; a linguagem será
neutra; não haverá 3D nem recursos que sugiram ranking de perigo ou distorçam escalas.

## 14. Estratégia de deploy

O destino primário planejado é a Vercel. O build será estático e consumirá JSONs já presentes
em `dashboard/public/data/`. O ambiente de deploy não instalará Python, não executará `uv`, não
acessará Parquets ou modelos e não regenerará dados científicos.

Na Fase 6E, o build estático será validado em ambiente limpo, incluindo rotas, caminhos de
assets, tamanho do bundle, cache, acessibilidade e responsividade. A arquitetura continuará
portável para outra hospedagem estática. Segredos, banco e funções serverless não fazem parte
do contrato atual.

## 15. Responsabilidades 6B–6E

- **6A — Arquitetura e contratos:** congela este documento e as matrizes de planejamento.
- **6B — Exportação:** implementa o pipeline Python/Polars, JSONs, manifesto, hashes e testes.
- **6C — Infraestrutura web:** cria a aplicação Next.js, layout, navegação, leitura de JSON e
  estado local de filtros exploratórios.
- **6D — Integração científica:** implementa visualizações e páginas conforme fontes e
  fronteiras congeladas.
- **6E — Fechamento web:** executa polimento visual, responsividade, acessibilidade,
  otimização, build estático e deploy.

Nenhuma responsabilidade das Fases 6B–6E foi antecipada na Fase 6A.

## 16. Riscos arquiteturais

| Risco | Mitigação congelada |
|---|---|
| JSON excessivamente grande | Medir assets na 6B, dividir por finalidade/ano ou reduzir dimensões. |
| Produto cartesiano de filtros | Criar agregações específicas por página e separar os escopos temporal e contextual de Exploração, nunca todas as combinações. |
| Mistura entre exploração e experimento | Separar tipos de asset, rotas e estados de filtro. |
| Proporção interpretada como risco | Exibir caveat de exposição nas páginas pertinentes. |
| Recálculo acidental no frontend | Negar métricas científicas e testar contratos de derivação. |
| Duplicação de lógica em TypeScript | Centralizar transformação científica no exportador Python. |
| Divergência entre JSON e fonte | Manifesto com fontes, hashes, contagens e schema versionado. |
| Filtro sem suporte na agregação | Exportar opções e combinações permitidas; falhar na validação 6B. |
| Deploy dependente de Python | Versionar JSONs e validar build apenas com o ambiente frontend. |
| Mudança futura de schema | Usar `schema_version`, validação explícita e migração deliberada. |

## 17. Decisões congeladas

As seguintes decisões têm status `FROZEN`:

- frontend futuro em `dashboard/`;
- Next.js, React e TypeScript com App Router;
- aplicação estática e Vercel como destino primário planejado;
- ausência de backend, banco em produção, Python e modelo em runtime;
- JSONs versionados em `dashboard/public/data/`;
- geração determinística por Python e Polars;
- manifesto e schema de dashboard versão `"1"`;
- nenhuma ocorrência individual no navegador;
- separação entre páginas exploratórias e resultados congelados;
- escopos temporal e contextual independentes em `/exploracao`, sem filtros combináveis entre seções;
- páginas de ML e metodologia sem filtros exploratórios;
- nenhum slider de limiar;
- nenhuma recomputação de métricas do experimento ou SHAP;
- geografia sem coroplético de gravidade por padrão;
- caveat de exposição obrigatório nas páginas pertinentes.

Alterar uma decisão congelada exigirá nova versão documental e revisão científica antes da
implementação correspondente.

## 18. Pontos que permanecem para implementação

A Fase 6B ainda deverá definir schemas físicos dos arquivos, particionamento real, limites de
tamanho, política determinística de timestamp, serialização, ordem de linhas, escrita atômica,
hashes e testes. A Fase 6C verificará versões e criará a infraestrutura frontend. As Fases 6D e
6E decidirão componentes visuais, detalhes de interação, acessibilidade aplicada, otimização e
deploy.

Também permanecem para revisão de implementação: permanência de F7 no dashboard, forma exata
da alternância de interpretação já publicada, breakpoints, biblioteca de gráficos, estratégia
de cache e configuração final da Vercel. Nenhum desses pontos autoriza criar nova evidência
científica ou alterar os resultados congelados.
