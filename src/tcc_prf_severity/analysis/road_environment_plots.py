from pathlib import Path

import matplotlib
import polars as pl

from tcc_prf_severity.analysis.road_environment import (
    MIN_RATE_HIGHLIGHT_OCCURRENCES,
    RoadEnvironmentAnalysis,
)

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def _category_with_sample(table: pl.DataFrame, category: str) -> list[str]:
    return [
        f"{label}\n(n={total:,})".replace(",", ".")
        for label, total in zip(
            table.get_column(category).to_list(),
            table.get_column("total_occurrences").to_list(),
            strict=True,
        )
    ]


def _write_vertical_rate(
    table: pl.DataFrame,
    category: str,
    title: str,
    x_label: str,
    path: Path,
) -> None:
    rates = table.get_column("severe_rate_percent").to_list()
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(_category_with_sample(table, category), rates)
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel("Ocorrências graves (%)")
    axis.set_ylim(0, max(40, max(rates) * 1.1))
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def _write_horizontal_rate(
    table: pl.DataFrame,
    category: str,
    title: str,
    y_label: str,
    path: Path,
) -> None:
    ordered = table.reverse()
    rates = ordered.get_column("severe_rate_percent").to_list()
    figure, axis = plt.subplots(figsize=(10, 7))
    axis.barh(_category_with_sample(ordered, category), rates)
    axis.set_title(title)
    axis.set_xlabel("Ocorrências graves (%)")
    axis.set_ylabel(y_label)
    axis.set_xlim(0, max(45, max(rates) * 1.1))
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def write_road_environment_figures(
    analysis: RoadEnvironmentAnalysis, output_dir: Path
) -> tuple[Path, ...]:
    """Gera as quatro figuras científicas previstas para a Fase 2D."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = tuple(
        output_dir / filename
        for filename in (
            "phase_2d_severe_rate_by_road_type.png",
            "phase_2d_severe_rate_by_land_use.png",
            "phase_2d_severe_rate_by_weather.png",
            "phase_2d_severe_rate_by_road_layout_component.png",
        )
    )
    _write_vertical_rate(
        analysis.road_type_summary,
        "tipo_pista",
        "Proporção de ocorrências graves por tipo de pista",
        "Tipo de pista",
        paths[0],
    )
    _write_vertical_rate(
        analysis.land_use_summary,
        "uso_solo",
        "Proporção de ocorrências graves por uso do solo",
        "Uso do solo conforme campo da PRF",
        paths[1],
    )
    _write_horizontal_rate(
        analysis.weather_rate_highlights,
        "condicao_metereologica",
        "Proporção grave por condição meteorológica informada (n ≥ 500)",
        "Condição meteorológica",
        paths[2],
    )
    components = analysis.road_layout_component_summary.filter(
        pl.col("total_occurrences") >= MIN_RATE_HIGHLIGHT_OCCURRENCES
    )
    _write_horizontal_rate(
        components,
        "road_layout_component",
        "Proporção grave por componente de traçado (n ≥ 500)",
        "Componente não exclusivo",
        paths[3],
    )
    return paths
