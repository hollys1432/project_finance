"""
스퀴즈 모멘텀 전략 (Squeeze Momentum Strategy)
LazyBear의 전략을 Python으로 구현
"""
from .base import BaseStrategy
from ..indicators import calculate_squeeze_momentum, calculate_ema
import pandas as pd
import numpy as np


class SqueezeMomentumStrategy(BaseStrategy):
    """
    스퀴즈 모멘텀 전략

    볼린저 밴드와 켈트너 채널을 사용하여 변동성 축소/폭발 시점을 포착하고,
    모멘텀의 방향성을 이용하여 매매 신호를 생성합니다.

    롱 진입 조건:
    - 스퀴즈 상태가 ON에서 OFF로 전환 (변동성 폭발)
    - 모멘텀이 상승 중
    - 모멘텀이 과거 100개 봉 중 최저값보다 높음
    - 종가가 전일 대비 상승
    - 종가가 100일 EMA 위에 위치

    롱 청산 조건:
    - 모멘텀이 하락 전환

    숏 진입 조건:
    - 스퀴즈 상태가 ON에서 OFF로 전환 (변동성 폭발)
    - 모멘텀이 하락 중
    - 모멘텀이 과거 100개 봉 중 최고값보다 낮음
    - 종가가 전일 대비 하락
    - 종가가 100일 EMA 아래에 위치

    숏 청산 조건:
    - 모멘텀이 상승 전환
    """

    def __init__(self, parameters=None):
        """
        Args:
            parameters: dict
                - length: BB/KC 기간 (기본값: 20)
                - mult_bb: 볼린저 밴드 배수 (기본값: 2.0)
                - mult_kc: 켈트너 채널 배수 (기본값: 1.5)
                - use_true_range: True Range 사용 여부 (기본값: True)
                - ema_period: EMA 기간 (기본값: 100)
                - momentum_lookback: 모멘텀 비교 기간 (기본값: 100)
        """
        default_params = {
            'length': 20,
            'mult_bb': 2.0,
            'mult_kc': 1.5,
            'use_true_range': True,
            'ema_period': 100,
            'momentum_lookback': 100
        }

        if parameters:
            default_params.update(parameters)

        super().__init__(default_params)

    def generate_signals(self, df):
        """
        스퀴즈 모멘텀 신호 생성

        Args:
            df: pandas DataFrame (OHLCV 데이터)

        Returns:
            pandas DataFrame: 신호가 추가된 데이터프레임
        """
        self.validate_data(df)

        # 데이터 복사
        result_df = df.copy()

        # 파라미터 추출
        length = self.parameters['length']
        mult_bb = self.parameters['mult_bb']
        mult_kc = self.parameters['mult_kc']
        use_true_range = self.parameters['use_true_range']
        ema_period = self.parameters['ema_period']
        momentum_lookback = self.parameters['momentum_lookback']

        # 스퀴즈 모멘텀 계산
        squeeze = calculate_squeeze_momentum(
            result_df['high'],
            result_df['low'],
            result_df['close'],
            length=length,
            mult_bb=mult_bb,
            mult_kc=mult_kc,
            use_true_range=use_true_range
        )

        result_df['squeeze_on'] = squeeze['squeeze_on']
        result_df['squeeze_off'] = squeeze['squeeze_off']
        result_df['momentum'] = squeeze['momentum']
        result_df['bb_upper'] = squeeze['bb_upper']
        result_df['bb_lower'] = squeeze['bb_lower']
        result_df['kc_upper'] = squeeze['kc_upper']
        result_df['kc_lower'] = squeeze['kc_lower']

        # EMA 계산
        result_df['ema'] = calculate_ema(result_df['close'], ema_period)

        # 모멘텀 최고/최저값 계산
        result_df['momentum_highest'] = result_df['momentum'].rolling(
            window=momentum_lookback, min_periods=1
        ).max().shift(1)
        result_df['momentum_lowest'] = result_df['momentum'].rolling(
            window=momentum_lookback, min_periods=1
        ).min().shift(1)

        # 신호 초기화
        result_df['signal'] = 0
        result_df['position'] = 0

        # 이전 값과 비교하기 위한 shift
        result_df['prev_squeeze_on'] = result_df['squeeze_on'].shift(1)
        result_df['prev_momentum'] = result_df['momentum'].shift(1)
        result_df['prev_close'] = result_df['close'].shift(1)

        # 롱/숏 진입/청산 신호 생성
        for i in range(1, len(result_df)):
            if pd.notna(result_df['momentum'].iloc[i]) and pd.notna(result_df['ema'].iloc[i]):
                curr_squeeze_on = result_df['squeeze_on'].iloc[i]
                prev_squeeze_on = result_df['prev_squeeze_on'].iloc[i]
                curr_squeeze_off = result_df['squeeze_off'].iloc[i]
                curr_momentum = result_df['momentum'].iloc[i]
                prev_momentum = result_df['prev_momentum'].iloc[i]
                curr_close = result_df['close'].iloc[i]
                prev_close = result_df['prev_close'].iloc[i]
                curr_ema = result_df['ema'].iloc[i]
                momentum_lowest = result_df['momentum_lowest'].iloc[i]
                momentum_highest = result_df['momentum_highest'].iloc[i]
                prev_position = result_df['position'].iloc[i-1]

                # 스퀴즈 OFF로 전환 (ON -> OFF)
                squeeze_off_transition = (curr_squeeze_off and prev_squeeze_on)

                # 롱 진입 조건
                if (squeeze_off_transition and
                    curr_momentum > prev_momentum and
                    pd.notna(momentum_lowest) and curr_momentum > momentum_lowest and
                    curr_close > prev_close and
                    curr_close > curr_ema):
                    result_df.loc[result_df.index[i], 'signal'] = 1
                    result_df.loc[result_df.index[i], 'position'] = 1

                # 숏 진입 조건
                elif (squeeze_off_transition and
                      curr_momentum < prev_momentum and
                      pd.notna(momentum_highest) and curr_momentum < momentum_highest and
                      curr_close < prev_close and
                      curr_close < curr_ema):
                    result_df.loc[result_df.index[i], 'signal'] = -1
                    result_df.loc[result_df.index[i], 'position'] = -1

                # 롱 청산 조건 (포지션이 롱이고 모멘텀이 하락)
                elif prev_position == 1 and curr_momentum < prev_momentum:
                    result_df.loc[result_df.index[i], 'signal'] = -1
                    result_df.loc[result_df.index[i], 'position'] = 0

                # 숏 청산 조건 (포지션이 숏이고 모멘텀이 상승)
                elif prev_position == -1 and curr_momentum > prev_momentum:
                    result_df.loc[result_df.index[i], 'signal'] = 1
                    result_df.loc[result_df.index[i], 'position'] = 0

                # 포지션 유지
                else:
                    result_df.loc[result_df.index[i], 'position'] = prev_position

        return result_df

    def get_name(self):
        """전략 이름 반환"""
        length = self.parameters['length']
        mult_bb = self.parameters['mult_bb']
        mult_kc = self.parameters['mult_kc']
        return f"Squeeze Momentum ({length}, BB:{mult_bb}, KC:{mult_kc})"
