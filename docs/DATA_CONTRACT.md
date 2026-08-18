# Contrato de dados — Fase 1B

## Propósito e escopo

Este contrato define a interface bloqueante do dataset de ocorrências da Polícia Rodoviária
Federal (PRF) entre 2021 e 2025. Ele assegura que cada execução recebe a mesma estrutura,
tipos e invariantes antes de qualquer etapa analítica. Os CSVs em `data/raw/` são somente
leitura: nunca são corrigidos, sobrescritos ou enriquecidos.

Cada arquivo oficial agrupado por ocorrência fornece 30 colunas. A ingestão acrescenta
somente `source_year` e `target_grave`, totalizando 32 colunas. O schema Pandera usa
`strict=True`; colunas ausentes ou extras são inválidas.

Esta fase não remove registros, não imputa valores, não harmoniza taxonomias variáveis, não
expande campos multivalorados e não gera Parquet.

## Tipos internos e regras por coluna

| Coluna | Tipo Polars | Nula | Regra bloqueante |
|---|---|---:|---|
| `id` | `String` | não | identificador único no conjunto validado |
| `data_inversa` | `Date` | não | ano igual a `source_year` |
| `dia_semana` | `String` | não | categoria fechada e compatível com `data_inversa` |
| `horario` | `Time` | não | hora válida |
| `uf` | `String` | não | UF brasileira permitida |
| `br` | `Int64` | não | maior ou igual a 0 |
| `km` | `Float64` | não | maior ou igual a 0 |
| `municipio` | `String` | não | texto preservado |
| `causa_acidente` | `String` | não | texto preservado, sem lista fechada |
| `tipo_acidente` | `String` | não | texto preservado, sem lista fechada |
| `classificacao_acidente` | `String` | sim | categoria fechada quando preenchida |
| `fase_dia` | `String` | não | categoria fechada |
| `sentido_via` | `String` | não | categoria fechada |
| `condicao_metereologica` | `String` | não | categoria fechada |
| `tipo_pista` | `String` | não | categoria fechada |
| `tracado_via` | `String` | não | texto preservado, inclusive composições com `;` |
| `uso_solo` | `String` | não | `Não` ou `Sim` |
| `pessoas` | `Int64` | não | maior ou igual a 1 |
| `mortos` | `Int64` | não | maior ou igual a 0 |
| `feridos_leves` | `Int64` | não | maior ou igual a 0 |
| `feridos_graves` | `Int64` | não | maior ou igual a 0 |
| `ilesos` | `Int64` | não | maior ou igual a 0 |
| `ignorados` | `Int64` | não | maior ou igual a 0 |
| `feridos` | `Int64` | não | não negativo e igual a leves mais graves |
| `veiculos` | `Int64` | não | maior ou igual a 1 |
| `latitude` | `Float64` | não | entre -35 e 6, inclusive |
| `longitude` | `Float64` | não | entre -75 e -32, inclusive |
| `regional` | `String` | sim | texto preservado |
| `delegacia` | `String` | sim | texto preservado |
| `uop` | `String` | sim | texto preservado |
| `source_year` | `Int64` | não | entre 2021 e 2025, inclusive |
| `target_grave` | `Boolean` | não | regra oficial descrita abaixo |

## Categorias estáveis

- `uf`: AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR,
  RJ, RN, RO, RR, RS, SC, SE, SP e TO.
- `dia_semana`: domingo, segunda-feira, terça-feira, quarta-feira, quinta-feira,
  sexta-feira e sábado. O nome em português deve corresponder ao dia calendário de
  `data_inversa`.
- `fase_dia`: Amanhecer, Anoitecer, Plena Noite e Pleno dia.
- `sentido_via`: Crescente, Decrescente e Não Informado.
- `condicao_metereologica`: Chuva, Céu Claro, Garoa/Chuvisco, Granizo, Ignorado, Neve,
  Nevoeiro/Neblina, Nublado, Sol e Vento.
- `tipo_pista`: Dupla, Múltipla e Simples.
- `uso_solo`: Não e Sim.
- `classificacao_acidente`, quando preenchida: Sem Vítimas, Com Vítimas Feridas e Com
  Vítimas Fatais.

`Ignorado` e `Não Informado` são categorias oficiais com significado próprio. Elas não são
convertidas em nulo. Não há listas fechadas para `causa_acidente`, `tipo_acidente` e
`tracado_via`, porque suas taxonomias ou composições variam entre anos.

## Target oficial

```text
target_grave = (mortos > 0) OR (feridos_graves > 0)
```

`classificacao_acidente` não é usada para construir o target. Ela é uma classificação
administrativa da origem e pode estar nula; derivar a resposta das contagens físicas torna a
regra explícita, reproduzível e diretamente alinhada à definição de gravidade do projeto.

## Invariantes entre colunas

A validação completa aplica primeiro o schema Pandera e depois exige:

1. nenhum `id` duplicado;
2. `feridos == feridos_leves + feridos_graves`;
3. ano de `data_inversa` igual a `source_year`;
4. `target_grave` exatamente igual à regra oficial;
5. `dia_semana` em português compatível com `data_inversa`.

Não se exige `pessoas == mortos + feridos_leves + feridos_graves + ilesos + ignorados`.
Existem 18.538 divergências dessa decomposição nos dados oficiais atuais. Bloqueá-las
eliminaria observações válidas ou exigiria uma correção sem fundamento; por isso a quantidade
continua visível apenas na auditoria.

## Bloqueios versus auditoria

Validações bloqueantes impedem o uso de estruturas, domínios ou relações que contradizem o
contrato. Métricas de auditoria descrevem anomalias conhecidas sem alterar o dataset. Além da
divergência de `pessoas`, valores suspeitos porém admissíveis, como `br = 0` e `km = 0`, são
preservados e contados. Nenhuma métrica de auditoria autoriza mutação dos dados RAW.
