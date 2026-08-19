"""Contratos físicos congelados para a exportação estática da Fase 6B."""

from dataclasses import dataclass

SCHEMA_VERSION = "1"
EXPECTED_BRANCH = "feat/phase-6b-dashboard-data-export"
DATA_PERIOD = {"start_year": 2021, "end_year": 2025}
SOURCE_SCOPE = "Acidentes registrados pela PRF em rodovias federais, 2021-2025."
TARGET_DEFINITION = "target_grave = (mortos > 0) OR (feridos_graves > 0)"

EXPOSURE_CAVEAT = (
    "Os percentuais representam a proporção de ocorrências graves entre acidentes "
    "registrados pela PRF. Sem denominador de exposição ao tráfego, esses valores não "
    "representam risco de ocorrência de acidente."
)
ASSOCIATION_CAVEAT = "Associações descritivas não devem ser interpretadas como causais."
FROZEN_RESULT_CAVEAT = (
    "Resultados de machine learning são congelados e não são recalculados no dashboard."
)
SHAP_CAVEAT = "Contribuições Tree SHAP descrevem o modelo e não representam efeitos causais."

TEMPORAL_DIMENSIONS = ("source_year", "dia_semana", "hour")
CONTEXTUAL_DIMENSIONS = (
    "source_year",
    "tipo_pista",
    "condicao_metereologica",
    "uso_solo",
)
GEOGRAPHY_DIMENSIONS = ("source_year", "uf", "br")
EXPLORATORY_MEASURES = (
    "total_occurrences",
    "severe_occurrences",
    "non_severe_occurrences",
    "severe_proportion",
)


@dataclass(frozen=True)
class AssetSpec:
    """Contrato de uma parte física associada a um asset lógico da 6A."""

    asset_id: str
    part_id: str
    path: str
    purpose: str
    scientific_status: str
    source_artifacts: tuple[str, ...]
    required_caveats: tuple[str, ...] = ()


