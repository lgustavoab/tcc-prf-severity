"""Análises científicas reproduzíveis do projeto."""

from tcc_prf_severity.analysis.general import run_general_analysis
from tcc_prf_severity.analysis.geographic import run_geographic_analysis
from tcc_prf_severity.analysis.occurrence_dynamics import run_occurrence_dynamics_analysis
from tcc_prf_severity.analysis.road_environment import run_road_environment_analysis
from tcc_prf_severity.analysis.temporal import run_temporal_analysis

__all__ = (
    "run_general_analysis",
    "run_geographic_analysis",
    "run_occurrence_dynamics_analysis",
    "run_road_environment_analysis",
    "run_temporal_analysis",
)
