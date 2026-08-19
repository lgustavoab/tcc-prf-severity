from __future__ import annotations

from bisect import bisect_right
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, time
from math import inf, isfinite
from pathlib import Path
from typing import Any

import polars as pl

from tcc_prf_severity.analysis.road_environment import extract_road_layout_components
from tcc_prf_severity.analysis.temporal import derive_temporal_columns
from tcc_prf_severity.config import (
    FIGURES_DIR,
    INTERIM_MANIFEST_PATH,
    INTERIM_PARQUET_PATH,
    RAW_DIR,
    TABLES_DIR,
)
from tcc_prf_severity.data.interim import verify_interim_dataset

DEVELOPMENT_YEARS = (2021, 2022, 2023, 2024)
COMPARISON_YEAR = 2025
DEVELOPMENT_PERIOD = "2021-2024"
COMPARISON_PERIOD = "2025"

CATEGORICAL_VARIABLES = (
    "month_name",
    "dia_semana",
    "hour",
    "fase_dia",
    "uf",
    "br",
    "municipio",
    "sentido_via",
    "condicao_metereologica",
    "tipo_pista",
    "uso_solo",
    "tipo_acidente",
    "causa_acidente",
    "tracado_via",
    "pessoas",
    "veiculos",
)
CONTINUOUS_VARIABLES = ("km", "latitude", "longitude")
DISCRETE_COUNT_VARIABLES = ("pessoas", "veiculos")
EXCLUDED_VARIABLES = (
    "mortos",
    "feridos_graves",
    "feridos_leves",
    "feridos",
    "ilesos",
    "ignorados",
    "classificacao_acidente",
    "regional",
    "delegacia",
    "uop",
)


@dataclass(frozen=True)
class TemporalDriftAnalysis:
    drift_inventory: pl.DataFrame
    categorical_drift_summary: pl.DataFrame
    numeric_drift_summary: pl.DataFrame
    unseen_categories_2025: pl.DataFrame
    annual_cardinality: pl.DataFrame
    multilabel_drift_summary: pl.DataFrame
    drift_decision_summary: pl.DataFrame


@dataclass(frozen=True)
class TemporalDriftAnalysisRun:
    analysis: TemporalDriftAnalysis
    table_paths: tuple[Path, ...]
    figure_paths: tuple[Path, ...]


def _require_columns(df: pl.DataFrame, columns: Iterable[str]) -> None:
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes para a Fase 3A: {missing}")


def _category_label(value: object) -> str:
    if value is None:
        return "<NULL>"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _normalized_distribution(values: Mapping[object, int | float]) -> dict[object, float]:
    total = float(sum(values.values()))
    if total <= 0:
        return {}
    return {category: float(count) / total for category, count in values.items()}


def total_variation_distance(
    development: Mapping[Any, int | float], comparison: Mapping[Any, int | float]
) -> float:
    """Calcula TVD entre duas distribuições discretas, incluindo suportes distintos."""
    dev = _normalized_distribution(development)
    comp = _normalized_distribution(comparison)
    categories = set(dev) | set(comp)
    if not categories:
        return 0.0
    return 0.5 * sum(
        abs(dev.get(category, 0.0) - comp.get(category, 0.0)) for category in categories
    )


def _counts(df: pl.DataFrame, variable: str) -> Counter[object]:
    return Counter(df.get_column(variable).to_list())


def _required_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"Valor inteiro inválido para {label}: {value!r}")
    return value


def _required_float(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"Valor numérico inválido para {label}: {value!r}")
    return float(value)


