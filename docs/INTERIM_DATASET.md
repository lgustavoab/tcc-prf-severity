# Dataset intermediário — Fase 1C

## Finalidade e camadas

A camada `interim` oferece uma representação única, tipada e validada das ocorrências da
Polícia Rodoviária Federal entre 2021 e 2025. Ela elimina o custo de reler cinco CSVs em etapas
futuras sem introduzir decisões analíticas.

- `raw`: os cinco CSVs oficiais, imutáveis e preservados como recebidos.
- `interim`: consolidação técnica fiel, com tipos internos, `source_year` e `target_grave`.
- `processed`: camada futura para decisões analíticas; não é criada nesta fase.

As fontes são `datatran2021.csv`, `datatran2022.csv`, `datatran2023.csv`,
`datatran2024.csv` e `datatran2025.csv`, sempre processadas em ordem cronológica.

## Artefato

O comando gera `data/interim/prf_accidents_2021_2025.parquet`, com 342.624 linhas e 32
colunas: as 30 colunas originais, `source_year` e `target_grave`. A ordem lógica das colunas e
os dtypes definidos pelo contrato são preservados.

Apache Parquet foi escolhido por armazenar tipos nativos, permitir leitura colunar eficiente e
oferecer boa compactação. A escrita usa compressão Zstandard (`zstd`). Strings categóricas não
são convertidas em códigos.

Nenhuma limpeza analítica é aplicada: não há remoção, imputação, tratamento de outliers,
expansão de `tracado_via` ou harmonização de `causa_acidente` e `tipo_acidente`. `Ignorado`,
`Não Informado`, `br = 0` e `km = 0` permanecem intactos.

O target segue a regra definitiva:

```text
target_grave = (mortos > 0) OR (feridos_graves > 0)
```

## Validação e gravação segura

Cada fonte passa pelo fluxo existente de tipagem e pelo contrato completo. Após a concatenação,
o dataset é validado novamente e conferido contra o baseline de linhas, colunas, anos, graves e
IDs únicos.

O Parquet é escrito primeiro em um arquivo temporário na pasta de destino. Esse temporário é
relido e passa novamente por todo o contrato. Linhas, colunas, ordem, dtypes, target, anos e IDs
são comparados com o dataset em memória. Somente após sucesso ele substitui atomicamente o
artefato final; uma falha não publica um arquivo parcial.

## Proveniência

`artifacts/interim/interim_manifest.json` registra data e hora UTC, formato, compressão,
contagens, anos, taxa de graves, schema Polars, versões, tamanho e SHA-256 do Parquet, além do
SHA-256 de cada CSV RAW utilizado. Os hashes RAW também são recalculados antes da publicação
para detectar alterações durante a construção.

## Reconstrução

Com os cinco CSVs disponíveis em `data/raw/`, execute:

```powershell
uv run prf-build-interim
```

O Parquet e o manifesto são artefatos derivados e potencialmente grandes ou específicos de uma
execução. Por isso não são versionados no Git; podem ser reconstruídos e verificados pelos
hashes registrados no manifesto.
