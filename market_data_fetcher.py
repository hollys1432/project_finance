"""
시장 지수 데이터를 가져오는 모듈
달러/원 환율, 코스피, 코스닥, S&P 500, 러셀 2000 데이터 수집
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import os

# Yahoo Finance 캐시 설정 (Render 서버용)
try:
    yf.set_tz_cache_location("/tmp/yfinance_cache")
except:
    pass

# yfinance가 proxy를 사용하지 않도록 설정
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'


class MarketDataFetcher:
    """시장 지수 데이터 수집 클래스"""

    # 지수 심볼 매핑
    INDICES = {
        'usd_krw': {
            'symbol': 'KRW=X',
            'name': '달러/원',
            'badge': '환율'
        },
        'kospi': {
            'symbol': '^KS11',
            'name': '코스피',
            'badge': '한국'
        },
        'kosdaq': {
            'symbol': '^KQ11',
            'name': '코스닥',
            'badge': '한국'
        },
        'sp500': {
            'symbol': '^GSPC',
            'name': 'S&P 500',
            'badge': '미국'
        },
        'dow': {
            'symbol': '^DJI',
            'name': '다우지수',
            'badge': '미국'
        },
        'nasdaq': {
            'symbol': '^IXIC',
            'name': '나스닥지수',
            'badge': '미국'
        },
        'russell2000': {
            'symbol': '^RUT',
            'name': '러셀 2000',
            'badge': '미국'
        },
        'gold': {
            'symbol': 'GC=F',
            'name': '금',
            'badge': '원자재'
        },
        'silver': {
            'symbol': 'SI=F',
            'name': '은',
            'badge': '원자재'
        },
        'copper': {
            'symbol': 'HG=F',
            'name': '구리',
            'badge': '원자재'
        },
        'wti': {
            'symbol': 'CL=F',
            'name': 'WTI유',
            'badge': '원자재'
        }
    }

    def __init__(self):
        pass

    def get_index_data(self, symbol: str, period: str = '1mo') -> Dict[str, Any]:
        """
        특정 지수의 데이터를 가져옵니다.

        Args:
            symbol: yfinance 심볼 (예: '^KS11', 'KRW=X')
            period: 데이터 기간 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')

        Returns:
            지수 정보를 담은 딕셔너리
        """
        try:
            # yfinance는 자체적으로 User-Agent를 처리함
            ticker = yf.Ticker(symbol)

            # 히스토리 데이터 가져오기
            hist = ticker.history(period=period)

            if hist.empty:
                return self._get_empty_data(symbol)

            # 최신 데이터
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest

            current_value = float(latest['Close'])
            prev_close = float(previous['Close'])
            change = current_value - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0

            # 차트 데이터 (30일)
            chart_data = []
            for idx, row in hist.iterrows():
                chart_data.append({
                    'date': idx.strftime('%Y-%m-%d'),
                    'value': float(row['Close']),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'volume': int(row['Volume']) if 'Volume' in row and row['Volume'] > 0 else 0
                })

            # 기간 내 최고/최저
            high = float(hist['High'].max())
            low = float(hist['Low'].min())

            return {
                'symbol': symbol,
                'value': round(current_value, 2),
                'change': round(change, 2),
                'changePercent': round(change_percent, 2),
                'open': float(latest['Open']),
                'high': high,
                'low': low,
                'prevClose': prev_close,
                'volume': int(latest['Volume']) if 'Volume' in latest and latest['Volume'] > 0 else 0,
                'chartData': chart_data,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return self._get_empty_data(symbol)

    def _get_empty_data(self, symbol: str) -> Dict[str, Any]:
        """데이터를 가져올 수 없을 때 빈 데이터 반환"""
        return {
            'symbol': symbol,
            'value': 0,
            'change': 0,
            'changePercent': 0,
            'open': 0,
            'high': 0,
            'low': 0,
            'prevClose': 0,
            'volume': 0,
            'chartData': [],
            'timestamp': datetime.now().isoformat(),
            'error': 'Data not available'
        }

    def get_all_indices(self, period: str = '1mo') -> Dict[str, Any]:
        """
        모든 지수 데이터를 가져옵니다.

        Args:
            period: 데이터 기간

        Returns:
            모든 지수 정보를 담은 딕셔너리
        """
        result = {}

        for index_id, index_info in self.INDICES.items():
            symbol = index_info['symbol']
            data = self.get_index_data(symbol, period)

            # 메타데이터 추가
            data['id'] = index_id
            data['name'] = index_info['name']
            data['badge'] = index_info['badge']

            result[index_id] = data

        return result

    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        실시간 시세 정보를 가져옵니다 (가장 최근 데이터만)

        Args:
            symbol: yfinance 심볼

        Returns:
            실시간 시세 정보
        """
        try:
            # yfinance는 자체적으로 User-Agent를 처리함
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 빠른 데이터 (최근 1일)
            hist = ticker.history(period='1d', interval='1m')

            if hist.empty:
                hist = ticker.history(period='5d')

            if hist.empty:
                return self._get_empty_data(symbol)

            latest = hist.iloc[-1]

            return {
                'symbol': symbol,
                'value': float(latest['Close']),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'volume': int(latest['Volume']) if 'Volume' in latest and latest['Volume'] > 0 else 0,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error fetching realtime quote for {symbol}: {e}")
            return self._get_empty_data(symbol)


def main():
    """테스트용 메인 함수"""
    fetcher = MarketDataFetcher()

    print("=== 모든 지수 데이터 가져오기 ===\n")
    all_data = fetcher.get_all_indices(period='1mo')

    for index_id, data in all_data.items():
        print(f"{data['name']} ({data['symbol']})")
        print(f"  현재가: {data['value']:,.2f}")
        print(f"  변동: {data['change']:+,.2f} ({data['changePercent']:+.2f}%)")
        print(f"  고가: {data['high']:,.2f} / 저가: {data['low']:,.2f}")
        print(f"  차트 데이터 포인트: {len(data['chartData'])}개")
        print()

    # JSON으로 저장 (웹에서 사용)
    with open('market_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("데이터가 market_data.json 파일에 저장되었습니다.")


if __name__ == '__main__':
    main()
