"""
베이스 커맨드 클래스
주식 데이터 수집 커맨드의 공통 로직을 제공하는 추상 클래스
"""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction, models

from . import _data_utils as utils

logger = logging.getLogger(__name__)


class BaseCompanyInfoCommand(BaseCommand, ABC):
    """회사 정보 수집 커맨드의 베이스 클래스"""

    def add_arguments(self, parser):
        """공통 인자 정의"""
        parser.add_argument("--batch-size", type=int, default=500, help="bulk 배치 크기")
        parser.add_argument("--ignore-conflicts", action="store_true", help="중복키 무시하고 신규만 삽입")
        parser.add_argument("--update", action="store_true", help="값 변경된 레코드 bulk_update 수행")
        parser.add_argument("--dry-run", action="store_true", help="DB 쓰기 없이 요약만 출력")
        parser.add_argument("--filter", type=str, default=None, help="회사명/코드 포함 텍스트로 필터")

        # 서브클래스가 추가 인자를 정의할 수 있도록
        self.add_custom_arguments(parser)

    def add_custom_arguments(self, parser):
        """서브클래스에서 추가 인자를 정의하기 위한 메서드"""
        pass

    @abstractmethod
    def fetch_all_companies(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 회사 정보를 수집하는 추상 메서드

        Returns:
            {code: {field: value, ...}, ...} 형태의 딕셔너리
        """
        pass

    @abstractmethod
    def get_model_class(self) -> type[models.Model]:
        """
        사용할 모델 클래스를 반환하는 추상 메서드

        Returns:
            CompanyInfo 또는 USCompanyInfo 등의 모델 클래스
        """
        pass

    @abstractmethod
    def get_code_field_name(self) -> str:
        """
        코드 필드명을 반환 (company_code 또는 symbol)

        Returns:
            코드 필드명 문자열
        """
        pass

    @abstractmethod
    def create_model_instance(self, code: str, data: Dict[str, Any]) -> models.Model:
        """
        모델 인스턴스 생성

        Args:
            code: 회사 코드
            data: 회사 정보 딕셔너리

        Returns:
            모델 인스턴스
        """
        pass

    @abstractmethod
    def get_update_fields(self) -> List[str]:
        """
        업데이트할 필드 목록 반환

        Returns:
            필드명 리스트
        """
        pass

    def handle(self, *args, **options):
        """메인 실행 로직"""
        batch_size = options["batch_size"]
        ignore_conflicts = options["ignore_conflicts"]
        do_update = options["update"]
        dry = options["dry_run"]
        word = options["filter"]

        self.stdout.write(self.style.NOTICE("종목 정보 수집 시작..."))
        all_map = self.fetch_all_companies()

        if not all_map:
            self.stdout.write(self.style.ERROR("종목 정보를 가져올 수 없습니다."))
            return

        self.stdout.write(self.style.NOTICE(f"총 {len(all_map)}개 종목 정보 수집 완료"))

        # 필터 적용
        if word:
            all_map = self.apply_filter(all_map, word)
            self.stdout.write(self.style.NOTICE(f"필터 적용 후 {len(all_map)}개 종목"))

        # 기존 데이터 조회
        existing_map = self.get_existing_data(word)

        # 신규/변경 대상 분류
        to_create = self.identify_new_records(all_map, existing_map)
        to_update = self.identify_updated_records(all_map, existing_map) if do_update else []

        self.stdout.write(self.style.NOTICE(f"신규 {len(to_create)}건, 변경 {len(to_update)}건"))

        if dry:
            self.print_dry_run_summary(to_create, to_update)
            return

        # DB 저장
        self.save_to_database(to_create, to_update, batch_size, ignore_conflicts)
        self.stdout.write(self.style.SUCCESS("회사 기본정보 동기화 완료"))

    def apply_filter(self, all_map: Dict[str, Dict], word: str) -> Dict[str, Dict]:
        """필터 적용"""
        return {
            k: v for k, v in all_map.items()
            if word in k or (v.get("company_name") and word in v["company_name"])
        }

    def get_existing_data(self, word: Optional[str]) -> Dict[str, models.Model]:
        """기존 데이터 조회"""
        model = self.get_model_class()
        code_field = self.get_code_field_name()

        qs = model.objects.all()
        if word:
            # 동적으로 Q 객체 생성
            from django.db.models import Q
            qs = qs.filter(
                Q(**{f"{code_field}__icontains": word}) |
                Q(company_name__icontains=word)
            )

        return {getattr(obj, code_field): obj for obj in qs}

    def identify_new_records(self, all_map: Dict, existing_map: Dict) -> List[models.Model]:
        """신규 생성 대상 식별"""
        to_create = []
        for code, data in all_map.items():
            if code not in existing_map:
                to_create.append(self.create_model_instance(code, data))
        return to_create

    def identify_updated_records(self, all_map: Dict, existing_map: Dict) -> List[models.Model]:
        """변경 대상 식별"""
        to_update = []
        for code, data in all_map.items():
            obj = existing_map.get(code)
            if not obj:
                continue

            changed = False
            for field, new_value in data.items():
                if not hasattr(obj, field):
                    continue

                current_value = getattr(obj, field)

                # 타입별 비교 처리
                if field == "is_active":
                    new_value = bool(new_value)

                if current_value != new_value and new_value is not None:
                    setattr(obj, field, new_value)
                    changed = True

            if changed:
                to_update.append(obj)

        return to_update

    def print_dry_run_summary(self, to_create: List, to_update: List):
        """Dry-run 결과 출력"""
        code_field = self.get_code_field_name()

        if to_create:
            self.stdout.write("신규 생성 예정:")
            for obj in to_create[:5]:
                code = getattr(obj, code_field)
                self.stdout.write(f"  {code}: {obj.company_name}")
            if len(to_create) > 5:
                self.stdout.write(f"  ... 외 {len(to_create) - 5}건")

        if to_update:
            self.stdout.write("업데이트 예정:")
            for obj in to_update[:5]:
                code = getattr(obj, code_field)
                self.stdout.write(f"  {code}: {obj.company_name}")
            if len(to_update) > 5:
                self.stdout.write(f"  ... 외 {len(to_update) - 5}건")

        self.stdout.write(self.style.WARNING("DRY-RUN: DB 변경 없이 종료합니다."))

    def save_to_database(self, to_create: List, to_update: List, batch_size: int, ignore_conflicts: bool):
        """데이터베이스에 저장"""
        model = self.get_model_class()

        with transaction.atomic():
            if to_create:
                model.objects.bulk_create(
                    to_create,
                    batch_size=batch_size,
                    ignore_conflicts=ignore_conflicts,
                )
                logger.info("%s bulk_create: %s건", model.__name__, len(to_create))
                self.stdout.write(self.style.SUCCESS(f"신규 생성: {len(to_create)}건"))

            if to_update:
                model.objects.bulk_update(
                    to_update,
                    fields=self.get_update_fields(),
                    batch_size=batch_size,
                )
                logger.info("%s bulk_update: %s건", model.__name__, len(to_update))
                self.stdout.write(self.style.SUCCESS(f"업데이트: {len(to_update)}건"))


class BasePriceDataCommand(BaseCommand, ABC):
    """가격 데이터 수집 커맨드의 베이스 클래스"""

    def add_arguments(self, parser):
        """공통 인자 정의"""
        parser.add_argument("--start", type=str, default=None, help="YYYY-MM-DD (미지정시 각 종목 최종저장일+1)")
        parser.add_argument("--end", type=str, default=None, help="YYYY-MM-DD (기본: 오늘)")
        parser.add_argument("--max-chunk-days", type=int, default=365, help="API 호출 chunk 일수")
        parser.add_argument("--batch-size", type=int, default=1000, help="bulk 배치 크기")
        parser.add_argument("--sleep-min", type=float, default=0.5, help="호출 간 최소 대기")
        parser.add_argument("--sleep-max", type=float, default=1.5, help="호출 간 최대 대기")
        parser.add_argument("--dry-run", action="store_true", help="DB 쓰기 없이 요약만")
        parser.add_argument("--only-latest", action="store_true", help="당일/최근 분만 증분 수집")
        parser.add_argument("--full-history", action="store_true", help="기존 데이터 무시하고 전체 수집")
        parser.add_argument("--retry", type=int, default=2, help="API 실패시 재시도 횟수")

        # 서브클래스가 추가 인자를 정의할 수 있도록
        self.add_custom_arguments(parser)

    def add_custom_arguments(self, parser):
        """서브클래스에서 추가 인자를 정의하기 위한 메서드"""
        pass

    @abstractmethod
    def get_company_model(self) -> type[models.Model]:
        """회사 정보 모델 클래스 반환"""
        pass

    @abstractmethod
    def get_price_model(self) -> type[models.Model]:
        """가격 데이터 모델 클래스 반환"""
        pass

    @abstractmethod
    def get_target_companies(self, options: Dict) -> List[models.Model]:
        """대상 회사 목록 조회"""
        pass

    @abstractmethod
    def fetch_price_data(self, company: models.Model, start: date, end: date) -> Any:
        """가격 데이터 조회 (API 호출)"""
        pass

    @abstractmethod
    def parse_to_model_objects(self, raw_data: Any, company: models.Model) -> List[models.Model]:
        """API 응답을 모델 객체 리스트로 변환"""
        pass

    def handle(self, *args, **options):
        """메인 실행 로직"""
        start_arg = utils.parse_date(options.get("start"))
        end_arg = utils.parse_date(options.get("end"))
        chunk_days = options["max_chunk_days"]
        batch_size = options["batch_size"]
        smin, smax = options["sleep_min"], options["sleep_max"]
        dry = options["dry_run"]
        only_latest = options["only_latest"]
        full_history = options["full_history"]
        retry = options["retry"]

        companies = self.get_target_companies(options)
        self.stdout.write(self.style.NOTICE(f"대상 종목 수: {len(companies)}"))

        if not companies:
            self.stdout.write(self.style.ERROR("대상 종목이 없습니다."))
            return

        # 수집 모드 출력
        mode_msg = self.get_collection_mode_message(only_latest, full_history, start_arg, end_arg)
        self.stdout.write(self.style.NOTICE(f"수집 모드: {mode_msg}"))

        total_inserted = 0
        total_skipped = 0
        total_errors = 0

        for idx, company in enumerate(companies, 1):
            try:
                result = self.process_company(
                    company, idx, len(companies), start_arg, end_arg,
                    only_latest, full_history, chunk_days, batch_size,
                    smin, smax, dry, retry
                )
                if result["status"] == "success":
                    total_inserted += result["count"]
                elif result["status"] == "skipped":
                    total_skipped += 1
            except Exception as e:
                total_errors += 1
                logger.exception("회사 처리 중 오류: %s", e)
                self.stderr.write(self.style.ERROR(f"오류: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"완료 — 저장시도 {total_inserted}건, 스킵 {total_skipped}종목, 오류 {total_errors}종목"
            )
        )

    def process_company(
        self, company: models.Model, idx: int, total: int,
        start_arg: Optional[date], end_arg: Optional[date],
        only_latest: bool, full_history: bool, chunk_days: int,
        batch_size: int, smin: float, smax: float, dry: bool, retry: int
    ) -> Dict[str, Any]:
        """개별 회사 처리"""
        # 수집 기간 결정
        start, end = self.decide_date_range(company, start_arg, end_arg, only_latest, full_history)

        if start is None or (end - start).days < 1:
            return {"status": "skipped", "count": 0}

        self.stdout.write(
            self.style.NOTICE(
                f"[{idx}/{total}] {self.get_company_identifier(company)} : "
                f"{utils.get_date_range_message(start, end)}"
            )
        )

        if dry:
            self.stdout.write(self.style.WARNING("DRY-RUN: 처리 예정"))
            return {"status": "skipped", "count": 0}

        # 데이터 수집
        all_objs = self.collect_price_data(company, start, end, chunk_days, smin, smax, retry)

        if not all_objs:
            self.stdout.write(f"  수집된 데이터 없음")
            return {"status": "skipped", "count": 0}

        # DB 저장
        self.save_price_data(all_objs, batch_size)
        self.stdout.write(self.style.SUCCESS(f"저장 시도: {len(all_objs)}건"))

        return {"status": "success", "count": len(all_objs)}

    def decide_date_range(
        self, company: models.Model, start_arg: Optional[date],
        end_arg: Optional[date], only_latest: bool, full_history: bool
    ) -> tuple[Optional[date], date]:
        """수집 기간 결정"""
        price_model = self.get_price_model()
        from django.db.models import Max

        last_saved = price_model.objects.filter(stock=company).aggregate(Max("date"))['date__max']

        return utils.calculate_date_range(
            last_saved, start_arg, end_arg, only_latest, full_history
        )

    def collect_price_data(
        self, company: models.Model, start: date, end: date,
        chunk_days: int, smin: float, smax: float, retry: int
    ) -> List[models.Model]:
        """기간별로 분할하여 가격 데이터 수집"""
        all_objs = []

        for s, e in utils.daterange(start, end, chunk_days):
            if s > e:
                continue

            try:
                raw_data = utils.retry_api_call(
                    self.fetch_price_data,
                    company, s, e,
                    retry_count=retry,
                    error_msg_prefix=f"{self.get_company_identifier(company)} API 호출"
                )

                if raw_data is None or self.is_empty_data(raw_data):
                    utils.sleep_random(smin, smax)
                    continue

                chunk_objs = self.parse_to_model_objects(raw_data, company)
                all_objs.extend(chunk_objs)

                self.stdout.write(f"  {s}~{e}: {len(chunk_objs)}건")
                utils.sleep_random(smin, smax)

            except Exception as chunk_error:
                logger.error(f"{s}~{e} 구간 처리 실패: {chunk_error}")
                continue

        return all_objs

    def save_price_data(self, objs: List[models.Model], batch_size: int):
        """가격 데이터 저장"""
        price_model = self.get_price_model()

        with transaction.atomic():
            price_model.objects.bulk_create(
                objs, batch_size=batch_size, ignore_conflicts=True
            )

    def is_empty_data(self, data: Any) -> bool:
        """데이터가 비어있는지 확인 (DataFrame 등)"""
        if hasattr(data, 'empty'):
            return data.empty
        return not data

    @abstractmethod
    def get_company_identifier(self, company: models.Model) -> str:
        """회사 식별자 반환 (로깅용)"""
        pass

    def get_collection_mode_message(
        self, only_latest: bool, full_history: bool,
        start_arg: Optional[date], end_arg: Optional[date]
    ) -> str:
        """수집 모드 메시지 생성"""
        if only_latest:
            return "증분 수집 모드 (최근 데이터만)"
        elif full_history:
            return "전체 이력 수집 모드"
        elif start_arg:
            return f"지정 기간 수집 모드 ({start_arg} ~ {end_arg or '오늘'})"
        else:
            return "스마트 증분 수집 모드 (미수집 데이터 자동 탐지)"
