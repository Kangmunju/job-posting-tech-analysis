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


def collect_ids_for_category(cat_id: int) -> list[int]:
    """한 카테고리의 공고 id를 PER_CAT 만큼 페이징 수집."""

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
                "limit": LIST_LIMIT,
                "offset": offset,
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


def fetch_detail(job_id: int) -> dict | None:
    """상세 1건. 캐시가 있으면 다시 요청하지 않고 재사용."""

    cache = DETAIL_DIR / f"{job_id}.json"

    # 이미 받아 둔 공고는 파일에서 읽음
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))

        except Exception:
            # 캐시 파일이 깨졌다면 아래에서 다시 요청
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


def _row_from_detail(js: dict, cat_id: int, cat_name: str) -> dict:
    job = js["job"]

    det = job.get("detail") or {}
    comp = job.get("company") or {}

    return {
        "job_id": int(job["id"]),
        "category_id": cat_id,
        "category_name": cat_name,
        "position": job.get("position"),
        "company": comp.get("name"),
        "industry": comp.get("industry_name"),
        "annual_from": job.get("annual_from"),
        "annual_to": job.get("annual_to"),
        "requirements": det.get("requirements"),
        "main_tasks": det.get("main_tasks"),
        "preferred": det.get("preferred_points"),
        "intro": det.get("intro"),
        "benefits": det.get("benefits"),
        "skill_tags": json.dumps(
            job.get("skill_tags") or [],
            ensure_ascii=False,
        ),
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# =====================================================================
# 8. CSV 저장
# =====================================================================


def save_csv(rows: list[dict]):
    if not rows:
        return

    fieldnames = list(rows[0].keys())

    with CSV_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as f:
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
        for job_id in ids:
            if job_id not in job_categories:
                job_categories[job_id] = (cat_id, cat_name)

    print()
    print(f"고유 공고 id: {len(job_categories):,}건 (중복 제거 후)")

    # -------------------------------------------------------------
    # 이미 받은 상세 캐시 확인
    # -------------------------------------------------------------

    cached = sum((DETAIL_DIR / f"{job_id}.json").exists() for job_id in job_categories)

    print(f"이미 받은 상세(캐시): {cached:,}건 → 나머지만 네트워크 호출")

    # -------------------------------------------------------------
    # 상세 공고 수집
    # -------------------------------------------------------------

    rows = []

    success = 0
    fail = 0

    total = len(job_categories)

    for i, (job_id, category) in enumerate(
        job_categories.items(),
        start=1,
    ):
        cat_id, cat_name = category

        js = fetch_detail(job_id)

        if js:
            rows.append(
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
