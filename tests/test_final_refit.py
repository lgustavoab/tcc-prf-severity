from __future__ import annotations

import pickle
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from tcc_prf_severity.data.audit import sha256_file
from tcc_prf_severity.modeling import final_refit
from tcc_prf_severity.modeling.experimental_design import build_experimental_contract
from tcc_prf_severity.modeling.final_refit import (
    EXPECTED_BOOSTING_ROUNDS,
    EXPECTED_TRAINING_POSITIVE,
    EXPECTED_TRAINING_ROWS,
    FINAL_PIPELINE_PATH,
    FROZEN_THRESHOLD_TEXT,
    FinalRefitContracts,
    FinalRefitResult,
    build_final_model_manifest,
    build_refit_checklist,
    create_final_pipeline,
    fit_final_pipeline,
    load_development_dataset,
    load_final_pipeline,
    persist_final_pipeline,
    validate_development_dataset,
    validate_final_refit_contracts,
    write_final_refit_tables,
)
from tcc_prf_severity.modeling.model_comparison import XGBOOST_MODEL_ID
from tcc_prf_severity.modeling.preprocessing import (
    PreprocessingGroups,
    build_preprocessing_contract,
    build_preprocessor,
)
from tcc_prf_severity.modeling.threshold_selection import SELECTED_MODEL_FAMILY
from tcc_prf_severity.modeling.xgboost_baseline import build_xgboost_model_contract

CATEGORICAL = (
    "month_name",
    "dia_semana",
    "hour",
    "uf",
    "br",
    "sentido_via",
    "condicao_metereologica",
    "tipo_pista",
    "uso_solo",
)
BINARY = (
    "tracado_aclive",
    "tracado_curva",
    "tracado_declive",
    "tracado_desvio_temporario",
    "tracado_em_obras",
    "tracado_intersecao_de_vias",
    "tracado_ponte",
    "tracado_reta",
    "tracado_retorno_regulamentado",
    "tracado_rotatoria",
    "tracado_tunel",
    "tracado_viaduto",
)
GROUPS = PreprocessingGroups(CATEGORICAL, ("km",), BINARY)


class RecordingPipeline(Pipeline):
    fit_columns: tuple[str, ...] = ()
    fit_target_rows: int = 0

    def fit(self, X: Any, y: Any = None, **params: Any) -> RecordingPipeline:
        type(self).fit_columns = tuple(str(column) for column in X.columns)
        type(self).fit_target_rows = len(y)
        return super().fit(X, y, **params)


def _key_values(table: pl.DataFrame) -> dict[str, str]:
    return {str(row["key"]): str(row["value"]) for row in table.iter_rows(named=True)}


def _dataset() -> pl.DataFrame:
    years = np.repeat(np.arange(2021, 2026), 8)
    total = len(years)
    data: dict[str, object] = {
        "id": [f"{year}-{index}" for year in range(2021, 2026) for index in range(8)],
        "source_year": years,
        "target_grave": np.asarray([(index % 3) == 0 for index in range(total)]),
        "month_name": np.resize(np.asarray(["Janeiro", "Fevereiro"]), total),
        "dia_semana": np.resize(np.asarray(["segunda-feira", "terça-feira"]), total),
        "hour": np.arange(total) % 24,
        "uf": np.resize(np.asarray(["SP", "MG"]), total),
        "br": np.resize(np.asarray([101, 116]), total),
        "sentido_via": np.resize(np.asarray(["Crescente", "Decrescente"]), total),
        "condicao_metereologica": np.resize(np.asarray(["Chuva", "Céu Claro"]), total),
        "tipo_pista": np.resize(np.asarray(["Simples", "Dupla"]), total),
        "uso_solo": np.resize(np.asarray(["Sim", "Não"]), total),
        "km": np.linspace(0.0, 500.0, total),
    }
    for index, column in enumerate(BINARY):
        data[column] = (np.arange(total) + index) % 2
    return pl.DataFrame(data)


def _development() -> pl.DataFrame:
    return _dataset().filter(pl.col("source_year").is_in((2021, 2022, 2023, 2024)))


