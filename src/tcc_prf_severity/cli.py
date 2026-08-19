from typing import Any

import polars as pl

from tcc_prf_severity.analysis.general import run_general_analysis
from tcc_prf_severity.analysis.geographic import run_geographic_analysis
from tcc_prf_severity.analysis.occurrence_dynamics import run_occurrence_dynamics_analysis
from tcc_prf_severity.analysis.road_environment import run_road_environment_analysis
from tcc_prf_severity.analysis.severity_associations import run_severity_associations_analysis
from tcc_prf_severity.analysis.temporal import run_temporal_analysis
from tcc_prf_severity.analysis.temporal_drift import run_temporal_drift_analysis
from tcc_prf_severity.config import (
    AUDIT_DIR,
    RAW_DIR,
)
from tcc_prf_severity.data.analytical import (
    build_primary_analytical_dataset,
    verify_primary_analytical_dataset,
)
from tcc_prf_severity.data.audit import run_audit
from tcc_prf_severity.data.interim import build_interim_dataset, verify_interim_dataset
from tcc_prf_severity.modeling.experimental_design import PRIMARY_METRIC, run_experimental_design
from tcc_prf_severity.modeling.logistic_baseline import run_logistic_baseline
from tcc_prf_severity.modeling.model_comparison import run_model_comparison
from tcc_prf_severity.modeling.model_selection import run_model_selection
from tcc_prf_severity.modeling.preprocessing import run_preprocessing_validation
from tcc_prf_severity.modeling.random_forest_baseline import run_random_forest_baseline
from tcc_prf_severity.modeling.threshold_selection import run_threshold_selection
from tcc_prf_severity.modeling.xgboost_baseline import (
    EXPECTED_XGBOOST_VERSION,
    run_xgboost_baseline,
)


def audit_main() -> None:
    summary = run_audit(RAW_DIR, AUDIT_DIR)
    combined = summary["combined"]
    print("Auditoria concluída.")
    print(f"Registros: {combined['rows']:,}".replace(",", "."))
    print(f"Graves (target_grave): {combined['graves']:,}".replace(",", "."))
    print(f"Taxa de graves: {combined['grave_rate']:.2%}")
    print(f"Relatórios: {AUDIT_DIR}")


def build_interim_main() -> None:
    result = build_interim_dataset()
    print("Dataset intermediário criado.")
    print(f"Registros: {result.rows:,}".replace(",", "."))
    print(f"Colunas: {result.columns}")
    print(f"Graves: {result.graves:,}".replace(",", "."))
    print(f"Taxa de graves: {result.grave_rate:.2%}")
    print(f"Parquet: {result.parquet_path}")
    print(f"Manifesto: {result.manifest_path}")


def verify_interim_main() -> None:
    result = verify_interim_dataset()
    print("Dataset intermediário verificado.")
    print(f"Registros: {result.rows:,}".replace(",", "."))
    print(f"Colunas: {result.columns}")
    print(f"Graves: {result.graves:,}".replace(",", "."))
    print(f"Taxa de graves: {result.grave_rate:.2%}")
    print(f"SHA-256: {result.sha256}")
    print(f"RAW sources: {result.raw_sources_verified}/5 OK")
    print("Manifesto: OK")


def build_analytical_main() -> None:
    result = build_primary_analytical_dataset()
    print("Dataset analítico principal criado.")
    print(f"Registros: {result.rows:,}".replace(",", "."))
    print(f"Colunas: {result.columns}")
    print(f"Predictors físicos: {result.predictor_columns}")
    print(f"Graves: {result.graves:,}".replace(",", "."))
    print(f"Taxa de graves: {result.grave_rate:.2%}")
    print(f"Valores nulos: {sum(result.missingness.values()):,}".replace(",", "."))
    print(f"Parquet: {result.parquet_path}")
    print(f"Esquema: {result.schema_path}")
    print(f"Manifesto: {result.manifest_path}")


