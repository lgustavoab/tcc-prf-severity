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
2. Caracterizar temporal e geograficamente as ocorrências. **Ainda não executado.**
3. Investigar fatores associados à gravidade. **Ainda não executado.**
4. Definir operacionalmente uma variável-alvo de gravidade. **Concluído na Fase 1.**
5. Treinar e comparar modelos de classificação. **Ainda não executado.**
6. Avaliar os modelos com métricas adequadas ao problema. **Ainda não executado.**
7. Investigar quais variáveis mais influenciam os modelos. **Ainda não executado.**
8. Avaliar generalização temporal, reservando 2025 para teste final quando a modelagem for
   iniciada. **Estratégia planejada; ainda não executada.**

Nenhuma atividade de treinamento, comparação, avaliação ou interpretação de modelos foi
executada até o encerramento da Fase 1.

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

Nenhum achado EDA foi registrado. A Fase 2 ainda não foi iniciada. Registros detalhados devem
nascer em [EDA_FINDINGS.md](EDA_FINDINGS.md) e somente depois de revisão podem ser sintetizados
aqui com IDs `EDAxxx`.

## Hipóteses

Nenhuma hipótese analítica foi registrada até o momento. Hipóteses futuras devem ser
identificadas com IDs `Hxxx` e não podem ser apresentadas como resultados.

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

**Limitação:** variáveis como `causa_acidente` e `tipo_acidente` podem ser definidas ou
consolidadas após a ocorrência.

**Consequência:** são úteis para EDA, mas exigirão avaliação específica de disponibilidade
temporal e leakage antes de eventual uso em ML.

**Status:** ativa.

### L004 — Qualidade dos registros

**Limitação:** existem categorias como `Ignorado` e `Não Informado`, além das inconsistências
conhecidas na decomposição de `pessoas`.

**Consequência:** categorias ausentes ou desconhecidas e inconsistências preservadas devem ser
explicitamente quantificadas e consideradas nas análises.

**Status:** ativa.

## Figuras e tabelas associadas

Nenhuma figura ou tabela científica foi produzida. Artefatos futuros devem ser armazenados em
`reports/figures/` e `reports/tables/` e referenciados pelo ID do registro correspondente.

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