def _partition(development: pl.DataFrame | None = None) -> dict[str, Any]:
    if development is None:
        return {
            "partition_id": "development",
            "partition_role": "development",
            "years": "2021,2022,2023,2024",
            "rows": EXPECTED_TRAINING_ROWS,
            "severe": EXPECTED_TRAINING_POSITIVE,
            "non_severe": EXPECTED_TRAINING_ROWS - EXPECTED_TRAINING_POSITIVE,
        }
    positive = int(development["target_grave"].sum())
    return {
        "partition_id": "development",
        "partition_role": "development",
        "years": "2021,2022,2023,2024",
        "rows": development.height,
        "severe": positive,
        "non_severe": development.height - positive,
    }


def _fast_pipeline(groups: PreprocessingGroups) -> Pipeline:
    return RecordingPipeline(
        (
            ("preprocessor", build_preprocessor(groups)),
            (
                "classifier",
                XGBClassifier(
                    n_estimators=2,
                    learning_rate=0.1,
                    max_depth=2,
                    min_child_weight=1.0,
                    gamma=0.0,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=0.0,
                    reg_lambda=1.0,
                    objective="binary:logistic",
                    eval_metric="logloss",
                    tree_method="hist",
                    device="cpu",
                    n_jobs=-1,
                    random_state=42,
                    scale_pos_weight=1.0,
                    booster="gbtree",
                    enable_categorical=False,
                    verbosity=0,
                ),
            ),
        )
    )