def verify_analytical_main() -> None:
    result = verify_primary_analytical_dataset()
    print("Dataset analítico principal verificado.")
    print(f"Registros: {result.rows:,}".replace(",", "."))
    print(f"Colunas: {result.columns}")
    print(f"Predictors físicos: {result.predictor_columns}")
    print(f"Graves: {result.graves:,}".replace(",", "."))
    print(f"Taxa de graves: {result.grave_rate:.2%}")
    print(f"IDs únicos: {result.unique_ids:,}".replace(",", "."))
    print(f"Valores nulos: {sum(result.missingness.values()):,}".replace(",", "."))
    print(f"SHA-256: {result.sha256}")
    print("Contrato 3B: OK")
    print("Esquema: OK")
    print("Manifesto: OK")


def design_experiment_main() -> None:
    result = run_experimental_design()
    design = result.design
    print("Fase 3D concluída.")
    print("Desenvolvimento: 2021-2024")
    print("Avaliação temporal final: 2025")
    print("Folds internos:")
    for fold in design.folds:
        train = "-".join((str(fold.train_years[0]), str(fold.train_years[-1])))
        if len(fold.train_years) == 1:
            train = str(fold.train_years[0])
        print(f"{fold.fold}: {train} -> {fold.validation_year}")
    print(f"Predictors físicos: {len(design.predictors)}")
    print(f"Métrica principal futura: {PRIMARY_METRIC}")
    print("Threshold: definido futuramente somente por OOF de 2022-2024")
    print("Nenhum modelo treinado.")
    print("2025 não foi usado para fitting ou otimização.")
    print(f"Tabelas: {result.table_paths[0].parent}")


def validate_preprocessing_main() -> None:
    result = run_preprocessing_validation()
    validation = result.validation
    groups = validation.groups
    print("Fase 3E concluída.")
    print(f"Folds validados: {len(validation.folds)}")
    print("2025 utilizado: não")
    print(f"Categóricas: {len(groups.categorical)}")
    print(f"Numéricas: {len(groups.numeric)}")
    print(f"Binárias: {len(groups.binary)}")
    print(f"Predictors físicos: {len(groups.predictors)}")
    for fold in validation.folds:
        years = "-".join((str(fold.fit_years[0]), str(fold.fit_years[-1])))
        if len(fold.fit_years) == 1:
            years = str(fold.fit_years[0])
        print(
            f"Fold {fold.fold}: train {years} -> validation {fold.validation_year}; "
            f"features transformadas: {fold.output_feature_count}; sparse: sim"
        )
    print("Unknown categories foram toleradas e auditadas.")
    print("Nenhum modelo treinado.")
    print("Nenhum preprocessor fitado foi persistido.")
    print(f"Tabelas: {result.table_paths[0].parent}")


def run_logistic_baseline_main() -> None:
    run = run_logistic_baseline()
    result = run.result
    summary = {str(row["key"]): str(row["value"]) for row in result.summary.iter_rows(named=True)}
    print("Fase 4A — Regressão Logística")
    for fold in result.fold_results:
        train = "-".join((str(fold.train_years[0]), str(fold.train_years[-1])))
        if len(fold.train_years) == 1:
            train = str(fold.train_years[0])
        print(
            f"Fold {fold.fold}: {train} -> {fold.validation_year}; "
            f"AP: {fold.average_precision:.6f}; iterações: {fold.iterations}"
        )
    print(f"AP média não ponderada: {float(summary['ap_unweighted_mean']):.6f}")
    print(f"AP desvio padrão populacional: {float(summary['ap_population_std']):.6f}")
    print("2025 utilizado: não")
    print("Threshold selecionado: não")
    print("Todos os folds convergiram: sim")
    print(f"OOF: {run.oof_path}")
    print(f"OOF SHA-256: {run.oof_sha256}")
    print(f"Tabelas: {run.table_paths[0].parent}")


