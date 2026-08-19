# Fase 2 — Síntese da Análise Exploratória

## 1. Escopo e população analisada

A Fase 2 analisou 342.624 ocorrências registradas pela Polícia Rodoviária Federal entre 2021
e 2025. A unidade de análise é a ocorrência, e 96.857 registros (28,2692%) satisfazem a
definição operacional:

```text
target_grave = (mortos > 0) OR (feridos_graves > 0)
```

O estudo descreve a gravidade **condicional à existência de uma ocorrência registrada pela
PRF**. Ele não contém viagens sem acidente, fluxo de veículos ou veículo-quilômetro e,
portanto, não estima a probabilidade de um acidente ocorrer nem o risco absoluto de circular
em uma rodovia.

Esta síntese usa os achados documentados e as matrizes da Fase 2F. Não recalcula a EDA, não
harmoniza categorias e não cria dataset processed ou modelo.

## 2. Resultado global

A proporção anual de `target_grave` variou de 28,0608% a 28,4943%, amplitude de 0,4335 ponto
percentual. Isso caracteriza baixa amplitude **descritiva** da prevalência anual no período,
sem demonstrar estabilidade das distribuições das features.

A hipótese H001 permanece ativa: antes da modelagem temporal, cada variável deverá ser
avaliada quanto a mudanças de distribuição entre anos. A estabilidade do target não substitui
essa verificação.

## 3. Achados centrais

Os oito achados abaixo são prioridades editoriais da Fase 2F, não um ranking de perigo. As
taxas descrevem a composição das ocorrências registradas, sem controle multivariado ou
denominador de exposição.

### 3.1 Dinâmica da ocorrência

| Comparação | Taxa focal | Taxa de referência | Diferença | n focal | Consistência temporal | Limitação principal |
|---|---:|---:|---:|---:|---|---|
| Pedestre andava na pista vs Reação tardia ou ineficiente do condutor | 75,4139% | 23,9291% | 51,4847 p.p. | 3.262 | 5 anos; 74,2574%–77,7946%; amplitude 3,5371 p.p. | Causa registrada pode ser consolidada após a ocorrência e sua taxonomia variou. |
| Atropelamento de Pedestre vs Colisão traseira | 68,0206% | 23,6737% | 44,3469 p.p. | 15.313 | 5 anos; 67,1573%–68,7717%; amplitude 1,6144 p.p. | Tipo descreve a dinâmica e pode depender de conhecimento durante ou após a ocorrência. |
| Colisão frontal vs Colisão traseira | 63,0592% | 23,6737% | 39,3855 p.p. | 23.045 | 5 anos; 62,2785%–63,5335%; amplitude 1,2550 p.p. | Tipo não está automaticamente disponível no momento de uma previsão. |
| Transitar na contramão vs Reação tardia ou ineficiente do condutor | 60,2333% | 23,9291% | 36,3042 p.p. | 11.145 | 5 anos; 58,8663%–60,8291%; amplitude 1,9628 p.p. | A causa é uma classificação registrada, não uma demonstração causal. |

Esses contrastes são fortes e recorrentes no dataset. Ainda assim, `tipo_acidente` e
`causa_acidente` permanecem em `requer_decisao_metodologica`: sua disponibilidade temporal,
seu caráter potencialmente pós-ocorrência e suas mudanças de taxonomia impedem autorização
automática para ML.

### 3.2 Contexto temporal, geográfico e viário

| Comparação | Taxa focal | Taxa de referência | Diferença | n focal | Consistência temporal | Limitação principal |
|---|---:|---:|---:|---:|---|---|
| Nordeste vs Sul | 35,9171% | 24,8740% | 11,0431 p.p. | 74.232 | 5 anos; 34,5087%–36,9122%; amplitude 2,4035 p.p. | Macrorregião é derivada de UF e não há denominador de exposição. |
| Pista Simples vs Dupla | 33,7115% | 23,3513% | 10,3602 p.p. | 167.198 | 5 anos; 33,2003%–34,0749%; amplitude 0,8746 p.p. | A comparação não controla composição geográfica, temporal ou de tráfego. |
| Plena Noite vs Pleno dia | 32,4726% | 25,3047% | 7,1678 p.p. | 119.581 | 5 anos; 31,9258%–33,2122%; amplitude 1,2865 p.p. | Não há exposição por fase do dia e existem relações com outras dimensões temporais. |
| Fim de semana vs Dias úteis | 30,1925% | 27,3303% | 2,8621 p.p. | 112.389 | 5 anos; 29,7023%–30,6912%; amplitude 0,9888 p.p. | O agrupamento de calendário não mede volume de circulação. |

