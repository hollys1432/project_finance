"""
RSI 전략
"""
from .base import BaseStrategy
from ..indicators import calculate_rsi
import pandas as pd


class RSIStrategy(BaseStrategy):
    """
    RSI(Relative Strength Index) 전략

    매수 신호: RSI가 과매도 구간(기본 30) 이하에서 상향 돌파
    매도 신호: RSI가 과매수 구간(기본 70) 이상에서 하향 돌파
    """

    def __init__(self, parameters=None):
        """
        Args:
            parameters: dict
                - period: RSI 계산 기간 (기본값: 14)
                - oversold: 과매도 기준 (기본값: 30)
                - overbought: 과매수 기준 (기본값: 70)
        """
        default_params = {
            'period': 14,
            'oversold': 30,
            'overbought': 70
        }

        if parameters:
            default_params.update(parameters)

        super().__init__(default_params)

    def generate_signals(self, df):
        """
        RSI 신호 생성

        Args:
            df: pandas DataFrame (OHLCV 데이터)

        Returns:
            pandas DataFrame: 신호가 추가된 데이터프레임
        """
        self.validate_data(df)

        # 데이터 복사
        result_df = df.copy()

        period = self.parameters['period']
        oversold = self.parameters['oversold']
        overbought = self.parameters['overbought']

        # RSI 계산
        result_df['rsi'] = calculate_rsi(result_df['close'], period)

        # 신호 초기화
        result_df['signal'] = 0
        result_df['position'] = 0

        # RSI 신호 생성
        for i in range(1, len(result_df)):
            if pd.notna(result_df['rsi'].iloc[i]):
                prev_rsi = result_df['rsi'].iloc[i-1]
                curr_rsi = result_df['rsi'].iloc[i]

                # 과매도 구간에서 상향 돌파 (매수 신호)
                if prev_rsi <= oversold and curr_rsi > oversold:
                    result_df.loc[result_df.index[i], 'signal'] = 1

                # 과매수 구간에서 하향 돌파 (매도 신호)
                elif prev_rsi >= overbought and curr_rsi < overbought:
                    result_df.loc[result_df.index[i], 'signal'] = -1

        # 포지션 계산 (누적)
        result_df['position'] = result_df['signal'].replace(0, pd.NA).ffill().fillna(0)

        return result_df

    def get_name(self):
        """전략 이름 반환"""
        period = self.parameters['period']
        oversold = self.parameters['oversold']
        overbought = self.parameters['overbought']
        return f"RSI ({period}) [{oversold}/{overbought}]"