def run_random_forest_baseline_main() -> None:
    run = run_random_forest_baseline()
    result = run.result
    summary = {str(row["key"]): str(row["value"]) for row in result.summary.iter_rows(named=True)}
    print("Fase 4B — Random Forest")
    for fold in result.fold_results:
        train = "-".join((str(fold.train_years[0]), str(fold.train_years[-1])))
        if len(fold.train_years) == 1:
            train = str(fold.train_years[0])
        print(
            f"Fold {fold.fold}: {train} -> {fold.validation_year}; "
            f"AP: {fold.average_precision:.6f}; profundidade média: {fold.mean_tree_depth:.2f}"
        )
    print(f"AP média não ponderada: {float(summary['ap_unweighted_mean']):.6f}")
    print(f"AP desvio padrão populacional: {float(summary['ap_population_std']):.6f}")
    print("2025 utilizado: não")
    print("Threshold selecionado: não")
    print("Tuning realizado: não")
    print(f"OOF: {run.oof_path}")
    print(f"OOF SHA-256: {run.oof_sha256}")
    print(f"Tabelas: {run.table_paths[0].parent}")


def run_xgboost_baseline_main() -> None:
    run = run_xgboost_baseline()
    result = run.result
    summary = {str(row["key"]): str(row["value"]) for row in result.summary.iter_rows(named=True)}
    print("Fase 4C — XGBoost")
    print(f"XGBoost: {EXPECTED_XGBOOST_VERSION}")
    for fold in result.fold_results:
        train = "-".join((str(fold.train_years[0]), str(fold.train_years[-1])))
        if len(fold.train_years) == 1:
            train = str(fold.train_years[0])
        print(
            f"Fold {fold.fold}: {train} -> {fold.validation_year}; "
            f"AP: {fold.average_precision:.6f}; rounds: {fold.completed_boosting_rounds}"
        )
    print(f"AP média não ponderada: {float(summary['ap_unweighted_mean']):.6f}")
    print(f"AP desvio padrão populacional: {float(summary['ap_population_std']):.6f}")
    print("300 rounds completos: sim")
    print("2025 utilizado: não")
    print("Threshold selecionado: não")
    print("Tuning realizado: não")
    print("Early stopping: não")
    print(f"OOF: {run.oof_path}")
    print(f"OOF SHA-256: {run.oof_sha256}")
    print(f"Tabelas: {run.table_paths[0].parent}")


def compare_models_main() -> None:
    run = run_model_comparison()
    comparison = run.result.model_comparison
    labels = {
        "phase_4a_logistic_baseline": "Logistic Regression",
        "phase_4b_random_forest_baseline": "Random Forest",
        "phase_4c_xgboost_baseline": "XGBoost",
    }
    print("Fase 4D — Comparação de modelos")
    for row in comparison.iter_rows(named=True):
        print(f"{labels[str(row['model_id'])]}: AP média {float(row['ap_unweighted_mean']):.6f}")
    largest_mean = comparison.sort("ap_unweighted_mean", descending=True).row(0, named=True)
    smallest_std = comparison.sort("ap_population_std").row(0, named=True)
    largest_fold3 = comparison.sort("ap_fold3", descending=True).row(0, named=True)
    print(f"Maior AP média observada: {labels[str(largest_mean['model_id'])]}")
    print(f"Menor AP std observada: {labels[str(smallest_std['model_id'])]}")
    print(f"Maior AP Fold 3 observada: {labels[str(largest_fold3['model_id'])]}")
    print("Seleção final realizada: não")
    print("2025 utilizado: não")
    print(f"Tabelas: {run.table_paths[0].parent}")


def select_model_main() -> None:
    run = run_model_selection()
    result = run.result
    labels = {
        "phase_4a_logistic_baseline": "Logistic Regression",
        "phase_4b_random_forest_baseline": "Random Forest",
        "phase_4c_xgboost_baseline": "XGBoost",
    }
    selected = result.comparison.filter(pl.col("model_id") == result.selected_model_id).row(
        0, named=True
    )
    print("Fase 4E — Seleção formal")
    print("Critério: Average Precision — média não ponderada dos 3 folds")
    for row in result.comparison.iter_rows(named=True):
        print(f"{labels[str(row['model_id'])]}: AP média {float(row['ap_unweighted_mean']):.6f}")
    print(f"Modelo selecionado: {labels[result.selected_model_id]}")
    print("Motivo: maior AP média não ponderada nos folds internos.")
    print(f"AP Fold 3: {float(selected['ap_fold3']):.6f}")
    print(f"AP std: {float(selected['ap_population_std']):.6f}")
    print("2025 utilizado: não")
    print("Threshold selecionado: não")
    print("Refit realizado: não")
    print("Próximo passo: Fase 4F — threshold OOF")
    print(f"Tabelas: {run.table_paths[0].parent}")


