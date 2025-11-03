"""
백테스팅 엔진
"""
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime


class BacktestEngine:
    """백테스팅 엔진 클래스"""

    def __init__(self, initial_capital=10000000):
        """
        Args:
            initial_capital: 초기 자본금 (기본값: 1천만원)
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # 현재 보유 수량
        self.entry_price = 0  # 진입 가격
        self.trades = []  # 거래 내역
        self.equity_curve = []  # 자본 곡선

    def run(self, df_with_signals):
        """
        백테스트 실행

        Args:
            df_with_signals: 신호가 포함된 DataFrame
                필수 컬럼: date, close, signal

        Returns:
            dict: 백테스트 결과
        """
        self.reset()

        for idx, row in df_with_signals.iterrows():
            date = row['date']
            close = row['close']
            signal = row['signal']

            # 매수 신호
            if signal == 1 and self.position == 0:
                # 전량 매수
                quantity = int(self.capital / close)
                if quantity > 0:
                    cost = quantity * close
                    self.capital -= cost
                    self.position = quantity
                    self.entry_price = close

                    self.trades.append({
                        'date': date,
                        'type': 'buy',
                        'price': close,
                        'quantity': quantity,
                        'capital': self.capital + (self.position * close)
                    })

            # 매도 신호
            elif signal == -1 and self.position > 0:
                # 전량 매도
                revenue = self.position * close
                self.capital += revenue

                profit = (close - self.entry_price) * self.position
                profit_rate = ((close - self.entry_price) / self.entry_price) * 100

                self.trades.append({
                    'date': date,
                    'type': 'sell',
                    'price': close,
                    'quantity': self.position,
                    'capital': self.capital,
                    'profit': profit,
                    'profit_rate': profit_rate
                })

                self.position = 0
                self.entry_price = 0

            # 자본 곡선 기록
            current_equity = self.capital + (self.position * close)
            self.equity_curve.append({
                'date': date,
                'equity': current_equity,
                'price': close
            })

        # 마지막에 보유 중이면 청산
        if self.position > 0:
            last_row = df_with_signals.iloc[-1]
            last_price = last_row['close']
            self.capital += self.position * last_price
            self.position = 0

        # 결과 계산
        results = self.calculate_metrics(df_with_signals)

        return results

    def reset(self):
        """백테스트 상태 초기화"""
        self.capital = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.trades = []
        self.equity_curve = []

    def calculate_metrics(self, df):
        """
        성과 지표 계산

        Args:
            df: DataFrame

        Returns:
            dict: 성과 지표
        """
        final_capital = self.capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100

        # 기간 계산
        start_date = df['date'].iloc[0]
        end_date = df['date'].iloc[-1]

        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        days = (end_date - start_date).days
        years = days / 365.25

        # 연 수익률
        annual_return = (total_return / years) if years > 0 else 0

        # MDD 계산
        equity_values = [e['equity'] for e in self.equity_curve]
        max_drawdown = self.calculate_mdd(equity_values)

        # 거래 분석
        buy_trades = [t for t in self.trades if t['type'] == 'buy']
        sell_trades = [t for t in self.trades if t['type'] == 'sell']

        total_trades = len(sell_trades)
        win_trades = len([t for t in sell_trades if t.get('profit', 0) > 0])
        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

        # 샤프 비율 계산 (일간 수익률 기준)
        sharpe_ratio = self.calculate_sharpe_ratio()

        return {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'win_trades': win_trades,
            'win_rate': win_rate,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'start_date': start_date,
            'end_date': end_date
        }

    def calculate_mdd(self, equity_values):
        """
        최대 낙폭(MDD) 계산

        Args:
            equity_values: 자본 곡선 리스트

        Returns:
            float: MDD (%)
        """
        if not equity_values or len(equity_values) < 2:
            return 0

        max_equity = equity_values[0]
        max_drawdown = 0

        for equity in equity_values:
            if equity > max_equity:
                max_equity = equity

            drawdown = ((max_equity - equity) / max_equity) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    def calculate_sharpe_ratio(self, risk_free_rate=0.02):
        """
        샤프 비율 계산

        Args:
            risk_free_rate: 무위험 수익률 (기본값: 2%)

        Returns:
            float: 샤프 비율
        """
        if len(self.equity_curve) < 2:
            return 0

        # 일간 수익률 계산
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i-1]['equity']
            curr_equity = self.equity_curve[i]['equity']
            daily_return = (curr_equity - prev_equity) / prev_equity
            returns.append(daily_return)

        if not returns:
            return 0

        # 평균 수익률
        avg_return = np.mean(returns)

        # 수익률 표준편차
        std_return = np.std(returns)

        if std_return == 0:
            return 0

        # 연간 샤프 비율 (일간 -> 연간 변환: √252)
        daily_risk_free = risk_free_rate / 252
        sharpe = (avg_return - daily_risk_free) / std_return * np.sqrt(252)

        return sharpe
