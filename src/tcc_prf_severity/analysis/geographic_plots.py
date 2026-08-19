from pathlib import Path

import matplotlib
import polars as pl

from tcc_prf_severity.analysis.geographic import GeographicAnalysis

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def _write_vertical_bar(
    table: pl.DataFrame,
    category: str,
    value: str,
    title: str,
    x_label: str,
    y_label: str,
    path: Path,
    *,
    percentage: bool = False,
) -> None:
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(
        [str(item) for item in table.get_column(category).to_list()],
        table.get_column(value).to_list(),
    )
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    if percentage:
        values = table.get_column(value).to_list()
        axis.set_ylim(0, max(35, max(values) * 1.1))
    else:
        axis.ticklabel_format(axis="y", style="plain")
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def _write_horizontal_bar(
    table: pl.DataFrame,
    category: str,
    value: str,
    title: str,
    x_label: str,
    y_label: str,
    path: Path,
    *,
    percentage: bool = False,
    figsize: tuple[float, float] = (9, 7),
) -> None:
    ordered = table.sort(value)
    figure, axis = plt.subplots(figsize=figsize)
    axis.barh(
        [str(item) for item in ordered.get_column(category).to_list()],
        ordered.get_column(value).to_list(),
    )
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    if percentage:
        values = ordered.get_column(value).to_list()
        axis.set_xlim(0, max(45, max(values) * 1.1))
    else:
        axis.ticklabel_format(axis="x", style="plain")
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def write_geographic_figures(analysis: GeographicAnalysis, output_dir: Path) -> tuple[Path, ...]:
    """Gera as seis figuras científicas previstas para a Fase 2C."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = tuple(
        output_dir / filename
        for filename in (
            "phase_2c_occurrences_by_macroregion.png",
            "phase_2c_severe_rate_by_macroregion.png",
            "phase_2c_occurrences_by_uf.png",
            "phase_2c_severe_rate_by_uf.png",
            "phase_2c_br_volume_top15.png",
            "phase_2c_municipality_volume_top15.png",
        )
    )
    _write_vertical_bar(
        analysis.macroregion_summary,
        "macroregion",
        "total_occurrences",
        "Ocorrências registradas por macrorregião",
        "Macrorregião",
        "Número de ocorrências registradas",
        paths[0],
    )
    _write_vertical_bar(
        analysis.macroregion_summary,
        "macroregion",
        "severe_rate_percent",
        "Proporção de ocorrências graves por macrorregião",
        "Macrorregião",
        "Ocorrências graves (%)",
        paths[1],
        percentage=True,
    )
    _write_horizontal_bar(
        analysis.uf_summary,
        "uf",
        "total_occurrences",
        "Ocorrências registradas por UF",
        "Número de ocorrências registradas",
        "UF",
        paths[2],
        figsize=(9, 10),
    )
    _write_horizontal_bar(
        analysis.uf_summary,
        "uf",
        "severe_rate_percent",
        "Proporção de ocorrências graves por UF",
        "Ocorrências graves (%)",
        "UF",
        paths[3],
        percentage=True,
        figsize=(9, 10),
    )
    _write_horizontal_bar(
        analysis.br_volume_top15,
        "br_label",
        "total_occurrences",
        "BRs com maior volume de ocorrências registradas",
        "Número de ocorrências registradas",
        "BR",
        paths[4],
    )
    _write_horizontal_bar(
        analysis.municipality_volume_top15,
        "municipality_label",
        "total_occurrences",
        "Municípios/UF com maior volume de ocorrências registradas",
        "Número de ocorrências registradas",
        "Município/UF",
        paths[5],
        figsize=(10, 8),
    )
    return paths
