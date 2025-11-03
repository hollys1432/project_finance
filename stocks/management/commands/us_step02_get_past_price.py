# === management/commands/us_step02_get_past_price.py ===
from __future__ import annotations
import logging
from datetime import date, timedelta
from typing import List, Dict, Any
from decimal import Decimal

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    yf = None
    pd = None

from stocks.models import USCompanyInfo, USPriceData

from ._base_commands import BasePriceDataCommand

logger = logging.getLogger(__name__)


class Command(BasePriceDataCommand):
    help = "미국 주식 과거/증분 일별 시세 수집. 재실행 안전, 증분 수집, 배치 삽입"

    def add_custom_arguments(self, parser):
        """미국 시장 특화 인자"""
        parser.add_argument("--symbols", type=str, default=None,
                          help="쉼표로 구분된 심볼 리스트(미지정시 전체 활성 종목)")
        parser.add_argument("--auto-adjust", action="store_true",
                          help="배당/분할 자동 조정 (기본: False, 원시 데이터 저장)")

    def handle(self, *args, **options):
        """yfinance 패키지 확인 후 부모 클래스의 handle 호출"""
        if yf is None:
            self.stderr.write(
                self.style.ERROR(
                    "yfinance 패키지가 필요합니다: pip install yfinance pandas"
                )
            )
            return

        self._auto_adjust = options.get("auto_adjust", False)
        super().handle(*args, **options)

    def get_company_model(self):
        """회사 정보 모델 반환"""
        return USCompanyInfo

    def get_price_model(self):
        """가격 데이터 모델 반환"""
        return USPriceData

    def get_target_companies(self, options: Dict) -> List[USCompanyInfo]:
        """대상 회사 목록 조회"""
        symbols = options.get("symbols")

        qs = USCompanyInfo.objects.all()
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
            qs = qs.filter(symbol__in=symbol_list)
        else:
            qs = qs.filter(is_active=True)

        return list(qs.order_by("symbol"))

    def fetch_price_data(self, company: USCompanyInfo, start: date, end: date) -> Any:
        """yfinance로 가격 데이터 조회"""
        ticker = yf.Ticker(company.symbol)
        data = ticker.history(
            start=start.strftime('%Y-%m-%d'),
            end=(end + timedelta(days=1)).strftime('%Y-%m-%d'),  # yfinance는 end 날짜를 포함하지 않음
            auto_adjust=self._auto_adjust,
            prepost=False,  # 시간외 거래 제외
            actions=True,   # 배당/분할 정보 포함
            rounding=True   # 반올림
        )
        return data

    def parse_to_model_objects(self, df, company: USCompanyInfo) -> List[USPriceData]:
        """DataFrame을 USPriceData 객체 리스트로 변환"""
        objs: List[USPriceData] = []
        
        if df is None or df.empty:
            return objs
        
        for index, row in df.iterrows():
            trade_date = index.date() if hasattr(index, 'date') else index.to_pydatetime().date()
            
            # yfinance 컬럼명은 영어 (Open, High, Low, Close, Volume)
            try:
                open_price = row.get('Open')
                high_price = row.get('High')
                low_price = row.get('Low')
                close_price = row.get('Close')
                volume = row.get('Volume')
                
                # auto_adjust=False인 경우 Adj Close도 별도 저장
                adj_close = close_price  # auto_adjust=True면 Close가 이미 조정됨
                if not self._auto_adjust and 'Adj Close' in row:
                    adj_close = row.get('Adj Close')
                
                # None이나 NaN 값 처리
                if pd.isna(close_price) or close_price == 0:
                    continue
                
                # Decimal 변환 (정밀도 보장)
                def to_decimal(val):
                    if pd.isna(val) or val is None:
                        return None
                    return Decimal(str(round(float(val), 4)))
                
                objs.append(
                    USPriceData(
                        stock=company,
                        symbol=company.symbol,
                        date=trade_date,
                        open_price=to_decimal(open_price),
                        high_price=to_decimal(high_price),
                        low_price=to_decimal(low_price),
                        close_price=to_decimal(close_price),
                        adj_close_price=to_decimal(adj_close),
                        volume=int(volume) if not pd.isna(volume) else None,
                    )
                )
            except Exception as e:
                logger.warning(f"{company.symbol} {trade_date} 행 파싱 실패: {e}")
                continue
        
        return objs

    def get_company_identifier(self, company: USCompanyInfo) -> str:
        """회사 식별자 반환 (로깅용)"""
        return f"{company.symbol} {company.company_name}"