def _categorical_drift_row(
    development: pl.DataFrame, comparison: pl.DataFrame, variable: str
) -> tuple[dict[str, object], list[object], list[object]]:
    dev_counts = _counts(development, variable)
    comp_counts = _counts(comparison, variable)
    dev_dist = _normalized_distribution(dev_counts)
    comp_dist = _normalized_distribution(comp_counts)
    dev_categories = set(dev_counts)
    comp_categories = set(comp_counts)
    shared = dev_categories & comp_categories
    unseen = sorted(comp_categories - dev_categories, key=_category_label)
    missing = sorted(dev_categories - comp_categories, key=_category_label)
    changes = {
        category: (comp_dist.get(category, 0.0) - dev_dist.get(category, 0.0)) * 100
        for category in dev_categories | comp_categories
    }
    largest_category = min(
        changes,
        key=lambda category: (-abs(changes[category]), _category_label(category)),
    )
    unseen_occurrences = sum(comp_counts[category] for category in unseen)
    comparison_total = sum(comp_counts.values())
    method = (
        "discrete_exact_tvd"
        if variable in DISCRETE_COUNT_VARIABLES
        else "high_cardinality_categorical_tvd"
        if variable == "tracado_via"
        else "categorical_tvd"
    )
    return (
        {
            "variable": variable,
            "audit_method": method,
            "tvd": round(total_variation_distance(dev_counts, comp_counts), 9),
            "development_categories": len(dev_categories),
            "comparison_categories": len(comp_categories),
            "shared_categories": len(shared),
            "new_categories_2025": len(unseen),
            "missing_categories_2025": len(missing),
            "unseen_occurrences_2025": unseen_occurrences,
            "unseen_share_2025_percent": round(
                unseen_occurrences / comparison_total * 100 if comparison_total else 0.0, 9
            ),
            "largest_change_category": _category_label(largest_category),
            "largest_absolute_share_change_percentage_points": round(
                abs(changes[largest_category]), 9
            ),
            "development_share_percent_for_largest_change": round(
                dev_dist.get(largest_category, 0.0) * 100, 9
            ),
            "comparison_share_percent_for_largest_change": round(
                comp_dist.get(largest_category, 0.0) * 100, 9
            ),
        },
        unseen,
        missing,
    )


def categorical_drift_summary(
    df: pl.DataFrame, variables: Sequence[str] = CATEGORICAL_VARIABLES
) -> pl.DataFrame:
    """Compara distribuições exclusivas de 2021-2024 com 2025."""
    _require_columns(df, ("source_year", *variables))
    development = df.filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS))
    comparison = df.filter(pl.col("source_year") == COMPARISON_YEAR)
    if development.is_empty() or comparison.is_empty():
        raise ValueError("A auditoria requer dados em 2021-2024 e em 2025.")
    rows = [_categorical_drift_row(development, comparison, variable)[0] for variable in variables]
    return pl.DataFrame(rows).sort("tvd", "variable", descending=[True, False])


def unseen_categories_table(
    df: pl.DataFrame, variables: Sequence[str] = CATEGORICAL_VARIABLES
) -> pl.DataFrame:
    """Lista categorias observadas em 2025 e ausentes no desenvolvimento."""
    _require_columns(df, ("source_year", *variables))
    development = df.filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS))
    comparison = df.filter(pl.col("source_year") == COMPARISON_YEAR)
    rows: list[dict[str, object]] = []
    for variable in variables:
        _, unseen, _ = _categorical_drift_row(development, comparison, variable)
        counts = _counts(comparison, variable)
        total = sum(counts.values())
        for category in unseen:
            if variable in ("tipo_acidente", "causa_acidente"):
                note = "Taxonomia original preservada; não harmonizar automaticamente."
            elif variable == "tracado_via":
                note = "Combinação original do campo multivalorado; não é erro automático."
            elif variable in DISCRETE_COUNT_VARIABLES:
                note = "Valor discreto exato; decisão de representação permanece para a Fase 3B."
            else:
                note = "Categoria nova não tratada automaticamente como erro."
            first_year = _required_int(
                df.filter(pl.col(variable) == category).get_column("source_year").min(),
                f"primeiro ano de {variable}",
            )
            rows.append(
                {
                    "variable": variable,
                    "category": _category_label(category),
                    "occurrences_2025": counts[category],
                    "share_2025_percent": round(counts[category] / total * 100, 9),
                    "first_year_observed": first_year,
                    "note": note,
                }
            )
    schema = {
        "variable": pl.String,
        "category": pl.String,
        "occurrences_2025": pl.Int64,
        "share_2025_percent": pl.Float64,
        "first_year_observed": pl.Int64,
        "note": pl.String,
    }
    return pl.DataFrame(rows, schema=schema).sort(
        "variable", "occurrences_2025", "category", descending=[False, True, False]
    )