def select_threshold_main() -> None:
    run = run_threshold_selection()
    result = run.result
    selected = result.search.selected
    reference = result.reference
    print("Fase 4F — Threshold OOF")
    print("Modelo: XGBoost")
    print(f"OOF: 2022-2024; {selected.rows} ocorrências")
    print("Objetivo: maximizar F1 da classe grave")
    print(f"Threshold selecionado: {selected.threshold}")
    print(f"Precision: {selected.precision:.6f}")
    print(f"Recall: {selected.recall:.6f}")
    print(f"F1: {selected.f1:.6f}")
    print("Referência 0.5:")
    print(f"F1: {reference.f1:.6f}")
    print(f"Recall: {reference.recall:.6f}")
    print(f"Precision: {reference.precision:.6f}")
    print("2025 utilizado: não")
    print("Refit realizado: não")
    print("Próximo passo: Fase 4G — refit 2021-2024")
    print(f"Tabelas: {run.table_paths[0].parent}")


def eda_general_main() -> None:
    result = run_general_analysis()
    analysis = result.analysis
    summary = analysis.annual_summary
    stability = analysis.stability
    rows = int(summary.get_column("total_occurrences").sum())
    graves = int(summary.get_column("severe_occurrences").sum())
    years = summary.get_column("source_year")

    print("Fase 2A concluída.")
    print(f"Registros: {rows:,}".replace(",", "."))
    print(f"Período: {years.min()}-{years.max()}")
    print(f"Graves: {graves:,}".replace(",", "."))
    print(f"Taxa global: {stability.weighted_global_rate_percent:.2f}%")
    print(f"Menor taxa anual: {stability.minimum_annual_rate_percent:.2f}%")
    print(f"Maior taxa anual: {stability.maximum_annual_rate_percent:.2f}%")
    print(f"Tabelas: {result.table_paths[0].parent}")
    print(f"Figuras: {result.figure_paths[0].parent}")


def eda_temporal_main() -> None:
    result = run_temporal_analysis()
    analysis = result.analysis

    def maximum(table: object, metric: str) -> dict[str, Any]:
        import polars as pl

        if not isinstance(table, pl.DataFrame):
            raise TypeError("Resumo temporal inválido.")
        return table.sort(metric, descending=True).row(0, named=True)

    def count(value: Any) -> str:
        return f"{int(value):,}".replace(",", ".")

    def rate(row: dict[str, Any]) -> str:
        return f"{float(row['severe_rate_percent']):.2f}% (n={count(row['total_occurrences'])})"

    month_volume = maximum(analysis.month_summary, "total_occurrences")
    month_rate = maximum(analysis.month_summary, "severe_rate_percent")
    weekday_volume = maximum(analysis.weekday_summary, "total_occurrences")
    weekday_rate = maximum(analysis.weekday_summary, "severe_rate_percent")
    hour_volume = maximum(analysis.hour_summary, "total_occurrences")
    hour_rate = maximum(analysis.hour_summary, "severe_rate_percent")
    phase_rate = maximum(analysis.day_phase_summary, "severe_rate_percent")
    rows = int(analysis.month_summary.get_column("total_occurrences").sum())

    print("Fase 2B concluída.")
    print(f"Registros: {count(rows)}")
    print("Período: 2021-2025")
    print(
        f"Mês com maior volume: {month_volume['month_name']} "
        f"({count(month_volume['total_occurrences'])})"
    )
    print(f"Mês com maior proporção grave: {month_rate['month_name']} — {rate(month_rate)}")
    print(
        f"Dia com maior volume: {weekday_volume['dia_semana']} "
        f"({count(weekday_volume['total_occurrences'])})"
    )
    print(f"Dia com maior proporção grave: {weekday_rate['dia_semana']} — {rate(weekday_rate)}")
    print(
        f"Hora com maior volume: {hour_volume['hour']}h ({count(hour_volume['total_occurrences'])})"
    )
    print(f"Hora com maior proporção grave: {hour_rate['hour']}h — {rate(hour_rate)}")
    print(f"Fase do dia com maior proporção grave: {phase_rate['fase_dia']} — {rate(phase_rate)}")
    print(f"Tabelas: {result.table_paths[0].parent}")
    print(f"Figuras: {result.figure_paths[0].parent}")