def _contract_for_pipeline(pipeline: Pipeline) -> dict[str, str]:
    classifier = pipeline.named_steps["classifier"]
    assert isinstance(classifier, XGBClassifier)
    params = classifier.get_params()
    keys = (
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
    return {
        key: str(params[key]).lower() if isinstance(params[key], bool) else str(params[key])
        for key in keys
    }


def _contracts(analytical_path: Path) -> FinalRefitContracts:
    return FinalRefitContracts(
        model_selection={
            "selection_status": "selected",
            "selected_model_id": XGBOOST_MODEL_ID,
            "selected_model_family": SELECTED_MODEL_FAMILY,
            "development_period": "2021-2024",
            "final_test_year": "2025_reserved",
            "final_test_used": "false",
            "refit_performed": "false",
        },
        threshold_selection={
            "selection_status": "selected",
            "selected_model_id": XGBOOST_MODEL_ID,
            "selected_model_family": SELECTED_MODEL_FAMILY,
            "selected_threshold": FROZEN_THRESHOLD_TEXT,
            "final_test_year": "2025_reserved",
            "final_test_used": "false",
            "refit_performed": "false",
        },
        model_contract=_key_values(build_xgboost_model_contract()),
        experimental_contract=build_experimental_contract(GROUPS.predictors),
        preprocessing_contract=build_preprocessing_contract(GROUPS),
        development_partition=_partition(),
        analytical_manifest={
            "predictor_column_count": 22,
            "physical_predictor_columns": list(GROUPS.predictors),
            "target_column": "target_grave",
            "sha256": sha256_file(analytical_path),
            "size_bytes": analytical_path.stat().st_size,
        },
    )


@pytest.fixture(scope="module")
def fast_audit() -> final_refit.FinalFitAudit:
    development = _development()
    return fit_final_pipeline(
        development,
        GROUPS,
        _contract_for_pipeline(_fast_pipeline(GROUPS)),
        _partition(development),
        _fast_pipeline,
    )


def test_correct_4e_4f_and_authoritative_contracts_are_accepted(tmp_path: Path) -> None:
    analytical = tmp_path / "analytical.parquet"
    _dataset().write_parquet(analytical)

    validate_final_refit_contracts(_contracts(analytical), GROUPS, analytical)


def test_different_selected_model_is_rejected(tmp_path: Path) -> None:
    analytical = tmp_path / "analytical.parquet"
    _dataset().write_parquet(analytical)
    contracts = _contracts(analytical)
    divergent = contracts.model_selection | {"selected_model_id": "phase_4b_random_forest_baseline"}

    with pytest.raises(ValueError, match="4E"):
        validate_final_refit_contracts(
            replace(contracts, model_selection=divergent), GROUPS, analytical
        )


def test_divergent_or_recalculated_threshold_is_rejected(tmp_path: Path) -> None:
    analytical = tmp_path / "analytical.parquet"
    _dataset().write_parquet(analytical)
    contracts = _contracts(analytical)
    divergent = contracts.threshold_selection | {"selected_threshold": "0.24"}

    with pytest.raises(ValueError, match="4F"):
        validate_final_refit_contracts(
            replace(contracts, threshold_selection=divergent), GROUPS, analytical
        )


def test_lazy_load_materializes_only_2021_2024_and_never_2025(tmp_path: Path) -> None:
    analytical = tmp_path / "analytical.parquet"
    _dataset().write_parquet(analytical)

    development = load_development_dataset(analytical, GROUPS.predictors)

    assert development["source_year"].unique().sort().to_list() == [2021, 2022, 2023, 2024]
    assert 2025 not in development["source_year"]
    assert set(development.columns) == {"id", "source_year", "target_grave", *GROUPS.predictors}


def test_development_requires_unique_ids_boolean_target_and_22_predictors() -> None:
    development = _development()
    validate_development_dataset(development, GROUPS, _partition(development))

    duplicated = development.with_columns(
        pl.when(pl.col("id") == development["id"][-1])
        .then(pl.lit(development["id"][0]))
        .otherwise(pl.col("id"))
        .alias("id")
    )
    with pytest.raises(ValueError, match="não são únicos"):
        validate_development_dataset(duplicated, GROUPS, _partition(development))
    with pytest.raises(ValueError, match="booleano"):
        validate_development_dataset(
            development.with_columns(pl.col("target_grave").cast(pl.Int8)),
            GROUPS,
            _partition(development),
        )


def test_2025_is_rejected_before_factory_or_fit_is_called() -> None:
    called = False

    def forbidden_factory(groups: PreprocessingGroups) -> Pipeline:
        nonlocal called
        called = True
        return _fast_pipeline(groups)

    with pytest.raises(ValueError, match="2021-2024"):
        fit_final_pipeline(
            _dataset(),
            GROUPS,
            _contract_for_pipeline(_fast_pipeline(GROUPS)),
            _partition(_development()),
            forbidden_factory,
        )
    assert not called


def test_production_path_reuses_build_xgboost_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[PreprocessingGroups] = []

    def spy(groups: PreprocessingGroups) -> Pipeline:
        called.append(groups)
        return _fast_pipeline(groups)

    monkeypatch.setattr(final_refit, "build_xgboost_pipeline", spy)

    pipeline = create_final_pipeline(GROUPS)

    assert called == [GROUPS]
    assert isinstance(pipeline.named_steps["classifier"], XGBClassifier)


def test_fit_receives_only_predictors_and_development_target(fast_audit: Any) -> None:
    assert RecordingPipeline.fit_columns == GROUPS.predictors
    assert not {"id", "source_year", "target_grave"} & set(RecordingPipeline.fit_columns)
    assert RecordingPipeline.fit_target_rows == _development().height
    assert fast_audit.training_rows == _development().height


def test_rounds_and_transformed_feature_count_are_derived(fast_audit: Any) -> None:
    preprocessor = fast_audit.pipeline.named_steps["preprocessor"]

    assert fast_audit.configured_boosting_rounds == 2
    assert fast_audit.completed_boosting_rounds == 2
    assert fast_audit.transformed_feature_count == len(preprocessor.get_feature_names_out())
    assert fast_audit.transformed_feature_count > fast_audit.predictor_count == 22


def test_no_tuning_threshold_search_or_performance_evaluation_code_was_added() -> None:
    source = Path("src/tcc_prf_severity/modeling/final_refit.py").read_text(encoding="utf-8")

    for forbidden in (
        "predict_proba",
        "average_precision",
        "roc_auc",
        "f1_score",
        "GridSearchCV",
        "RandomizedSearchCV",
        "Optuna",
        "eval_set=",
    ):
        assert forbidden not in source


def test_pipeline_persistence_and_sha_use_tmp_path(tmp_path: Path, fast_audit: Any) -> None:
    path = tmp_path / "model.pkl"

    sha256, size = persist_final_pipeline(fast_audit.pipeline, path)
    loaded = load_final_pipeline(path, sha256)

    assert path.is_file()
    assert sha256 == sha256_file(path)
    assert size == path.stat().st_size > 0
    assert isinstance(loaded, Pipeline)


def test_integrity_failure_happens_before_pickle_load(
    tmp_path: Path, fast_audit: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "model.pkl"
    expected_sha256, _ = persist_final_pipeline(fast_audit.pipeline, path)
    with path.open("ab") as file:
        file.write(b"alterado")
    called = False

    def forbidden_load(file: Any) -> Any:
        nonlocal called
        called = True
        return pickle.load(file)

    monkeypatch.setattr(final_refit.pickle, "load", forbidden_load)
    with pytest.raises(ValueError, match="antes da desserialização"):
        load_final_pipeline(path, expected_sha256)
    assert not called


def test_loader_rejects_non_pipeline_and_wrong_classifier(tmp_path: Path) -> None:
    invalid_object = tmp_path / "object.pkl"
    invalid_object.write_bytes(pickle.dumps({"not": "pipeline"}))
    with pytest.raises(TypeError, match="não é sklearn Pipeline"):
        load_final_pipeline(invalid_object, sha256_file(invalid_object))

    wrong_classifier = tmp_path / "wrong.pkl"
    wrong_classifier.write_bytes(
        pickle.dumps(Pipeline((("preprocessor", "passthrough"), ("classifier", DummyClassifier()))))
    )
    with pytest.raises(TypeError, match="não é XGBClassifier"):
        load_final_pipeline(wrong_classifier, sha256_file(wrong_classifier))


def test_manifest_freezes_threshold_and_reserves_2025(tmp_path: Path, fast_audit: Any) -> None:
    path = tmp_path / "model.pkl"
    sha256, size = persist_final_pipeline(fast_audit.pipeline, path)
    manifest = _key_values(build_final_model_manifest(fast_audit, path, sha256, size))

    assert manifest["frozen_threshold"] == FROZEN_THRESHOLD_TEXT
    assert manifest["threshold_source"] == "phase_4f"
    assert manifest["final_test_year"] == "2025_reserved"
    assert manifest["final_test_used"] == "false"
    assert manifest["final_evaluation_performed"] == "false"
    assert manifest["hyperparameter_tuning"] == "false"


def test_checklist_passes_for_audited_production_invariants(
    tmp_path: Path, fast_audit: Any
) -> None:
    path = tmp_path / "model.pkl"
    sha256, _ = persist_final_pipeline(fast_audit.pipeline, path)
    production_audit = replace(
        fast_audit,
        training_rows=EXPECTED_TRAINING_ROWS,
        training_unique_ids=EXPECTED_TRAINING_ROWS,
        training_positive=EXPECTED_TRAINING_POSITIVE,
        training_negative=EXPECTED_TRAINING_ROWS - EXPECTED_TRAINING_POSITIVE,
        configured_boosting_rounds=EXPECTED_BOOSTING_ROUNDS,
        completed_boosting_rounds=EXPECTED_BOOSTING_ROUNDS,
    )

    checklist = build_refit_checklist(production_audit, path, sha256)

    assert checklist.height == 16
    assert checklist["status"].unique().to_list() == ["PASS"]


def test_table_writing_uses_tmp_path_and_persists_only_two_csvs(
    tmp_path: Path, fast_audit: Any
) -> None:
    artifact = tmp_path / "model.pkl"
    sha256, size = persist_final_pipeline(fast_audit.pipeline, artifact)
    production_audit = replace(
        fast_audit,
        training_rows=EXPECTED_TRAINING_ROWS,
        training_unique_ids=EXPECTED_TRAINING_ROWS,
        configured_boosting_rounds=EXPECTED_BOOSTING_ROUNDS,
        completed_boosting_rounds=EXPECTED_BOOSTING_ROUNDS,
    )
    result = FinalRefitResult(
        audit=production_audit,
        frozen_threshold=float(FROZEN_THRESHOLD_TEXT),
        artifact_path=artifact,
        artifact_sha256=sha256,
        artifact_size_bytes=size,
        manifest=build_final_model_manifest(production_audit, artifact, sha256, size),
        checklist=build_refit_checklist(production_audit, artifact, sha256),
    )
    tables_dir = tmp_path / "tables"

    paths = write_final_refit_tables(result, tables_dir)

    assert {path.name for path in paths} == {
        "phase_4g_final_model_manifest.csv",
        "phase_4g_refit_checklist.csv",
    }
    assert len(list(tables_dir.iterdir())) == 2


def test_official_pickle_path_is_ignored_selectively_or_by_parent_rule() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert FINAL_PIPELINE_PATH.name.endswith(".pkl")
    assert "/artifacts/*" in gitignore or "artifacts/models/*.pkl" in gitignore