Volume e proporção grave são resultados distintos. Nordeste, pista Simples, Plena Noite e
fim de semana apresentaram proporções maiores nas comparações adotadas, mas isso não significa
que provoquem gravidade nem permite classificá-los como contextos de maior risco absoluto.

## 4. Achados secundários

Os resultados secundários complementam a interpretação sem competir com os oito achados
centrais:

- mês: Maio vs Fevereiro, diferença de 1,7401 ponto percentual;
- hora: 19h vs 8h, 10,6080 pontos;
- meteorologia informada: Nevoeiro/Neblina vs Garoa/Chuvisco, 9,2367 pontos;
- `uso_solo`: `Não` vs `Sim`, 3,5738 pontos;
- componentes de `tracado_via`: Ponte vs Rotatória, 11,7443 pontos, lembrando que componentes
  não são mutuamente exclusivos;
- veículos: 5 vs 1, 19,8610 pontos, sem relação estritamente crescente em todos os valores
  elegíveis;
- pessoas: 9 vs 1, 49,0286% vs 18,7820%, diferença de 30,2466 pontos;
- tipo de pista: Simples vs Múltipla, 11,8435 pontos.

Para `pessoas`, a associação de 1 a 9 é monotonicamente crescente entre valores com
`n >= 500`. Ela é real no dataset, mas parte pode ser mecanicamente influenciada pela
definição do target no nível da ocorrência: mais pessoas oferecem mais oportunidades para que
ao menos uma seja morta ou gravemente ferida. Por isso, `pessoas` não é evidência central nem
feature automaticamente autorizada.

## 5. Resultados contextuais e de qualidade

A heterogeneidade por UF foi mantida como resultado contextual; MA e SP formaram os extremos
da comparação consolidada da Fase 2F. BR e município foram analisados na Fase 2C, mas não
entraram na comparação global de associação devido à dependência contextual e à alta
cardinalidade. Foram observados 2.050 nomes municipais e 2.098 pares `uf + municipio`.

Latitude e longitude permanecem disponíveis, mas exigem cautela de generalização e futura
definição de representação. Nenhuma transformação espacial foi criada.

As seguintes categorias foram preservadas como qualidade de dados, não como evidência
substantiva de suas dimensões:

- `br = 0`: 883 registros;
- `sentido_via = Não Informado`: 883 registros;
- `condicao_metereologica = Ignorado`: 4.492 registros.

A variável original pode ser elegível no futuro, mas a categoria especial não recebe status
independente de feature e não deve ser interpretada como condição observada.

## 6. Taxonomia e estabilidade temporal

`tipo_acidente` apresentou união de 18 categorias, das quais 16 estiveram presentes nos cinco
anos. `causa_acidente` apresentou união de 76 categorias, com 65 presentes nos cinco anos.
Entradas, saídas e diferenças de rótulo ao longo do período são relevantes para validação
temporal e drift.

Nenhuma categoria foi harmonizada na Fase 2. Antes da modelagem será necessário definir como
tratar taxonomias variáveis e categorias que existam no teste, mas não no treino, sem usar
informação futura no desenvolvimento.

## 7. Limitações científicas

1. **Ausência de denominador de exposição:** não há fluxo, viagens ou veículo-quilômetro para
   transformar proporção grave em risco de acidente.
2. **Associação não implica causalidade:** os contrastes são descritivos e não ajustados.
3. **Disponibilidade temporal:** tipo, causa, pessoas e veículos podem ser conhecidos ou
   consolidados durante ou após a ocorrência.
4. **Target no nível da ocorrência:** a definição de `target_grave` influencia a interpretação
   da associação com `pessoas`.
5. **Mudanças taxonômicas:** tipo e, sobretudo, causa apresentam categorias que mudam no
   período.
6. **Ausência semântica:** `Ignorado`, `Não Informado` e códigos especiais devem ser tratados
   como qualidade, não como condições substantivas.
7. **Tamanhos amostrais diferentes:** taxas de categorias raras são mais instáveis; o corte
   `n >= 500` foi editorial e não uma regra científica universal.
