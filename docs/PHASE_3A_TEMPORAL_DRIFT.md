# Fase 3A — Auditoria temporal e drift das features

## Objetivo e escopo

A Fase 3A auditou descritivamente as distribuições das 22 variáveis marcadas com
`requires_temporal_drift_check = true` na matriz de elegibilidade da Fase 2F. A comparação
principal contrapõe o desenvolvimento planejado, 2021–2024, ao holdout temporal planejado,
2025. Esse recorte é apenas analítico: nenhum split, dataset processed, `X`/`y`, encoding,
seleção definitiva de features ou modelo foi criado.

A população continua sendo a de 342.624 ocorrências registradas pela PRF. O
`target_grave` aparece apenas como contexto: sua proporção anual foi relativamente estável na
Fase 2, mas ele não foi tratado como feature nem usado nos cálculos de drift.

## Metodologia

### Distribuições categóricas e discretas

Para categorias mutuamente exclusivas foi calculada a Total Variation Distance (TVD):

`TVD = 0,5 × Σ |p_dev - p_2025|`

A TVD varia de zero, para distribuições iguais, a um, para suportes totalmente disjuntos. Os
valores são apresentados como magnitudes e rankings descritivos; não foram criados thresholds
universais ou rótulos automáticos de estabilidade. Também foram calculados cardinalidade,
categorias compartilhadas, novas e ausentes, participação de categorias não vistas e maior
mudança absoluta de participação.

`br` foi tratada como identificador categórico e `hour` como variável discreta 0–23. Os
valores de `pessoas` e `veiculos` foram preservados exatamente, incluindo suas caudas. Strings
de `tipo_acidente`, `causa_acidente` e `tracado_via` não foram harmonizadas.

### Variáveis contínuas

Para `km`, `latitude` e `longitude`, os decis foram definidos exclusivamente com 2021–2024.
As mesmas fronteiras foram aplicadas a 2025, com intervalos externos capazes de receber
valores abaixo ou acima dos limites internos. Quantis repetidos são reduzidos
deterministicamente. Não houve imputação, remoção de outliers ou winsorização.

### Data, horário e traçado multivalorado

- `data_inversa`: `calendar_coverage`, com parseabilidade, datas mínima/máxima, cobertura
  mensal e consistência de `month_name`. Datas completas não receberam TVD.
- `horario`: `derived_hour_proxy`, com parseabilidade, faixa e consistência de `hour`; o drift
  principal foi calculado sobre `hour`.
- `tracado_via`: TVD das combinações originais de alta cardinalidade.
- `tracado_via_components`: diferenças de prevalência multilabel. Cada componente contou no
  máximo uma vez por ocorrência e não recebeu TVD de distribuição exclusiva.

## Resultados categóricos — 2021–2024 versus 2025

| Posição | Variável | TVD | Categorias dev/2025 | Novas/ausentes em 2025 | Maior mudança |
|---:|---|---:|---:|---:|---|
| 1 | municipio | 0,089805 | 2.001 / 1.844 | 49 / 206 | RIO DE JANEIRO: +0,2171 p.p. |
| 2 | tracado_via | 0,082051 | 1.046 / 605 | 168 / 609 | Reta: −2,3295 p.p. |
| 3 | causa_acidente | 0,079368 | 76 / 69 | 0 / 7 | Ausência de reação do condutor: +3,5355 p.p. |
| 4 | tipo_acidente | 0,032081 | 18 / 17 | 0 / 1 | Saída de leito carroçável: −1,5428 p.p. |
| 5 | br | 0,030241 | 125 / 115 | 1 / 11 | BR 101: +0,7803 p.p. |
| 6 | uf | 0,029849 | 27 / 27 | 0 / 0 | RJ: +0,9984 p.p. |
| 7 | condicao_metereologica | 0,019615 | 10 / 9 | 0 / 1 | Céu Claro: +1,8740 p.p. |
| 8 | dia_semana | 0,013845 | 7 / 7 | 0 / 0 | domingo: −0,7754 p.p. |
| 9 | veiculos | 0,013573 | 27 / 21 | 3 / 9 | 1 veículo: −1,1815 p.p. |
| 10 | tipo_pista | 0,011554 | 3 / 3 | 0 / 0 | Simples: −1,1554 p.p. |
| 11 | fase_dia | 0,011510 | 4 / 4 | 0 / 0 | Pleno dia: +1,1510 p.p. |
| 12 | hour | 0,010779 | 24 / 24 | 0 / 0 | 7h: +0,2454 p.p. |
| 13 | month_name | 0,010448 | 12 / 12 | 0 / 0 | Novembro: +0,3954 p.p. |
| 14 | pessoas | 0,009196 | 72 / 66 | 3 / 9 | 1 pessoa: −0,6631 p.p. |
| 15 | uso_solo | 0,005919 | 2 / 2 | 0 / 0 | Sim: −0,5919 p.p. |
| 16 | sentido_via | 0,002277 | 3 / 3 | 0 / 0 | Decrescente: +0,2277 p.p. |

`Ignorado`, `Não Informado` e `br = 0` foram preservados. Esses valores continuam sendo
interpretados também como aspectos de qualidade, e não como categorias substantivas
automaticamente equivalentes às demais.

## Variáveis contínuas

| Variável | TVD em bins | Mediana dev | Mediana 2025 | P95 dev | P95 2025 |
|---|---:|---:|---:|---:|---:|
| longitude | 0,019970 | −47,5794 | −46,8593 | −35,6095 | −35,3609 |
| latitude | 0,018407 | −20,4687 | −20,3636 | −5,0625 | −5,0809 |
| km | 0,011486 | 193,0 | 192,5 | 711,0 | 712,0 |

