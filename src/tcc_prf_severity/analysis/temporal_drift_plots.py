from pathlib import Path

import matplotlib
import polars as pl

from tcc_prf_severity.analysis.temporal_drift import (
    CONTINUOUS_VARIABLES,
    TemporalDriftAnalysis,
)

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def _horizontal_ranking(
    labels: list[str], values: list[float], title: str, xlabel: str, path: Path
) -> None:
    figure, axis = plt.subplots(figsize=(10, max(4.5, len(labels) * 0.38)))
    axis.barh(labels, values)
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel("Variável")
    axis.set_xlim(0, max(values) * 1.1 if values and max(values) > 0 else 1)
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)


def write_temporal_drift_figures(
    analysis: TemporalDriftAnalysis, output_dir: Path
) -> tuple[Path, ...]:
    """Gera até três rankings descritivos, sem rótulos arbitrários de drift."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    categorical = analysis.categorical_drift_summary.sort("tvd")
    categorical_path = output_dir / "phase_3a_categorical_tvd.png"
    _horizontal_ranking(
        categorical.get_column("variable").to_list(),
        categorical.get_column("tvd").cast(pl.Float64).to_list(),
        "Mudança descritiva das distribuições categóricas: 2021-2024 vs 2025",
        "Total Variation Distance (TVD)",
        categorical_path,
    )
    paths.append(categorical_path)

    numeric = analysis.numeric_drift_summary.filter(
        pl.col("variable").is_in(CONTINUOUS_VARIABLES)
    ).sort("distribution_tvd")
    numeric_path = output_dir / "phase_3a_numeric_binned_tvd.png"
    _horizontal_ranking(
        numeric.get_column("variable").to_list(),
        numeric.get_column("distribution_tvd").cast(pl.Float64).to_list(),
        "Mudança das variáveis contínuas em bins definidos no desenvolvimento",
        "TVD sobre bins de decis de 2021-2024",
        numeric_path,
    )
    paths.append(numeric_path)

    unseen = (
        analysis.unseen_categories_2025.group_by("variable")
        .agg(pl.col("share_2025_percent").sum().alias("unseen_share_2025_percent"))
        .filter(pl.col("unseen_share_2025_percent") > 0)
        .sort("unseen_share_2025_percent")
    )
    if not unseen.is_empty():
        unseen_path = output_dir / "phase_3a_unseen_category_share_2025.png"
        _horizontal_ranking(
            unseen.get_column("variable").to_list(),
            unseen.get_column("unseen_share_2025_percent").cast(pl.Float64).to_list(),
            "Registros de 2025 em categorias não vistas no desenvolvimento",
            "Participação em 2025 (%)",
            unseen_path,
        )
        paths.append(unseen_path)

    return tuple(paths)
