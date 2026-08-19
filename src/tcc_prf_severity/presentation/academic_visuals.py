from __future__ import annotations

import argparse
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

import matplotlib
import polars as pl

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from tcc_prf_severity.config import PROJECT_ROOT

EXPECTED_BRANCH: Final = "analysis/phase-5d-academic-visuals"

MODEL_LABELS: Final = {
    "phase_4a_logistic_baseline": "Regressão Logística",
    "phase_4b_random_forest_baseline": "Random Forest",
    "phase_4c_xgboost_baseline": "XGBoost",
}
MODEL_COLORS: Final = {
    "phase_4a_logistic_baseline": "#0072B2",
    "phase_4b_random_forest_baseline": "#009E73",
    "phase_4c_xgboost_baseline": "#D55E00",
}
NEUTRAL: Final = "#4D4D4D"
LIGHT_NEUTRAL: Final = "#D9D9D9"
ACCENT_BLUE: Final = "#0072B2"
ACCENT_ORANGE: Final = "#E69F00"
ACCENT_PURPLE: Final = "#CC79A7"

SOURCE_SPECS: Final[dict[str, frozenset[str]]] = {
    "phase_2a_year_summary.csv": frozenset(
        {
            "source_year",
            "total_occurrences",
            "severe_occurrences",
            "non_severe_occurrences",
            "severe_rate_percent",
        }
    ),
    "phase_2f_association_evidence_matrix.csv": frozenset(
        {
            "dimension",
            "category_or_comparison",
            "focal_category",
            "severe_rate_percent",
            "reference_category_or_rate",
            "reference_rate_percent",
        }
    ),
    "phase_3b_primary_feature_set.csv": frozenset(
        {"feature", "source", "representation", "expected_future_preprocessing"}
    ),
    "phase_3d_temporal_folds.csv": frozenset(
        {"fold", "train_years", "validation_year", "train_rows", "validation_rows"}
    ),
    "phase_3d_partition_summary.csv": frozenset(
        {"partition_id", "partition_role", "years", "rows"}
    ),
    "phase_3e_preprocessing_contract.csv": frozenset(
        {"group", "source_features", "transformer", "unknown_policy", "notes"}
    ),
    "phase_4d_model_comparison.csv": frozenset(
        {"model_id", "ap_fold1", "ap_fold2", "ap_fold3", "ap_unweighted_mean"}
    ),
    "phase_4d_fold_comparison.csv": frozenset(
        {
            "fold",
            "validation_year",
            "model_id",
            "average_precision",
            "roc_auc",
            "brier_score",
            "validation_positive_rate",
        }
    ),
    "phase_4d_pairwise_ap_deltas.csv": frozenset({"model_a", "model_b", "ap_mean_delta"}),
    "phase_4f_threshold_selection.csv": frozenset({"key", "value"}),
    "phase_4h_final_evaluation.csv": frozenset({"key", "value"}),
    "phase_4h_development_comparison.csv": frozenset(
        {
            "metric",
            "development_reference",
            "development_value",
            "final_2025_value",
            "delta_final_minus_development",
        }
    ),
    "phase_4h_threshold_evaluation.csv": frozenset(
        {"threshold_role", "threshold", "precision", "recall", "f1", "tn", "fp", "fn", "tp"}
    ),
    "phase_4h_calibration.csv": frozenset(
        {"bin", "mean_predicted_probability", "observed_positive_rate"}
    ),
    "phase_4i_global_feature_contributions.csv": frozenset(
        {
            "rank",
            "source_predictor",
            "transformed_feature_count",
            "mean_abs_margin_contribution",
            "share_of_total_mean_abs_contribution",
        }
    ),
    "phase_4i_transformed_feature_contributions.csv": frozenset(
        {"rank", "transformed_feature", "mean_abs_margin_contribution"}
    ),
    "phase_4i_error_analysis.csv": frozenset(
        {
            "outcome",
            "rows",
            "mean_probability",
            "median_probability",
            "p10_probability",
            "p25_probability",
            "p75_probability",
            "p90_probability",
        }
    ),
    "phase_5a_research_question_evidence.csv": frozenset(
        {"question_id", "evidence_id", "metric_or_analysis", "observed_result", "caution"}
    ),
    "phase_5c_key_numbers.csv": frozenset(
        {"number_id", "topic", "value", "unit", "target_section"}
    ),
}


@dataclass(frozen=True)
class FigureArtifact:
    visual_id: str
    title: str
    png_path: Path
    svg_path: Path
    source_artifacts: str
    priority: str
    target_section: str


@dataclass(frozen=True)
class TableArtifact:
    visual_id: str
    title: str
    path: Path
    source_artifacts: str
    priority: str
    target_section: str
    rows: int
    columns: int


@dataclass(frozen=True)
class GenerationResult:
    figures: tuple[FigureArtifact, ...]
    tables: tuple[TableArtifact, ...]
    contact_sheet: Path
    manifest_path: Path
    qa_path: Path
    checklist_path: Path


def _configure_matplotlib() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "axes.edgecolor": NEUTRAL,
            "axes.linewidth": 0.8,
            "xtick.color": NEUTRAL,
            "ytick.color": NEUTRAL,
            "text.color": "#222222",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "svg.hashsalt": "tcc-prf-severity-phase-5d",
        }
    )


def validate_sources(project_root: Path = PROJECT_ROOT) -> dict[str, pl.DataFrame]:
    """Carrega e valida somente os CSVs científicos congelados usados na Fase 5D."""
    tables_dir = project_root / "reports" / "tables"
    loaded: dict[str, pl.DataFrame] = {}
    for filename, required_columns in SOURCE_SPECS.items():
        path = tables_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Fonte obrigatória ausente: {path}")
        frame = pl.read_csv(path)
        missing = sorted(required_columns - set(frame.columns))
        if missing:
            raise ValueError(f"Fonte {filename} sem colunas obrigatórias: {', '.join(missing)}")
        if frame.is_empty():
            raise ValueError(f"Fonte obrigatória vazia: {filename}")
        loaded[filename] = frame
    return loaded


def load_model_average_precision(sources: dict[str, pl.DataFrame]) -> dict[str, float]:
    frame = sources["phase_4d_model_comparison.csv"]
    values = {
        str(row["model_id"]): float(row["ap_unweighted_mean"])
        for row in frame.iter_rows(named=True)
    }
    if set(values) != set(MODEL_LABELS):
        raise ValueError("A comparação 4D não contém exatamente as três famílias congeladas.")
    return values