Cada variável contínua teve 270.095 observações no desenvolvimento e 72.529 em 2025. Os
resultados descrevem mudança de cobertura/distribuição geográfica; não constituem medida de
distância física nem justificam exclusão automática.

## Categorias não vistas em 2021–2024

Cinco variáveis apresentaram valores de 2025 ausentes no desenvolvimento:

| Variável | Categorias novas | Ocorrências em 2025 | Participação em 2025 |
|---|---:|---:|---:|
| tracado_via | 168 | 198 | 0,272994% |
| municipio | 49 | 71 | 0,097892% |
| pessoas | 3 | 5 | 0,006894% |
| veiculos | 3 | 3 | 0,004136% |
| br | 1 | 1 | 0,001379% |

A BR nova foi `431`; os valores novos foram 69, 71 e 76 para `pessoas`, e 21, 31 e 82 para
`veiculos`. A lista integral, preservando todos os rótulos, está na tabela de categorias
unseen. Categoria nova não foi tratada automaticamente como erro.

## Taxonomia de tipo e causa

`tipo_acidente` teve TVD 0,032081, 18 categorias no desenvolvimento, 17 em 2025, nenhuma
categoria nova e uma ausente (`Colisão lateral`). A maior mudança foi a redução de 1,5428 p.p.
em `Saída de leito carroçável`.

`causa_acidente` teve TVD 0,079368, 76 categorias no desenvolvimento, 69 em 2025, nenhuma
categoria nova e sete ausentes. A maior mudança foi o aumento de 3,5355 p.p. em `Ausência de
reação do condutor`, de 12,2775% para 15,8130%. A cardinalidade anual já variava antes de 2025:
71, 71, 75, 69 e 69 categorias entre 2021 e 2025. Isso reforça o alerta taxonômico sem
harmonizar redações ou capitalização.

## Traçado da via

As strings brutas de `tracado_via` apresentaram TVD 0,082051. Havia 1.046 combinações no
desenvolvimento e 605 em 2025: 168 novas, 609 ausentes e 0,272994% dos registros de 2025 em
combinações não vistas. Esse resultado reflete tanto mudança temporal quanto a natureza
combinatória e a ordem das strings originais.

Na representação multilabel, todos os 12 componentes apareceram nos cinco anos. A maior
mudança foi `Reta`, de 69,9217% para 73,0935% das ocorrências (+3,1718 p.p.), seguida de
`Declive` (+1,7183 p.p.) e `Aclive` (+1,3062 p.p.). Não foi calculada TVD exclusiva para essas
prevalências.

## Pessoas e veículos

`pessoas` apresentou TVD exata 0,009196. Mediana, P75, P90, P95 e P99 permaneceram em 2, 3,
4, 5 e 8; o máximo mudou de 95 no desenvolvimento para 76 em 2025. `veiculos` apresentou TVD
0,013573; mediana, P75, P90, P95 e P99 permaneceram em 2, 2, 3, 4 e 6, e o máximo mudou de 131
para 82. Esses campos continuam exigindo decisão de disponibilidade e representação; a
auditoria não usa sua associação com o target para promovê-los.

## Cobertura anual

Todos os 342.624 valores de `data_inversa` e `horario` foram parseáveis e coerentes com as
derivações em memória. Cada ano cobriu os 12 meses e 365 datas distintas, ou 366 em 2024. A
cardinalidade de horários exatos foi 1.302, 1.388, 1.406, 1.415 e 1.412 entre 2021 e 2025; por
isso `hour`, e não as strings exatas, permanece como proxy distributivo apropriado.

As tabelas anuais mostram que algumas mudanças antecedem 2025. Por exemplo, a cardinalidade
bruta de `tracado_via` passou de 390 em 2021 para 440, 584 e 659 antes de chegar a 605 em 2025.
A mudança observada no holdout não deve ser interpretada isoladamente como ruptura súbita.

## Implicações para a Fase 3B

- preparar política explícita para categorias desconhecidas sem aprender vocabulário em 2025;
- decidir representação de município e demais variáveis geográficas de alta granularidade;
- escolher entre `tracado_via` bruto, componentes ou representação controlada, evitando
  redundância;
- resolver os pares `data_inversa`/`month_name` e `horario`/`hour`;
- avaliar disponibilidade preditiva de tipo, causa, pessoas e veículos antes de incluí-los;
- preservar bins, vocabulários e transformações aprendidos somente no desenvolvimento;
- monitorar as magnitudes observadas sem converter TVD em rótulos arbitrários.

## Situação de H001

A auditoria oferece apoio descritivo ao princípio de H001: a baixa variação anual de
`target_grave` não implicou distribuições idênticas das features. Foram observadas mudanças de
magnitude, cardinalidade e suporte, especialmente em município, traçado e causa. H001 não foi
“provada” nem aceita por teste estatístico; não houve teste inferencial ou p-value.

## Limitações

A TVD resume magnitude, mas não causalidade, relevância preditiva ou efeito sobre uma métrica
de modelo. Categorias raras podem elevar cardinalidade com pouca participação. Ausência em
2025 não significa remoção permanente da taxonomia. A análise continua condicionada às
ocorrências registradas pela PRF e não mede risco de acidente ou exposição rodoviária.

## Reprodução

```powershell
uv run prf-verify-interim
uv run prf-audit-temporal-drift
```

As sete tabelas estão em `reports/tables/` e as três figuras em `reports/figures/`.
