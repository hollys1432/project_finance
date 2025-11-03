"""
이동평균 크로스오버 전략
"""
from .base import BaseStrategy
from ..indicators import calculate_sma, calculate_ema
import pandas as pd


class MovingAverageCrossStrategy(BaseStrategy):
    """
    이동평균 크로스오버 전략

    매수 신호: 단기 이동평균선이 장기 이동평균선을 상향 돌파 (골든 크로스)
    매도 신호: 단기 이동평균선이 장기 이동평균선을 하향 돌파 (데드 크로스)
    """

    def __init__(self, parameters=None):
        """
        Args:
            parameters: dict
                - short_period: 단기 이동평균 기간 (기본값: 5)
                - long_period: 장기 이동평균 기간 (기본값: 20)
                - ma_type: 이동평균 유형 'sma' 또는 'ema' (기본값: 'sma')
        """
        default_params = {
            'short_period': 5,
            'long_period': 20,
            'ma_type': 'sma'
        }

        if parameters:
            default_params.update(parameters)

        super().__init__(default_params)

    def generate_signals(self, df):
        """
        이동평균 크로스오버 신호 생성

        Args:
            df: pandas DataFrame (OHLCV 데이터)

        Returns:
            pandas DataFrame: 신호가 추가된 데이터프레임
        """
        self.validate_data(df)

        # 데이터 복사
        result_df = df.copy()

        short_period = self.parameters['short_period']
        long_period = self.parameters['long_period']
        ma_type = self.parameters['ma_type']

        # 이동평균 계산
        if ma_type == 'ema':
            result_df['ma_short'] = calculate_ema(result_df['close'], short_period)
            result_df['ma_long'] = calculate_ema(result_df['close'], long_period)
        else:  # sma
            result_df['ma_short'] = calculate_sma(result_df['close'], short_period)
            result_df['ma_long'] = calculate_sma(result_df['close'], long_period)

        # 신호 초기화
        result_df['signal'] = 0
        result_df['position'] = 0

        # 크로스오버 신호 생성
        # 골든 크로스: 단기선이 장기선을 상향 돌파 -> 매수(1)
        # 데드 크로스: 단기선이 장기선을 하향 돌파 -> 매도(-1)

        for i in range(1, len(result_df)):
            if pd.notna(result_df['ma_short'].iloc[i]) and pd.notna(result_df['ma_long'].iloc[i]):
                # 이전 값
                prev_short = result_df['ma_short'].iloc[i-1]
                prev_long = result_df['ma_long'].iloc[i-1]

                # 현재 값
                curr_short = result_df['ma_short'].iloc[i]
                curr_long = result_df['ma_long'].iloc[i]

                # 골든 크로스 (매수 신호)
                if prev_short <= prev_long and curr_short > curr_long:
                    result_df.loc[result_df.index[i], 'signal'] = 1

                # 데드 크로스 (매도 신호)
                elif prev_short >= prev_long and curr_short < curr_long:
                    result_df.loc[result_df.index[i], 'signal'] = -1

        # 포지션 계산 (누적)
        result_df['position'] = result_df['signal'].replace(0, pd.NA).ffill().fillna(0)

        return result_df

    def get_name(self):
        """전략 이름 반환"""
        ma_type = self.parameters['ma_type'].upper()
        short = self.parameters['short_period']
        long = self.parameters['long_period']
        return f"{ma_type} Cross ({short}/{long})"