ASSET_SPECS = (
    AssetSpec(
        "META",
        "default",
        "meta.json",
        "Metadados globais e cautelas científicas.",
        "DOCUMENTATION",
        (
            "docs/PHASE_1_ACCEPTANCE.md",
            "docs/PHASE_3B_FEATURE_POLICY.md",
            "reports/tables/tcc/T1_population_characterization.csv",
        ),
    ),
    AssetSpec(
        "OVERVIEW",
        "default",
        "overview/summary.json",
        "Resumo populacional geral e anual publicado.",
        "MIXED",
        (
            "reports/tables/tcc/T1_population_characterization.csv",
            "data/processed/prf_primary_analytical_2021_2025.parquet",
        ),
        (EXPOSURE_CAVEAT,),
    ),
    AssetSpec(
        "EXPLORATION",
        "temporal",
        "exploration/temporal.json",
        "Agregações observadas do escopo temporal.",
        "EXPLORATORY",
        (
            "data/processed/prf_primary_analytical_2021_2025.parquet",
            "reports/tables/phase_3c_analytical_schema.csv",
        ),
        (EXPOSURE_CAVEAT, ASSOCIATION_CAVEAT),
    ),
    AssetSpec(
        "EXPLORATION",
        "contextual",
        "exploration/contextual.json",
        "Agregações observadas do escopo contextual.",
        "EXPLORATORY",
        (
            "data/processed/prf_primary_analytical_2021_2025.parquet",
            "reports/tables/phase_3c_analytical_schema.csv",
        ),
        (EXPOSURE_CAVEAT, ASSOCIATION_CAVEAT),
    ),
    AssetSpec(
        "GEOGRAPHY",
        "default",
        "geography/geography.json",
        "Agregações observadas por ano, UF e BR.",
        "EXPLORATORY",
        (
            "data/processed/prf_primary_analytical_2021_2025.parquet",
            "reports/tables/phase_3c_analytical_schema.csv",
        ),
        (EXPOSURE_CAVEAT, ASSOCIATION_CAVEAT),
    ),
    AssetSpec(
        "MODEL_COMPARISON",
        "default",
        "models/model_comparison.json",
        "Comparação e seleção publicadas das três famílias de modelos.",
        "FROZEN_RESULT",
        (
            "reports/tables/phase_4d_model_comparison.csv",
            "reports/tables/phase_4d_pairwise_ap_deltas.csv",
            "reports/tables/phase_4e_model_selection.csv",
        ),
        (FROZEN_RESULT_CAVEAT,),
    ),
    AssetSpec(
        "TEMPORAL_VALIDATION",
        "default",
        "validation/temporal_validation.json",
        "Métricas publicadas dos nove pares modelo/fold.",
        "FROZEN_RESULT",
        (
            "reports/tables/phase_4d_fold_comparison.csv",
            "reports/tables/phase_4d_temporal_stability.csv",
        ),
        (FROZEN_RESULT_CAVEAT,),
    ),
    AssetSpec(
        "FINAL_2025",
        "default",
        "models/final_2025.json",
        "Avaliação temporal final publicada para 2025.",
        "FROZEN_RESULT",
        (
            "reports/tables/tcc/T2_final_2025_evaluation.csv",
            "reports/tables/phase_4h_final_evaluation.csv",
            "reports/tables/phase_4h_development_comparison.csv",
        ),
        (FROZEN_RESULT_CAVEAT,),
    ),
    AssetSpec(
        "CALIBRATION_2025",
        "default",
        "models/calibration_2025.json",
        "Faixas quantílicas de calibração publicadas para 2025.",
        "FROZEN_RESULT",
        ("reports/tables/phase_4h_calibration.csv",),
        (FROZEN_RESULT_CAVEAT,),
    ),
    AssetSpec(
        "THRESHOLD_2025",
        "default",
        "threshold/threshold_2025.json",
        "Ponto de operação congelado e avaliação publicada em 2025.",
        "FROZEN_RESULT",
        (
            "reports/tables/phase_4f_threshold_selection.csv",
            "reports/tables/phase_4h_threshold_evaluation.csv",
        ),
        (FROZEN_RESULT_CAVEAT,),
    ),
    AssetSpec(
        "INTERPRETATION",
        "source_predictors",
        "interpretation/source_predictors.json",
        "Contribuições Tree SHAP publicadas por variável de origem.",
        "FROZEN_RESULT",
        ("reports/tables/phase_4i_global_feature_contributions.csv",),
        (FROZEN_RESULT_CAVEAT, SHAP_CAVEAT),
    ),
    AssetSpec(
        "INTERPRETATION",
        "transformed_top15",
        "interpretation/transformed_top15.json",
        "Top 15 publicado de features transformadas.",
        "FROZEN_RESULT",
        (
            "reports/tables/tcc/A1_top15_transformed_features.csv",
            "reports/tables/phase_4i_transformed_feature_contributions.csv",
        ),
        (FROZEN_RESULT_CAVEAT, SHAP_CAVEAT),
    ),
    AssetSpec(
        "METHODOLOGY_DESIGN",
        "default",
        "methodology/design.json",
        "Contrato estruturado do desenho experimental temporal.",
        "DOCUMENTATION",
        (
            "reports/tables/phase_3d_temporal_folds.csv",
            "reports/tables/phase_3d_experimental_contract.csv",
            "docs/PHASE_3D_EXPERIMENTAL_DESIGN.md",
        ),
    ),
    AssetSpec(
        "METHODOLOGY_FEATURES",
        "default",
        "methodology/features.json",
        "Contrato estruturado das variáveis e do preprocessing.",
        "DOCUMENTATION",
        (
            "reports/tables/tcc/M2_features_preprocessing.csv",
            "reports/tables/phase_3b_primary_feature_set.csv",
            "reports/tables/phase_3c_analytical_schema.csv",
            "reports/tables/phase_3e_preprocessing_contract.csv",
        ),
    ),
)

MANAGED_ASSET_PATHS = tuple(spec.path for spec in ASSET_SPECS)
MANAGED_PATHS = (*MANAGED_ASSET_PATHS, "manifest.json")
LOGICAL_ASSET_IDS = tuple(dict.fromkeys(spec.asset_id for spec in ASSET_SPECS))

PHASE_6A_CONTRACTS = (
    "docs/PHASE_6A_DASHBOARD_ARCHITECTURE.md",
    "reports/tables/phase_6a_repository_layout.csv",
    "reports/tables/phase_6a_route_matrix.csv",
    "reports/tables/phase_6a_filter_contract.csv",
    "reports/tables/phase_6a_data_asset_contract.csv",
    "reports/tables/phase_6a_scientific_boundary_matrix.csv",
    "reports/tables/phase_6a_architecture_checklist.csv",
)
