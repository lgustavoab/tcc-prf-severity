from pathlib import Path

import matplotlib
import polars as pl

from tcc_prf_severity.analysis.occurrence_dynamics import OccurrenceDynamicsAnalysis

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def _sample_labels(table: pl.DataFrame, category: str) -> list[str]:
    return [
        f"{label}\n(n={total:,})".replace(",", ".")
        for label, total in zip(
            table.get_column(category).to_list(),
            table.get_column("total_occurrences").to_list(),
            strict=True,
        )
    ]


def _write_horizontal_ranking(
    table: pl.DataFrame,
    category: str,
    value: str,
    title: str,
    x_label: str,
    y_label: str,
    path: Path,
    *,
    show_sample: bool = False,
    percentage: bool = False,
) -> None:
    ordered = table.sort(value)
    labels = (
        _sample_labels(ordered, category)
        if show_sample
        else [str(item) for item in ordered.get_column(category).to_list()]
    )
    values = ordered.get_column(value).to_list()
    figure, axis = plt.subplots(figsize=(11, 8))
    axis.barh(labels, values)
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    if percentage:
        axis.set_xlim(0, max(50, max(values) * 1.1))
    else:
        axis.ticklabel_format(axis="x", style="plain")
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def _write_exact_distribution(
    table: pl.DataFrame, column: str, title: str, x_label: str, path: Path
) -> None:
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(
        table.get_column(column).to_list(),
        table.get_column("total_occurrences").to_list(),
    )
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel("Número de ocorrências registradas (escala logarítmica)")
    axis.set_yscale("log")
    axis.ticklabel_format(axis="x", style="plain")
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def write_occurrence_dynamics_figures(
    analysis: OccurrenceDynamicsAnalysis, output_dir: Path
) -> tuple[Path, ...]:
    """Gera as seis figuras científicas previstas para a Fase 2E."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = tuple(
        output_dir / filename
        for filename in (
            "phase_2e_accident_type_volume_top15.png",
            "phase_2e_accident_type_severe_rate_top15_n500.png",
            "phase_2e_cause_volume_top15.png",
            "phase_2e_cause_severe_rate_top15_n500.png",
            "phase_2e_people_distribution.png",
            "phase_2e_vehicle_distribution.png",
        )
    )
    _write_horizontal_ranking(
        analysis.accident_type_volume_top15,
        "tipo_acidente",
        "total_occurrences",
        "Tipos de acidente registrados com maior volume",
        "Número de ocorrências registradas",
        "Tipo de acidente registrado",
        paths[0],
    )
    _write_horizontal_ranking(
        analysis.accident_type_severe_rate_top15,
        "tipo_acidente",
        "severe_rate_percent",
        "Proporção grave por tipo de acidente registrado (n ≥ 500)",
        "Ocorrências graves (%)",
        "Tipo de acidente registrado",
        paths[1],
        show_sample=True,
        percentage=True,
    )
    _write_horizontal_ranking(
        analysis.cause_volume_top15,
        "causa_acidente",
        "total_occurrences",
        "Causas registradas pela PRF com maior volume",
        "Número de ocorrências registradas",
        "Causa registrada pela PRF",
        paths[2],
    )
    _write_horizontal_ranking(
        analysis.cause_severe_rate_top15,
        "causa_acidente",
        "severe_rate_percent",
        "Proporção grave por causa registrada pela PRF (n ≥ 500)",
        "Ocorrências graves (%)",
        "Causa registrada pela PRF",
        paths[3],
        show_sample=True,
        percentage=True,
    )
    _write_exact_distribution(
        analysis.people_distribution,
        "pessoas",
        "Distribuição exata do número de pessoas envolvidas",
        "Pessoas envolvidas",
        paths[4],
    )
    _write_exact_distribution(
        analysis.vehicle_distribution,
        "veiculos",
        "Distribuição exata do número de veículos envolvidos",
        "Veículos envolvidos",
        paths[5],
    )
    return paths
