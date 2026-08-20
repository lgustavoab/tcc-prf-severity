# Fase 6E.1 — Polimento final e QA de produção do dashboard

## Objetivo

Preparar o dashboard científico estático para apresentação final e para uma futura publicação,
sem alterar arquitetura, dados, resultados, experimentos ou conclusões. Esta etapa realizou
somente auditoria de interface, correções localizadas e validação de produção. Nenhum deploy foi
executado.

## Escopo preservado

As nove rotas permanecem: `/`, `/visao-geral`, `/exploracao`, `/geografia`, `/modelos`,
`/validacao-temporal`, `/limiar`, `/interpretacao` e `/metodologia`. O dashboard continua usando
Next.js App Router com `output: "export"`, sem backend, banco, inferência ou treinamento em
produção. A fronteira científica também foi preservada: as proporções descrevem ocorrências
graves entre acidentes registrados pela PRF e não representam risco absoluto, exposição ao
tráfego ou causalidade.

## Acessibilidade e teclado

A auditoria confirmou um `h1` e um landmark `main` por rota, idioma `pt-BR`, skip link,
navegação principal nomeada, labels associados aos controles, estados de loading e erro,
foco global visível, controles nativos e ausência de `tabindex` positivo. O salto de hierarquia
`h1` para `h3` no primeiro gráfico de `/modelos` foi corrigido: o card agora aceita `h2` ou
`h3` conforme seu nível no documento, sem mudar sua aparência ou seus dados.

Os filtros continuam baseados em `select`, `fieldset`, `legend`, `details`, `summary`, labels e
checkboxes nativos. Selects, summaries, opções clicáveis e o botão `Limpar seleção` passaram a
ter área mínima de 44 px. Os cinco aprofundamentos da Home permanecem em `details/summary`
nativo, funcionam por teclado e mantêm as ressalvas científicas sempre visíveis.

Os contrastes principais verificados foram: texto/fundo 14,99:1, texto secundário/branco
5,61:1, link de navegação/sidebar 10,16:1, accent/branco 6,13:1 e foco/branco 5,86:1. Gráficos
não dependem apenas de cor: títulos, descrições, tooltips, notas, tabelas ou equivalentes
textuais preservam o significado publicado.

## Responsividade e navegação mobile

As nove rotas foram verificadas estruturalmente em 390, 768 e 1280 px, totalizando 27
combinações. Não houve overflow global, gráfico fora do viewport, ID duplicado ou tabela fora
de seu contêiner rolável. Em 390 px, os cinco `details` da Home foram abertos simultaneamente
sem gerar overflow. Houve também inspeção visual representativa da Home, dos filtros, dos
modelos e da matriz de confusão nas três larguras.

A navegação horizontal em telas abaixo de 1024 px foi mantida. O refinamento adiciona scrollbar
fina de alto contraste e um fade discreto à direita para comunicar que há mais itens, sem
hamburger, drawer ou JavaScript adicional. Cards, glossário, CTAs, filtros, gráficos e tabelas
continuam adaptando-se aos breakpoints existentes.

## Gráficos, tabelas e estados

Os gráficos mantêm biblioteca, séries, cores, escalas, valores e interpretação. Todos os cards
possuem título e descrição; Recharts mantém a camada de acessibilidade; valores relevantes são
repetidos em tabelas, chips, notas ou texto. As tabelas conservam cabeçalhos e rolagem horizontal
interna. `LoadingState` usa status anunciado de forma polida e `ErrorState` usa alerta com
mensagem explícita; não foi necessário criar novo sistema de tratamento de erros.

## Performance

O build de produção gerou como maior chunk JavaScript 381.019 bytes, coerente com o histórico
de aproximadamente 380 KB da Fase 6D. As rotas com gráficos referenciam até 1.013.151 bytes de
JavaScript não comprimido somando seus chunks; o total de JavaScript emitido foi 1.168.891
bytes e o CSS, 17.178 bytes. A maior parte do custo está associada ao Next.js, React e Recharts.
Para um dashboard acadêmico estático de nove rotas, o resultado foi mantido: lazy loading em
massa, troca de biblioteca ou refatoração ampla teriam risco desproporcional nesta fase.

