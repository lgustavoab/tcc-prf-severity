from pathlib import Path

import matplotlib
import polars as pl

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def _year_labels(summary: pl.DataFrame) -> list[str]:
    return [str(year) for year in summary.get_column("source_year").to_list()]


def write_general_figures(summary: pl.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    """Gera as duas figuras científicas previstas para a caracterização geral."""
    output_dir.mkdir(parents=True, exist_ok=True)
    years = _year_labels(summary)

    occurrences_path = output_dir / "phase_2a_occurrences_by_year.png"
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(years, summary.get_column("total_occurrences").to_list())
    axis.set_title("Ocorrências registradas por ano")
    axis.set_xlabel("Ano")
    axis.set_ylabel("Número de ocorrências registradas")
    axis.ticklabel_format(axis="y", style="plain")
    figure.tight_layout()
    figure.savefig(occurrences_path, dpi=300, bbox_inches="tight")
    plt.close(figure)

    severe_rate_path = output_dir / "phase_2a_severe_rate_by_year.png"
    rates = summary.get_column("severe_rate_percent").to_list()
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(years, rates, marker="o")
    axis.set_title("Proporção de ocorrências graves por ano")
    axis.set_xlabel("Ano")
    axis.set_ylabel("Ocorrências graves (%)")
    axis.set_ylim(0, max(35, max(rates) * 1.1))
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(severe_rate_path, dpi=300, bbox_inches="tight")
    plt.close(figure)

    return occurrences_path, severe_rate_path
