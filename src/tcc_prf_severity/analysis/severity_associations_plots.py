from pathlib import Path

import matplotlib
import polars as pl

from tcc_prf_severity.analysis.severity_associations import SeverityAssociationsAnalysis

matplotlib.use("Agg")
from matplotlib import pyplot as plt

SELECTED_COMPARISON_DIMENSIONS = (
    "weekday_group",
    "fase_dia",
    "macroregion",
    "tipo_pista",
    "tipo_acidente",
    "causa_acidente",
    "pessoas",
)


def write_severity_association_figures(
    analysis: SeverityAssociationsAnalysis, output_dir: Path
) -> tuple[Path, ...]:
    """Gera uma figura de síntese de magnitudes, sem score ou inferência causal."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "phase_2f_selected_severe_rate_comparisons.png"
    selected = (
        analysis.association_evidence_matrix.filter(
            pl.col("dimension").is_in(SELECTED_COMPARISON_DIMENSIONS)
            & pl.col("substantive_evidence")
            & pl.col("absolute_difference_percentage_points").is_not_null()
        )
        .unique(subset="dimension", keep="first", maintain_order=True)
        .sort("absolute_difference_percentage_points")
    )
    figure, axis = plt.subplots(figsize=(11, 7))
    axis.barh(
        selected.get_column("category_or_comparison").to_list(),
        selected.get_column("absolute_difference_percentage_points").to_list(),
    )
    axis.set_title("Magnitude de contrastes descritivos selecionados")
    axis.set_xlabel("Diferença absoluta na proporção grave (pontos percentuais)")
    axis.set_ylabel("Comparação")
    axis.set_xlim(
        0,
        max(selected.get_column("absolute_difference_percentage_points").to_list()) * 1.1,
    )
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return (path,)
