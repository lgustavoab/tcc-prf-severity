export type ScientificStatus =
  | "MIXED"
  | "EXPLORATORY"
  | "FROZEN_RESULT"
  | "DOCUMENTATION";

export interface AssetMetadata {
  schema_version: "1";
  asset_id: string;
  part_id: string;
  scientific_status: ScientificStatus;
  source_artifacts: string[];
  required_caveats: string[];
}

export interface ManifestAsset {
  asset_id: string;
  part_id: string;
  path: string;
  purpose: string;
  scientific_status: ScientificStatus;
  source_artifacts: string[];
  row_count: number;
  size_bytes: number;
  sha256: string;
  generation_status: string;
}

export interface Manifest {
  schema_version: "1";
  generated_at: string;
  data_period: { start_year: number; end_year: number };
  source_scope: string;
  target_definition: string;
  assets: ManifestAsset[];
}

export interface Metadata {
  metadata: AssetMetadata;
  data_period: { start_year: number; end_year: number };
  source_scope: string;
  target_definition: string;
  scientific_scope: { exploratory: string; frozen_results: string };
  caveats: string[];
}

export interface ExploratoryCounts {
  total_occurrences: number;
  severe_occurrences: number;
  non_severe_occurrences: number;
  severe_proportion: number;
}

export interface OverviewRow extends ExploratoryCounts {
  scope: string;
  source_year: number | null;
}

export interface OverviewAsset {
  metadata: AssetMetadata;
  filters: { years: number[] };
  summary: OverviewRow;
  data: OverviewRow[];
}

export interface ExplorationTemporalRow extends ExploratoryCounts {
  source_year: number;
  dia_semana: string;
  hour: number;
}

export interface ExplorationTemporalAsset {
  metadata: AssetMetadata;
  dimensions: string[];
  filters: { years: number[]; weekdays: string[]; hours: number[] };
  data: ExplorationTemporalRow[];
}

export interface ExplorationContextualRow extends ExploratoryCounts {
  source_year: number;
  tipo_pista: string;
  condicao_metereologica: string;
  uso_solo: string;
}

export interface ExplorationContextualAsset {
  metadata: AssetMetadata;
  dimensions: string[];
  filters: {
    years: number[];
    road_types: string[];
    weather_conditions: string[];
    land_use: string[];
  };
  data: ExplorationContextualRow[];
}

export interface GeographyRow extends ExploratoryCounts {
  source_year: number;
  uf: string;
  br: number;
}

export interface GeographyAsset {
  metadata: AssetMetadata;
  dimensions: string[];
  filters: {
    years: number[];
    ufs: string[];
    brs: number[];
    br_by_uf: Record<string, number[]>;
  };
  data: GeographyRow[];
}

export interface ModelComparisonAsset {
  metadata: AssetMetadata;
  selection_metric: string;
  selection_aggregation: string;
  selected_model_id: string;
  data: Array<{
    model_id: string;
    model_family: string;
    mean_average_precision: number;
    ap_standard_deviation: number;
    mean_roc_auc: number;
    mean_brier_score: number;
    primary_metric_rank: number;
    ap_fold3_rank: number;
    selection_status: string;
  }>;
  pairwise_ap_deltas: Array<{
    model_a: string;
    model_b: string;
    ap_delta_fold1: number;
    ap_delta_fold2: number;
    ap_delta_fold3: number;
    ap_mean_delta: number;
  }>;
}

export interface TemporalValidationAsset {
  metadata: AssetMetadata;
  validation_year_role: string;
  data: Array<{
    fold: number;
    validation_year: number;
    model_id: string;
    average_precision: number;
    roc_auc: number;
    brier_score: number;
    validation_positive_rate: number;
  }>;
  temporal_stability: Array<{
    model_id: string;
    ap_min: number;
    ap_max: number;
    ap_range: number;
    ap_standard_deviation: number;
    fold1_to_fold2_delta: number;
    fold2_to_fold3_delta: number;
  }>;
}

export interface Final2025Asset {
  metadata: AssetMetadata;
  selected_model_id: string;
  training_period: string;
  final_test_year: number;
  final_rows: number;
  data: Array<{
    metric: string;
    development_reference: number;
    final_2025_value: number;
    delta_final_minus_development: number;
    reference_description: string;
  }>;
  development_comparison: Array<{
    metric: string;
    development_reference: string;
    development_value: number;
    final_2025_value: number;
    delta_final_minus_development: number;
  }>;
}

export interface Calibration2025Asset {
  metadata: AssetMetadata;
  data: Array<{
    quantile_bin: number;
    bin_count: number;
    probability_min: number;
    probability_max: number;
    mean_predicted_probability: number;
    observed_severe_proportion: number;
  }>;
}

export interface Threshold2025Asset {
  metadata: AssetMetadata;
  threshold_role: string;
  data: Array<{
    threshold: number;
    rows: number;
    actual_positive: number;
    actual_negative: number;
    predicted_positive: number;
    predicted_negative: number;
    positive_precision: number;
    recall: number;
    f1: number;
    true_negative: number;
    false_positive: number;
    false_negative: number;
    true_positive: number;
  }>;
}

export interface InterpretationSourceAsset {
  metadata: AssetMetadata;
  data: Array<{
    rank: number;
    source_predictor: string;
    predictor_group: string;
    transformed_feature_cardinality: number;
    mean_absolute_shap: number;
    mean_signed_margin_contribution: number;
    contribution_share: number;
  }>;
}

export interface InterpretationTransformedAsset {
  metadata: AssetMetadata;
  data: Array<{
    rank: number;
    transformed_feature: string;
    source_predictor: string;
    predictor_group: string;
    category_or_level: string | null;
    mean_absolute_shap: number;
    mean_signed_margin_contribution: number;
  }>;
}

export interface MethodologyDesignAsset {
  metadata: AssetMetadata;
  data: Array<{
    fold: number;
    train_years: number[];
    validation_year: number;
    train_rows: number;
    validation_rows: number;
    train_severe: number;
    validation_severe: number;
  }>;
  contract: Array<{ key: string; value: string; rationale: string }>;
}

export interface MethodologyFeaturesAsset {
  metadata: AssetMetadata;
  data: Array<{
    feature: string;
    source: string;
    representation: string;
    rationale: string;
    expected_future_preprocessing: string;
  }>;
  preprocessing_groups: Array<{
    group: string;
    source_features: string;
    transformer: string;
    learned_parameters: string;
    fit_scope: string;
    unknown_policy: string;
    output_type: string;
    notes: string;
  }>;
  physical_predictors: Array<{
    column: string;
    role: string;
    conceptual_feature: string;
    source: string;
    derivation: string;
    dtype: string;
    nullable: string;
    allowed_values_note: string;
    included_in_model_matrix: string;
  }>;
  published_summary: Array<{
    Grupo: string;
    "Predictors físicos": string;
    "Representações conceituais": string;
    Preprocessing: string;
    "Política adicional": string;
  }>;
}