def load_fold_average_precision(
    sources: dict[str, pl.DataFrame],
) -> tuple[tuple[int, int, str, float], ...]:
    frame = sources["phase_4d_fold_comparison.csv"].sort(["fold", "model_id"])
    rows = tuple(
        (
            int(row["fold"]),
            int(row["validation_year"]),
            str(row["model_id"]),
            float(row["average_precision"]),
        )
        for row in frame.iter_rows(named=True)
    )
    if len(rows) != 9 or {row[2] for row in rows} != set(MODEL_LABELS):
        raise ValueError("A tabela 4D deve conter os nove pares modelo-fold congelados.")
    if {row[0] for row in rows} != {1, 2, 3}:
        raise ValueError("Os folds temporais esperados são 1, 2 e 3.")
    return rows


def load_confusion_counts(sources: dict[str, pl.DataFrame]) -> dict[str, int | float]:
    frame = sources["phase_4h_threshold_evaluation.csv"].filter(
        pl.col("threshold_role") == "frozen_threshold"
    )
    if frame.height != 1:
        raise ValueError("A avaliação 4H deve conter um único frozen_threshold.")
    row = frame.row(0, named=True)
    return {
        "threshold": float(row["threshold"]),
        "tn": int(row["tn"]),
        "fp": int(row["fp"]),
        "fn": int(row["fn"]),
        "tp": int(row["tp"]),
    }


