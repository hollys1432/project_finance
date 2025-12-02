from __future__ import annotations
import logging
from typing import Dict, Any, List
import time
import random

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    yf = None
    pd = None

from stocks.models import USCompanyInfo

from ._base_commands import BaseCompanyInfoCommand

logger = logging.getLogger(__name__)


def _get_sp500_symbols() -> List[str]:
    """S&P 500 종목 심볼 리스트 가져오기"""
    if pd is None:
        logger.error("pandas가 설치되지 않았습니다: pip install pandas")
        return []
    
    try:
        # User-Agent 헤더 추가하여 403 에러 방지
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        import requests
        from io import StringIO

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # StringIO로 감싸서 FutureWarning 방지
        tables = pd.read_html(StringIO(response.text))

        # Symbol 컬럼이 있는 테이블 찾기 (보통 두 번째 테이블)
        df = None
        for table in tables:
            if 'Symbol' in table.columns:
                df = table
                break

        if df is None:
            raise ValueError("Symbol 컬럼을 가진 테이블을 찾을 수 없습니다")

        symbols = df['Symbol'].tolist()
        
        # 심볼 정리 (점이 포함된 경우 등 처리)
        symbols = [s.replace('.', '-') for s in symbols if isinstance(s, str)]
        
        logger.info(f"S&P 500 심볼 {len(symbols)}개 수집")
        return symbols
    
    except Exception as e:
        logger.error(f"S&P 500 심볼 수집 실패: {e}")
        return []


def _get_nasdaq100_symbols() -> List[str]:
    """NASDAQ 100 종목 심볼 리스트 가져오기"""
    if pd is None:
        return []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        url = "https://en.wikipedia.org/wiki/NASDAQ-100"
        # requests를 사용하여 헤더 포함해서 가져오기
        import requests
        from io import StringIO

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # StringIO로 감싸서 FutureWarning 방지
        tables = pd.read_html(StringIO(response.text))

        # NASDAQ-100 테이블 찾기
        for table in tables:
            if 'Ticker' in table.columns:
                symbols = table['Ticker'].tolist()
                symbols = [s.replace('.', '-') for s in symbols if isinstance(s, str)]
                if len(symbols) > 50:
                    logger.info(f"NASDAQ 100 심볼 {len(symbols)}개 수집")
                    return symbols
        return []
    except Exception as e:
        logger.error(f"NASDAQ 100 심볼 수집 실패: {e}")
        return []


def _get_nyse_symbols() -> List[str]:
    """NYSE에 상장된 모든 종목 심볼 리스트 가져오기"""
    if pd is None:
        logger.error("pandas가 설치되지 않았습니다: pip install pandas")
        return []

    try:
        # NASDAQ FTP 서버에서 NYSE 종목 리스트 다운로드
        # otherlisted.txt에는 NYSE, NYSE American, NYSE Arca 종목이 포함됨
        url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt"

        logger.info("NYSE 종목 리스트 다운로드 중...")
        df = pd.read_csv(url, sep='|')

        # 마지막 행은 파일 생성 날짜 정보이므로 제외
        df = df[:-1]

        # NYSE, NYSE American, NYSE Arca만 필터링 (원하는 경우)
        # Exchange 컬럼: A=NYSE MKT, N=NYSE, P=NYSE Arca
        nyse_exchanges = ['A', 'N', 'P']
        df_nyse = df[df['Exchange'].isin(nyse_exchanges)]

        symbols = df_nyse['ACT Symbol'].tolist()

        # 심볼 정리 (yfinance 형식에 맞게)
        symbols = [s.strip().replace('.', '-') for s in symbols if isinstance(s, str) and s.strip()]

        # 테스트 가능한 심볼만 필터링 (특수문자 제거)
        symbols = [s for s in symbols if s.replace('-', '').isalnum()]

        logger.info(f"NYSE 심볼 {len(symbols)}개 수집")
        return symbols

    except Exception as e:
        logger.error(f"NYSE 심볼 수집 실패: {e}")
        return []


