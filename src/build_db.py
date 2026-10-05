from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

from db import DB_PATH, JOB_COLS, connect, upsert_jobs


# =====================================================================
# 1. 경로 설정
# =====================================================================

# pathlib.Path.resolve() : 상대 경로를 심볼릭 링크(바로가기 파일)까지 포함해 완전히 정규화된 절대 경로로 변환
ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "data" / "raw" / "wanted_jobs.csv"


# =====================================================================
# 2. CSV 불러오기
# =====================================================================


def load_csv():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"원본 CSV를 찾을 수 없습니다: {CSV_PATH}\n 먼저 src/collect_wanted.py를 실행하세요"
        )

    df = pd.read_csv(CSV_PATH)

    rows_in = len(df)

    # DB 저장에 필요한 컬럼이 모두 존재하는지 확인
    missing_cols = []

    for col in JOB_COLS:
        if col not in df.columns:
            missing_cols.append(col)

    if missing_cols:
        raise ValueError(f"CSV에 필요한 컬럼이 없습니다: {missing_cols}")

    # job_id가 없는 행은 DB의 공고로 사용할 수 없으므로 제거해야 함
    df = df.dropna(subset=["job_id"]).copy()

    df["job_id"] = df["job_id"].astype(int)

    # duplicated() : 데이터프레임에서 중복된 행을 찾아 T/F로 이루어진 Series 반환
    duplicated_count = df.duplicated(subset=["job_id"]).sum()

    # drop_duplicates() : 데이터프레임에서 중복된 행 제거
    df = df.drop_duplicates(subset=["job_id"], keep="last").copy()

    return df, rows_in, duplicated_count


# =====================================================================
# 3. 적재 기록 저장
# =====================================================================


def save_build_log(con, rows_in, inserted, updated):
    note = f"source={CSV_PATH.name}"

    # execute() : DB 커서 객체에서 SQL 쿼리 실행할 때 사용하는 메서드
    # con.execute(SQL문, SQL문에 넣을 값)
    # 직접 문자열에 값을 끼워 넣지 않고 ?를 사용해 값을 따로 전달
    con.execute(
        """
        INSERT INTO build_log (
            run_at,
            rows_in,
            rows_inserted,
            rows_updated,
            note
            )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            # timezone.utc : 현재 시간을 특정 지역 기준(로컬)이 아닌 세계 표준시(UTC) 기준으로 가져옴
            # isoformat() : 날짜와 시간을 국제 표준 형태로 변환
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            rows_in,
            inserted,
            updated,
            note,
        ),
    )

    # commit() : DB 작업 내용을 영구적으로 반영하거나 pre-commit 등을 다룰 때 사용
    con.commit()


# =====================================================================
# 4. 적재 후 품질 확인
# =====================================================================


def quality_check(con):
    # DB 전체 공고 수
    total = con.execute(
        """
        SELECT COUNT(*)
        FROM jobs
        """
        # fetchone() : DB 쿼리 실행 결과에서 단 하나의 행만 가져오는 커서 메서드
    ).fetchone()[0]

    # requirements가 비어 있는 공고 수
    empty_requirements = con.execute(
        """
        SELECT COUNT(*)
        FROM jobs
        WHERE requirements IS NULL
            OR TRIM(requirements) = ''
        """
    ).fetchone()[0]

    if total > 0:
        empty_ratio = empty_requirements / total * 100
    else:
        empty_ratio = 0.0

    print()
    print(f"[품질] DB 전체 공고: {total:,}건")
    print(f"[품질] requirements 빈 공고: {empty_requirements:,}건 ({empty_ratio:.1f}%)")

    # 수집 카테고리별 공고 수
    category_rows = con.execute(
        """
        SELECT category_name, COUNT(*)
        FROM jobs
        GROUP BY category_name
        ORDER BY COUNT(*) DESC
        """
    ).fetchall()

    category_counts = {}

    for category_name, count in category_rows:
        category_counts[category_name] = count

    print(f"[품질] 수집 카테고리 분포: {category_counts}")

    # 최소 요구 경력 범위
    annual_range = con.execute(
        """
        SELECT MIN(annual_from), max(annual_from)
        FROM jobs
        WHERE annual_from IS NOT NULL
        """
    ).fetchone()

    annual_min, annual_max = annual_range

    print(f"[품질] annual_from 범위: {annual_min} ~ {annual_max}")


# =====================================================================
# 5. 전체 DB 적재 실행
# =====================================================================


def main():
    print("=" * 64)
    print("원티드 채용공고 CSV → SQLite 적재")
    print("=" * 64)

    # -------------------------------------------------------------
    # CSV 로드 + 중복 확인
    # -------------------------------------------------------------

    df, rows_in, duplicate_count = load_csv()

    print(
        f"CSV로드: {rows_in:,}행 (job_id 중복 {duplicate_count:,}건 제거 → {len(df):,}행)"
    )

    # -------------------------------------------------------------
    # DB 연결 + UPSERT
    # -------------------------------------------------------------

    con = connect()

    try:
        inserted, updated = upsert_jobs(con, df)

        # 현재 DB 전체 행 수
        total = con.execute(
            """
            SELECT COUNT(*)
            FROM jobs
            """
        ).fetchone()[0]

        print(f"적재: 신규 {inserted:,} / 갱신 {updated:,} → DB 총 {total:,}행")

        # ---------------------------------------------------------
        # build_log 기록
        # ---------------------------------------------------------

        save_build_log(con, rows_in, inserted, updated)

        # ---------------------------------------------------------
        # 품질 확인
        # ---------------------------------------------------------

        quality_check(con)

    finally:
        con.close()

    print()
    print(f"DB 저장 완료: {DB_PATH}")


if __name__ == "__main__":
    main()


# ================================================================
# 원티드 채용공고 CSV → SQLite 적재
# ================================================================
# CSV로드: 1,273행 (job_id 중복 0건 제거 → 1,273행)
# 적재: 신규 1,273 / 갱신 0 → DB 총 1,273행

# [품질] DB 전체 공고: 1,273건
# [품질] requirements 빈 공고: 0건 (0.0%)
# [품질] 수집 카테고리 분포: {'백엔드개발자': 371, '프론트엔드개발자': 332, '데이터엔지니어': 316, '데이터사이언티스트': 139, '데이터분석가': 115}
# [품질] annual_from 범위: 0 ~ 20

# DB 저장 완료: C:\Users\swrkd\Desktop\job-posting-tech-analysis\data\jobs.db


# 재실행 이후에도 DB 총 개수가 1,273행 인 것을 확인


# =====================================================================

# wanted_jobs.csv를 불러와 SQLite jobs.db에 적재함
# DB 저장 전 필수 컬럼을 확인함
# job_id의 결측을 제거하고 job_id 기준으로 중복을 제거함

# db.py의 connect()로 DB에 연결하고 upsert_jobs로 데이터를 적재
# job_id를 PRIMARY KEY로 사용해 신규 공고 추가, 기존 공고 갱신
# 동일 데이터를 다시 적재해도 DB 전체 행 수가 증가하지 않는다는 것을 확인함

# build_log에 실행 시각, 입력 행 수, 신규/갱신 건수를 기록함

# 적재 후 DB 전체 공고 수, requirements 결측 비율, 카테고리별 공고 수, annual_from 범위로 데이터 확인
