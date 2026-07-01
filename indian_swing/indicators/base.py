"""
Base indicator with result caching.
All indicators are stateless, vectorized, and operate on pandas DataFrames.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

import numpy as np
import pandas as pd


class BaseIndicator(ABC):
    """
    All indicators extend this.
    Subclasses implement compute() using vectorized pandas/numpy operations.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series | pd.DataFrame:
        """
        Compute indicator on OHLCV DataFrame.

        Args:
            df: OHLCV DataFrame with DatetimeIndex.
            **kwargs: Indicator parameters e.g. period=14.

        Returns:
            Series or DataFrame with indicator values aligned to df.index.
        """
        ...

    def __call__(self, df: pd.DataFrame, **kwargs) -> pd.Series | pd.DataFrame:
        return self.compute(df, **kwargs)
