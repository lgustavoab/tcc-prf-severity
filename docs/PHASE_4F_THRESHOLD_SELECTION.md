# Fase 4F — Seleção de threshold OOF

## Objetivo e escopo

A Fase 4F congela um único cutoff binário para o XGBoost selecionado na Fase 4E. A decisão
usa exclusivamente as previsões out-of-fold temporais de 2022, 2023 e 2024 já produzidas
pela Fase 4C. Nenhum classificador foi carregado ou treinado, não houve tuning, comparação de
modelos, refit ou consulta a 2025.

O resultado é o **threshold selecionado no OOF temporal de desenvolvimento**. Ele não é um
cutoff universalmente ótimo e não deve ser reajustado a partir da avaliação final de 2025.

## AP para o modelo, F1 para o cutoff

Average Precision (AP) permaneceu a métrica autoritativa para comparar e selecionar a
família/modelo nos três folds. A Fase 4F não recalcula nem altera AP. Depois da seleção formal
do XGBoost, o F1 da classe `target_grave=True` é usado somente para escolher como converter a
probabilidade já existente em decisão binária.

Assim, AP selecionou o modelo; F1 OOF selecionou o cutoff.

## Fonte e auditoria do OOF

O artefato usado foi
`data/processed/phase_4c_xgboost_oof_predictions.parquet`, identificado nesta materialização
por SHA-256
`28925211b1542c2c7965b8b45cd6b5f360389f200ea197de57f9068f777a6bdb`.

A auditoria confirmou:

- seleção 4E igual a `phase_4c_xgboost_baseline`, família
  `xgboost_gradient_boosted_trees`;
- 205.528 linhas e 205.528 IDs únicos;
- apenas 2022, 2023 e 2024;
- mapeamento 2022→Fold 1, 2023→Fold 2 e 2024→Fold 3;
- contagens por fold reconciliadas com as métricas 4C;
- target booleano e probabilidades finitas no intervalo `[0, 1]`;
- ausência de 2021 e 2025.

O hash identifica o arquivo efetivamente usado para congelar o threshold. Ele não é tratado
como definição universal de equivalência numérica entre materializações cientificamente
equivalentes.

## Candidatos, algoritmo e desempate

Os candidatos foram exatamente os 202.207 valores únicos observados em
`predicted_probability_grave`. O cutoff 0,5 não foi inserido como candidato especial: ele foi
calculado separadamente apenas como referência.

A busca ordena as probabilidades de forma decrescente, agrupa scores iguais e acumula TP e FP;
FN e TN são derivados das contagens totais. A complexidade é `O(n log n)`, dominada pela
ordenação. Para cada score único, a regra é:

```text
predicted_grave = predicted_probability_grave >= threshold
```

O F1 é comparado como a fração inteira `2TP / (2TP + FP + FN)`, por multiplicação cruzada,
sem tolerância numérica inventada. Empates exatos seriam resolvidos por maior recall —
equivalente a maior TP com número fixo de positivos — e, persistindo o empate, pelo menor
threshold. Houve um único candidato no F1 máximo; nenhum desempate precisou ser aplicado.

## Threshold congelado e resultado pooled

O threshold selecionado foi `0.23723246157169342`.

| Métrica | Threshold selecionado | Referência 0,5 | Diferença selecionado − referência |
|---|---:|---:|---:|
| Precision | 0,33330114898136526 | 0,5713684210526315 | -0,23806727207126627 |
| Recall | 0,7704563403495519 | 0,04659547436733853 | +0,7238608659822133 |
| F1 | 0,46530870405989 | 0,08616420090164455 | +0,37914450315824544 |
| TN | 57.517 | 145.246 | -87.729 |
| FP | 89.765 | 2.036 | +87.729 |
| FN | 13.370 | 55.532 | -42.162 |
| TP | 44.876 | 2.714 | +42.162 |

O ganho de recall e F1 vem acompanhado de menor precision e muito mais decisões positivas.
Isso descreve o compromisso observado no OOF; não estabelece utilidade operacional externa.

## Diagnóstico temporal com o mesmo cutoff

O threshold congelado foi aplicado sem ajuste em cada ano:

| Ano | Linhas | Precision | Recall | F1 | TN | FP | FN | TP |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022 | 64.606 | 0,33473501051257887 | 0,7524037155739041 | 0,4633371245065899 | 18.669 | 27.528 | 4.558 | 13.851 |
| 2023 | 67.766 | 0,33233334803899944 | 0,7841973766396002 | 0,4668298577758498 | 18.286 | 30.268 | 4.146 | 15.066 |
| 2024 | 73.156 | 0,33297863461859456 | 0,773769696969697 | 0,46559596224818756 | 20.562 | 31.969 | 4.666 | 15.959 |

Essas linhas são diagnósticos temporais, não três thresholds. Nenhum resultado anual alterou
o cutoff após a busca pooled.

## Artefatos e reprodução

```powershell
uv run prf-select-model
uv run prf-select-threshold
```

O segundo comando não reproduz a Fase 4C. Se o OOF estiver ausente, ele interrompe com uma
mensagem explícita para materializá-lo separadamente. Uma execução válida publica:

- `phase_4f_threshold_selection.csv`: contrato principal key/value;
- `phase_4f_threshold_evaluation.csv`: pooled, referência 0,5 e diagnósticos anuais;
- `phase_4f_threshold_search_summary.csv`: auditoria compacta da busca;
- `phase_4f_threshold_checklist.csv`: 17 verificações substantivas.

## Limitações, proteção de 2025 e congelamento

O threshold otimiza F1 no pool temporal OOF de desenvolvimento e depende da prevalência, dos
custos implícitos e da materialização analisada. Não incorpora custo operacional, capacidade
de atendimento, análise causal ou calibração para outro domínio. O cutoff 0,5 é apenas uma
referência, não um concorrente metodológico privilegiado.

Após a Fase 4F ficam congelados o XGBoost/configuração 4C, o preprocessing 3E, as features
3B/3C e o threshold `0.23723246157169342`. O ano de 2025 segue reservado: não participou do
fit, da seleção de modelo, da busca de threshold ou de qualquer ajuste.

O próximo passo autorizado é a **Fase 4G — refit em 2021–2024**, mantendo o threshold
congelado e sem usá-lo para redefinir o modelo.