def eda_geographic_main() -> None:
    import polars as pl

    result = run_geographic_analysis()
    analysis = result.analysis

    def maximum(table: pl.DataFrame, metric: str) -> dict[str, Any]:
        return table.sort(metric, descending=True).row(0, named=True)

    def count(value: Any) -> str:
        return f"{int(value):,}".replace(",", ".")

    def rate(row: dict[str, Any]) -> str:
        return f"{float(row['severe_rate_percent']):.2f}% (n={count(row['total_occurrences'])})"

    macroregion_volume = maximum(analysis.macroregion_summary, "total_occurrences")
    uf_volume = maximum(analysis.uf_summary, "total_occurrences")
    uf_rate = maximum(analysis.uf_summary, "severe_rate_percent")
    br_volume = analysis.br_volume_top15.row(0, named=True)
    municipality_volume = analysis.municipality_volume_top15.row(0, named=True)
    br_rate = analysis.br_severe_rate_top15.row(0, named=True)
    municipality_rate = analysis.municipality_severe_rate_top15.row(0, named=True)
    br_zero = analysis.br_summary.filter(pl.col("br") == 0).row(0, named=True)
    rows = int(analysis.macroregion_summary.get_column("total_occurrences").sum())

    print("Fase 2C concluída.")
    print(f"Registros: {count(rows)}")
    print(
        f"Macrorregião com maior volume: {macroregion_volume['macroregion']} "
        f"({count(macroregion_volume['total_occurrences'])})"
    )
    print(f"UF com maior volume: {uf_volume['uf']} ({count(uf_volume['total_occurrences'])})")
    print(f"UF com maior proporção grave: {uf_rate['uf']} — {rate(uf_rate)}")
    print(f"BR com maior volume: {br_volume['br_label']} ({count(br_volume['total_occurrences'])})")
    print(
        f"Município/UF com maior volume: {municipality_volume['municipality_label']} "
        f"({count(municipality_volume['total_occurrences'])})"
    )
    print(f"BR com maior proporção grave entre n>=500: {br_rate['br_label']} — {rate(br_rate)}")
    print(
        "Município/UF com maior proporção grave entre n>=500: "
        f"{municipality_rate['municipality_label']} — {rate(municipality_rate)}"
    )
    print(f"BR 0: {count(br_zero['total_occurrences'])} registros preservados.")
    print(f"Tabelas: {result.table_paths[0].parent}")
    print(f"Figuras: {result.figure_paths[0].parent}")


