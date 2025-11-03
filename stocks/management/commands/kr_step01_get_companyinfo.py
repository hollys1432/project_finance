# === management/commands/kr_step01_get_companyinfo.py ===
from __future__ import annotations
import logging
from typing import Dict, Any
from datetime import datetime

from stocks.models import CompanyInfo

from ._base_commands import BaseCompanyInfoCommand

logger = logging.getLogger(__name__)

try:
    from stocks.src.stockinfo import StockDataManager
except Exception:
    StockDataManager = None


def _fetch_all_tickers_with_dates() -> Dict[str, Dict[str, Any]]:
    """전 상장 종목 메타데이터 수집.
    반환 예: {
        "005930": {"company_name": "삼성전자", "market": "KOSPI", "listing_date": date, "is_active": True},
        ...
    }
    """
    if StockDataManager is not None:
        sdm = StockDataManager()
        return sdm.get_all_tickers_with_dates()  # 기존 구현 재사용

    # Fallback (pykrx 사용) — 필요한 경우만.
    from datetime import date
    from pykrx import stock
    import time
    import random

    tickers = {}
    for market in ("KOSPI", "KOSDAQ", "KONEX"):
        try:
            market_codes = stock.get_market_ticker_list(market=market)
            for code in market_codes:
                try:
                    name = stock.get_market_ticker_name(code)
                    
                    # 상장일 조회 (기존 방식과 동일)
                    listing_date = None
                    try:
                        start_date = "19600101"
                        end_date = datetime.now().strftime("%Y%m%d")
                        data = stock.get_market_ohlcv_by_date(start_date, end_date, code)
                        if not data.empty:
                            first_date = data.index[0]
                            if hasattr(first_date, 'date'):
                                listing_date = first_date.date()
                            else:
                                listing_date = first_date.to_pydatetime().date()
                    except Exception as e:
                        logger.warning(f"{code} 상장일 조회 실패: {e}")
                    
                    tickers[code] = {
                        "company_name": name,
                        "market": market,
                        "listing_date": listing_date,
                        "is_active": True,
                    }
                    
                    # API 부하 방지
                    time.sleep(random.uniform(0.1, 0.3))
                    
                except Exception as e:
                    logger.error(f"{code} 정보 수집 실패: {e}")
                    
        except Exception as e:
            logger.error(f"{market} 시장 정보 수집 실패: {e}")
            
    return tickers


class Command(BaseCompanyInfoCommand):
    help = "한국 상장사 기본정보 동기화: 신규 insert + 변경분 bulk_update. 재실행 안전."

    def fetch_all_companies(self) -> Dict[str, Dict[str, Any]]:
        """전 상장 종목 메타데이터 수집"""
        return _fetch_all_tickers_with_dates()

    def get_model_class(self):
        """사용할 모델 클래스 반환"""
        return CompanyInfo

    def get_code_field_name(self) -> str:
        """코드 필드명 반환"""
        return "company_code"

    def create_model_instance(self, code: str, data: Dict[str, Any]) -> CompanyInfo:
        """모델 인스턴스 생성"""
        return CompanyInfo(
            company_code=code,
            company_name=data.get("company_name"),
            market=data.get("market"),
            listing_date=data.get("listing_date"),
            is_active=data.get("is_active", True),
        )

    def get_update_fields(self):
        """업데이트할 필드 목록"""
        return ["company_name", "market", "listing_date", "is_active"]