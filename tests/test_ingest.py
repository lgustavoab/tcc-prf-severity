import polars as pl

from tcc_prf_severity.data.ingest import standardize_types


def _raw_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "id": ["1"],
            "data_inversa": ["2025-01-01"],
            "dia_semana": ["quarta-feira"],
            "horario": ["12:30:00"],
            "uf": ["SP"],
            "br": ["116"],
            "km": ["128,5"],
            "municipio": ["SAO PAULO"],
            "causa_acidente": ["Exemplo"],
            "tipo_acidente": ["Exemplo"],
            "classificacao_acidente": ["Com Vítimas Feridas"],
            "fase_dia": ["Pleno dia"],
            "sentido_via": ["Crescente"],
            "condicao_metereologica": ["Céu Claro"],
            "tipo_pista": ["Dupla"],
            "tracado_via": ["Reta;Declive"],
            "uso_solo": ["Sim"],
            "pessoas": ["2"],
            "mortos": ["0"],
            "feridos_leves": ["1"],
            "feridos_graves": ["1"],
            "ilesos": ["0"],
            "ignorados": ["0"],
            "feridos": ["2"],
            "veiculos": ["1"],
            "latitude": ["-23,55"],
            "longitude": ["-46,63"],
            "regional": ["SPRF-SP"],
            "delegacia": ["DEL01-SP"],
            "uop": ["UOP01-SP"],
        }
    )


def test_standardize_types_builds_target() -> None:
    result = standardize_types(_raw_frame(), year=2025)

    assert result["target_grave"].item() is True
    assert result["source_year"].item() == 2025
    assert result["km"].item() == 128.5
    assert result["latitude"].item() == -23.55