8. **Cobertura dos registros:** os dados representam ocorrências registradas pela PRF, não
   necessariamente toda a experiência de circulação nas rodovias federais.

## 8. Elegibilidade para modelagem

A fonte autoritativa é
`reports/tables/phase_2f_modeling_eligibility_matrix.csv`. Ela contém 13 candidatas, cinco
candidatas com cautela, quatro variáveis que requerem decisão metodológica, três exclusões
administrativas e sete exclusões por leakage.

### Candidatas

- `data_inversa`, `month_name`, `dia_semana`, `horario`, `hour`, `fase_dia`;
- `uf`, `br`, `km`;
- `sentido_via`, `condicao_metereologica`, `tipo_pista`, `uso_solo`.

O status indica somente possibilidade de avançar para avaliação futura. Não garante inclusão,
representação adequada, ausência de drift ou capacidade preditiva.

### Candidatas com cautela

- `municipio`, `latitude`, `longitude`: alta granularidade e sensibilidade à generalização;
- `tracado_via`: campo multivalorado com alta cardinalidade aparente pelas combinações; não
  deve ser tratado ingenuamente como 1.214 categorias independentes;
- `tracado_via_components`: representação derivada multirrótulo, com contagens não mutuamente
  exclusivas.

### Requerem decisão metodológica

- `tipo_acidente` e `causa_acidente`: podem incorporar conhecimento durante ou após a
  ocorrência e apresentam mudanças taxonômicas;
- `pessoas`: disponibilidade potencialmente posterior, divergências conhecidas e associação
  parcialmente mecânica com o target;
- `veiculos`: disponibilidade no momento preditivo ainda não definida.

### Exclusões administrativas

- `regional`, `delegacia`, `uop`.

Esses campos permanecem excluídos inicialmente por funcionarem como proxies administrativos.

### Exclusões por leakage

- `mortos`;
- `feridos_graves`;
- `feridos_leves`;
- `feridos`;
- `ilesos`;
- `ignorados`;
- `classificacao_acidente`.

As sete variáveis estão explicitamente bloqueadas para modelagem futura por serem resultados,
consequências ou proxies imediatos da definição de gravidade.

## 9. Drift futuro

A matriz sinaliza 22 variáveis para avaliação temporal antes da modelagem. A Fase 2 não
executou essa avaliação.

### Verificações obrigatórias antes da modelagem

- comparar distribuições por ano e entre desenvolvimento (2021–2024) e período futuro;
- identificar categorias novas, desaparecidas ou restritas a certos anos;
- medir mudanças de frequência nas categorias;
- verificar consistência e faixa de valores numéricos;
- revisar mudanças de taxonomia, principalmente em tipo e causa;
- definir tratamento de categorias não vistas no treino sem consultar o teste final.

## 10. Resposta provisória da EDA à pergunta de pesquisa

Entre as ocorrências registradas pela PRF de 2021 a 2025, foram observadas associações
descritivas importantes com gravidade em dimensões temporais, geográficas, viárias e da
dinâmica da ocorrência. Os contrastes mais marcantes envolveram categorias registradas de
causa e tipo de acidente, enquanto macrorregião, tipo de pista, fase do dia e calendário
também apresentaram diferenças recorrentes nos cinco anos.

Esses resultados não constituem prova causal, não medem a probabilidade de ocorrer um
acidente e não autorizam automaticamente todas as variáveis para predição. Em particular,
tipo, causa, pessoas e veículos dependem de decisão sobre disponibilidade temporal e leakage.
Nenhum desempenho de ML pode ser relatado, pois nenhum modelo foi treinado.

## 11. Decisões finais da EDA

- a Fase 2 está encerrada como análise descritiva e metodológica;
- os oito achados centrais orientam a futura redação, sem formar ranking de perigo;
- a matriz de elegibilidade da Fase 2F é a autoridade para seleção futura;
- categorias especiais continuam como qualidade de dados;
- tipo, causa, pessoas e veículos permanecem pendentes;
- campos administrativos e de leakage permanecem excluídos conforme seus status;
- H001 permanece ativa e exige avaliação de drift antes da preparação/modelagem;
- nenhuma transformação, split ou decisão de algoritmo foi tomada.

A tabela editorial correspondente está em
`reports/tables/phase_2g_eda_decision_summary.csv`.