## Metadata e favicon

O metadata básico usa o título `Gravidade de Acidentes em Rodovias Federais | TCC` e uma
descrição fiel à análise descritiva e à avaliação de modelos, sem keywords, tracking, analytics
ou SEO elaborado. Não existe favicon customizado; o comportamento padrão foi mantido para não
introduzir um asset visual sem revisão nem uma dependência desnecessária.

## Produção estática e preservação científica

O build exportou as nove rotas esperadas. O verificador encontrou nove rotas e cinco assets
essenciais. Os 15 JSONs versionados em `dashboard/public/data` foram hasheados antes e depois e
permaneceram bitwise idênticos. Não houve alteração em `src/`, `tests/`, scripts Python,
`pyproject.toml`, `uv.lock`, modelos, pipelines ou artefatos científicos.

## Validações

- `npm run lint`: PASS.
- `npm run typecheck`: PASS.
- `npm run build`: PASS, sem warning de produção.
- `npm run check:export`: PASS, nove rotas e cinco assets essenciais.
- `npm run check`: PASS.
- console das nove rotas: zero warnings e zero erros.
- `git diff --check`: PASS.

O relatório detalhado está em `reports/tables/phase_6e_final_qa.csv`.

## Pendências para a Fase 6E.2

A etapa seguinte pode tratar exclusivamente da revisão final do destino de hospedagem, base
path/URLs quando exigidos pelo provedor, política de cache e execução controlada do deploy.
Favicon customizado é opcional e só deve ser criado com uma decisão visual explícita. Analytics,
tracking, backend e inferência em produção permanecem fora do escopo.

## Fase 6E.2 — Deploy de produção

Em 19/08/2026, o dashboard foi publicado na Vercel no projeto `tcc-prf-severity`, com
`dashboard` como Root Directory, framework Next.js autodetectado e integração GitHub ligada à
branch de produção `main`. O deploy utilizou o commit
`379d455280a3bd74d500e7f53c847794158c73fb`, executou `npm run build` (`next build`) e foi
concluído com status `READY` sob o identificador
`dpl_484Z5z4UdnZ3paGEVrzG8HV4zfdF`.

URL pública aprovada: <https://tcc-prf-severity.vercel.app>.

As nove rotas foram acessadas diretamente em produção e renderizaram com `main` e `h1`; a
navegação interna e o refresh direto em `/modelos` também foram aprovados, sem 404. A inspeção
representativa em 390, 768 e 1280 px confirmou navegação horizontal mobile, ausência de
overflow global e apresentação funcional da Home, da Visão Geral, dos modelos, de tabela e de
gráficos maiores. A Home preservou título, resumo, definição operacional de acidente grave,
RQ1–RQ5, cinco aprofundamentos, ressalvas, resultados congelados, glossário, escopo e CTAs.

Os 15 JSONs em `dashboard/public/data/` responderam HTTP 200 com `application/json`; os 14
assets declarados coincidiram em tamanho e SHA-256 com o manifesto, que também foi servido na
materialização versionada. CSS e chunks JavaScript responderam HTTP 200 com MIME apropriado.
Não foram observados erros ou warnings no console, erros de runtime, falhas de hidratação ou
assets quebrados. Nenhum dado, código, dependência, variável de ambiente, backend, função,
banco, analytics, tracking ou domínio customizado foi adicionado.

A primeira tentativa, feita por upload local a partir de `dashboard/`, falhou antes do build
porque a Root Directory remota `dashboard` foi aplicada novamente ao diretório já recortado. Os
logs identificaram objetivamente a causa; a configuração correta foi preservada e o deploy
final foi disparado da fonte Git no commit acima, sem alteração de código ou tentativa aleatória.