def _quantile(series: pl.Series, probability: float) -> float | None:
    value = series.quantile(probability, interpolation="linear")
    return float(value) if value is not None else None


def numeric_statistics(values: pl.Series) -> dict[str, int | float | None]:
    """Resume uma série numérica sem imputação, remoção ou winsorização."""
    clean = values.drop_nulls().cast(pl.Float64)
    clean = clean.filter(clean.is_finite())
    if clean.is_empty():
        return {
            "n": 0,
            "minimum": None,
            "p25": None,
            "median": None,
            "mean": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "maximum": None,
        }
    return {
        "n": clean.len(),
        "minimum": _required_float(clean.min(), "mínimo"),
        "p25": _quantile(clean, 0.25),
        "median": _required_float(clean.median(), "mediana"),
        "mean": _required_float(clean.mean(), "média"),
        "p75": _quantile(clean, 0.75),
        "p90": _quantile(clean, 0.90),
        "p95": _quantile(clean, 0.95),
        "p99": _quantile(clean, 0.99),
        "maximum": _required_float(clean.max(), "máximo"),
    }


def development_quantile_bin_edges(values: pl.Series) -> tuple[float, ...]:
    """Define bins por decis únicos usando exclusivamente valores do desenvolvimento."""
    clean = values.drop_nulls().cast(pl.Float64)
    clean = clean.filter(clean.is_finite())
    if clean.is_empty():
        raise ValueError("Não há valores de desenvolvimento para definir bins.")
    internal = {
        float(value)
        for probability in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
        if (value := clean.quantile(probability, interpolation="linear")) is not None
        and isfinite(float(value))
    }
    return (-inf, *sorted(internal), inf)


def apply_numeric_bins(values: pl.Series, edges: Sequence[float]) -> Counter[int]:
    """Aplica fronteiras fixas a uma série, incluindo valores fora dos quantis internos."""
    if len(edges) < 2 or edges[0] != -inf or edges[-1] != inf:
        raise ValueError("Bins numéricos devem começar em -inf e terminar em inf.")
    internal = list(edges[1:-1])
    counts: Counter[int] = Counter()
    for raw_value in values.drop_nulls().cast(pl.Float64).to_list():
        value = float(raw_value)
        if isfinite(value):
            counts[bisect_right(internal, value)] += 1
    return counts


def numeric_drift_summary(
    df: pl.DataFrame,
    continuous_variables: Sequence[str] = CONTINUOUS_VARIABLES,
    discrete_variables: Sequence[str] = DISCRETE_COUNT_VARIABLES,
) -> pl.DataFrame:
    """Resume contínuas com bins de desenvolvimento e contagens discretas sem bins."""
    variables = (*continuous_variables, *discrete_variables)
    _require_columns(df, ("source_year", *variables))
    development = df.filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS))
    comparison = df.filter(pl.col("source_year") == COMPARISON_YEAR)
    rows: list[dict[str, object]] = []
    for variable in variables:
        dev_values = development.get_column(variable)
        comp_values = comparison.get_column(variable)
        dev_stats = numeric_statistics(dev_values)
        comp_stats = numeric_statistics(comp_values)
        if variable in continuous_variables:
            edges = development_quantile_bin_edges(dev_values)
            dev_bins = apply_numeric_bins(dev_values, edges)
            comp_bins = apply_numeric_bins(comp_values, edges)
            tvd = total_variation_distance(dev_bins, comp_bins)
            audit_method = "development_decile_binned_tvd"
            boundaries = "|".join(f"{edge:.12g}" for edge in edges[1:-1])
            bin_count = len(edges) - 1
        else:
            tvd = total_variation_distance(
                _counts(development, variable), _counts(comparison, variable)
            )
            audit_method = "discrete_exact_tvd"
            boundaries = None
            bin_count = None
        row: dict[str, object] = {
            "variable": variable,
            "audit_method": audit_method,
            "distribution_tvd": round(tvd, 9),
            "development_bin_count": bin_count,
            "development_internal_bin_boundaries": boundaries,
        }
        for prefix, stats in (("development", dev_stats), ("comparison", comp_stats)):
            row.update({f"{prefix}_{name}": value for name, value in stats.items()})
        rows.append(row)
    return pl.DataFrame(rows).sort("distribution_tvd", "variable", descending=[True, False])


