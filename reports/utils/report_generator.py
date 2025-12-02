"""
보고서 생성 유틸리티 (최적화 버전)
"""
from datetime import datetime, timedelta
from django.db.models import Avg, Max, Min, Sum, Count, Q, F, OuterRef, Subquery
from django.utils import timezone
from stocks.models import CompanyInfo, PriceData, USCompanyInfo, USPriceData
from quant.indicators import calculate_rsi, calculate_sma
from collections import defaultdict


class MarketAnalyzer:
    """시장 분석 클래스"""

    def __init__(self, market='all', report_date=None):
        self.market = market
        self.report_date = report_date or timezone.now().date()

        # 캐시
        self._kr_latest_date = None
        self._kr_prev_date = None
        self._us_latest_date = None
        self._us_prev_date = None

    def generate_market_indices(self):
        """시장 지수 정보 생성"""
        indices = {}

        if self.market in ['kr', 'all']:
            kr_data = self._get_kr_market_stats()
            if kr_data:
                indices['kr'] = kr_data

        if self.market in ['us', 'all']:
            us_data = self._get_us_market_stats()
            if us_data:
                indices['us'] = us_data

        return indices

    def _get_trading_dates(self, model):
        """거래일 가져오기 (최적화)"""
        dates = list(model.objects.filter(
            date__lte=self.report_date
        ).values_list('date', flat=True).distinct().order_by('-date')[:2])

        if not dates:
            return None, None

        latest = dates[0]
        prev = dates[1] if len(dates) > 1 else None
        return latest, prev

    def _get_kr_market_stats(self):
        """한국 시장 통계 (최적화)"""
        latest_date, prev_date = self._get_trading_dates(PriceData)

        if not latest_date:
            return None

        self._kr_latest_date = latest_date
        self._kr_prev_date = prev_date

        # 당일 데이터 (단일 쿼리)
        today_data = PriceData.objects.filter(date=latest_date).aggregate(
            total_volume=Sum('volume'),
            count=Count('id')
        )

        avg_change = 0
        if prev_date:
            # 등락률 계산 (2개 쿼리로 최적화)
            today_prices = {p.stock_id: p.close_price for p in
                          PriceData.objects.filter(date=latest_date).select_related('stock')}
            prev_prices = {p.stock_id: p.close_price for p in
                         PriceData.objects.filter(date=prev_date)}

            changes = []
            for stock_id, today_price in today_prices.items():
                if stock_id in prev_prices and prev_prices[stock_id] > 0:
                    change_pct = ((today_price - prev_prices[stock_id]) / prev_prices[stock_id]) * 100
                    changes.append(change_pct)

            if changes:
                avg_change = sum(changes) / len(changes)

        # 시장별 통계 (단일 쿼리)
        market_counts = CompanyInfo.objects.filter(
            is_active=True,
            market__in=['KOSPI', 'KOSDAQ']
        ).values('market').annotate(count=Count('id'))

        counts = {m['market']: m['count'] for m in market_counts}

        return {
            'date': latest_date.strftime('%Y-%m-%d'),
            'total_volume': int(today_data['total_volume'] or 0),
            'avg_change': round(float(avg_change), 2),
            'kospi_count': counts.get('KOSPI', 0),
            'kosdaq_count': counts.get('KOSDAQ', 0),
            'total_stocks': today_data['count'],
        }

    def _get_us_market_stats(self):
        """미국 시장 통계 (최적화)"""
        latest_date, prev_date = self._get_trading_dates(USPriceData)

        if not latest_date:
            return None

        self._us_latest_date = latest_date
        self._us_prev_date = prev_date

        # 당일 데이터
        today_data = USPriceData.objects.filter(date=latest_date).aggregate(
            total_volume=Sum('volume'),
            count=Count('id')
        )

        avg_change = 0
        if prev_date:
            # 등락률 계산 (2개 쿼리)
            today_prices = {p.stock_id: p.close_price for p in
                          USPriceData.objects.filter(date=latest_date)}
            prev_prices = {p.stock_id: p.close_price for p in
                         USPriceData.objects.filter(date=prev_date)}

            changes = []
            for stock_id, today_price in today_prices.items():
                if stock_id in prev_prices and prev_prices[stock_id] > 0:
                    change_pct = ((today_price - prev_prices[stock_id]) / prev_prices[stock_id]) * 100
                    changes.append(change_pct)

            if changes:
                avg_change = sum(changes) / len(changes)

        # 거래소별 통계
        exchange_counts = USCompanyInfo.objects.filter(
            is_active=True,
            exchange__in=['NASDAQ', 'NYSE']
        ).values('exchange').annotate(count=Count('id'))

        counts = {e['exchange']: e['count'] for e in exchange_counts}

        return {
            'date': latest_date.strftime('%Y-%m-%d'),
            'total_volume': int(today_data['total_volume'] or 0),
            'avg_change': round(float(avg_change), 2),
            'nasdaq_count': counts.get('NASDAQ', 0),
            'nyse_count': counts.get('NYSE', 0),
            'total_stocks': today_data['count'],
        }

    def get_top_volume_stocks(self, limit=20):
        """거래량 상위 종목 (최적화)"""
        top_stocks = []

        if self.market in ['kr', 'all']:
            kr_top = self._get_kr_top_volume(limit)
            top_stocks.extend(kr_top)

        if self.market in ['us', 'all']:
            us_top = self._get_us_top_volume(limit)
            top_stocks.extend(us_top)

        top_stocks.sort(key=lambda x: x['volume'], reverse=True)
        return top_stocks[:limit]

    def _get_kr_top_volume(self, limit):
        """한국 거래량 상위 종목 (최적화)"""
        if not self._kr_latest_date:
            latest_date, _ = self._get_trading_dates(PriceData)
            if not latest_date:
                return []
            self._kr_latest_date = latest_date

        # 단일 쿼리로 select_related 사용
        top_volume = PriceData.objects.filter(
            date=self._kr_latest_date
        ).select_related('stock').order_by('-volume')[:limit]

        return [{
            'market': 'KR',
            'code': price.stock.company_code,
            'name': price.stock.company_name,
            'close_price': float(price.close_price),
            'volume': int(price.volume),
            'date': price.date.strftime('%Y-%m-%d'),
        } for price in top_volume]

    def _get_us_top_volume(self, limit):
        """미국 거래량 상위 종목 (최적화)"""
        if not self._us_latest_date:
            latest_date, _ = self._get_trading_dates(USPriceData)
            if not latest_date:
                return []
            self._us_latest_date = latest_date

        top_volume = USPriceData.objects.filter(
            date=self._us_latest_date
        ).select_related('stock').order_by('-volume')[:limit]

        return [{
            'market': 'US',
            'code': price.stock.symbol,
            'name': price.stock.company_name,
            'close_price': float(price.close_price),
            'volume': int(price.volume),
            'date': price.date.strftime('%Y-%m-%d'),
        } for price in top_volume]

    def get_top_gainers_losers(self, limit=20):
        """가격 변동률 상위/하위 종목 (최적화)"""
        gainers = []
        losers = []

        if self.market in ['kr', 'all']:
            kr_gainers, kr_losers = self._get_kr_gainers_losers(limit * 2)
            gainers.extend(kr_gainers)
            losers.extend(kr_losers)

        if self.market in ['us', 'all']:
            us_gainers, us_losers = self._get_us_gainers_losers(limit * 2)
            gainers.extend(us_gainers)
            losers.extend(us_losers)

        gainers.sort(key=lambda x: x['change_pct'], reverse=True)
        losers.sort(key=lambda x: x['change_pct'])

        return gainers[:limit], losers[:limit]

    def _get_kr_gainers_losers(self, limit):
        """한국 상승/하락 종목 (최적화)"""
        if not self._kr_latest_date:
            latest_date, prev_date = self._get_trading_dates(PriceData)
        else:
            latest_date = self._kr_latest_date
            prev_date = self._kr_prev_date

        if not latest_date or not prev_date:
            return [], []

        # 2개 쿼리로 모든 데이터 가져오기
        today_prices = {p.stock_id: (p, p.stock) for p in
                       PriceData.objects.filter(date=latest_date).select_related('stock')}
        prev_prices = {p.stock_id: p.close_price for p in
                      PriceData.objects.filter(date=prev_date)}

        changes = []
        for stock_id, (today_price, stock) in today_prices.items():
            if stock_id in prev_prices and prev_prices[stock_id] > 0:
                change_pct = ((today_price.close_price - prev_prices[stock_id]) / prev_prices[stock_id]) * 100

                changes.append({
                    'market': 'KR',
                    'code': stock.company_code,
                    'name': stock.company_name,
                    'close_price': float(today_price.close_price),
                    'prev_close': float(prev_prices[stock_id]),
                    'change_pct': round(float(change_pct), 2),
                    'volume': int(today_price.volume),
                    'date': today_price.date.strftime('%Y-%m-%d'),
                })

        changes.sort(key=lambda x: x['change_pct'], reverse=True)
        gainers = changes[:limit]
        losers = changes[-limit:]

        return gainers, losers

    def _get_us_gainers_losers(self, limit):
        """미국 상승/하락 종목 (최적화)"""
        if not self._us_latest_date:
            latest_date, prev_date = self._get_trading_dates(USPriceData)
        else:
            latest_date = self._us_latest_date
            prev_date = self._us_prev_date

        if not latest_date or not prev_date:
            return [], []

        # 2개 쿼리
        today_prices = {p.stock_id: (p, p.stock) for p in
                       USPriceData.objects.filter(date=latest_date).select_related('stock')}
        prev_prices = {p.stock_id: p.close_price for p in
                      USPriceData.objects.filter(date=prev_date)}

        changes = []
        for stock_id, (today_price, stock) in today_prices.items():
            if stock_id in prev_prices and prev_prices[stock_id] > 0:
                change_pct = ((today_price.close_price - prev_prices[stock_id]) / prev_prices[stock_id]) * 100

                changes.append({
                    'market': 'US',
                    'code': stock.symbol,
                    'name': stock.company_name,
                    'close_price': float(today_price.close_price),
                    'prev_close': float(prev_prices[stock_id]),
                    'change_pct': round(float(change_pct), 2),
                    'volume': int(today_price.volume),
                    'date': today_price.date.strftime('%Y-%m-%d'),
                })

        changes.sort(key=lambda x: x['change_pct'], reverse=True)
        gainers = changes[:limit]
        losers = changes[-limit:]

        return gainers, losers

    def get_sector_analysis(self):
        """섹터별 분석 (최적화)"""
        if self.market == 'kr':
            return {}

        if not self._us_latest_date:
            latest_date, prev_date = self._get_trading_dates(USPriceData)
        else:
            latest_date = self._us_latest_date
            prev_date = self._us_prev_date

        if not latest_date or not prev_date:
            return {}

        # 2개 쿼리로 모든 데이터 가져오기
        today_data = {p.stock_id: p for p in
                     USPriceData.objects.filter(date=latest_date).select_related('stock')}
        prev_data = {p.stock_id: p.close_price for p in
                    USPriceData.objects.filter(date=prev_date)}

        # 섹터별 집계
        sectors = defaultdict(lambda: {'changes': [], 'volumes': []})

        for stock_id, today_price in today_data.items():
            if not today_price.stock.sector or stock_id not in prev_data:
                continue

            prev_close = prev_data[stock_id]
            if prev_close > 0:
                change_pct = ((today_price.close_price - prev_close) / prev_close) * 100
                sectors[today_price.stock.sector]['changes'].append(change_pct)
                sectors[today_price.stock.sector]['volumes'].append(today_price.volume)

        # 평균 계산
        sector_summary = {}
        for sector, data in sectors.items():
            if data['changes']:
                sector_summary[sector] = {
                    'avg_change': round(float(sum(data['changes']) / len(data['changes'])), 2),
                    'total_volume': int(sum(data['volumes'])),
                    'stock_count': len(data['changes']),
                }

        return sector_summary

    def get_technical_summary(self):
        """기술적 분석 요약 (최적화 - 샘플링)"""
        summary = {}

        if self.market in ['kr', 'all']:
            kr_summary = self._get_kr_technical_summary()
            if kr_summary:
                summary['kr'] = kr_summary

        if self.market in ['us', 'all']:
            us_summary = self._get_us_technical_summary()
            if us_summary:
                summary['us'] = us_summary

        return summary

    def _get_kr_technical_summary(self):
        """한국 기술적 분석 요약 (샘플링으로 최적화)"""
        if not self._kr_latest_date:
            latest_date, _ = self._get_trading_dates(PriceData)
            if not latest_date:
                return None
            self._kr_latest_date = latest_date
        else:
            latest_date = self._kr_latest_date

        # 거래량 상위 50개만 분석 (성능 최적화)
        top_stocks = PriceData.objects.filter(
            date=latest_date
        ).select_related('stock').order_by('-volume')[:50]

        rsi_oversold = 0
        rsi_overbought = 0
        above_ma20 = 0
        below_ma20 = 0
        total_analyzed = 0

        for price_data in top_stocks:
            # 최근 30일 데이터
            prices = list(PriceData.objects.filter(
                stock=price_data.stock,
                date__lte=latest_date
            ).order_by('-date')[:30].values_list('close_price', flat=True))

            if len(prices) < 20:
                continue

            total_analyzed += 1
            prices.reverse()  # 오래된 순서로

            # pandas Series로 변환
            import pandas as pd
            price_series = pd.Series([float(p) for p in prices])

            # RSI 계산
            try:
                rsi_values = calculate_rsi(price_series, period=14)
                if rsi_values is not None and len(rsi_values) > 0:
                    current_rsi = rsi_values.iloc[-1]
                    if pd.notna(current_rsi):
                        if current_rsi < 30:
                            rsi_oversold += 1
                        elif current_rsi > 70:
                            rsi_overbought += 1
            except:
                pass

            # 20일 이동평균
            try:
                ma20 = calculate_sma(price_series, period=20)
                if ma20 is not None and len(ma20) > 0:
                    current_ma20 = ma20.iloc[-1]
                    current_price = price_series.iloc[-1]
                    if pd.notna(current_ma20) and pd.notna(current_price):
                        if current_price > current_ma20:
                            above_ma20 += 1
                        else:
                            below_ma20 += 1
            except:
                pass

        return {
            'total_analyzed': total_analyzed,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought,
            'above_ma20': above_ma20,
            'below_ma20': below_ma20,
            'date': latest_date.strftime('%Y-%m-%d'),
        }

    def _get_us_technical_summary(self):
        """미국 기술적 분석 요약 (샘플링)"""
        if not self._us_latest_date:
            latest_date, _ = self._get_trading_dates(USPriceData)
            if not latest_date:
                return None
            self._us_latest_date = latest_date
        else:
            latest_date = self._us_latest_date

        # 거래량 상위 50개만 분석
        top_stocks = USPriceData.objects.filter(
            date=latest_date
        ).select_related('stock').order_by('-volume')[:50]

        rsi_oversold = 0
        rsi_overbought = 0
        above_ma20 = 0
        below_ma20 = 0
        total_analyzed = 0

        for price_data in top_stocks:
            prices = list(USPriceData.objects.filter(
                stock=price_data.stock,
                date__lte=latest_date
            ).order_by('-date')[:30].values_list('close_price', flat=True))

            if len(prices) < 20:
                continue

            total_analyzed += 1
            prices.reverse()

            # pandas Series로 변환
            import pandas as pd
            price_series = pd.Series([float(p) for p in prices])

            # RSI
            try:
                rsi_values = calculate_rsi(price_series, period=14)
                if rsi_values is not None and len(rsi_values) > 0:
                    current_rsi = rsi_values.iloc[-1]
                    if pd.notna(current_rsi):
                        if current_rsi < 30:
                            rsi_oversold += 1
                        elif current_rsi > 70:
                            rsi_overbought += 1
            except:
                pass

            # 20일 이동평균
            try:
                ma20 = calculate_sma(price_series, period=20)
                if ma20 is not None and len(ma20) > 0:
                    current_ma20 = ma20.iloc[-1]
                    current_price = price_series.iloc[-1]
                    if pd.notna(current_ma20) and pd.notna(current_price):
                        if current_price > current_ma20:
                            above_ma20 += 1
                        else:
                            below_ma20 += 1
            except:
                pass

        return {
            'total_analyzed': total_analyzed,
            'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought,
            'above_ma20': above_ma20,
            'below_ma20': below_ma20,
            'date': latest_date.strftime('%Y-%m-%d'),
        }
