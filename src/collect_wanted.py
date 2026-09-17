from pathlib import Path
from datetime import datetime, timezone
import csv
import json
import random
import time

import requests


# =====================================================================
# 1. 경로 설정
# =====================================================================

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"
DETAIL_DIR = RAW_DIR / "details"
CSV_PATH = RAW_DIR / "wanted_jobs.csv"

RAW_DIR.mkdir(parents=True, exist_ok=True)
DETAIL_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================================
# 2. 원티드 API 설정
# =====================================================================

BASE_URL = "https://www.wanted.co.kr"

# 채용 공고 목록을 가져오는 주소
# 여기서 여러 공고의 ID를 먼저 얻음
LIST_URL = f"{BASE_URL}/api/v4/jobs"

# 공고 하나의 상세 내용을 가져오는 주소
# ID를 이용해 자격요건, 주요업무, 우대사항 등을 얻음
DETAIL_URL = f"{BASE_URL}/api/v4/jobs/{{jid}}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

TIMEOUT = 15


# =====================================================================
# 3. 수집 대상 직무 카테고리
# =====================================================================

# 원티드 tag_type_id
# URL 예: https://www.wanted.co.kr/wdlist/518/655 = 데이터 엔지니어
# 카테고리 필터에는 인접 직무가 섞일 수 있으므로
# 이후 classify.py에서 공고 제목을 기준으로 다시 분류


# 원티드가 각 직무 카테고리에 실제로 부여한 tag_type_id를 사용
JOB_CATEGORIES = {
    656: "데이터분석가",  # wdlist/507/656
    655: "데이터엔지니어",  # wdlist/518/655
    1024: "데이터사이언티스트",  # wdlist/518/1024
    674: "백엔드개발자",  # wdlist/518/674
    669: "프론트엔드개발자",  # wdlist/518/669
}

# 각 카테고리에서 최대 400개의 공고 ID까지만 수집할 것
PER_CAT = 400

# 목록 API를 한 번 호출할 때 최대 100개씩 가져옴
LIST_LIMIT = 100

SLEEP = 0.35


# =====================================================================
# 4. API 요청
# =====================================================================


def _get(url, params=None, retries=3):
    # 마지막으로 발생한 오류 저장
    last = None

    for k in range(retries):
        try:
            r = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=TIMEOUT,
            )

            if r.status_code == 200:
                return r.json()

            last = f"HTTP {r.status_code}"

        except Exception as e:
            last = repr(e)

        # 요청 실패 시 기다리는 시간을 점점 늘려 다시 시도
        time.sleep(SLEEP * (2**k) + random.uniform(0, 0.3))

    print(f"  [skip] {url} params={params} :: {last}")

    return None


# =====================================================================
# 5. 카테고리별 공고 ID 수집
# =====================================================================


# 한 카테고리의 공고 id를 PER_CAT 만큼 페이징 수집
def collect_ids_for_category(cat_id: int) -> list[int]:

    ids = []
    offset = 0

    while len(ids) < PER_CAT:
        js = _get(
            LIST_URL,
            {
                "country": "kr",
                "job_sort": "job.latest_order",
                "locations": "all",
                "years": "-1",
                "tag_type_ids": cat_id,
                "limit": LIST_LIMIT,  # 페이지 크기
                "offset": offset,  # 다음 페이지 시작 위치 설정
            },
        )

        if not js:
            break

        data = js.get("data", [])

        if not data:
            break

        ids += [int(x["id"]) for x in data]

        # 다음 페이지가 없으면 수집 종료
        if not (js.get("links") or {}).get("next"):
            break

        offset += LIST_LIMIT
        time.sleep(SLEEP)

    return ids[:PER_CAT]


# =====================================================================
# 6. 공고 상세 수집 + JSON 캐시
# =====================================================================
# collect_ids_for_category()로 공고 ID만 받아왔음
# fetch_detail()로 자격 요건, 우대 사항, 주요 업무 등 상세 내용 가져올 것


# 상세 1건(캐시가 있으면 다시 요청하지 않고 재사용)
# API 호출 전 캐시부터 확인
def fetch_detail(job_id: int) -> dict | None:

    cache = DETAIL_DIR / f"{job_id}.json"

    # 이미 받아 둔 공고는 파일에서 읽음
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))

        # 캐시 파일이 깨졌다면 아래에서 다시 요청
        except Exception:
            pass

    js = _get(DETAIL_URL.format(jid=job_id))

    # 정상적인 상세 응답인지 확인
    if js and "job" in js:
        cache.write_text(
            json.dumps(js, ensure_ascii=False),
            encoding="utf-8",
        )

        time.sleep(SLEEP)

        return js

    return None


