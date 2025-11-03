"""
퀀트 전략에 사용되는 기술적 지표 계산 함수들
"""
import pandas as pd
import numpy as np


def calculate_sma(data, period):
    """
    단순 이동평균(Simple Moving Average) 계산

    Args:
        data: pandas Series (종가 데이터)
        period: 이동평균 기간

    Returns:
        pandas Series: SMA 값
    """
    return data.rolling(window=period, min_periods=period).mean()


def calculate_ema(data, period):
    """
    지수 이동평균(Exponential Moving Average) 계산

    Args:
        data: pandas Series (종가 데이터)
        period: 이동평균 기간

    Returns:
        pandas Series: EMA 값
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data, period=14):
    """
    RSI(Relative Strength Index) 계산

    Args:
        data: pandas Series (종가 데이터)
        period: RSI 계산 기간 (기본값: 14)

    Returns:
        pandas Series: RSI 값 (0~100)
    """
    delta = data.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_bollinger_bands(data, period=20, std_dev=2):
    """
    볼린저 밴드(Bollinger Bands) 계산

    Args:
        data: pandas Series (종가 데이터)
        period: 이동평균 기간 (기본값: 20)
        std_dev: 표준편차 배수 (기본값: 2)

    Returns:
        dict: {'middle': 중간선, 'upper': 상단선, 'lower': 하단선}
    """
    middle = data.rolling(window=period, min_periods=period).mean()
    std = data.rolling(window=period, min_periods=period).std()

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return {
        'middle': middle,
        'upper': upper,
        'lower': lower
    }


def calculate_macd(data, fast=12, slow=26, signal=9):
    """
    MACD(Moving Average Convergence Divergence) 계산

    Args:
        data: pandas Series (종가 데이터)
        fast: 단기 EMA 기간 (기본값: 12)
        slow: 장기 EMA 기간 (기본값: 26)
        signal: 시그널선 기간 (기본값: 9)

    Returns:
        dict: {'macd': MACD선, 'signal': 시그널선, 'histogram': 히스토그램}
    """
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)

    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line

    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_stochastic(high, low, close, k_period=14, d_period=3):
    """
    스토캐스틱(Stochastic Oscillator) 계산

    Args:
        high: pandas Series (고가 데이터)
        low: pandas Series (저가 데이터)
        close: pandas Series (종가 데이터)
        k_period: %K 기간 (기본값: 14)
        d_period: %D 기간 (기본값: 3)

    Returns:
        dict: {'k': %K, 'd': %D}
    """
    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period, min_periods=d_period).mean()

    return {
        'k': k,
        'd': d
    }


def calculate_atr(high, low, close, period=14):
    """
    ATR(Average True Range) 계산

    Args:
        high: pandas Series (고가 데이터)
        low: pandas Series (저가 데이터)
        close: pandas Series (종가 데이터)
        period: ATR 계산 기간 (기본값: 14)

    Returns:
        pandas Series: ATR 값
    """
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period, min_periods=period).mean()

    return atr


def calculate_momentum(data, period=10):
    """
    모멘텀(Momentum) 계산

    Args:
        data: pandas Series (종가 데이터)
        period: 모멘텀 계산 기간 (기본값: 10)

    Returns:
        pandas Series: 모멘텀 값
    """
    return data.diff(period)


def calculate_roc(data, period=10):
    """
    ROC(Rate of Change) 계산

    Args:
        data: pandas Series (종가 데이터)
        period: ROC 계산 기간 (기본값: 10)

    Returns:
        pandas Series: ROC 값 (%)
    """
    return ((data - data.shift(period)) / data.shift(period)) * 100


def calculate_obv(close, volume):
    """
    OBV(On-Balance Volume) 계산

    Args:
        close: pandas Series (종가 데이터)
        volume: pandas Series (거래량 데이터)

    Returns:
        pandas Series: OBV 값
    """
    obv = pd.Series(index=close.index, dtype=float)
    obv.iloc[0] = volume.iloc[0]

    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]

    return obv


def calculate_vwap(high, low, close, volume):
    """
    VWAP(Volume Weighted Average Price) 계산

    Args:
        high: pandas Series (고가 데이터)
        low: pandas Series (저가 데이터)
        close: pandas Series (종가 데이터)
        volume: pandas Series (거래량 데이터)

    Returns:
        pandas Series: VWAP 값
    """
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()

    return vwap


def calculate_keltner_channel(high, low, close, period=20, mult=1.5, use_true_range=True):
    """
    켈트너 채널(Keltner Channel) 계산

    Args:
        high: pandas Series (고가 데이터)
        low: pandas Series (저가 데이터)
        close: pandas Series (종가 데이터)
        period: 이동평균 기간 (기본값: 20)
        mult: ATR 배수 (기본값: 1.5)
        use_true_range: True Range 사용 여부 (기본값: True)

    Returns:
        dict: {'middle': 중간선, 'upper': 상단선, 'lower': 하단선}
    """
    middle = calculate_sma(close, period)

    if use_true_range:
        range_val = calculate_atr(high, low, close, period)
    else:
        range_val = (high - low).rolling(window=period, min_periods=period).mean()

    upper = middle + (range_val * mult)
    lower = middle - (range_val * mult)

    return {
        'middle': middle,
        'upper': upper,
        'lower': lower
    }


def calculate_linear_regression(data, period):
    """
    선형 회귀(Linear Regression) 계산

    Args:
        data: pandas Series (데이터)
        period: 회귀 기간

    Returns:
        pandas Series: 선형 회귀 값
    """
    def linreg(y):
        if len(y) < period:
            return np.nan
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        return intercept + slope * (len(y) - 1)

    return data.rolling(window=period, min_periods=period).apply(linreg, raw=True)


def calculate_squeeze_momentum(high, low, close, length=20, mult_bb=2.0, mult_kc=1.5, use_true_range=True):
    """
    스퀴즈 모멘텀(Squeeze Momentum) 계산

    Args:
        high: pandas Series (고가 데이터)
        low: pandas Series (저가 데이터)
        close: pandas Series (종가 데이터)
        length: 기간 (기본값: 20)
        mult_bb: 볼린저 밴드 배수 (기본값: 2.0)
        mult_kc: 켈트너 채널 배수 (기본값: 1.5)
        use_true_range: True Range 사용 여부 (기본값: True)

    Returns:
        dict: {
            'squeeze_on': 스퀴즈 ON 여부,
            'squeeze_off': 스퀴즈 OFF 여부,
            'momentum': 모멘텀 값,
            'bb_upper': BB 상단,
            'bb_lower': BB 하단,
            'kc_upper': KC 상단,
            'kc_lower': KC 하단
        }
    """
    # 볼린저 밴드 계산
    bb = calculate_bollinger_bands(close, period=length, std_dev=mult_bb)

    # 켈트너 채널 계산
    kc = calculate_keltner_channel(high, low, close, period=length, mult=mult_kc, use_true_range=use_true_range)

    # 스퀴즈 상태 판별
    squeeze_on = (bb['lower'] > kc['lower']) & (bb['upper'] < kc['upper'])
    squeeze_off = (bb['lower'] < kc['lower']) & (bb['upper'] > kc['upper'])

    # 모멘텀 계산
    # highest high와 lowest low의 평균
    highest = high.rolling(window=length, min_periods=length).max()
    lowest = low.rolling(window=length, min_periods=length).min()
    sma = calculate_sma(close, length)

    # 중간값 계산
    avg1 = (highest + lowest) / 2
    avg2 = (avg1 + sma) / 2

    # 선형 회귀 모멘텀
    momentum = calculate_linear_regression(close - avg2, length)

    return {
        'squeeze_on': squeeze_on,
        'squeeze_off': squeeze_off,
        'momentum': momentum,
        'bb_upper': bb['upper'],
        'bb_lower': bb['lower'],
        'kc_upper': kc['upper'],
        'kc_lower': kc['lower']
    }
