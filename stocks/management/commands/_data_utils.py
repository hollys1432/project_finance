"""
공통 유틸리티 함수 모듈
주식 데이터 수집 관련 커맨드에서 공통으로 사용되는 함수들
"""
from __future__ import annotations
import time
import random
import logging
from datetime import datetime, date, timedelta
from typing import Iterable, Optional, Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')


def daterange(d0: date, d1: date, chunk_days: int = 365) -> Iterable[tuple[date, date]]:
    """
    [d0, d1] 구간을 chunk_days 단위로 분할해 (start, end) 구간 시퀀스 생성.

    Args:
        d0: 시작 날짜
        d1: 종료 날짜
        chunk_days: 분할 단위 (일)

    Yields:
        (start, end) 날짜 튜플
    """
    cur = d0
    while cur <= d1:
        end = min(cur + timedelta(days=chunk_days - 1), d1)
        yield cur, end
        cur = end + timedelta(days=1)


def parse_date(s: Optional[str]) -> Optional[date]:
    """
    YYYY-MM-DD 형식의 문자열을 date 객체로 변환

    Args:
        s: 날짜 문자열 (YYYY-MM-DD 형식)

    Returns:
        date 객체 또는 None
    """
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


def sleep_random(min_seconds: float, max_seconds: float) -> None:
    """
    API 부하 방지를 위한 랜덤 대기

    Args:
        min_seconds: 최소 대기 시간(초)
        max_seconds: 최대 대기 시간(초)
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def retry_api_call(
    func: Callable[..., T],
    *args,
    retry_count: int = 2,
    base_delay: float = 1.5,
    error_msg_prefix: str = "API 호출",
    **kwargs
) -> T:
    """
    API 호출을 재시도 로직과 함께 실행

    Args:
        func: 실행할 함수
        *args: 함수에 전달할 위치 인자
        retry_count: 재시도 횟수
        base_delay: 기본 대기 시간 (배수로 증가)
        error_msg_prefix: 에러 로그 메시지 접두사
        **kwargs: 함수에 전달할 키워드 인자

    Returns:
        함수 실행 결과

    Raises:
        마지막 시도에서 발생한 예외
    """
    last_error = None
    for i in range(retry_count + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if i < retry_count:
                delay = base_delay * (i + 1) + random.uniform(0.1, 0.5)
                time.sleep(delay)
                logger.warning(f"{error_msg_prefix} 실패 (시도 {i+1}/{retry_count+1}): {e}")

    logger.error(f"{error_msg_prefix} 최종 실패: {last_error}")
    raise last_error


def calculate_date_range(
    last_saved_date: Optional[date],
    start_arg: Optional[date],
    end_arg: Optional[date],
    only_latest: bool = False,
    full_history: bool = False,
    default_history_days: int = 1095
) -> tuple[Optional[date], date]:
    """
    수집할 날짜 범위를 결정

    Args:
        last_saved_date: 마지막으로 저장된 날짜
        start_arg: 명령줄에서 지정한 시작 날짜
        end_arg: 명령줄에서 지정한 종료 날짜
        only_latest: 최근 데이터만 수집 여부
        full_history: 전체 이력 수집 여부
        default_history_days: 기본 히스토리 수집 일수 (기본값: 1095일 = 3년)

    Returns:
        (start_date, end_date) 튜플. start_date가 None이면 수집 불필요
    """
    today = datetime.now().date()
    end = min(end_arg or today, today)

    if only_latest:
        # 최근 데이터만 증분 수집
        start = (last_saved_date + timedelta(days=1)) if last_saved_date else end
    elif full_history:
        # 전체 이력 수집
        start = today - timedelta(days=default_history_days)
    else:
        # 일반 모드: 스마트 증분 수집
        if start_arg:
            start = start_arg
        elif last_saved_date is None:
            # 저장된 데이터 없으면 기본 기간부터
            start = today - timedelta(days=default_history_days)
        else:
            # 다음날부터 증분 수집
            start = last_saved_date + timedelta(days=1)

    if start > end:
        return None, end
    return start, end


def format_number(num: int) -> str:
    """
    숫자를 천 단위 구분 기호와 함께 포맷팅

    Args:
        num: 포맷팅할 숫자

    Returns:
        포맷팅된 문자열
    """
    return f"{num:,}"


def get_date_range_message(start: date, end: date) -> str:
    """
    날짜 범위 메시지 생성

    Args:
        start: 시작 날짜
        end: 종료 날짜

    Returns:
        "YYYY-MM-DD ~ YYYY-MM-DD (N일)" 형식의 문자열
    """
    days = (end - start).days + 1
    return f"{start} ~ {end} ({days}일)"


def safe_int_convert(value: Any, default: Optional[int] = None) -> Optional[int]:
    """
    값을 안전하게 int로 변환

    Args:
        value: 변환할 값
        default: 변환 실패 시 반환할 기본값

    Returns:
        int 값 또는 기본값
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
