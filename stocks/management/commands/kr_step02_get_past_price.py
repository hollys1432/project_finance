# === management/commands/kr_step02_get_past_price.py ===
from __future__ import annotations
import logging
from datetime import date
from typing import List, Dict, Any

from pykrx import stock

from stocks.models import CompanyInfo, PriceData

from ._base_commands import BasePriceDataCommand

logger = logging.getLogger(__name__)


class Command(BasePriceDataCommand):
    help = "한국 주식 과거/증분 일별 시세 수집. 재실행 안전, 증분 수집, 배치 삽입"

    def add_custom_arguments(self, parser):
        """한국 시장 특화 인자"""
        parser.add_argument("--codes", type=str, default=None, help="쉼표로 구분된 종목코드 목록(미지정시 전체 활성 종목)")
        parser.add_argument("--markets", type=str, default=None, help="시장 필터 (쉼표구분: KOSPI,KOSDAQ,KONEX)")

    def get_company_model(self):
        """회사 정보 모델 반환"""
        return CompanyInfo

    def get_price_model(self):
        """가격 데이터 모델 반환"""
        return PriceData

    def get_target_companies(self, options: Dict) -> List[CompanyInfo]:
        """대상 회사 목록 조회"""
        codes = options.get("codes")
        markets = options.get("markets")

        qs = CompanyInfo.objects.all()
        if codes:
            code_list = [c.strip() for c in codes.split(",") if c.strip()]
            qs = qs.filter(company_code__in=code_list)
        else:
            qs = qs.filter(is_active=True)

        if markets:
            raw = [m.strip().upper() for m in markets.split(",") if m.strip()]
            alias = {"코스피": "KOSPI", "코스닥": "KOSDAQ", "유가증권": "KOSPI", "코넥스": "KONEX"}
            market_list = [alias.get(m, m) for m in raw]
            qs = qs.filter(market__in=market_list)

        return list(qs.order_by("company_code"))

    def fetch_price_data(self, company: CompanyInfo, start: date, end: date) -> Any:
        """pykrx로 가격 데이터 조회"""
        s = start.strftime("%Y%m%d")
        e = end.strftime("%Y%m%d")
        return stock.get_market_ohlcv_by_date(s, e, company.company_code)

    def parse_to_model_objects(self, df, company: CompanyInfo) -> List[PriceData]:
        """DataFrame을 PriceData 객체 리스트로 변환"""
        objs: List[PriceData] = []
        
        # DataFrame 컬럼명 확인 및 표준화
        if df is None or df.empty:
            return objs
            
        # pykrx의 컬럼명은 한글일 수 있음 ('시가', '고가', '저가', '종가', '거래량')
        # 또는 영문일 수 있음 ('Open', 'High', 'Low', 'Close', 'Volume')
        
        for row in df.itertuples():
            trade_date = getattr(row, "Index")
            if hasattr(trade_date, 'date'):
                trade_date = trade_date.date()
            elif hasattr(trade_date, 'to_pydatetime'):
                trade_date = trade_date.to_pydatetime().date()
            
            # 컬럼명 유연하게 처리
            open_price = None
            high_price = None  
            low_price = None
            close_price = None
            volume = None
            
            # 한글 컬럼명 시도
            try:
                open_price = getattr(row, "시가", None)
                high_price = getattr(row, "고가", None)
                low_price = getattr(row, "저가", None)
                close_price = getattr(row, "종가", None)
                volume = getattr(row, "거래량", None)
            except AttributeError:
                pass
            
            # 영문 컬럼명 시도 (한글이 없는 경우)
            if open_price is None:
                try:
                    open_price = getattr(row, "Open", None)
                    high_price = getattr(row, "High", None)
                    low_price = getattr(row, "Low", None)
                    close_price = getattr(row, "Close", None)
                    volume = getattr(row, "Volume", None)
                except AttributeError:
                    pass
            
            # 인덱스 기반으로 시도 (마지막 수단)
            if open_price is None and len(row) >= 6:
                try:
                    open_price = row[1]  # 첫 번째는 Index
                    high_price = row[2]
                    low_price = row[3] 
                    close_price = row[4]
                    volume = row[5]
                except (IndexError, AttributeError):
                    logger.warning(f"{company.company_code} 행 파싱 실패: {row}")
                    continue
            
            # None 값을 0으로 변환하거나 스킵
            if close_price is None or close_price == 0:
                continue
                
            objs.append(
                PriceData(
                    stock=company,
                    stock_name=company.company_name,
                    date=trade_date,
                    open_price=int(open_price) if open_price is not None else None,
                    high_price=int(high_price) if high_price is not None else None,
                    low_price=int(low_price) if low_price is not None else None,
                    close_price=int(close_price) if close_price is not None else None,
                    volume=int(volume) if volume is not None else None,
                )
            )
            
        return objs

    def get_company_identifier(self, company: CompanyInfo) -> str:
        """회사 식별자 반환 (로깅용)"""
        return f"{company.company_code} {company.company_name}"