def eda_road_environment_main() -> None:
    import polars as pl

    result = run_road_environment_analysis()
    analysis = result.analysis

    def highest_rate(table: pl.DataFrame) -> dict[str, Any]:
        return table.sort("severe_rate_percent", descending=True).row(0, named=True)

    def count(value: Any) -> str:
        return f"{int(value):,}".replace(",", ".")

    def rate(row: dict[str, Any]) -> str:
        return f"{float(row['severe_rate_percent']):.2f}% (n={count(row['total_occurrences'])})"

    road_type = highest_rate(analysis.road_type_summary)
    land_use = highest_rate(analysis.land_use_summary)
    direction = highest_rate(analysis.direction_summary)
    weather = analysis.weather_rate_highlights.row(0, named=True)
    layout_volume = analysis.road_layout_component_summary.row(0, named=True)
    layout_rate = analysis.road_layout_component_rate_highlights.row(0, named=True)
    not_informed = analysis.direction_summary.filter(pl.col("sentido_via") == "Não Informado").row(
        0, named=True
    )
    rows = int(analysis.road_type_summary.get_column("total_occurrences").sum())

    print("Fase 2D concluída.")
    print(f"Registros: {count(rows)}")
    print(f"Tipo de pista com maior proporção grave: {road_type['tipo_pista']} — {rate(road_type)}")
    print(f"Uso do solo com maior proporção grave: {land_use['uso_solo']} — {rate(land_use)}")
    print(f"Sentido com maior proporção grave: {direction['sentido_via']} — {rate(direction)}")
    print(f"Não Informado em sentido: {count(not_informed['total_occurrences'])} registros.")
    print(
        "Meteorologia informada com maior proporção entre n>=500: "
        f"{weather['condicao_metereologica']} — {rate(weather)}"
    )
    print(
        f"Componente de traçado com maior volume: {layout_volume['road_layout_component']} "
        f"({count(layout_volume['total_occurrences'])})"
    )
    print(
        "Componente com maior proporção entre n>=500: "
        f"{layout_rate['road_layout_component']} — {rate(layout_rate)}"
    )
    print(f"Tokens de traçado confirmados: {analysis.road_layout_tokens.height}")
    print(f"Tabelas: {result.table_paths[0].parent}")
    print(f"Figuras: {result.figure_paths[0].parent}")


def eda_occurrence_dynamics_main() -> None:
    import polars as pl

    result = run_occurrence_dynamics_analysis()
    analysis = result.analysis

    def count(value: Any) -> str:
        return f"{int(value):,}".replace(",", ".")

    def rate(row: dict[str, Any]) -> str:
        return f"{float(row['severe_rate_percent']):.2f}% (n={count(row['total_occurrences'])})"

    accident_type_volume = analysis.accident_type_volume_top15.row(0, named=True)
    accident_type_rate = analysis.accident_type_severe_rate_top15.row(0, named=True)
    cause_volume = analysis.cause_volume_top15.row(0, named=True)
    cause_rate = analysis.cause_severe_rate_top15.row(0, named=True)
    people = analysis.people_summary_statistics.row(0, named=True)
    vehicles = analysis.vehicle_summary_statistics.row(0, named=True)
    cause_taxonomy = analysis.taxonomy_diagnostics.filter(pl.col("dimension") == "cause")
    cause_annual = cause_taxonomy.filter(pl.col("scope") == "year").sort("source_year")
    cause_period = cause_taxonomy.filter(pl.col("scope") == "period").row(0, named=True)
    rows = int(analysis.accident_type_summary.get_column("total_occurrences").sum())

    print("Fase 2E concluída.")
    print(f"Registros: {count(rows)}")
    print(
        f"Tipo com maior volume: {accident_type_volume['tipo_acidente']} "
        f"({count(accident_type_volume['total_occurrences'])})"
    )
    print(
        "Tipo com maior proporção entre n>=500: "
        f"{accident_type_rate['tipo_acidente']} — {rate(accident_type_rate)}"
    )
    print(
        f"Causa registrada com maior volume: {cause_volume['causa_acidente']} "
        f"({count(cause_volume['total_occurrences'])})"
    )
    print(
        "Causa com maior proporção entre n>=500: "
        f"{cause_rate['causa_acidente']} — {rate(cause_rate)}"
    )
    print("Categorias de causa registradas:")
    for row in cause_annual.iter_rows(named=True):
        print(f"  {row['source_year']}: {row['distinct_categories']}")
    print(f"  União 2021-2025: {cause_period['union_categories']}")
    print(
        f"Pessoas: mediana {people['median']:.0f}; P95 {people['p95']:.0f}; "
        f"máximo {people['maximum']:.0f}."
    )
    print(
        f"Veículos: mediana {vehicles['median']:.0f}; P95 {vehicles['p95']:.0f}; "
        f"máximo {vehicles['maximum']:.0f}."
    )
    print(f"Tabelas: {result.table_paths[0].parent}")
    print(f"Figuras: {result.figure_paths[0].parent}")


