"""Análises científicas reproduzíveis do projeto."""

from tcc_prf_severity.analysis.general import run_general_analysis
from tcc_prf_severity.analysis.geographic import run_geographic_analysis
from tcc_prf_severity.analysis.temporal import run_temporal_analysis

__all__ = ("run_general_analysis", "run_geographic_analysis", "run_temporal_analysis")
