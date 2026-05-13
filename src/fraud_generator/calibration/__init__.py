"""
Calibration module — extracts statistical distributions from user-uploaded
real transaction data to calibrate the generator's output distributions.
"""

from .distribution_extractor import CalibrationProfile, extract_distributions

__all__ = ["extract_distributions", "CalibrationProfile"]
