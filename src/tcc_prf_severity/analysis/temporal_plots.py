from pathlib import Path

import matplotlib
import polars as pl

from tcc_prf_severity.analysis.temporal import TemporalAnalysis

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def _labels(table: pl.DataFrame, category: str) -> list[str]:
    return [str(value) for value in table.get_column(category).to_list()]


def _write_bar(
    table: pl.DataFrame,
    category: str,
    value: str,
    title: str,
    x_label: str,
    y_label: str,
    path: Path,
    rotate: int = 0,
) -> None:
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(_labels(table, category), table.get_column(value).to_list())
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.tick_params(axis="x", labelrotation=rotate)
    axis.ticklabel_format(axis="y", style="plain")
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def _write_rate(
    table: pl.DataFrame,
    category: str,
    title: str,
    x_label: str,
    path: Path,
    rotate: int = 0,
) -> None:
    rates = table.get_column("severe_rate_percent").to_list()
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.plot(_labels(table, category), rates, marker="o")
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel("Ocorrências graves (%)")
    axis.set_ylim(0, max(35, max(rates) * 1.1))
    axis.tick_params(axis="x", labelrotation=rotate)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def write_temporal_figures(analysis: TemporalAnalysis, output_dir: Path) -> tuple[Path, ...]:
    """Gera as sete figuras científicas previstas para a Fase 2B."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = tuple(
        output_dir / filename
        for filename in (
            "phase_2b_occurrences_by_month.png",
            "phase_2b_severe_rate_by_month.png",
            "phase_2b_occurrences_by_weekday.png",
            "phase_2b_severe_rate_by_weekday.png",
            "phase_2b_occurrences_by_hour.png",
            "phase_2b_severe_rate_by_hour.png",
            "phase_2b_severe_rate_by_day_phase.png",
        )
    )
    _write_bar(
        analysis.month_summary,
        "month_name",
        "total_occurrences",
        "Ocorrências registradas por mês",
        "Mês",
        "Número de ocorrências registradas",
        paths[0],
        30,
    )
    _write_rate(
        analysis.month_summary,
        "month_name",
        "Proporção de ocorrências graves por mês",
        "Mês",
        paths[1],
        30,
    )
    _write_bar(
        analysis.weekday_summary,
        "dia_semana",
        "total_occurrences",
        "Ocorrências registradas por dia da semana",
        "Dia da semana",
        "Número de ocorrências registradas",
        paths[2],
        25,
    )
    _write_rate(
        analysis.weekday_summary,
        "dia_semana",
        "Proporção de ocorrências graves por dia da semana",
        "Dia da semana",
        paths[3],
        25,
    )
    _write_bar(
        analysis.hour_summary,
        "hour",
        "total_occurrences",
        "Ocorrências registradas por hora",
        "Hora",
        "Número de ocorrências registradas",
        paths[4],
    )
    _write_rate(
        analysis.hour_summary,
        "hour",
        "Proporção de ocorrências graves por hora",
        "Hora",
        paths[5],
    )
    _write_rate(
        analysis.day_phase_summary,
        "fase_dia",
        "Proporção de ocorrências graves por fase do dia",
        "Fase do dia",
        paths[6],
        15,
    )
    return paths