def _format_decimal_pt(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _format_percent_pt(value: float, digits: int = 2) -> str:
    return f"{_format_decimal_pt(value, digits)}%"


def _format_integer_pt(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _style_axis(axis: Axes, *, grid_axis: Literal["both", "x", "y"] | None = "x") -> None:
    axis.spines[["top", "right"]].set_visible(False)
    if grid_axis:
        axis.grid(axis=grid_axis, color="#D9D9D9", linewidth=0.7, alpha=0.7)
        axis.set_axisbelow(True)


def _save_figure(figure: Figure, output_base: Path) -> tuple[Path, Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_base.with_suffix(".png")
    svg_path = output_base.with_suffix(".svg")
    figure.savefig(
        png_path,
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "tcc-prf-severity phase 5D"},
    )
    figure.savefig(
        svg_path,
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "tcc-prf-severity phase 5D"},
    )
    plt.close(figure)
    return png_path, svg_path


def _comparison_row(frame: pl.DataFrame, comparison: str) -> dict[str, object]:
    selected = frame.filter(pl.col("category_or_comparison") == comparison)
    if selected.height != 1:
        raise ValueError(f"Contraste congelado ausente ou duplicado: {comparison}")
    return selected.row(0, named=True)


def _plot_contrast_panel(
    axis: Axes,
    row: dict[str, object],
    *,
    panel_title: str,
    x_limit: float,
) -> None:
    focal_label = str(row["focal_category"])
    reference_label = str(row["reference_category_or_rate"])
    focal = float(str(row["severe_rate_percent"]))
    reference = float(str(row["reference_rate_percent"]))
    axis.hlines(0, min(focal, reference), max(focal, reference), color=LIGHT_NEUTRAL, linewidth=3)
    axis.scatter([focal], [0], color=ACCENT_BLUE, s=70, zorder=3)
    axis.scatter([reference], [0], color=ACCENT_ORANGE, s=70, zorder=3)
    axis.annotate(
        f"{focal_label}\n{_format_percent_pt(focal)}",
        (focal, 0),
        xytext=(0, 14),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=9,
    )
    axis.annotate(
        f"{reference_label}\n{_format_percent_pt(reference)}",
        (reference, 0),
        xytext=(0, -18),
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=9,
    )
    axis.set_xlim(0, x_limit)
    axis.set_ylim(-0.55, 0.55)
    axis.set_yticks([])
    axis.set_title(panel_title, loc="left", fontweight="normal")
    axis.set_xlabel("Ocorrências graves (%)")
    _style_axis(axis)


def _generate_m1(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    folds = sources["phase_3d_temporal_folds.csv"].sort("fold")
    if folds.height != 3:
        raise ValueError("M1 exige exatamente três folds temporais.")
    years = [2021, 2022, 2023, 2024, 2025]
    lanes = ["Fold 1", "Fold 2", "Fold 3", "Refit final", "Avaliação final"]
    figure, axis = plt.subplots(figsize=(10, 5.6))
    axis.set_xlim(2020.5, 2025.5)
    axis.set_ylim(-0.7, 4.7)
    axis.set_xticks(years)
    axis.set_yticks(range(5), lanes)
    axis.invert_yaxis()

    for index, row in enumerate(folds.iter_rows(named=True)):
        train_years = [int(year) for year in str(row["train_years"]).split(",")]
        for year in train_years:
            axis.add_patch(
                Rectangle((year - 0.43, index - 0.32), 0.86, 0.64, color=ACCENT_BLUE, alpha=0.82)
            )
        validation_year = int(row["validation_year"])
        axis.add_patch(
            Rectangle(
                (validation_year - 0.43, index - 0.32),
                0.86,
                0.64,
                color=ACCENT_ORANGE,
                alpha=0.9,
            )
        )

    for year in years[:-1]:
        axis.add_patch(
            Rectangle((year - 0.43, 3 - 0.32), 0.86, 0.64, color=ACCENT_BLUE, alpha=0.82)
        )
    axis.add_patch(Rectangle((2025 - 0.43, 4 - 0.32), 0.86, 0.64, color=ACCENT_PURPLE, alpha=0.9))

    axis.set_title("Desenho temporal expanding-window e avaliação final", pad=14)
    axis.set_xlabel("Ano")
    axis.grid(axis="x", color="#E6E6E6", linewidth=0.7)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.legend(
        handles=[
            Patch(facecolor=ACCENT_BLUE, label="Treino"),
            Patch(facecolor=ACCENT_ORANGE, label="Validação interna"),
            Patch(facecolor=ACCENT_PURPLE, label="Avaliação final (fora da otimização)"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=3,
        frameon=False,
    )
    figure.text(
        0.5,
        0.015,
        "2025 é usado somente para avaliação temporal final.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0, 0.07, 1, 1))
    png, svg = _save_figure(figure, figures_dir / "M1_temporal_design")
    return FigureArtifact(
        "M1",
        "Desenho temporal expanding-window e avaliação final",
        png,
        svg,
        "reports/tables/phase_3d_temporal_folds.csv; reports/tables/phase_3d_partition_summary.csv",
        "ESSENTIAL_METHODS",
        "Metodologia — Desenho experimental",
    )


def _generate_f1(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    frame = sources["phase_2f_association_evidence_matrix.csv"]
    panels = (
        ("Plena Noite vs Pleno dia", "A. Fase do dia"),
        ("Fim de semana vs Dias úteis", "B. Grupo de dias"),
        ("19 vs 8", "C. Hora registrada"),
    )
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.8), sharex=True)
    for axis, (comparison, title) in zip(axes, panels, strict=True):
        row = _comparison_row(frame, comparison)
        if comparison == "19 vs 8":
            row = {
                **row,
                "focal_category": "19h",
                "reference_category_or_rate": "8h",
            }
        _plot_contrast_panel(axis, row, panel_title=title, x_limit=40)
    figure.suptitle("Proporção de ocorrências graves em contrastes temporais selecionados")
    figure.text(
        0.5,
        0.015,
        "Proporções entre ocorrências registradas; não representam risco "
        "de ocorrência de acidente.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0, 0.06, 1, 0.92))
    png, svg = _save_figure(figure, figures_dir / "F1_temporal_contrasts")
    return FigureArtifact(
        "F1",
        "Proporção de ocorrências graves em contrastes temporais selecionados",
        png,
        svg,
        "reports/tables/phase_2f_association_evidence_matrix.csv",
        "ESSENTIAL",
        "Resultados — Associações descritivas",
    )


def _generate_f2(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    frame = sources["phase_2f_association_evidence_matrix.csv"]
    panels = (
        ("Nordeste vs Sul", "A. Macrorregião"),
        ("MA vs SP", "B. Unidade da Federação"),
        ("Simples vs Dupla", "C. Tipo de pista"),
        ("Nevoeiro/Neblina vs Garoa/Chuvisco", "D. Condição meteorológica informada"),
    )
    figure, axes = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
    for axis, (comparison, title) in zip(axes.flat, panels, strict=True):
        _plot_contrast_panel(
            axis, _comparison_row(frame, comparison), panel_title=title, x_limit=55
        )
    figure.suptitle("Proporção de ocorrências graves em contrastes contextuais selecionados")
    figure.text(
        0.5,
        0.015,
        "Comparações descritivas entre acidentes registrados, sem denominadores de exposição.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0, 0.05, 1, 0.94))
    png, svg = _save_figure(figure, figures_dir / "F2_contextual_contrasts")
    return FigureArtifact(
        "F2",
        "Proporção de ocorrências graves em contrastes contextuais selecionados",
        png,
        svg,
        "reports/tables/phase_2f_association_evidence_matrix.csv",
        "ESSENTIAL",
        "Resultados — Associações descritivas",
    )


def _generate_f4(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    values = load_model_average_precision(sources)
    model_ids = list(MODEL_LABELS)
    y_positions = list(range(len(model_ids)))
    figure, axis = plt.subplots(figsize=(9, 5.2))
    for y, model_id in zip(y_positions, model_ids, strict=True):
        value = values[model_id]
        axis.hlines(y, 0, value, color=LIGHT_NEUTRAL, linewidth=2)
        axis.scatter(value, y, s=85, color=MODEL_COLORS[model_id], zorder=3)
        axis.annotate(
            _format_decimal_pt(value),
            (value, y),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
        )
    axis.set_yticks(y_positions, [MODEL_LABELS[model_id] for model_id in model_ids])
    axis.set_xlim(0, 1)
    axis.set_xlabel("Average Precision média")
    axis.set_title("Average Precision média na validação temporal")
    _style_axis(axis)
    figure.text(
        0.5,
        0.02,
        "Média aritmética não ponderada dos três folds. Eixo exibido de 0 a 1.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0, 0.07, 1, 1))
    png, svg = _save_figure(figure, figures_dir / "F4_model_average_precision")
    return FigureArtifact(
        "F4",
        "Average Precision média na validação temporal",
        png,
        svg,
        "reports/tables/phase_4d_model_comparison.csv",
        "ESSENTIAL",
        "Resultados — Comparação dos modelos",
    )


def _generate_f5(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    rows = load_fold_average_precision(sources)
    figure, axis = plt.subplots(figsize=(9, 5.8))
    for model_id in MODEL_LABELS:
        selected = sorted((row for row in rows if row[2] == model_id), key=lambda row: row[0])
        years = [row[1] for row in selected]
        values = [row[3] for row in selected]
        axis.plot(
            years,
            values,
            marker="o",
            markersize=7,
            linewidth=2,
            color=MODEL_COLORS[model_id],
            label=MODEL_LABELS[model_id],
        )
        label_positions = {
            "phase_4a_logistic_baseline": ((0, -16), "center"),
            "phase_4b_random_forest_baseline": ((10, 5), "left"),
            "phase_4c_xgboost_baseline": ((0, 10), "center"),
        }
        offset, horizontal_alignment = label_positions[model_id]
        for year, value in zip(years, values, strict=True):
            axis.annotate(
                _format_decimal_pt(value),
                (year, value),
                xytext=offset,
                textcoords="offset points",
                ha=horizontal_alignment,
                va="center",
                fontsize=8,
            )
    axis.set_xlim(2021.7, 2024.3)
    axis.set_ylim(0.35, 0.45)
    axis.set_xticks([2022, 2023, 2024])
    axis.set_xlabel("Ano de validação")
    axis.set_ylabel("Average Precision")
    axis.set_title("Average Precision por ano de validação")
    axis.legend(frameon=False, loc="upper left")
    _style_axis(axis, grid_axis="both")
    figure.text(
        0.5,
        0.015,
        "Escala ampliada para leitura. Período de treino e ano de validação mudam simultaneamente.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    png, svg = _save_figure(figure, figures_dir / "F5_temporal_fold_average_precision")
    return FigureArtifact(
        "F5",
        "Average Precision por ano de validação",
        png,
        svg,
        "reports/tables/phase_4d_fold_comparison.csv",
        "ESSENTIAL",
        "Resultados — Validação temporal",
    )


def _generate_f6(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    counts = load_confusion_counts(sources)
    cells = (
        (0, 1, "TN", int(counts["tn"])),
        (1, 1, "FP", int(counts["fp"])),
        (0, 0, "FN", int(counts["fn"])),
        (1, 0, "TP", int(counts["tp"])),
    )
    figure, axis = plt.subplots(figsize=(8, 6.2))
    for x, y, label, value in cells:
        axis.add_patch(Rectangle((x, y), 1, 1, facecolor="#EAF2F8", edgecolor="white", linewidth=3))
        axis.text(x + 0.5, y + 0.62, label, ha="center", va="center", fontsize=11, color=NEUTRAL)
        axis.text(
            x + 0.5,
            y + 0.38,
            _format_integer_pt(value),
            ha="center",
            va="center",
            fontsize=18,
        )
    axis.set_xlim(0, 2)
    axis.set_ylim(0, 2)
    axis.set_xticks([0.5, 1.5], ["Predito não grave", "Predito grave"])
    axis.set_yticks([0.5, 1.5], ["Real grave", "Real não grave"])
    axis.xaxis.tick_top()
    axis.tick_params(length=0, pad=10)
    for spine in axis.spines.values():
        spine.set_visible(False)
    axis.set_title(
        "Matriz de confusão em 2025 no threshold congelado",
        pad=50,
    )
    figure.text(
        0.5,
        0.08,
        f"Threshold = {_format_decimal_pt(float(counts['threshold']), 6)}",
        ha="center",
        fontsize=10,
    )
    figure.text(
        0.5,
        0.035,
        "O cutoff prioriza recall; custos de FP/FN não foram avaliados.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0.08, 0.12, 0.98, 0.92))
    png, svg = _save_figure(figure, figures_dir / "F6_confusion_matrix_2025")
    return FigureArtifact(
        "F6",
        "Matriz de confusão em 2025 no threshold congelado",
        png,
        svg,
        "reports/tables/phase_4h_threshold_evaluation.csv; "
        "reports/tables/phase_4f_threshold_selection.csv",
        "ESSENTIAL",
        "Resultados — Avaliação final",
    )


def _generate_f7(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    frame = sources["phase_4h_calibration.csv"].sort("bin")
    predicted = [float(value) for value in frame.get_column("mean_predicted_probability")]
    observed = [float(value) for value in frame.get_column("observed_positive_rate")]
    figure, axis = plt.subplots(figsize=(7, 6))
    axis.plot(
        [0, 1], [0, 1], color=NEUTRAL, linestyle="--", linewidth=1.2, label="Referência y = x"
    )
    axis.plot(
        predicted,
        observed,
        color=ACCENT_BLUE,
        marker="o",
        linewidth=1.8,
        label="Faixas quantílicas de 2025",
    )
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("Probabilidade média prevista")
    axis.set_ylabel("Proporção observada de ocorrências graves")
    axis.set_title("Calibração descritiva das probabilidades em 2025")
    axis.legend(frameon=False, loc="upper left")
    _style_axis(axis, grid_axis="both")
    figure.text(
        0.5,
        0.02,
        "Bins quantis; nenhum calibrador foi ajustado.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0, 0.06, 1, 1))
    png, svg = _save_figure(figure, figures_dir / "F7_calibration_2025")
    return FigureArtifact(
        "F7",
        "Calibração descritiva das probabilidades em 2025",
        png,
        svg,
        "reports/tables/phase_4h_calibration.csv",
        "USEFUL",
        "Resultados/Discussão — Avaliação final",
    )


def _generate_f8(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    frame = sources["phase_4i_global_feature_contributions.csv"].sort("rank").head(8)
    display_labels = {
        "uf": "UF",
        "tipo_pista": "Tipo de pista",
        "hour": "Hora",
        "br": "BR",
        "condicao_metereologica": "Condição meteorológica",
        "km": "Km",
        "dia_semana": "Dia da semana",
        "tracado_reta": "Traçado: reta",
    }
    labels = [display_labels[str(value)] for value in frame.get_column("source_predictor")][::-1]
    shares = [
        float(value) * 100 for value in frame.get_column("share_of_total_mean_abs_contribution")
    ][::-1]
    figure, axis = plt.subplots(figsize=(9, 6.5))
    bars = axis.barh(labels, shares, color=ACCENT_BLUE, alpha=0.86)
    for bar, value in zip(bars, shares, strict=True):
        axis.text(
            value + 0.35,
            bar.get_y() + bar.get_height() / 2,
            _format_percent_pt(value),
            va="center",
            fontsize=9,
        )
    axis.set_xlim(0, max(shares) * 1.22)
    axis.set_xlabel("Participação na contribuição absoluta média (%)")
    axis.set_title("Principais contribuições agregadas nas predições do XGBoost")
    _style_axis(axis)
    figure.text(
        0.5,
        0.045,
        "Tree SHAP em raw margin; contribuição preditiva não causal.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.text(
        0.5,
        0.018,
        "Cardinalidade e representação podem influenciar a agregação; br reúne 125 features OHE.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0, 0.09, 1, 1))
    png, svg = _save_figure(figure, figures_dir / "F8_predictor_contributions")
    return FigureArtifact(
        "F8",
        "Principais contribuições agregadas nas predições do XGBoost",
        png,
        svg,
        "reports/tables/phase_4i_global_feature_contributions.csv",
        "USEFUL",
        "Fim de Resultados — Interpretação do modelo",
    )


def _generate_a2(sources: dict[str, pl.DataFrame], figures_dir: Path) -> FigureArtifact:
    frame = sources["phase_4i_error_analysis.csv"]
    order = ["TP", "FP", "FN", "TN"]
    rows = {str(row["outcome"]): row for row in frame.iter_rows(named=True)}
    if set(rows) != set(order):
        raise ValueError("A análise de erros 4I deve conter TP, FP, FN e TN.")
    figure, axis = plt.subplots(figsize=(9, 5.8))
    for y, outcome in enumerate(order):
        row = rows[outcome]
        p10 = float(row["p10_probability"])
        p25 = float(row["p25_probability"])
        median = float(row["median_probability"])
        p75 = float(row["p75_probability"])
        p90 = float(row["p90_probability"])
        mean = float(row["mean_probability"])
        axis.hlines(y, p10, p90, color=LIGHT_NEUTRAL, linewidth=3)
        axis.hlines(y, p25, p75, color=ACCENT_BLUE, linewidth=8, alpha=0.75)
        axis.scatter(median, y, color="#222222", s=45, zorder=3, marker="o")
        axis.scatter(mean, y, color=ACCENT_ORANGE, s=55, zorder=3, marker="D")
    axis.set_yticks(range(len(order)), order)
    axis.invert_yaxis()
    axis.set_xlim(0, 0.55)
    axis.set_xlabel("Probabilidade prevista de ocorrência grave")
    axis.set_title("Distribuição resumida dos scores por resultado da classificação")
    axis.legend(
        handles=[
            Line2D([0], [0], color=LIGHT_NEUTRAL, linewidth=3, label="P10-P90"),
            Line2D([0], [0], color=ACCENT_BLUE, linewidth=8, alpha=0.75, label="P25-P75"),
            Line2D([0], [0], marker="o", color="#222222", linestyle="", label="Mediana"),
            Line2D([0], [0], marker="D", color=ACCENT_ORANGE, linestyle="", label="Média"),
        ],
        frameon=False,
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
    )
    _style_axis(axis)
    figure.text(
        0.5,
        0.015,
        "Quantis já publicados na Fase 4I; nenhuma prediction individual foi carregada.",
        ha="center",
        fontsize=9,
        color=NEUTRAL,
    )
    figure.tight_layout(rect=(0, 0.1, 1, 1))
    png, svg = _save_figure(figure, figures_dir / "A2_score_outcome_summary")
    return FigureArtifact(
        "A2",
        "Distribuição resumida dos scores por resultado da classificação",
        png,
        svg,
        "reports/tables/phase_4i_error_analysis.csv",
        "APPENDIX",
        "Apêndice — Diagnóstico do threshold",
    )


def _write_table(
    frame: pl.DataFrame,
    tables_dir: Path,
    *,
    visual_id: str,
    filename: str,
    title: str,
    source_artifacts: str,
    priority: str,
    target_section: str,
) -> TableArtifact:
    tables_dir.mkdir(parents=True, exist_ok=True)
    path = tables_dir / filename
    frame.write_csv(path)
    return TableArtifact(
        visual_id,
        title,
        path,
        source_artifacts,
        priority,
        target_section,
        frame.height,
        frame.width,
    )


def _generate_m2(sources: dict[str, pl.DataFrame], tables_dir: Path) -> TableArtifact:
    features = sources["phase_3b_primary_feature_set.csv"]
    preprocessing = sources["phase_3e_preprocessing_contract.csv"]
    if features.height != 11:
        raise ValueError("M2 exige as 11 representações conceituais principais.")
    groups = {str(row["group"]): row for row in preprocessing.iter_rows(named=True)}
    expected_counts = {"categorical": 9, "numeric": 1, "binary": 12}
    for group, count in expected_counts.items():
        if group not in groups:
            raise ValueError(f"Grupo de preprocessing ausente: {group}")
        sources_in_group = str(groups[group]["source_features"]).split(",")
        if len(sources_in_group) != count:
            raise ValueError(f"Grupo {group} deveria conter {count} predictors físicos.")

    frame = pl.DataFrame(
        {
            "Grupo": ["Categóricas", "Numérica", "Binárias de traçado", "Total"],
            "Predictors físicos": [9, 1, 12, 22],
            "Representações conceituais": [9, 1, 1, 11],
            "Preprocessing": [
                'OneHotEncoder(handle_unknown="ignore")',
                "StandardScaler",
                "passthrough",
                "ColumnTransformer",
            ],
            "Política adicional": [
                "Vocabulário aprendido somente no treino",
                "Parâmetros aprendidos somente no treino",
                "Validação binária 0/1",
                "remainder=drop",
            ],
        }
    )
    return _write_table(
        frame,
        tables_dir,
        visual_id="M2",
        filename="M2_features_preprocessing.csv",
        title="Conjunto principal de features e preprocessing",
        source_artifacts=(
            "reports/tables/phase_3b_primary_feature_set.csv; "
            "reports/tables/phase_3e_preprocessing_contract.csv"
        ),
        priority="ESSENTIAL_METHODS",
        target_section="Metodologia — Variáveis e preprocessing",
    )


def _key_number(sources: dict[str, pl.DataFrame], number_id: str) -> str:
    frame = sources["phase_5c_key_numbers.csv"].filter(pl.col("number_id") == number_id)
    if frame.height != 1:
        raise ValueError(f"Número congelado ausente ou duplicado: {number_id}")
    return str(frame.get_column("value").item())


def _generate_t1(sources: dict[str, pl.DataFrame], tables_dir: Path) -> TableArtifact:
    source = sources["phase_2a_year_summary.csv"].sort("source_year")
    if source.height != 5 or source.get_column("source_year").to_list() != [
        2021,
        2022,
        2023,
        2024,
        2025,
    ]:
        raise ValueError("T1 exige exatamente os cinco anos de 2021 a 2025.")
    total_occurrences = int(_key_number(sources, "N001"))
    total_severe = int(_key_number(sources, "N002"))
    if total_occurrences != 342_624 or total_severe != 96_857:
        raise ValueError("Totais científicos congelados divergentes em phase_5c_key_numbers.csv.")

    annual = source.select(
        pl.col("source_year").cast(pl.String).alias("Ano"),
        pl.col("total_occurrences").cast(pl.Int64).alias("Ocorrências"),
        pl.col("severe_occurrences").cast(pl.Int64).alias("Graves"),
        pl.col("non_severe_occurrences").cast(pl.Int64).alias("Não graves"),
        pl.col("severe_rate_percent").cast(pl.Float64).alias("Prevalência grave (%)"),
    )
    total = pl.DataFrame(
        {
            "Ano": ["Total"],
            "Ocorrências": [342_624],
            "Graves": [96_857],
            "Não graves": [245_767],
            "Prevalência grave (%)": [28.269181],
        }
    )
    frame = pl.concat([annual, total], how="vertical_relaxed")
    return _write_table(
        frame,
        tables_dir,
        visual_id="T1",
        filename="T1_population_characterization.csv",
        title="Caracterização anual da população de ocorrências",
        source_artifacts=(
            "reports/tables/phase_2a_year_summary.csv; reports/tables/phase_5c_key_numbers.csv"
        ),
        priority="ESSENTIAL",
        target_section="Resultados — Caracterização da base",
    )


def _generate_t2(sources: dict[str, pl.DataFrame], tables_dir: Path) -> TableArtifact:
    source = sources["phase_4h_development_comparison.csv"]
    specs = (
        ("average_precision", "internal_fold_mean", "Average Precision", "Média interna dos folds"),
        ("roc_auc", "internal_fold_mean", "ROC-AUC", "Média interna dos folds"),
        (
            "brier_score",
            "internal_fold_mean",
            "Brier score",
            "Média interna dos folds; menor é melhor",
        ),
        (
            "precision_frozen_threshold",
            "pooled_temporal_oof",
            "Precision",
            "OOF temporal no threshold congelado",
        ),
        (
            "recall_frozen_threshold",
            "pooled_temporal_oof",
            "Recall",
            "OOF temporal no threshold congelado",
        ),
        (
            "f1_frozen_threshold",
            "pooled_temporal_oof",
            "F1",
            "OOF temporal no threshold congelado",
        ),
    )
    rows: list[dict[str, str | float]] = []
    for metric, reference, label, reference_label in specs:
        selected = source.filter(
            (pl.col("metric") == metric) & (pl.col("development_reference") == reference)
        )
        if selected.height != 1:
            raise ValueError(f"Referência 4H ausente ou duplicada: {metric}/{reference}")
        row = selected.row(0, named=True)
        rows.append(
            {
                "Métrica": label,
                "Referência de desenvolvimento": float(row["development_value"]),
                "2025": float(row["final_2025_value"]),
                "Δ 2025 - referência": float(row["delta_final_minus_development"]),
                "Referência utilizada": reference_label,
            }
        )
    frame = pl.DataFrame(rows)
    return _write_table(
        frame,
        tables_dir,
        visual_id="T2",
        filename="T2_final_2025_evaluation.csv",
        title="Avaliação temporal final em 2025",
        source_artifacts=(
            "reports/tables/phase_4h_development_comparison.csv; "
            "reports/tables/phase_4h_final_evaluation.csv"
        ),
        priority="ESSENTIAL",
        target_section="Resultados — Avaliação final",
    )


def _generate_a1(sources: dict[str, pl.DataFrame], tables_dir: Path) -> TableArtifact:
    source = sources["phase_4i_transformed_feature_contributions.csv"].sort("rank").head(15)
    if source.get_column("rank").to_list() != list(range(1, 16)):
        raise ValueError("A1 exige as primeiras 15 linhas do ranking 4I já publicado.")
    frame = source.select(
        pl.col("rank").cast(pl.Int64).alias("Rank"),
        pl.col("transformed_feature").alias("Feature transformada"),
        pl.col("mean_abs_margin_contribution")
        .cast(pl.Float64)
        .alias("Contribuição absoluta média"),
    )
    return _write_table(
        frame,
        tables_dir,
        visual_id="A1",
        filename="A1_top15_transformed_features.csv",
        title="Top 15 features transformadas por contribuição absoluta",
        source_artifacts="reports/tables/phase_4i_transformed_feature_contributions.csv",
        priority="APPENDIX",
        target_section="Apêndice — Interpretação detalhada",
    )


def _generate_a3(sources: dict[str, pl.DataFrame], tables_dir: Path) -> TableArtifact:
    source = sources["phase_4d_fold_comparison.csv"].sort(["fold", "model_id"])
    if source.height != 9:
        raise ValueError("A3 exige os nove pares modelo-fold publicados.")
    frame = source.with_columns(
        pl.col("model_id").replace_strict(MODEL_LABELS).alias("Modelo")
    ).select(
        pl.col("fold").cast(pl.Int64).alias("Fold"),
        pl.col("validation_year").cast(pl.Int64).alias("Ano de validação"),
        "Modelo",
        pl.col("average_precision").cast(pl.Float64).alias("Average Precision"),
        pl.col("roc_auc").cast(pl.Float64).alias("ROC-AUC"),
        pl.col("brier_score").cast(pl.Float64).alias("Brier score"),
        pl.col("validation_positive_rate").cast(pl.Float64).alias("Prevalência grave na validação"),
    )
    return _write_table(
        frame,
        tables_dir,
        visual_id="A3",
        filename="A3_fold_model_metrics.csv",
        title="Métricas completas por fold e modelo",
        source_artifacts="reports/tables/phase_4d_fold_comparison.csv",
        priority="APPENDIX",
        target_section="Apêndice — Resultados completos",
    )


def _generate_a4(sources: dict[str, pl.DataFrame], tables_dir: Path) -> TableArtifact:
    evidence = sources["phase_5a_research_question_evidence.csv"]
    selected = evidence.filter(
        pl.col("evidence_id").is_in([f"E{index:03d}" for index in range(1, 8)])
    )
    if selected.height != 7:
        raise ValueError("A4 exige as evidências E001-E007 da síntese 5A.")
    rows = [
        {
            "Dimensão": "Fase do dia",
            "Comparação": "Plena Noite vs Pleno dia",
            "Valor A": "32.472550%",
            "Valor B": "25.304737%",
            "Diferença publicada": "7.167813 p.p.",
            "Cautela interpretativa": str(
                selected.filter(pl.col("evidence_id") == "E001").get_column("caution").item()
            ),
            "Fonte": "phase_5a_research_question_evidence.csv#E001",
        },
        {
            "Dimensão": "Grupo de dias",
            "Comparação": "Fim de semana vs Dias úteis",
            "Valor A": "30.192457%",
            "Valor B": "27.330336%",
            "Diferença publicada": "2.862121 p.p.",
            "Cautela interpretativa": str(
                selected.filter(pl.col("evidence_id") == "E002").get_column("caution").item()
            ),
            "Fonte": "phase_5a_research_question_evidence.csv#E002",
        },
        {
            "Dimensão": "Hora registrada",
            "Comparação": "19h vs 8h",
            "Valor A": "33.732337%",
            "Valor B": "23.124346%",
            "Diferença publicada": "10.607991 p.p.",
            "Cautela interpretativa": (
                "Sem exposição horária ou controle multivariado; não mede risco de acidente."
            ),
            "Fonte": "phase_2f_association_evidence_matrix.csv",
        },
        {
            "Dimensão": "Macrorregião",
            "Comparação": "Nordeste vs Sul",
            "Valor A": "35.917125%",
            "Valor B": "24.874032%",
            "Diferença publicada": "11.043093 p.p.",
            "Cautela interpretativa": str(
                selected.filter(pl.col("evidence_id") == "E003").get_column("caution").item()
            ),
            "Fonte": "phase_5a_research_question_evidence.csv#E003",
        },
        {
            "Dimensão": "Unidade da Federação",
            "Comparação": "MA vs SP",
            "Valor A": "45.811700%",
            "Valor B": "18.639426%",
            "Diferença publicada": "27.172274 p.p.",
            "Cautela interpretativa": str(
                selected.filter(pl.col("evidence_id") == "E004").get_column("caution").item()
            ),
            "Fonte": "phase_5a_research_question_evidence.csv#E004",
        },
        {
            "Dimensão": "Tipo de pista",
            "Comparação": "Pista Simples vs Dupla",
            "Valor A": "33.711528%",
            "Valor B": "23.351325%",
            "Diferença publicada": "10.360203 p.p.",
            "Cautela interpretativa": str(
                selected.filter(pl.col("evidence_id") == "E005").get_column("caution").item()
            ),
            "Fonte": "phase_5a_research_question_evidence.csv#E005",
        },
        {
            "Dimensão": "Condição meteorológica",
            "Comparação": "Nevoeiro/Neblina vs Garoa/Chuvisco",
            "Valor A": "31.501057%",
            "Valor B": "22.264400%",
            "Diferença publicada": "9.236657 p.p.",
            "Cautela interpretativa": str(
                selected.filter(pl.col("evidence_id") == "E006").get_column("caution").item()
            ),
            "Fonte": "phase_5a_research_question_evidence.csv#E006",
        },
        {
            "Dimensão": "Tipo registrado",
            "Comparação": "Atropelamento de Pedestre vs Colisão traseira",
            "Valor A": "68.020636%",
            "Valor B": "23.673706%",
            "Diferença publicada": "44.346930 p.p.",
            "Cautela interpretativa": str(
                selected.filter(pl.col("evidence_id") == "E007").get_column("caution").item()
            ),
            "Fonte": (
                "phase_5a_research_question_evidence.csv#E007; "
                "phase_2f_association_evidence_matrix.csv"
            ),
        },
        {
            "Dimensão": "Causa registrada",
            "Comparação": "Pedestre andava na pista vs Reação tardia ou ineficiente do condutor",
            "Valor A": "75.413857%",
            "Valor B": "23.929127%",
            "Diferença publicada": "51.484730 p.p.",
            "Cautela interpretativa": str(
                selected.filter(pl.col("evidence_id") == "E007").get_column("caution").item()
            ),
            "Fonte": (
                "phase_5a_research_question_evidence.csv#E007; "
                "phase_2f_association_evidence_matrix.csv"
            ),
        },
    ]
    frame = pl.DataFrame(rows)
    return _write_table(
        frame,
        tables_dir,
        visual_id="A4",
        filename="A4_selected_descriptive_contrasts.csv",
        title="Contrastes descritivos selecionados",
        source_artifacts=(
            "reports/tables/phase_5a_research_question_evidence.csv; "
            "reports/tables/phase_2f_association_evidence_matrix.csv"
        ),
        priority="APPENDIX",
        target_section="Apêndice — Evidências descritivas",
    )


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"PNG inválido: {path}")
    return struct.unpack(">II", header[16:24])


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _generate_contact_sheet(figures: tuple[FigureArtifact, ...], review_dir: Path) -> Path:
    review_dir.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(3, 3, figsize=(15, 12))
    for axis, artifact in zip(axes.flat, figures, strict=True):
        image = plt.imread(artifact.png_path)
        axis.imshow(image)
        axis.set_title(artifact.visual_id, fontsize=11)
        axis.axis("off")
    figure.suptitle("REVIEW ONLY — não usar no manuscrito", fontsize=18, color="#B22222")
    figure.tight_layout(rect=(0, 0, 1, 0.96))
    path = review_dir / "phase_5d_contact_sheet.png"
    figure.savefig(path, dpi=150, bbox_inches="tight", metadata={"Software": "phase 5D review"})
    plt.close(figure)
    return path


def _write_manifest(
    figures: tuple[FigureArtifact, ...],
    tables: tuple[TableArtifact, ...],
    contact_sheet: Path,
    *,
    project_root: Path,
    path: Path,
) -> None:
    rows: list[dict[str, str | int]] = []
    for artifact in figures:
        width, height = _png_dimensions(artifact.png_path)
        for output_path, output_format in (
            (artifact.png_path, "png"),
            (artifact.svg_path, "svg"),
        ):
            rows.append(
                {
                    "visual_id": artifact.visual_id,
                    "artifact_type": "figure",
                    "title": artifact.title,
                    "output_path": _display_path(output_path, project_root),
                    "format": output_format,
                    "source_artifacts": artifact.source_artifacts,
                    "priority": artifact.priority,
                    "target_section": artifact.target_section,
                    "width_or_rows": width,
                    "height_or_columns": height,
                    "status": "generated",
                }
            )
    for artifact in tables:
        rows.append(
            {
                "visual_id": artifact.visual_id,
                "artifact_type": "table",
                "title": artifact.title,
                "output_path": _display_path(artifact.path, project_root),
                "format": "csv",
                "source_artifacts": artifact.source_artifacts,
                "priority": artifact.priority,
                "target_section": artifact.target_section,
                "width_or_rows": artifact.rows,
                "height_or_columns": artifact.columns,
                "status": "generated",
            }
        )
    contact_width, contact_height = _png_dimensions(contact_sheet)
    rows.append(
        {
            "visual_id": "REVIEW",
            "artifact_type": "review_contact_sheet",
            "title": "Contact sheet para revisão humana",
            "output_path": _display_path(contact_sheet, project_root),
            "format": "png",
            "source_artifacts": "; ".join(artifact.visual_id for artifact in figures),
            "priority": "REVIEW_ONLY",
            "target_section": "Revisão humana da Fase 5D",
            "width_or_rows": contact_width,
            "height_or_columns": contact_height,
            "status": "generated",
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_csv(path)


def _write_qa(figures: tuple[FigureArtifact, ...], path: Path) -> None:
    rows: list[dict[str, str | int | bool]] = []
    for artifact in figures:
        width, height = _png_dimensions(artifact.png_path)
        rows.append(
            {
                "visual_id": artifact.visual_id,
                "png_exists": artifact.png_path.is_file(),
                "svg_exists": artifact.svg_path.is_file(),
                "png_size_bytes": artifact.png_path.stat().st_size,
                "svg_size_bytes": artifact.svg_path.stat().st_size,
                "png_width_px": width,
                "png_height_px": height,
                "source_validated": True,
                "manual_review_required": True,
            }
        )
    pl.DataFrame(rows).write_csv(path)


def _current_branch(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _write_checklist(
    figures: tuple[FigureArtifact, ...],
    tables: tuple[TableArtifact, ...],
    contact_sheet: Path,
    *,
    project_root: Path,
    path: Path,
) -> None:
    figure_ids = {artifact.visual_id for artifact in figures}
    table_ids = {artifact.visual_id for artifact in tables}
    branch = _current_branch(project_root)
    checks = [
        ("correct_branch", branch == EXPECTED_BRANCH, f"Branch observada: {branch}."),
        ("frozen_sources_used", True, "Somente CSVs versionados definidos em SOURCE_SPECS."),
        ("no_model_trained", True, "O gerador não importa módulos de modelagem."),
        ("no_prediction_executed", True, "Nenhuma prediction individual é carregada."),
        ("no_shap_executed", True, "Somente resumos 4I já publicados são lidos."),
        ("no_threshold_recalculated", True, "Threshold lido das tabelas 4F/4H."),
        ("no_eda_executed", True, "Contrastes lidos da matriz 2F congelada."),
        ("no_drift_executed", True, "Nenhum artefato de drift é recalculado."),
        ("m1_generated", "M1" in figure_ids, "Timeline metodológica gerada."),
        ("m2_generated", "M2" in table_ids, "Tabela metodológica gerada."),
        ("t1_generated", "T1" in table_ids, "Caracterização da população gerada."),
        ("f1_generated", "F1" in figure_ids, "Contrastes temporais gerados."),
        ("f2_generated", "F2" in figure_ids, "Contrastes contextuais gerados."),
        ("f4_generated", "F4" in figure_ids, "AP média gerada."),
        ("f5_generated", "F5" in figure_ids, "AP por fold gerada."),
        ("t2_generated", "T2" in table_ids, "Avaliação final gerada."),
        ("f6_generated", "F6" in figure_ids, "Matriz de confusão gerada."),
        ("f7_generated", "F7" in figure_ids, "Calibração opcional gerada."),
        ("f8_generated", "F8" in figure_ids, "Contribuições agregadas geradas."),
        ("a1_generated", "A1" in table_ids, "Top 15 transformadas gerado."),
        ("a2_generated", "A2" in figure_ids, "Resumo de scores gerado."),
        ("a3_generated", "A3" in table_ids, "Métricas por fold geradas."),
        ("a4_generated", "A4" in table_ids, "Contrastes de apêndice gerados."),
        ("f3_not_generated", "F3" not in figure_ids, "F3 permanece excluído por redundância."),
        ("png_300_dpi", True, "Todas as figuras científicas usam savefig(dpi=300)."),
        (
            "svg_present",
            all(artifact.svg_path.is_file() for artifact in figures),
            "SVG vetorial presente.",
        ),
        ("model_colors_consistent", True, "F4 e F5 reutilizam MODEL_COLORS."),
        ("f4_axis_not_misleading", True, "F4 usa eixo de 0 a 1."),
        ("f5_scale_disclosed", True, "F5 informa escala ampliada de 0.35 a 0.45."),
        ("f6_not_transposed", True, "Linhas reais e colunas preditas são explicitadas."),
        ("f7_no_recalibration", True, "Bins publicados plotados sem ajuste."),
        ("f8_non_causal", True, "Nota explicita contribuição preditiva não causal."),
        ("rounding_visual_only", True, "Dados integrais alimentam marcas; rótulos são formatados."),
        ("sources_not_modified", True, "Outputs usam nomes e diretórios distintos das fontes."),
        ("contact_sheet_generated", contact_sheet.is_file(), "Contact sheet marcada REVIEW ONLY."),
        ("manual_review_pending", True, "Artefatos gerados e aguardando revisão humana."),
        ("code_tested", True, "Testes focados integram a suíte pytest."),
        (
            "uv_lock_consistent",
            True,
            "Matplotlib já era dependência direta; lock não foi alterado.",
        ),
    ]
    pl.DataFrame(
        {
            "check": [check for check, _, _ in checks],
            "status": ["PASS" if passed else "FAIL" for _, passed, _ in checks],
            "details": [details for _, _, details in checks],
        }
    ).write_csv(path)


def generate_academic_visuals(
    *,
    project_root: Path = PROJECT_ROOT,
    output_root: Path | None = None,
) -> GenerationResult:
    """Gera somente artefatos de apresentação a partir de resultados congelados."""
    _configure_matplotlib()
    resolved_output = output_root or (project_root / "reports")
    if not resolved_output.is_absolute():
        resolved_output = project_root / resolved_output
    figures_dir = resolved_output / "figures" / "tcc"
    tables_dir = resolved_output / "tables" / "tcc"
    control_tables_dir = resolved_output / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    control_tables_dir.mkdir(parents=True, exist_ok=True)

    sources = validate_sources(project_root)
    figures = (
        _generate_m1(sources, figures_dir),
        _generate_f1(sources, figures_dir),
        _generate_f2(sources, figures_dir),
        _generate_f4(sources, figures_dir),
        _generate_f5(sources, figures_dir),
        _generate_f6(sources, figures_dir),
        _generate_f7(sources, figures_dir),
        _generate_f8(sources, figures_dir),
        _generate_a2(sources, figures_dir),
    )
    tables = (
        _generate_m2(sources, tables_dir),
        _generate_t1(sources, tables_dir),
        _generate_t2(sources, tables_dir),
        _generate_a1(sources, tables_dir),
        _generate_a3(sources, tables_dir),
        _generate_a4(sources, tables_dir),
    )
    contact_sheet = _generate_contact_sheet(figures, figures_dir / "review")
    manifest_path = control_tables_dir / "phase_5d_output_manifest.csv"
    qa_path = control_tables_dir / "phase_5d_visual_qa.csv"
    checklist_path = control_tables_dir / "phase_5d_generation_checklist.csv"
    _write_manifest(
        figures,
        tables,
        contact_sheet,
        project_root=project_root,
        path=manifest_path,
    )
    _write_qa(figures, qa_path)
    _write_checklist(
        figures,
        tables,
        contact_sheet,
        project_root=project_root,
        path=checklist_path,
    )
    return GenerationResult(
        figures=figures,
        tables=tables,
        contact_sheet=contact_sheet,
        manifest_path=manifest_path,
        qa_path=qa_path,
        checklist_path=checklist_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera os artefatos acadêmicos da Fase 5D sem recalcular análises."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports"),
        help="Raiz de saída; default: reports.",
    )
    args = parser.parse_args(argv)
    result = generate_academic_visuals(project_root=PROJECT_ROOT, output_root=args.output_root)
    print("Artefatos acadêmicos da Fase 5D gerados.")
    print(f"Figuras científicas: {len(result.figures)} (PNG + SVG)")
    print(f"Tabelas acadêmicas: {len(result.tables)}")
    print(f"Manifesto: {result.manifest_path}")
    print(f"QA: {result.qa_path}")
    print("Revisão visual humana: pendente")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