def _parse_date_series(series: pl.Series) -> pl.Series:
    if series.dtype == pl.Date:
        return series
    if series.dtype == pl.Datetime:
        return series.dt.date()
    return series.cast(pl.String).str.to_date(strict=False)


def _parse_time_value(value: object) -> time | None:
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, str):
        try:
            return time.fromisoformat(value)
        except ValueError:
            return None
    return None


def calendar_coverage(df: pl.DataFrame) -> pl.DataFrame:
    """Audita cobertura de datas e a consistência de `month_name` por ano."""
    _require_columns(df, ("source_year", "data_inversa", "month_name"))
    parsed = _parse_date_series(df.get_column("data_inversa"))
    work = df.with_columns(parsed.alias("_parsed_date"))
    rows: list[dict[str, object]] = []
    for year in sorted(work.get_column("source_year").unique().to_list()):
        annual = work.filter(pl.col("source_year") == year)
        parseable = annual.get_column("_parsed_date").drop_nulls()
        month_numbers = set(parseable.dt.month().to_list())
        expected_names = derive_temporal_columns(annual).get_column("month_name")
        consistent = int((expected_names == annual.get_column("month_name")).sum())
        rows.append(
            {
                "variable": "data_inversa",
                "source_year": int(year),
                "non_null_occurrences": annual.get_column("data_inversa").len()
                - annual.get_column("data_inversa").null_count(),
                "parseable_occurrences": parseable.len(),
                "distinct_values": parseable.n_unique(),
                "covered_months": len(month_numbers),
                "missing_months": "|".join(
                    str(month) for month in sorted(set(range(1, 13)) - month_numbers)
                ),
                "minimum_value": str(parseable.min()) if not parseable.is_empty() else None,
                "maximum_value": str(parseable.max()) if not parseable.is_empty() else None,
                "derivation_consistent_occurrences": consistent,
                "top_category": None,
                "top_category_occurrences": None,
                "top_category_share_percent": None,
            }
        )
    return pl.DataFrame(rows)


def horario_coverage(df: pl.DataFrame) -> pl.DataFrame:
    """Audita parseabilidade e consistência da derivação de `hour`."""
    _require_columns(df, ("source_year", "horario", "hour"))
    rows: list[dict[str, object]] = []
    for year in sorted(df.get_column("source_year").unique().to_list()):
        annual = df.filter(pl.col("source_year") == year)
        parsed = [_parse_time_value(value) for value in annual.get_column("horario").to_list()]
        valid = [value for value in parsed if value is not None and 0 <= value.hour <= 23]
        expected_hours = [value.hour if value is not None else None for value in parsed]
        actual_hours = annual.get_column("hour").to_list()
        consistent = sum(
            expected == actual
            for expected, actual in zip(expected_hours, actual_hours, strict=True)
        )
        rows.append(
            {
                "variable": "horario",
                "source_year": int(year),
                "non_null_occurrences": annual.get_column("horario").len()
                - annual.get_column("horario").null_count(),
                "parseable_occurrences": len(valid),
                "distinct_values": len(set(valid)),
                "covered_months": None,
                "missing_months": None,
                "minimum_value": str(min(valid)) if valid else None,
                "maximum_value": str(max(valid)) if valid else None,
                "derivation_consistent_occurrences": consistent,
                "top_category": None,
                "top_category_occurrences": None,
                "top_category_share_percent": None,
            }
        )
    return pl.DataFrame(rows)


