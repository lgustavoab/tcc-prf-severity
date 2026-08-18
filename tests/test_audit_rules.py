import polars as pl

from tcc_prf_severity.data.audit import tracado_tokens


def test_tracado_tokens_split_multivalued_field() -> None:
    df = pl.DataFrame({"tracado_via": ["Reta;Declive", "Curva", "Declive;Reta"]})

    assert tracado_tokens(df) == ["Curva", "Declive", "Reta"]
