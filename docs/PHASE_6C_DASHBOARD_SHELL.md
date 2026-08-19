# Fase 6C — Fundação da aplicação web estática

## 1. Objetivo

A Fase 6C materializa a infraestrutura frontend definida na 6A e consome exclusivamente os
JSONs auditados da 6B. A entrega cria a aplicação Next.js, as oito rotas, o layout global, a
camada tipada de dados, os controles exploratórios e os estados de interface. Não implementa
os gráficos científicos finais, não carrega modelo ou predições e não recalcula métricas.

## 2. Ambiente e versões

O ambiente validado utiliza Node.js `22.19.0` e npm `10.9.3`. O Next.js `16.3.1` exige Node
`>=20.9.0`; portanto, o runtime é compatível. As dependências foram fixadas exatamente em:

- Next.js `16.3.1`;
- React e React DOM `19.2.8`;
- TypeScript `6.0.3`;
- ESLint `9.39.5`;
- eslint-config-next `16.3.1`;
- @types/node `26.2.0`, @types/react `19.2.18` e @types/react-dom `19.2.4`.

O registry apresentava TypeScript `7.0.2` e ESLint `10.8.1` como releases mais recentes, mas
o conjunto de lint do Next 16.3.1 ainda rejeitava TypeScript 7 e possuía plugins com peer
dependency até ESLint 9. Foram adotadas as releases estáveis mais recentes das linhas
compatíveis, sem beta, RC, canary ou override de qualidade.

## 3. Estrutura e static export

O scaffold foi criado manualmente dentro de `dashboard/`, preservando `public/data/`. A
aplicação usa App Router, TypeScript estrito, CSS nativo, metadata estática e
`output: "export"`. O build gera `dashboard/out/`, ignorado pelo Git. O script
`scripts/check-static-export.mjs` usa apenas a biblioteca padrão do Node para confirmar as oito
páginas exportadas e a presença de manifesto, metadados e assets essenciais.

Os scripts reproduzíveis são `npm run lint`, `npm run typecheck`, `npm run build`,
`npm run check:export` e `npm run check`. Não existem API routes, middleware, proxy, Server
Actions, backend, SSR, ISR ou runtime de inferência.

## 4. Rotas e layout

As oito rotas congeladas foram implementadas: `/`, `/exploracao`, `/geografia`, `/modelos`,
`/validacao-temporal`, `/limiar`, `/interpretacao` e `/metodologia`. A navegação é definida uma
vez em `NAV_ITEMS`, usa `next/link`, indica a página atual com `aria-current` e permanece
utilizável em telas menores. O layout contém identidade acadêmica, período 2021–2025, skip
link, área principal e rodapé.

Cada página usa um header reutilizável com título, descrição e status científico. Páginas
exploratórias exibem o caveat obrigatório sobre ausência de denominador de exposição. Os
resultados congelados não recebem filtros populacionais.

## 5. Arquitetura de componentes

Os componentes separam quatro responsabilidades:

- `layout`: navegação e estrutura compartilhada;
- `filters`: seleção anual e multisseleção acessível baseada em controles nativos;
- `feedback`: loading, error, empty e placeholder de visualização;
- `scientific`: headers, caveat e fundações específicas das páginas.

`VisualizationPlaceholder` identifica explicitamente o asset futuro sem desenhar gráfico
falso. CSS nativo fornece tokens, superfícies, cards, containers de tabela, foco visível e
breakpoints para desktop, tablet e mobile. Nenhuma biblioteca de UI, gráficos ou fontes
externas foi adicionada.

## 6. Camada de dados e tipos

Todos os caminhos ficam centralizados em `src/lib/data/paths.ts`. `fetchJson<T>()` verifica
`response.ok`, exige schema versão `"1"`, confere `asset_id` e `part_id` esperados e retorna o
payload sem transformação. `useDashboardAsset<T>()` controla loading, success, error e
cancelamento por `AbortController`.

`src/types/dashboard.ts` representa o manifesto e os 14 JSONs físicos descritos no manifesto:
metadata, overview, os dois escopos de exploração, geografia, comparação, validação temporal,
avaliação final, calibração, threshold, duas partes de interpretação e dois assets de
metodologia. Os campos seguem os schemas reais da 6B; a validação científica continua no
pipeline Python.

## 7. Filtros exploratórios

Na home, `YEAR` é estado local e seleciona a linha global ou anual já publicada. Em
`/exploracao`, TEMPORAL possui estado próprio para `YEAR`, `WEEKDAY` e `HOUR`, enquanto
CONTEXTUAL possui outro estado para `YEAR`, `ROAD_TYPE`, `WEATHER` e `LAND_USE`. Nenhum estado
atravessa os escopos, e a interface somente conta células agregadas selecionadas nesta fase.

Em `/geografia`, `YEAR`, `UF` e `BR` são locais. As opções de BR vêm diretamente de
`br_by_uf`; alterar UF limpa qualquer seleção anterior de BR. BR 0 permanece disponível. Não
foi criado mapa ou ranking.

## 8. Resultados congelados e metodologia

Modelos, validação temporal, limiar e interpretação carregam somente seus JSONs publicados.
O limiar não possui slider, a matriz não é recalculada e a alternância da interpretação apenas
seleciona entre as duas visões publicadas, preservando a ordem. `validation_year` aparece como
dimensão do resultado, nunca como filtro populacional. Metodologia carrega os contratos de
desenho, features e metadados sem reproduzir o dataset analítico.

## 9. Acessibilidade

A fundação inclui landmarks semânticos, skip link, hierarquia de headings, labels, fieldsets,
legends, checkboxes nativos, foco visível, `aria-current` e mensagens textuais de loading e
erro. Tabelas possuem containers responsivos, cards reorganizam-se e a navegação passa a faixa
horizontal em viewport estreita. Nenhuma informação essencial depende de tooltip, animação ou
cor isolada.

## 10. Validação e limites

Lint, TypeScript, build e check do static export foram aprovados. O export contém oito rotas,
cinco assets essenciais verificados, 80 arquivos e 1.549.432 bytes. O aceite Python foi
aprovado com 378 testes. A adaptação de compatibilidade substituiu as restrições transitórias
de branch e ausência de frontend por uma garantia byte a byte de que a exportação 6B preserva
arquivos frontend existentes fora de `dashboard/public/data`. Os JSONs 6B não foram modificados.

A Fase 6C não cria gráficos finais, inferência, AP, ROC-AUC, Brier, SHAP, nova matriz, novo
threshold, API, backend ou deploy. A Fase 6D integrará as visualizações científicas aos
placeholders e dados já tipados; a 6E permanece responsável pelo fechamento visual e deploy.
