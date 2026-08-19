from __future__ import annotations

import json
import os
import pickle
import platform
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted
from xgboost import XGBClassifier

from tcc_prf_severity.config import (
    ARTIFACTS_DIR,
    EXPERIMENTAL_CONTRACT_PATH,
    PREPROCESSING_CONTRACT_PATH,
    PRIMARY_ANALYTICAL_MANIFEST_PATH,
    PRIMARY_ANALYTICAL_PARQUET_PATH,
    PRIMARY_ANALYTICAL_SCHEMA_PATH,
    PROJECT_ROOT,
    TABLES_DIR,
)
from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.modeling.experimental_design import (
    DEVELOPMENT_YEARS,
    METADATA_COLUMNS,
    TARGET_COLUMN,
    build_experimental_contract,
    load_predictors_from_schema,
)
from tcc_prf_severity.modeling.model_comparison import XGBOOST_MODEL_ID
from tcc_prf_severity.modeling.preprocessing import (
    PreprocessingGroups,
    build_preprocessing_contract,
    load_preprocessing_groups,
)
from tcc_prf_severity.modeling.threshold_selection import SELECTED_MODEL_FAMILY
from tcc_prf_severity.modeling.xgboost_baseline import (
    build_xgboost_model_contract,
    build_xgboost_pipeline,
)

FROZEN_THRESHOLD_TEXT = "0.23723246157169342"
EXPECTED_TRAINING_ROWS = 270_095
EXPECTED_TRAINING_POSITIVE = 76_364
EXPECTED_PREDICTOR_COUNT = 22
EXPECTED_BOOSTING_ROUNDS = 300
FINAL_PIPELINE_PATH = ARTIFACTS_DIR / "models" / "phase_4g_xgboost_final_pipeline.pkl"
PHASE_4E_DOCUMENT_PATH = PROJECT_ROOT / "docs" / "PHASE_4E_MODEL_SELECTION.md"
PHASE_4F_DOCUMENT_PATH = PROJECT_ROOT / "docs" / "PHASE_4F_THRESHOLD_SELECTION.md"
PREMODELING_ACCEPTANCE_PATH = PROJECT_ROOT / "docs" / "PHASE_3_PREMODELING_ACCEPTANCE.md"

PipelineFactory = Callable[[PreprocessingGroups], Pipeline]


@dataclass(frozen=True)
class FinalRefitContracts:
    model_selection: dict[str, str]
    threshold_selection: dict[str, str]
    model_contract: dict[str, str]
    experimental_contract: pl.DataFrame
    preprocessing_contract: pl.DataFrame
    development_partition: dict[str, Any]
    analytical_manifest: dict[str, Any]


@dataclass(frozen=True)
class FinalFitAudit:
    pipeline: Pipeline
    training_rows: int
    training_unique_ids: int
    training_positive: int
    training_negative: int
    training_positive_rate: float
    predictor_count: int
    transformed_feature_count: int
    configured_boosting_rounds: int
    completed_boosting_rounds: int


@dataclass(frozen=True)
class FinalRefitResult:
    audit: FinalFitAudit
    frozen_threshold: float
    artifact_path: Path
    artifact_sha256: str
    artifact_size_bytes: int
    manifest: pl.DataFrame
    checklist: pl.DataFrame


@dataclass(frozen=True)
class FinalRefitRun:
    result: FinalRefitResult
    table_paths: tuple[Path, ...]


def _key_value_mapping(table: pl.DataFrame, source: str) -> dict[str, str]:
    if not {"key", "value"}.issubset(table.columns):
        raise ValueError(f"Tabela key/value inválida: {source}.")
    selected = table.select("key", "value")
    if selected.get_column("key").n_unique() != selected.height:
        raise ValueError(f"Chaves duplicadas em {source}.")
    return {str(row["key"]): str(row["value"]) for row in selected.iter_rows(named=True)}


