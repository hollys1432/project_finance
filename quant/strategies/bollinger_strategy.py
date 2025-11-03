"""
볼린저 밴드 전략
"""
from .base import BaseStrategy
from ..indicators import calculate_bollinger_bands
import pandas as pd


class BollingerBandsStrategy(BaseStrategy):
    """
    볼린저 밴드 전략

    매수 신호: 종가가 하단 밴드를 하향 돌파 후 상향 복귀 (평균 회귀)
    매도 신호: 종가가 상단 밴드를 상향 돌파 후 하향 복귀 (평균 회귀)
    """

    def __init__(self, parameters=None):
        """
        Args:
            parameters: dict
                - period: 이동평균 기간 (기본값: 20)
                - std_dev: 표준편차 배수 (기본값: 2)
        """
        default_params = {
            'period': 20,
            'std_dev': 2
        }

        if parameters:
            default_params.update(parameters)

        super().__init__(default_params)

    def generate_signals(self, df):
        """
        볼린저 밴드 신호 생성

        Args:
            df: pandas DataFrame (OHLCV 데이터)

        Returns:
            pandas DataFrame: 신호가 추가된 데이터프레임
        """
        self.validate_data(df)

        # 데이터 복사
        result_df = df.copy()

        period = self.parameters['period']
        std_dev = self.parameters['std_dev']

        # 볼린저 밴드 계산
        bb = calculate_bollinger_bands(result_df['close'], period, std_dev)
        result_df['bb_upper'] = bb['upper']
        result_df['bb_middle'] = bb['middle']
        result_df['bb_lower'] = bb['lower']

        # 신호 초기화
        result_df['signal'] = 0
        result_df['position'] = 0

        # 볼린저 밴드 신호 생성
        for i in range(1, len(result_df)):
            if pd.notna(result_df['bb_lower'].iloc[i]) and pd.notna(result_df['bb_upper'].iloc[i]):
                prev_close = result_df['close'].iloc[i-1]
                curr_close = result_df['close'].iloc[i]
                prev_lower = result_df['bb_lower'].iloc[i-1]
                prev_upper = result_df['bb_upper'].iloc[i-1]
                curr_lower = result_df['bb_lower'].iloc[i]
                curr_upper = result_df['bb_upper'].iloc[i]

                # 하단 밴드 돌파 후 복귀 (매수 신호)
                if prev_close <= prev_lower and curr_close > curr_lower:
                    result_df.loc[result_df.index[i], 'signal'] = 1

                # 상단 밴드 돌파 후 복귀 (매도 신호)
                elif prev_close >= prev_upper and curr_close < curr_upper:
                    result_df.loc[result_df.index[i], 'signal'] = -1

        # 포지션 계산 (누적)
        result_df['position'] = result_df['signal'].replace(0, pd.NA).ffill().fillna(0)

        return result_df

    def get_name(self):
        """전략 이름 반환"""
        period = self.parameters['period']
        std_dev = self.parameters['std_dev']
        return f"Bollinger Bands ({period}, {std_dev}σ)"
