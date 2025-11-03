"""
전략 베이스 클래스
"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    """모든 전략의 기본이 되는 추상 클래스"""

    def __init__(self, parameters=None):
        """
        Args:
            parameters: 전략 파라미터 (dict)
        """
        self.parameters = parameters or {}
        self.signals = []

    @abstractmethod
    def generate_signals(self, df):
        """
        거래 신호 생성

        Args:
            df: pandas DataFrame (OHLCV 데이터)
                필수 컬럼: date, open, high, low, close, volume

        Returns:
            pandas DataFrame: 신호가 추가된 데이터프레임
                추가 컬럼: signal (1: 매수, -1: 매도, 0: 보유)
        """
        pass

    def validate_data(self, df):
        """
        데이터 유효성 검사

        Args:
            df: pandas DataFrame

        Returns:
            bool: 유효성 여부
        """
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"필수 컬럼 '{col}'이(가) 없습니다.")

        if df.empty:
            raise ValueError("데이터가 비어있습니다.")

        return True

    def get_name(self):
        """전략 이름 반환"""
        return self.__class__.__name__

    def get_parameters(self):
        """전략 파라미터 반환"""
        return self.parameters