# =====================================================================
# 7. 상세 JSON에서 분석용 데이터 추출
# =====================================================================


# 프로젝트 분석에 필요한 항목만 골라서 공고 하나당 하나의 딕셔너리로 정리
def _row_from_detail(js: dict, cat_id: int, cat_name: str) -> dict:
    job = js["job"]

    det = job.get("detail") or {}
    comp = job.get("company") or {}

    return {
        "job_id": int(job["id"]),  # 공고 고유 ID
        "category_id": cat_id,  # 원티드 직무 카테고리(수집용)
        "category_name": cat_name,  # 직무 카테고리 이름(수집용)
        "position": job.get("position"),  # 실제 채용공고 제목
        "company": comp.get("name"),  # 회사명
        "industry": comp.get("industry_name"),  # 업종
        "annual_from": job.get("annual_from"),  # 최소 요구 경력
        "annual_to": job.get("annual_to"),  # 최대 요구 경력
        "requirements": det.get("requirements"),  # 자격 요건
        "main_tasks": det.get("main_tasks"),  # 주요 업무
        "preferred": det.get("preferred_points"),  # 우대사항
        "intro": det.get("intro"),  # 회사/채용 소개
        "benefits": det.get("benefits"),  # 복지 및 혜택
        "skill_tags": json.dumps(
            job.get("skill_tags") or [],
            ensure_ascii=False,
        ),  # 원티드에서 제공하는 기술 태그
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# 공고 식별/분류 : job_id, category_id, category_name
# 공고 기본정보 : position, industry, annual_from, annual_to
# 기술 분석의 핵심 텍스트 : requirements, main_tasks, preferred
# 부가 정보 : intro, benefits, skill_tags
# 데이터 관리 정보 : collected_at


# =====================================================================
# 8. CSV 저장
# =====================================================================


def save_csv(rows: list[dict]):
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    # _row_from_detail()에서 정했던 딕셔너리의 키가 CSV의 열 이름이 되는 구조

    with CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        # 저장할 rows가 딕셔너리들
        # 일반 csv.writer가 아닌 DictWriter 사용
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# =====================================================================
# 9. 전체 수집 실행
# =====================================================================


def main():

    print("=" * 64)
    print("원티드 채용공고 수집 (인증키 불필요)")
    print("=" * 64)

    # -------------------------------------------------------------
    # 카테고리별 공고 ID 수집
    # -------------------------------------------------------------

    job_categories = {}

    for cat_id, cat_name in JOB_CATEGORIES.items():
        ids = collect_ids_for_category(cat_id)

        print(f"[목록] {cat_name} (id={cat_id}) 수집 {len(ids)}건")

        # 한 공고가 여러 카테고리에 포함될 수 있음
        # 최초로 발견한 카테고리를 대표 수집 카테고리로 저장
        # 공고 ID를 딕셔너리의 key로 사용해 중복을 제거
        for job_id in ids:
            if job_id not in job_categories:
                job_categories[job_id] = (cat_id, cat_name)

    print()
    print(f"고유 공고 id: {len(job_categories):,}건 (중복 제거 후)")

    # -------------------------------------------------------------
    # 이미 받은 상세 캐시 확인
    # -------------------------------------------------------------

    # job_categories 딕셔너리의 key(공고 ID)를 하나씩 가져옴
    # # 각 ID에 대해서 해당 공고의 캐시 파일 경로를 만들어 줌
    # .exists()로 그 파일이 실제로 존재하는 지 확인
    # 현재 수집 대상 중 이미 저장되어 있는 JSON이 몇 개 인지 체크
    cached = sum((DETAIL_DIR / f"{job_id}.json").exists() for job_id in job_categories)

    print(f"이미 받은 상세(캐시): {cached:,}건 → 나머지만 네트워크 호출")

    # -------------------------------------------------------------
    # 상세 공고 수집
    # -------------------------------------------------------------

    # 최종적으로 CSV에 저장할 공고 데이터들을 모아놓는 리스트
    rows = []

    success = 0  # 성공
    fail = 0  # 실패

    # 중복 제거 후 최종적으로 상세정보를 가져와야 할 공고의 개수
    total = len(job_categories)

    # enumerate()로 진행 순서를 붙임(1부터 시작)
    for i, (job_id, category) in enumerate(
        job_categories.items(),
        start=1,
    ):
        # 튜플 언패킹
        cat_id, cat_name = category

        # fetch_detail()로 상세정보 확보
        js = fetch_detail(job_id)

        if js:
            # append()로 변환된 공고를 rows에 누적
            rows.append(
                # _row_from_detail()로 분석용 형태 변환
                _row_from_detail(
                    js,
                    cat_id,
                    cat_name,
                )
            )

            success += 1

        else:
            fail += 1

        if i % 100 == 0 or i == total:
            print(f"상세 {i:,}/{total:,} ... 성공 {success:,} 실패 {fail:,}")

    print()
    print(f"상세 성공 {success:,} / 실패 {fail:,}")

    # -------------------------------------------------------------
    # CSV 저장
    # -------------------------------------------------------------

    save_csv(rows)

    print(
        f"저장: data/raw/wanted_jobs.csv "
        f"({len(rows):,}행 × "
        f"{len(rows[0]) if rows else 0}열)"
    )

    # -------------------------------------------------------------
    # 수집 결과 품질 확인
    # -------------------------------------------------------------

    # 수집한 데이터가 실제 분석에 쓸 만한 상태인지 간단하게 검사
    if rows:
        empty_requirements = sum(
            not str(row.get("requirements") or "").strip() for row in rows
        )

        empty_ratio = empty_requirements / len(rows) * 100

        print(f"requirements 빈 공고: {empty_requirements:,}건 ({empty_ratio:.1f}%)")

        category_counts = {}

        for row in rows:
            name = row["category_name"]

            category_counts[name] = category_counts.get(name, 0) + 1

        print(f"카테고리 분포: {category_counts}")


if __name__ == "__main__":
    main()

# 이 파일을 직접 실행할 때에만 전체 수집을 시작
# 다른 파일에서 모듈로 불러올 때는 함수 정의만 사용할 수 있도록 구분


# ================================================================
# 원티드 채용공고 수집 (인증키 불필요)
# ================================================================
# [목록] 데이터분석가 (id=656) 수집 115건
# [목록] 데이터엔지니어 (id=655) 수집 316건
# [목록] 데이터사이언티스트 (id=1024) 수집 215건
# [목록] 백엔드개발자 (id=674) 수집 400건
# [목록] 프론트엔드개발자 (id=669) 수집 355건

# 고유 공고 id: 1,273건 (중복 제거 후)
# 이미 받은 상세(캐시): 0건 → 나머지만 네트워크 호출
# 상세 100/1,273 ... 성공 100 실패 0
# 상세 200/1,273 ... 성공 200 실패 0
# 상세 300/1,273 ... 성공 300 실패 0
# 상세 400/1,273 ... 성공 400 실패 0
# 상세 500/1,273 ... 성공 500 실패 0
# 상세 600/1,273 ... 성공 600 실패 0
# 상세 700/1,273 ... 성공 700 실패 0
# 상세 800/1,273 ... 성공 800 실패 0
# 상세 900/1,273 ... 성공 900 실패 0
# 상세 1,000/1,273 ... 성공 1,000 실패 0
# 상세 1,100/1,273 ... 성공 1,100 실패 0
# 상세 1,200/1,273 ... 성공 1,200 실패 0
# 상세 1,273/1,273 ... 성공 1,273 실패 0

# 상세 성공 1,273 / 실패 0
# 저장: data/raw/wanted_jobs.csv (1,273행 × 15열)
# requirements 빈 공고: 0건 (0.0%)
# 카테고리 분포: {'데이터분석가': 115, '데이터엔지니어': 316, '데이터사이언티스트': 139, '백엔드개발자': 371, '프론트엔드개발자': 332}


# =====================================================================

# 원티드 직무 tag_type_id를 이용해 직무별 채용공고 ID를 수집함.
# limit=100, offset=0→100→200→300→400(카테고리 하나 당 최대) 방식으로 페이징

# 요청 실패 시 재시도
# 지수 백오프(실패할수록 대기시간 늘림)
# 랜덤 지터(약간의 랜덤 대기 시간 추가)로 연속적 재요청 줄임

# 상세 공고는 job_id별 JSON으로 캐시해 재실행 시 불필요한 API 호출을 줄임
# 동일 공고가 여러 카테고리에 포함될 수 있어 job_id를 기준으로 중복을 제거함
# 상세 JSON에서 자격요건, 주요업무, 우대사항 등 분석에 필요한 필드만 추출하고 rows에 누적
# requirements 결측 비율과 카테고리별 수집 건수를 추력해 수집 품질을 확인함
# 수집 카테고리는 최종 직무가 아니며 이후 classify.py에서 제목 기준으로 재분류할 것