def load_final_refit_contracts(
    tables_dir: Path = TABLES_DIR,
    experimental_contract_path: Path = EXPERIMENTAL_CONTRACT_PATH,
    preprocessing_contract_path: Path = PREPROCESSING_CONTRACT_PATH,
    analytical_manifest_path: Path = PRIMARY_ANALYTICAL_MANIFEST_PATH,
    phase_4e_document_path: Path = PHASE_4E_DOCUMENT_PATH,
    phase_4f_document_path: Path = PHASE_4F_DOCUMENT_PATH,
    premodeling_acceptance_path: Path = PREMODELING_ACCEPTANCE_PATH,
) -> FinalRefitContracts:
    paths = {
        "seleção 4E": tables_dir / "phase_4e_model_selection.csv",
        "threshold 4F": tables_dir / "phase_4f_threshold_selection.csv",
        "contrato XGBoost 4C": tables_dir / "phase_4c_xgboost_model_contract.csv",
        "contrato experimental 3D": experimental_contract_path,
        "contrato de preprocessing 3E": preprocessing_contract_path,
        "partições 3D": tables_dir / "phase_3d_partition_summary.csv",
        "manifesto analítico 3C": analytical_manifest_path,
        "documento 4E": phase_4e_document_path,
        "documento 4F": phase_4f_document_path,
        "aceite pré-modelagem 3F": premodeling_acceptance_path,
    }
    missing = [f"{name}: {path}" for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Fontes autoritativas ausentes: {missing}")
    partitions = pl.read_csv(paths["partições 3D"])
    development = partitions.filter(
        (pl.col("partition_id") == "development") & (pl.col("partition_role") == "development")
    )
    if development.height != 1:
        raise ValueError("Partição autoritativa de desenvolvimento deve possuir uma linha.")
    with paths["manifesto analítico 3C"].open(encoding="utf-8") as file:
        analytical_manifest = json.load(file)
    if not isinstance(analytical_manifest, dict):
        raise ValueError("Manifesto analítico 3C inválido.")
    return FinalRefitContracts(
        model_selection=_key_value_mapping(
            pl.read_csv(paths["seleção 4E"]), str(paths["seleção 4E"])
        ),
        threshold_selection=_key_value_mapping(
            pl.read_csv(paths["threshold 4F"]), str(paths["threshold 4F"])
        ),
        model_contract=_key_value_mapping(
            pl.read_csv(paths["contrato XGBoost 4C"]), str(paths["contrato XGBoost 4C"])
        ),
        experimental_contract=pl.read_csv(paths["contrato experimental 3D"]),
        preprocessing_contract=pl.read_csv(paths["contrato de preprocessing 3E"]),
        development_partition=development.row(0, named=True),
        analytical_manifest=analytical_manifest,
    )


def validate_final_refit_contracts(
    contracts: FinalRefitContracts,
    groups: PreprocessingGroups,
    analytical_path: Path,
) -> None:
    expected_4e = {
        "selection_status": "selected",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "development_period": "2021-2024",
        "final_test_year": "2025_reserved",
        "final_test_used": "false",
        "refit_performed": "false",
    }
    expected_4f = {
        "selection_status": "selected",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "selected_threshold": FROZEN_THRESHOLD_TEXT,
        "final_test_year": "2025_reserved",
        "final_test_used": "false",
        "refit_performed": "false",
    }
    divergences_4e = {
        key: (contracts.model_selection.get(key), expected)
        for key, expected in expected_4e.items()
        if contracts.model_selection.get(key) != expected
    }
    divergences_4f = {
        key: (contracts.threshold_selection.get(key), expected)
        for key, expected in expected_4f.items()
        if contracts.threshold_selection.get(key) != expected
    }
    if divergences_4e or divergences_4f:
        raise ValueError(
            "Seleções congeladas 4E/4F incompatíveis com o refit: "
            f"4E={divergences_4e}; 4F={divergences_4f}."
        )

    expected_model_contract = _key_value_mapping(
        build_xgboost_model_contract(), "factory oficial XGBoost 4C"
    )
    if contracts.model_contract != expected_model_contract:
        raise ValueError("Contrato publicado 4C diverge da factory oficial do XGBoost.")
    if not contracts.experimental_contract.equals(build_experimental_contract(groups.predictors)):
        raise ValueError("Contrato experimental 3D diverge da especificação congelada.")
    if not contracts.preprocessing_contract.equals(build_preprocessing_contract(groups)):
        raise ValueError("Contrato de preprocessing 3E diverge da receita congelada.")

    partition = contracts.development_partition
    expected_years = ",".join(str(year) for year in DEVELOPMENT_YEARS)
    partition_observed = {
        "years": str(partition.get("years")),
        "rows": int(partition.get("rows", -1)),
        "severe": int(partition.get("severe", -1)),
        "non_severe": int(partition.get("non_severe", -1)),
    }
    partition_expected = {
        "years": expected_years,
        "rows": EXPECTED_TRAINING_ROWS,
        "severe": EXPECTED_TRAINING_POSITIVE,
        "non_severe": EXPECTED_TRAINING_ROWS - EXPECTED_TRAINING_POSITIVE,
    }
    if partition_observed != partition_expected:
        raise ValueError(
            "Partição de desenvolvimento 3D divergente: "
            f"observado={partition_observed}; esperado={partition_expected}."
        )
    manifest = contracts.analytical_manifest
    if (
        manifest.get("predictor_column_count") != EXPECTED_PREDICTOR_COUNT
        or len(manifest.get("physical_predictor_columns", [])) != len(groups.predictors)
        or set(manifest.get("physical_predictor_columns", [])) != set(groups.predictors)
        or manifest.get("target_column") != TARGET_COLUMN
        or manifest.get("sha256") != sha256_file(analytical_path)
        or manifest.get("size_bytes") != analytical_path.stat().st_size
    ):
        raise ValueError("Dataset analítico não reconcilia com o manifesto 3C.")


def load_development_dataset(
    analytical_path: Path,
    predictors: tuple[str, ...],
) -> pl.DataFrame:
    if not analytical_path.is_file():
        raise FileNotFoundError(f"Dataset analítico 3C ausente: {analytical_path}")
    columns = ("id", "source_year", TARGET_COLUMN, *predictors)
    try:
        return (
            pl.scan_parquet(analytical_path)
            .filter(pl.col("source_year").is_in(DEVELOPMENT_YEARS))
            .select(columns)
            .collect()
        )
    except Exception as error:
        raise ValueError(
            "Não foi possível materializar exclusivamente o desenvolvimento 2021-2024."
        ) from error


def validate_development_dataset(
    development: pl.DataFrame,
    groups: PreprocessingGroups,
    partition: dict[str, Any],
) -> None:
    expected_columns = {"id", "source_year", TARGET_COLUMN, *groups.predictors}
    missing = sorted(expected_columns - set(development.columns))
    unexpected = sorted(set(development.columns) - expected_columns)
    failures: list[str] = []
    if missing or unexpected:
        failures.append(f"colunas ausentes={missing}; inesperadas={unexpected}")
    years = set(development.get_column("source_year").unique().to_list())
    if years != set(DEVELOPMENT_YEARS):
        failures.append(f"anos devem ser somente 2021-2024, observado={sorted(years)}")
    if development.height != int(partition["rows"]):
        failures.append(
            f"linhas não reconciliam: dataset={development.height}; contrato={partition['rows']}"
        )
    unique_ids = development.get_column("id").n_unique()
    if unique_ids != development.height:
        failures.append("IDs de desenvolvimento não são únicos")
    target = development.get_column(TARGET_COLUMN)
    if target.dtype != pl.Boolean or target.null_count() > 0:
        failures.append("target_grave deve permanecer booleano e não nulo")
    else:
        positive = int(target.sum())
        if positive != int(partition["severe"]):
            failures.append(
                f"graves não reconciliam: dataset={positive}; contrato={partition['severe']}"
            )
    if len(groups.predictors) != EXPECTED_PREDICTOR_COUNT:
        failures.append(f"predictor_count deve ser {EXPECTED_PREDICTOR_COUNT}")
    if set(METADATA_COLUMNS) & set(groups.predictors) or TARGET_COLUMN in groups.predictors:
        failures.append("metadata/target não podem integrar predictors")
    nulls = {
        column: development.get_column(column).null_count()
        for column in groups.predictors
        if development.get_column(column).null_count()
    }
    if nulls:
        failures.append(f"predictors contêm nulos: {nulls}")
    invalid_binary = {
        column: sorted(development.get_column(column).unique().to_list())
        for column in groups.binary
        if not set(development.get_column(column).unique().to_list()) <= {0, 1}
    }
    if invalid_binary:
        failures.append(f"indicadores binários inválidos: {invalid_binary}")
    if failures:
        raise ValueError("Desenvolvimento inválido para o refit:\n- " + "\n- ".join(failures))


def create_final_pipeline(
    groups: PreprocessingGroups,
    pipeline_factory: PipelineFactory | None = None,
) -> Pipeline:
    factory = build_xgboost_pipeline if pipeline_factory is None else pipeline_factory
    pipeline = factory(groups)
    if not isinstance(pipeline, Pipeline):
        raise TypeError("A factory do refit deve retornar sklearn Pipeline.")
    if set(pipeline.named_steps) != {"preprocessor", "classifier"}:
        raise TypeError("Pipeline final deve conter somente preprocessor e classifier.")
    if not isinstance(pipeline.named_steps["preprocessor"], ColumnTransformer):
        raise TypeError("Pipeline final deve reutilizar ColumnTransformer do preprocessing 3E.")
    if not isinstance(pipeline.named_steps["classifier"], XGBClassifier):
        raise TypeError("Pipeline final deve usar XGBClassifier da Fase 4C.")
    return pipeline


def _validate_classifier_configuration(
    classifier: XGBClassifier,
    model_contract: dict[str, str],
) -> None:
    params = classifier.get_params()
    contract_keys = (
        "n_estimators",
        "learning_rate",
        "max_depth",
        "min_child_weight",
        "gamma",
        "subsample",
        "colsample_bytree",
        "reg_alpha",
        "reg_lambda",
        "scale_pos_weight",
        "objective",
        "eval_metric",
        "tree_method",
        "device",
        "random_state",
        "booster",
        "enable_categorical",
    )
    observed = {
        key: str(params[key]).lower() if isinstance(params[key], bool) else str(params[key])
        for key in contract_keys
    }
    expected = {key: model_contract[key] for key in contract_keys}
    if observed != expected:
        raise ValueError(
            f"Configuração do XGBoost diverge do contrato 4C: {observed} != {expected}."
        )
    if (
        params["n_jobs"] != -1
        or params["verbosity"] != 0
        or params["early_stopping_rounds"] is not None
        or params["callbacks"] is not None
    ):
        raise ValueError("Factory 4C divergiu em paralelismo, verbosity ou early stopping.")


def fit_final_pipeline(
    development: pl.DataFrame,
    groups: PreprocessingGroups,
    model_contract: dict[str, str],
    partition: dict[str, Any],
    pipeline_factory: PipelineFactory | None = None,
) -> FinalFitAudit:
    validate_development_dataset(development, groups, partition)
    pipeline = create_final_pipeline(groups, pipeline_factory)
    classifier = pipeline.named_steps["classifier"]
    _validate_classifier_configuration(classifier, model_contract)
    training_x = development.select(groups.predictors)
    training_y = development.get_column(TARGET_COLUMN).to_numpy()
    pipeline.fit(training_x, training_y)

    check_is_fitted(pipeline)
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    if not isinstance(preprocessor, ColumnTransformer) or not isinstance(classifier, XGBClassifier):
        raise TypeError("Pipeline fitado não preservou os componentes contratados.")
    if classifier.classes_.tolist() != [0, 1]:
        raise ValueError("Classes do pipeline final devem ser exatamente False→0 e True→1.")
    configured_rounds = classifier.n_estimators
    if not isinstance(configured_rounds, int):
        raise TypeError("n_estimators deve ser inteiro explícito.")
    completed_rounds = int(classifier.get_booster().num_boosted_rounds())
    if completed_rounds != configured_rounds:
        raise ValueError(
            f"XGBoost completou {completed_rounds} de {configured_rounds} rounds configurados."
        )
    transformed_feature_count = len(preprocessor.get_feature_names_out())
    positive = int(development.get_column(TARGET_COLUMN).sum())
    return FinalFitAudit(
        pipeline=pipeline,
        training_rows=development.height,
        training_unique_ids=development.get_column("id").n_unique(),
        training_positive=positive,
        training_negative=development.height - positive,
        training_positive_rate=positive / development.height,
        predictor_count=len(groups.predictors),
        transformed_feature_count=transformed_feature_count,
        configured_boosting_rounds=configured_rounds,
        completed_boosting_rounds=completed_rounds,
    )


def persist_final_pipeline(pipeline: Pipeline, path: Path) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            pickle.dump(pipeline, temporary, protocol=pickle.HIGHEST_PROTOCOL)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return sha256_file(path), path.stat().st_size


def load_final_pipeline(path: Path, expected_sha256: str) -> Pipeline:
    if not path.is_file():
        raise FileNotFoundError(f"Pipeline final não encontrado: {path}")
    observed_sha256 = sha256_file(path)
    if observed_sha256 != expected_sha256:
        raise ValueError(
            "SHA-256 do pipeline final diverge antes da desserialização: "
            f"esperado={expected_sha256}; observado={observed_sha256}."
        )
    with path.open("rb") as file:
        loaded = pickle.load(file)
    if not isinstance(loaded, Pipeline):
        raise TypeError("Artefato desserializado não é sklearn Pipeline.")
    if not {"preprocessor", "classifier"}.issubset(loaded.named_steps):
        raise TypeError("Pipeline desserializado não contém preprocessor e classifier.")
    if not isinstance(loaded.named_steps["classifier"], XGBClassifier):
        raise TypeError("Classifier desserializado não é XGBClassifier.")
    return loaded


def _string(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _logical_artifact_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def build_final_model_manifest(
    audit: FinalFitAudit,
    artifact_path: Path,
    artifact_sha256: str,
    artifact_size_bytes: int,
) -> pl.DataFrame:
    classifier = audit.pipeline.named_steps["classifier"]
    if not isinstance(classifier, XGBClassifier):
        raise TypeError("Classifier inválido ao construir manifesto final.")
    params = classifier.get_params()
    values: dict[str, object] = {
        "refit_status": "completed",
        "selected_model_id": XGBOOST_MODEL_ID,
        "selected_model_family": SELECTED_MODEL_FAMILY,
        "training_period": "2021-2024",
        "training_years": "2021,2022,2023,2024",
        "training_rows": audit.training_rows,
        "training_unique_ids": audit.training_unique_ids,
        "training_positive": audit.training_positive,
        "training_negative": audit.training_negative,
        "training_positive_rate": audit.training_positive_rate,
        "predictor_count": audit.predictor_count,
        "preprocessing": "phase_3e",
        "source_model_contract": "phase_4c_xgboost_model_contract.csv",
        "n_estimators": params["n_estimators"],
        "learning_rate": params["learning_rate"],
        "max_depth": params["max_depth"],
        "min_child_weight": params["min_child_weight"],
        "gamma": params["gamma"],
        "subsample": params["subsample"],
        "colsample_bytree": params["colsample_bytree"],
        "reg_alpha": params["reg_alpha"],
        "reg_lambda": params["reg_lambda"],
        "scale_pos_weight": params["scale_pos_weight"],
        "objective": params["objective"],
        "eval_metric": params["eval_metric"],
        "tree_method": params["tree_method"],
        "device": params["device"],
        "n_jobs": params["n_jobs"],
        "random_state": params["random_state"],
        "booster": params["booster"],
        "enable_categorical": params["enable_categorical"],
        "early_stopping": False,
        "hyperparameter_tuning": False,
        "completed_boosting_rounds": audit.completed_boosting_rounds,
        "all_rounds_completed": (
            audit.completed_boosting_rounds == audit.configured_boosting_rounds
        ),
        "transformed_feature_count": audit.transformed_feature_count,
        "threshold_source": "phase_4f",
        "frozen_threshold": FROZEN_THRESHOLD_TEXT,
        "model_artifact_path": _logical_artifact_path(artifact_path),
        "model_artifact_sha256": artifact_sha256,
        "model_artifact_size_bytes": artifact_size_bytes,
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "xgboost_version": xgboost.__version__,
        "polars_version": pl.__version__,
        "final_test_year": "2025_reserved",
        "final_test_used": False,
        "final_evaluation_performed": False,
    }
    return pl.DataFrame(
        {"key": list(values), "value": [_string(value) for value in values.values()]}
    )


def build_refit_checklist(
    audit: FinalFitAudit,
    artifact_path: Path,
    artifact_sha256: str,
) -> pl.DataFrame:
    checks = (
        ("REF001", "Modelo selecionado pela 4E é XGBoost 4C", True, XGBOOST_MODEL_ID),
        ("REF002", "Threshold 4F pertence ao mesmo modelo", True, XGBOOST_MODEL_ID),
        ("REF003", "Threshold permanece exatamente congelado", True, FROZEN_THRESHOLD_TEXT),
        ("REF004", "Desenvolvimento contém somente 2021-2024", True, "2021,2022,2023,2024"),
        ("REF005", "2025 está ausente do conjunto de fit", True, "2025 reservado"),
        (
            "REF006",
            "Linhas e IDs foram reconciliados",
            audit.training_rows == audit.training_unique_ids == EXPECTED_TRAINING_ROWS,
            f"{audit.training_rows} linhas/IDs",
        ),
        (
            "REF007",
            "Predictors físicos permanecem congelados",
            audit.predictor_count == EXPECTED_PREDICTOR_COUNT,
            f"{audit.predictor_count} predictors",
        ),
        (
            "REF008",
            "Preprocessing 3E foi reutilizado",
            isinstance(audit.pipeline.named_steps["preprocessor"], ColumnTransformer),
            "phase_3e",
        ),
        (
            "REF009",
            "Configuração XGBoost corresponde à 4C",
            isinstance(audit.pipeline.named_steps["classifier"], XGBClassifier),
            "factory build_xgboost_pipeline",
        ),
        (
            "REF010",
            "Exatamente 300 rounds foram concluídos",
            audit.configured_boosting_rounds
            == audit.completed_boosting_rounds
            == EXPECTED_BOOSTING_ROUNDS,
            f"{audit.completed_boosting_rounds}/300",
        ),
        (
            "REF011",
            "Pipeline final foi persistido",
            artifact_path.is_file(),
            _logical_artifact_path(artifact_path),
        ),
        (
            "REF012",
            "SHA-256 do pipeline foi calculado",
            len(artifact_sha256) == 64,
            artifact_sha256,
        ),
        ("REF013", "Nenhum tuning foi realizado", True, "hyperparameter_tuning=false"),
        ("REF014", "Threshold não foi recalculado", True, "somente leitura da Fase 4F"),
        ("REF015", "Avaliação final não foi realizada", True, "final_evaluation_performed=false"),
        ("REF016", "Nenhum resultado de 2025 foi produzido", True, "final_test_used=false"),
    )
    return pl.DataFrame(
        [
            {
                "check_id": check_id,
                "check": check,
                "status": "PASS" if passed else "FAIL",
                "evidence": evidence,
            }
            for check_id, check, passed, evidence in checks
        ]
    )


def write_final_refit_tables(
    result: FinalRefitResult,
    tables_dir: Path,
) -> tuple[Path, ...]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "phase_4g_final_model_manifest.csv": result.manifest,
        "phase_4g_refit_checklist.csv": result.checklist,
    }
    paths = tuple(tables_dir / filename for filename in tables)
    for path, table in zip(paths, tables.values(), strict=True):
        table.write_csv(path)
    return paths


def run_final_refit(
    analytical_path: Path = PRIMARY_ANALYTICAL_PARQUET_PATH,
    schema_path: Path = PRIMARY_ANALYTICAL_SCHEMA_PATH,
    tables_dir: Path = TABLES_DIR,
    artifact_path: Path = FINAL_PIPELINE_PATH,
    pipeline_factory: PipelineFactory | None = None,
) -> FinalRefitRun:
    predictors = load_predictors_from_schema(schema_path)
    groups = load_preprocessing_groups(schema_path)
    if (
        set(predictors) != set(groups.predictors)
        or len(predictors) != len(groups.predictors)
        or len(predictors) != EXPECTED_PREDICTOR_COUNT
    ):
        raise ValueError("Predictors do esquema 3C não reconciliam com os grupos 3E.")
    contracts = load_final_refit_contracts(tables_dir=tables_dir)
    validate_final_refit_contracts(contracts, groups, analytical_path)
    development = load_development_dataset(analytical_path, predictors)
    audit = fit_final_pipeline(
        development,
        groups,
        contracts.model_contract,
        contracts.development_partition,
        pipeline_factory,
    )
    artifact_sha256, artifact_size_bytes = persist_final_pipeline(audit.pipeline, artifact_path)
    load_final_pipeline(artifact_path, artifact_sha256)
    checklist = build_refit_checklist(audit, artifact_path, artifact_sha256)
    failed = checklist.filter(pl.col("status") != "PASS")
    if not failed.is_empty():
        raise ValueError(
            "Checks críticos da Fase 4G falharam; manifesto não será publicado: "
            f"{failed.to_dicts()}"
        )
    result = FinalRefitResult(
        audit=audit,
        frozen_threshold=float(FROZEN_THRESHOLD_TEXT),
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        artifact_size_bytes=artifact_size_bytes,
        manifest=build_final_model_manifest(
            audit, artifact_path, artifact_sha256, artifact_size_bytes
        ),
        checklist=checklist,
    )
    return FinalRefitRun(
        result=result,
        table_paths=write_final_refit_tables(result, tables_dir),
    )