def _get_company_info(symbols: List[str], batch_delay: float = 0.5) -> Dict[str, Dict[str, Any]]:
    """yfinance로 회사 정보 수집"""
    if yf is None:
        logger.error("yfinance가 설치되지 않았습니다: pip install yfinance")
        return {}

    companies = {}
    total = len(symbols)

    for idx, symbol in enumerate(symbols, 1):
        try:
            logger.info(f"[{idx}/{total}] {symbol} 정보 수집 중...")

            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or 'symbol' not in info:
                logger.warning(f"{symbol}: 정보 없음")
                continue

            companies[symbol] = {
                'company_name': info.get('longName', info.get('shortName', symbol)),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'exchange': info.get('exchange'),
                'country': info.get('country', 'US'),
                'currency': info.get('currency', 'USD'),
                'is_active': True,
            }

            # API 부하 방지
            time.sleep(random.uniform(batch_delay * 0.5, batch_delay * 1.5))

        except Exception as e:
            logger.error(f"{symbol} 정보 수집 실패: {e}")
            continue

    return companies


class Command(BaseCompanyInfoCommand):
    help = "미국 상장사 기본정보 동기화: S&P500, NASDAQ100 등 주요 지수 종목"

    def add_custom_arguments(self, parser):
        """미국 시장 특화 인자"""
        parser.add_argument("--symbols", type=str, default=None,
                          help="쉼표로 구분된 심볼 리스트 (미지정시 S&P500 + NASDAQ100)")
        parser.add_argument("--sp500", action="store_true", help="S&P 500 종목만 수집")
        parser.add_argument("--nasdaq100", action="store_true", help="NASDAQ 100 종목만 수집")
        parser.add_argument("--nyse", action="store_true", help="NYSE 전체 종목 수집")
        parser.add_argument("--batch-delay", type=float, default=0.5, help="API 호출 간 대기 시간(초)")

    def handle(self, *args, **options):
        """yfinance 패키지 확인 후 부모 클래스의 handle 호출"""
        if yf is None:
            self.stderr.write(
                self.style.ERROR(
                    "yfinance 패키지가 필요합니다: pip install yfinance pandas"
                )
            )
            return

        # 심볼 수집 및 옵션 저장 (fetch_all_companies에서 사용)
        self._options = options
        super().handle(*args, **options)

    def fetch_all_companies(self) -> Dict[str, Dict[str, Any]]:
        """모든 회사 정보 수집"""
        options = self._options
        batch_delay = options["batch_delay"]

        # 대상 심볼 결정
        if options.get("symbols"):
            symbols = [s.strip().upper() for s in options["symbols"].split(",") if s.strip()]
            self.stdout.write(f"지정된 심볼 {len(symbols)}개 사용")
        else:
            symbols = []

            # NYSE 옵션이 지정된 경우
            if options.get("nyse"):
                symbols.extend(_get_nyse_symbols())
            # 다른 특정 옵션들
            elif options.get("sp500") or options.get("nasdaq100"):
                if options.get("sp500"):
                    symbols.extend(_get_sp500_symbols())
                if options.get("nasdaq100"):
                    symbols.extend(_get_nasdaq100_symbols())
            # 아무 옵션도 없으면 기본값 (S&P500 + NASDAQ100)
            else:
                symbols.extend(_get_sp500_symbols())
                symbols.extend(_get_nasdaq100_symbols())

            # 중복 제거
            symbols = list(dict.fromkeys(symbols))
            self.stdout.write(f"총 {len(symbols)}개 심볼 수집")

        if not symbols:
            return {}

        # 회사 정보 수집
        companies_data = _get_company_info(symbols, batch_delay)
        return companies_data

    def get_model_class(self):
        """사용할 모델 클래스 반환"""
        return USCompanyInfo

    def get_code_field_name(self) -> str:
        """코드 필드명 반환"""
        return "symbol"

    def create_model_instance(self, code: str, data: Dict[str, Any]) -> USCompanyInfo:
        """모델 인스턴스 생성"""
        return USCompanyInfo(
            symbol=code,
            company_name=data.get('company_name', code),
            sector=data.get('sector'),
            industry=data.get('industry'),
            market_cap=data.get('market_cap'),
            exchange=data.get('exchange'),
            country=data.get('country', 'US'),
            currency=data.get('currency', 'USD'),
            is_active=data.get('is_active', True),
        )

    def get_update_fields(self):
        """업데이트할 필드 목록"""
        return ["company_name", "sector", "industry", "market_cap",
                "exchange", "country", "currency", "is_active"]
