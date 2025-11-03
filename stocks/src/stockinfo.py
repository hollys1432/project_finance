# === stockinfo.py (optimized) ===
from __future__ import annotations
import logging
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, Any, Iterable, Tuple, Optional
from datetime import date, datetime

from pykrx import stock

logger = logging.getLogger(__name__)


@dataclass
class ManagerConfig:
    markets: Tuple[str, ...] = ("KOSPI", "KOSDAQ", "KONEX")
    min_date: date = date(1960, 1, 1)  # 상장일 탐색 하한을 더 과거로 설정
    max_workers: int = 4              # 동시 수집 워커 수를 줄여서 안정성 확보
    retry: int = 3                     # pykrx 호출 재시도 횟수 증가
    sleep_min: float = 0.1            # 호출 간 최소 대기 증가
    sleep_max: float = 0.3            # 호출 간 최대 대기 증가
    log_every: int = 50               # 진행로그 간격
    return_compat_name_key: bool = False  # True면 'name' 키도 함께 반환(구버전 호환)


class StockDataManager:
    """한국 주식 메타데이터 수집기 (고성능·재시도·동시성·호환키).

    * 기존 구현 대비 변경점
      - 단일 대역(1960~today) 대용량 조회를 유지하되, **멀티스레드**로 병렬 처리 + **지터 슬립**으로 부하 분산
      - **재시도(지수 백오프)** 및 예외 격리로 개별 티커 실패가 전체를 중단하지 않음
      - 반환 키를 `company_name`으로 표준화(필요 시 `name` 키도 동시 반환)
      - `listing_date`를 **datetime.date**로 반환하여 Django `DateField`와 직접 호환
      - 로깅 노이즈 감소: N개 간격으로만 진행률 로그 출력
    """

    def __init__(self, config: Optional[ManagerConfig] = None):
        self.cfg = config or ManagerConfig()

    # ----------------------------
    # 내부 유틸
    # ----------------------------
    def _sleep_jitter(self):
        time.sleep(random.uniform(self.cfg.sleep_min, self.cfg.sleep_max))

    def _with_retry(self, fn, *args, **kwargs):
        last_err = None
        for i in range(self.cfg.retry + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
                if i < self.cfg.retry:  # 마지막 시도가 아니면 대기
                    # 간단한 지수 백오프
                    delay = 1.0 * (2 ** i) + random.uniform(0.1, 0.5)
                    time.sleep(delay)
        raise last_err

    # ----------------------------
    # 핵심 로직
    # ----------------------------
    def _safe_get_company_name(self, ticker: str) -> Optional[str]:
        try:
            return self._with_retry(stock.get_market_ticker_name, ticker)
        except Exception as e:
            logger.warning("%s 종목명 조회 실패: %s", ticker, e)
            return None

    def _fast_listing_date(self, ticker: str) -> Optional[date]:
        """상장(최초 거래)일 추정: 한 번의 범위 호출 후 첫 index 사용.
        pykrx가 빈 구간을 자동 제외하므로 네트워크 비용이 상대적으로 적습니다.
        실패 시 None.
        """
        try:
            s = self.cfg.min_date.strftime("%Y%m%d")
            e = date.today().strftime("%Y%m%d")
            df = self._with_retry(stock.get_market_ohlcv_by_date, s, e, ticker)
            
            if df is not None and hasattr(df, 'empty') and not df.empty:
                first_dt = df.index[0]
                
                # pandas Timestamp -> date 변환 개선
                if hasattr(first_dt, 'date'):
                    return first_dt.date()
                elif hasattr(first_dt, 'to_pydatetime'):
                    return first_dt.to_pydatetime().date()
                else:
                    # 문자열인 경우 파싱 시도
                    try:
                        if isinstance(first_dt, str):
                            return datetime.strptime(first_dt, '%Y-%m-%d').date()
                        else:
                            return first_dt
                    except:
                        logger.warning(f"{ticker}: 날짜 변환 실패 - {type(first_dt)}: {first_dt}")
                        return None
            return None
        except Exception as e:
            logger.warning("%s 상장일 조회 실패: %s", ticker, e)
            return None

    def _gather_one(self, idx: int, total: int, ticker: str, market: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        try:
            name = self._safe_get_company_name(ticker)
            if not name:
                logger.debug("%s: 이름 없음 — 스킵", ticker)
                return None
                
            listing_dt = self._fast_listing_date(ticker)
            self._sleep_jitter()

            payload = {
                "company_name": name,
                "market": market,
                "listing_date": listing_dt,
                "is_active": True,
            }
            if self.cfg.return_compat_name_key:
                payload["name"] = name  # 구버전 호환용 키

            if idx % self.cfg.log_every == 0:
                logger.info("[%d/%d] %s %s 수집 (상장일: %s)", idx, total, ticker, name, listing_dt)
            return ticker, payload
        except Exception as e:
            logger.error("%s 정보 수집 실패: %s", ticker, e)
            return None

    def get_all_tickers_with_dates(self) -> Dict[str, Dict[str, Any]]:
        logger.info("전체 종목 정보 수집 시작...")

        # 1) 시장별 현재 상장 티커 조회
        market_tickers: Dict[str, list[str]] = {}
        total = 0
        for m in self.cfg.markets:
            try:
                tickers = self._with_retry(stock.get_market_ticker_list, market=m)
                market_tickers[m] = list(tickers)
                total += len(tickers)
                logger.info("%s: %d개", m, len(tickers))
            except Exception as e:
                logger.error("%s 시장 티커 조회 실패: %s", m, e)
                market_tickers[m] = []

        if total == 0:
            logger.error("조회된 종목이 없습니다.")
            return {}

        # 2) 병렬 수집
        out: Dict[str, Dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=self.cfg.max_workers) as ex:
            futures = []
            idx = 0
            for m, tickers in market_tickers.items():
                for t in tickers:
                    idx += 1
                    futures.append(ex.submit(self._gather_one, idx, total, t, m))

            completed_count = 0
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    completed_count += 1
                    if res is None:
                        continue
                    code, payload = res
                    out[code] = payload
                except Exception as e:
                    logger.error("Future 실행 중 오류: %s", e)
                    completed_count += 1

        successful_count = len(out)
        logger.info("총 %d개 종목 정보 수집 완료 (성공: %d/%d)", successful_count, successful_count, total)
        
        # 샘플 데이터 로깅
        sample_items = list(out.items())[:3]
        for code, info in sample_items:
            logger.info("샘플 데이터 - %s: %s", code, info)
            
        return out


# 기존 호환성을 위한 함수 (기존 코드에서 직접 호출하는 경우)
def get_all_tickers_with_dates():
    """기존 코드 호환성을 위한 래퍼 함수"""
    manager = StockDataManager()
    return manager.get_all_tickers_with_dates()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    mgr = StockDataManager(ManagerConfig(max_workers=4, log_every=50))
    data = mgr.get_all_tickers_with_dates()
    
    # 샘플 출력
    print(f"\n=== 수집 결과 요약 ===")
    print(f"총 종목 수: {len(data)}")
    
    # 상장일이 있는 종목 수 체크
    with_listing_date = sum(1 for v in data.values() if v.get('listing_date') is not None)
    print(f"상장일 정보가 있는 종목: {with_listing_date}/{len(data)}")
    
    # 샘플 데이터 출력
    n = min(5, len(data))
    print("\n=== 샘플 데이터 ===")
    for i, (code, info) in enumerate(list(data.items())[:n], 1):
        print(f"{i}) {code} -> {info}")