def eda_severity_associations_main() -> None:
    result = run_severity_associations_analysis()
    analysis = result.analysis
    evidence = analysis.association_evidence_matrix
    eligibility = analysis.modeling_eligibility_matrix
    priorities = {
        str(row["scientific_priority"]): int(row["len"])
        for row in evidence.group_by("scientific_priority").len().iter_rows(named=True)
    }
    statuses = {
        str(row["modeling_eligibility_status"]): int(row["len"])
        for row in eligibility.group_by("modeling_eligibility_status").len().iter_rows(named=True)
    }
    largest = analysis.core_findings.row(0, named=True)

    print("Fase 2F concluída.")
    print(f"Achados centrais: {priorities.get('central', 0)}")
    print(f"Achados secundários: {priorities.get('secundário', 0)}")
    print(
        "Maior contraste central: "
        f"{largest['category_or_comparison']} — "
        f"{float(largest['absolute_difference_percentage_points']):.2f} p.p."
    )
    print(f"Persistência temporal: {largest['temporal_consistency_note']}")
    print(f"Features candidatas: {statuses.get('candidata', 0)}")
    print(f"Candidatas com cautela: {statuses.get('candidata_com_cautela', 0)}")
    print(f"Excluídas por leakage: {statuses.get('excluir_por_leakage', 0)}")
    print(f"Tabelas: {result.table_paths[0].parent}")
    print(f"Figuras: {result.figure_paths[0].parent}")
    print("Nenhum dataset de modelagem criado.")


def audit_temporal_drift_main() -> None:
    import polars as pl

    result = run_temporal_drift_analysis()
    analysis = result.analysis
    categorical = analysis.categorical_drift_summary.row(0, named=True)
    numeric = analysis.numeric_drift_summary.filter(
        pl.col("audit_method") == "development_decile_binned_tvd"
    ).row(0, named=True)
    unseen = (
        analysis.unseen_categories_2025.group_by("variable")
        .agg(pl.col("share_2025_percent").sum().alias("share"))
        .sort("share", descending=True)
    )
    type_row = analysis.categorical_drift_summary.filter(pl.col("variable") == "tipo_acidente").row(
        0, named=True
    )
    cause_row = analysis.categorical_drift_summary.filter(
        pl.col("variable") == "causa_acidente"
    ).row(0, named=True)

    print("Fase 3A concluída.")
    print("Período de desenvolvimento auditado: 2021-2024")
    print("Comparação temporal: 2025")
    print(f"Features auditadas: {analysis.drift_inventory.height}")
    print(f"Maior TVD categórica: {categorical['variable']} — {float(categorical['tvd']):.6f}")
    print(
        "Maior TVD numérica em bins: "
        f"{numeric['variable']} — {float(numeric['distribution_tvd']):.6f}"
    )
    print(f"Variáveis com categorias unseen em 2025: {unseen.height}")
    if not unseen.is_empty():
        largest_unseen = unseen.row(0, named=True)
        print(
            "Maior share unseen em 2025: "
            f"{largest_unseen['variable']} — {float(largest_unseen['share']):.6f}%"
        )
    print("Taxonomia:")
    print(
        f"  tipo_acidente: TVD={float(type_row['tvd']):.6f}; "
        f"novas={type_row['new_categories_2025']}; ausentes={type_row['missing_categories_2025']}"
    )
    print(
        f"  causa_acidente: TVD={float(cause_row['tvd']):.6f}; "
        f"novas={cause_row['new_categories_2025']}; ausentes={cause_row['missing_categories_2025']}"
    )
    print(f"Tabelas: {result.table_paths[0].parent}")
    print(f"Figuras: {result.figure_paths[0].parent}")
    print("Nenhum dataset de modelagem criado.")
    print("Nenhuma feature foi selecionada definitivamente.")