def annual_cardinality_table(
    df: pl.DataFrame, variables: Sequence[str] = CATEGORICAL_VARIABLES
) -> pl.DataFrame:
    """Registra cardinalidade e categoria modal anual sem inferir tendência."""
    _require_columns(df, ("source_year", *variables))
    rows: list[dict[str, object]] = []
    for variable in variables:
        for year in sorted(df.get_column("source_year").unique().to_list()):
            annual = df.filter(pl.col("source_year") == year)
            counts = _counts(annual, variable)
            top_category = min(
                counts,
                key=lambda category: (-counts[category], _category_label(category)),
            )
            rows.append(
                {
                    "variable": variable,
                    "source_year": int(year),
                    "non_null_occurrences": annual.get_column(variable).len()
                    - annual.get_column(variable).null_count(),
                    "parseable_occurrences": None,
                    "distinct_values": len(counts),
                    "covered_months": None,
                    "missing_months": None,
                    "minimum_value": None,
                    "maximum_value": None,
                    "derivation_consistent_occurrences": None,
                    "top_category": _category_label(top_category),
                    "top_category_occurrences": counts[top_category],
                    "top_category_share_percent": round(
                        counts[top_category] / annual.height * 100, 9
                    ),
                }
            )
    categorical = pl.DataFrame(rows)
    return pl.concat(
        [categorical, calendar_coverage(df), horario_coverage(df)],
        how="diagonal_relaxed",
    ).sort("variable", "source_year")


