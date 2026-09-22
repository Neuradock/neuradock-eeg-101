"""Pinned third-party source used by the teaching quality gate."""

from .quality_tools import clean_eeg_data, eeg_quality_check

__all__ = ["clean_eeg_data", "eeg_quality_check"]