def multilabel_drift_summary(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Compara prevalências de componentes, sem aplicar TVD exclusiva."""
    _require_columns(df, ("source_year", "target_grave", "tracado_via"))
    components = extract_road_layout_components(df)
    development = components.filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS))
    comparison = components.filter(pl.col("source_year") == COMPARISON_YEAR)
    dev_total = df.filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS)).height
    comp_total = df.filter(pl.col("source_year") == COMPARISON_YEAR).height
    dev_counts = Counter(development.get_column("road_layout_component").to_list())
    comp_counts = Counter(comparison.get_column("road_layout_component").to_list())
    annual_presence = {
        component: sorted(
            components.filter(pl.col("road_layout_component") == component)
            .get_column("source_year")
            .unique()
            .to_list()
        )
        for component in set(dev_counts) | set(comp_counts)
    }
    rows: list[dict[str, object]] = []
    unseen_rows: list[dict[str, object]] = []
    for component in sorted(set(dev_counts) | set(comp_counts)):
        dev_share = dev_counts[component] / dev_total * 100 if dev_total else 0.0
        comp_share = comp_counts[component] / comp_total * 100 if comp_total else 0.0
        status = (
            "new_in_2025"
            if component not in dev_counts
            else "missing_in_2025"
            if component not in comp_counts
            else "shared"
        )
        rows.append(
            {
                "variable": "tracado_via_components",
                "component": component,
                "development_occurrences": dev_counts[component],
                "development_prevalence_percent": round(dev_share, 9),
                "comparison_occurrences": comp_counts[component],
                "comparison_prevalence_percent": round(comp_share, 9),
                "difference_percentage_points": round(comp_share - dev_share, 9),
                "absolute_difference_percentage_points": round(abs(comp_share - dev_share), 9),
                "years_present": "|".join(str(year) for year in annual_presence[component]),
                "temporal_presence_status": status,
                "audit_method": "multilabel_prevalence_shift",
            }
        )
        if status == "new_in_2025":
            unseen_rows.append(
                {
                    "variable": "tracado_via_components",
                    "category": component,
                    "occurrences_2025": comp_counts[component],
                    "share_2025_percent": round(comp_share, 9),
                    "first_year_observed": min(annual_presence[component]),
                    "note": (
                        "Componente multilabel; participação não integra distribuição exclusiva."
                    ),
                }
            )
    multilabel = pl.DataFrame(rows).sort(
        "absolute_difference_percentage_points", "component", descending=[True, False]
    )
    unseen_schema = {
        "variable": pl.String,
        "category": pl.String,
        "occurrences_2025": pl.Int64,
        "share_2025_percent": pl.Float64,
        "first_year_observed": pl.Int64,
        "note": pl.String,
    }
    return multilabel, pl.DataFrame(unseen_rows, schema=unseen_schema)


def _audit_method(variable: str) -> tuple[str, bool, str, str]:
    if variable == "data_inversa":
        return (
            "calendar_coverage",
            True,
            "month_name para sazonalidade",
            "Cobertura de calendário; sem TVD de datas completas.",
        )
    if variable == "horario":
        return (
            "derived_hour_proxy",
            False,
            "hour",
            "Parseabilidade e consistência; distribuição avaliada por hour.",
        )
    if variable == "tracado_via_components":
        return (
            "multilabel_prevalence_shift",
            False,
            "decomposição validada de tracado_via",
            "Componentes não mutuamente exclusivos; TVD exclusiva não aplicável.",
        )
    if variable in CONTINUOUS_VARIABLES:
        return (
            "development_decile_binned_tvd",
            True,
            "",
            "Bins definidos exclusivamente em 2021-2024.",
        )
    if variable in DISCRETE_COUNT_VARIABLES:
        return (
            "discrete_exact_tvd",
            True,
            "",
            "Valores exatos preservados; decisão metodológica pendente.",
        )
    if variable == "tracado_via":
        return (
            "high_cardinality_categorical_tvd",
            True,
            "",
            "Strings originais preservadas; resultado reflete combinações.",
        )
    return "categorical_tvd", True, "", "Strings originais preservadas; sem harmonização."


def build_drift_inventory(eligibility: pl.DataFrame) -> pl.DataFrame:
    """Constrói o escopo somente a partir das linhas drift=true da matriz 2F."""
    required = ("variable", "modeling_eligibility_status", "requires_temporal_drift_check")
    _require_columns(eligibility, required)
    scoped = eligibility.filter(pl.col("requires_temporal_drift_check") == True)  # noqa: E712
    if scoped.is_empty():
        raise ValueError("A matriz de elegibilidade não contém variáveis para auditoria temporal.")
    excluded = sorted(set(scoped.get_column("variable")) & set(EXCLUDED_VARIABLES))
    if excluded:
        raise ValueError(f"Variáveis já excluídas não podem entrar na auditoria: {excluded}")
    rows: list[dict[str, object]] = []
    for row in scoped.iter_rows(named=True):
        variable = str(row["variable"])
        method, direct, proxy, note = _audit_method(variable)
        rows.append(
            {
                "variable": variable,
                "modeling_eligibility_status": str(row["modeling_eligibility_status"]),
                "audit_method": method,
                "analyzed_directly": direct,
                "proxy_or_derivation": proxy,
                "development_period": DEVELOPMENT_PERIOD,
                "comparison_period": COMPARISON_PERIOD,
                "drift_metric": "TVD"
                if "tvd" in method
                else "prevalence_difference_pp"
                if method == "multilabel_prevalence_shift"
                else "coverage_consistency",
                "quality_note": note,
                "requires_followup_3b": True,
            }
        )
    inventory = pl.DataFrame(rows)
    if inventory.height != scoped.height:
        raise RuntimeError("O inventário da Fase 3A não reconciliou com a matriz 2F.")
    return inventory


def _decision_summary(
    inventory: pl.DataFrame,
    categorical: pl.DataFrame,
    numeric: pl.DataFrame,
    multilabel: pl.DataFrame,
    annual: pl.DataFrame,
) -> pl.DataFrame:
    categorical_rows = {str(row["variable"]): row for row in categorical.iter_rows(named=True)}
    numeric_rows = {str(row["variable"]): row for row in numeric.iter_rows(named=True)}
    rows: list[dict[str, object]] = []
    for item in inventory.iter_rows(named=True):
        variable = str(item["variable"])
        method = str(item["audit_method"])
        if variable in categorical_rows:
            evidence = categorical_rows[variable]
            observed = (
                f"TVD={float(evidence['tvd']):.6f}; maior mudança="
                f"{evidence['largest_change_category']} "
                f"({float(evidence['largest_absolute_share_change_percentage_points']):.6f} p.p.); "
                f"novas em 2025={evidence['new_categories_2025']}; "
                f"share unseen={float(evidence['unseen_share_2025_percent']):.6f}%."
            )
        elif variable in numeric_rows:
            evidence = numeric_rows[variable]
            observed = (
                f"TVD={float(evidence['distribution_tvd']):.6f}; "
                f"mediana dev={float(evidence['development_median']):.6f}; "
                f"mediana 2025={float(evidence['comparison_median']):.6f}."
            )
        elif variable == "tracado_via_components":
            largest = multilabel.row(0, named=True)
            observed = (
                "TVD exclusiva não aplicável; maior mudança de prevalência="
                f"{largest['component']} "
                f"({float(largest['absolute_difference_percentage_points']):.6f} p.p.)."
            )
        elif variable == "data_inversa":
            coverage = annual.filter(pl.col("variable") == variable)
            parseable = int(coverage.get_column("parseable_occurrences").sum())
            non_null = int(coverage.get_column("non_null_occurrences").sum())
            observed = f"Cobertura de calendário: {parseable}/{non_null} datas parseáveis."
        else:
            coverage = annual.filter(pl.col("variable") == variable)
            parseable = int(coverage.get_column("parseable_occurrences").sum())
            non_null = int(coverage.get_column("non_null_occurrences").sum())
            observed = f"Proxy hour: {parseable}/{non_null} horários parseáveis."

        if variable in ("tipo_acidente", "causa_acidente"):
            risk = (
                "Mudanças de taxonomia e de frequência entre períodos podem afetar "
                "representação e generalização; categorias desconhecidas também deverão ser "
                "tratadas explicitamente em uso futuro."
            )
            action = (
                "Definir disponibilidade preditiva e política explícita para categorias "
                "desconhecidas, sem harmonizar ainda."
            )
        elif variable in ("pessoas", "veiculos"):
            risk = (
                "Cauda longa, valores novos e disponibilidade temporal podem afetar generalização."
            )
            action = (
                "Decidir disponibilidade e representação da contagem antes de eventual inclusão."
            )
        elif variable in ("tracado_via", "tracado_via_components"):
            risk = (
                "Representações redundantes e natureza combinatória/multilabel podem produzir "
                "categorias raras."
            )
            action = (
                "Escolher representação única ou controlada na Fase 3B; não selecionar "
                "definitivamente nesta fase."
            )
        elif variable in ("data_inversa", "month_name", "horario", "hour"):
            risk = (
                "Representações temporais redundantes podem duplicar informação e depender do "
                "desenho temporal."
            )
            action = "Resolver redundância e disponibilidade temporal na Fase 3B."
        elif variable in CONTINUOUS_VARIABLES or variable == "municipio":
            risk = "Mudança espacial ou de cobertura pode reduzir generalização para 2025."
            action = "Revisar magnitude, missingness e representação geográfica na Fase 3B."
        else:
            risk = (
                "Mudança de participação entre períodos pode alterar o desempenho fora do "
                "desenvolvimento."
            )
            action = "Considerar o valor observado no desenho e monitoramento da Fase 3B."
        rows.append(
            {
                "variable": variable,
                "audit_method": method,
                "evidence_observed": observed,
                "temporal_generalization_risk": risk,
                "recommended_action_3b": action,
                "final_inclusion_decided": False,
            }
        )
    return pl.DataFrame(rows)


def analyze_temporal_drift(df: pl.DataFrame, eligibility: pl.DataFrame) -> TemporalDriftAnalysis:
    """Executa a auditoria descritiva sem modificar o DataFrame de entrada."""
    inventory = build_drift_inventory(eligibility)
    scoped_variables = set(inventory.get_column("variable"))
    expected_methods = (
        set(CATEGORICAL_VARIABLES)
        | set(CONTINUOUS_VARIABLES)
        | {
            "data_inversa",
            "horario",
            "tracado_via_components",
        }
    )
    unsupported = sorted(scoped_variables - expected_methods)
    if unsupported:
        raise ValueError(f"Variáveis drift=true sem método de auditoria definido: {unsupported}")
    _require_columns(
        df,
        (
            "source_year",
            "target_grave",
            *(scoped_variables - {"month_name", "hour", "tracado_via_components"}),
        ),
    )
    temporal = derive_temporal_columns(df)
    categorical_variables = tuple(
        variable for variable in CATEGORICAL_VARIABLES if variable in scoped_variables
    )
    categorical = categorical_drift_summary(temporal, categorical_variables)
    numeric = numeric_drift_summary(
        temporal,
        tuple(variable for variable in CONTINUOUS_VARIABLES if variable in scoped_variables),
        tuple(variable for variable in DISCRETE_COUNT_VARIABLES if variable in scoped_variables),
    )
    unseen = unseen_categories_table(temporal, categorical_variables)
    annual = annual_cardinality_table(temporal, categorical_variables)
    multilabel, multilabel_unseen = multilabel_drift_summary(temporal)
    if not multilabel_unseen.is_empty():
        unseen = pl.concat([unseen, multilabel_unseen], how="vertical_relaxed").sort(
            "variable", "occurrences_2025", "category", descending=[False, True, False]
        )
    decisions = _decision_summary(inventory, categorical, numeric, multilabel, annual)
    return TemporalDriftAnalysis(
        drift_inventory=inventory,
        categorical_drift_summary=categorical,
        numeric_drift_summary=numeric,
        unseen_categories_2025=unseen,
        annual_cardinality=annual,
        multilabel_drift_summary=multilabel,
        drift_decision_summary=decisions,
    )


def write_temporal_drift_tables(
    analysis: TemporalDriftAnalysis, output_dir: Path
) -> tuple[Path, ...]:
    """Grava somente as sete tabelas científicas consolidadas da Fase 3A."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = (
        (analysis.drift_inventory, "phase_3a_drift_inventory.csv"),
        (analysis.categorical_drift_summary, "phase_3a_categorical_drift_summary.csv"),
        (analysis.numeric_drift_summary, "phase_3a_numeric_drift_summary.csv"),
        (analysis.unseen_categories_2025, "phase_3a_unseen_categories_2025.csv"),
        (analysis.annual_cardinality, "phase_3a_annual_cardinality.csv"),
        (analysis.multilabel_drift_summary, "phase_3a_multilabel_drift_summary.csv"),
        (analysis.drift_decision_summary, "phase_3a_drift_decision_summary.csv"),
    )
    for table, filename in outputs:
        table.write_csv(output_dir / filename)
    return tuple(output_dir / filename for _, filename in outputs)


def run_temporal_drift_analysis(
    parquet_path: Path = INTERIM_PARQUET_PATH,
    manifest_path: Path = INTERIM_MANIFEST_PATH,
    raw_dir: Path = RAW_DIR,
    eligibility_path: Path = TABLES_DIR / "phase_2f_modeling_eligibility_matrix.csv",
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> TemporalDriftAnalysisRun:
    """Verifica fontes, executa a Fase 3A e publica tabelas e figuras."""
    verify_interim_dataset(raw_dir, parquet_path, manifest_path)
    if not eligibility_path.is_file():
        raise FileNotFoundError(f"Matriz de elegibilidade não encontrada: {eligibility_path}")
    eligibility = pl.read_csv(eligibility_path)
    analysis = analyze_temporal_drift(pl.read_parquet(parquet_path), eligibility)
    table_paths = write_temporal_drift_tables(analysis, tables_dir)
    from tcc_prf_severity.analysis.temporal_drift_plots import write_temporal_drift_figures

    figure_paths = write_temporal_drift_figures(analysis, figures_dir)
    return TemporalDriftAnalysisRun(analysis, table_paths, figure_paths)
