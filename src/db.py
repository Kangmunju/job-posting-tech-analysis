from pathlib import Path
import sqlite3

import pandas as pd


# =====================================================================
# 1. DB 경로
# =====================================================================

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "jobs.db"


# =====================================================================
# 2. jobs 테이블에 저장할 컬럼
# =====================================================================

# 원티드에서 데이터를 수집할 때 사용한 카테고리
# classify.py에서 공고 제목을 기준으로 직무를 재분류할 것
JOB_COLS = [
    "job_id",  # 공고 고유 ID
    "category_id",  # 원티드 직무 카테고리(수집용)
    "category_name",  # 직무 카테고리 이름(수집용)
    "position",  # 실제 채용공고 제목
    "company",  # 회사명
    "industry",  # 업종
    "annual_from",  # 최소 요구 경력
    "annual_to",  # 최대 요구 경력
    "requirements",  # 자격 요건
    "main_tasks",  # 주요 업무
    "preferred",  # 우대사항
    "intro",  # 회사/채용 소개
    "benefits",  # 복지 및 혜택
    "skill_tags",  # 원티드에서 제공하는 기술 태그
    "collected_at",  # 데이터 수집 시각
]


# =====================================================================
# 3. SQLite 테이블 구조
# =====================================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id INTEGER PRIMARY KEY,
    category_id INTEGER,
    category_name TEXT,
    position TEXT,
    company TEXT,
    industry TEXT,
    annual_from INTEGER,
    annual_to INTEGER,
    requirements TEXT,
    main_tasks TEXT,
    preferred TEXT,
    intro TEXT,
    benefits TEXT,
    skill_tags TEXT,
    collected_at TEXT
);

CREATE INDEX IF NOT EXISTS ix_jobs_cat
ON jobs (category_id);

CREATE TABLE IF NOT EXISTS build_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT,
    rows_in INTEGER,
    rows_inserted INTEGER,
    rows_updated INTEGER,
    note TEXT
);
"""


# =====================================================================
# 4. DB 연결 및 테이블 생성
# =====================================================================


def connect():
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    con.commit()

    return con


# =====================================================================
# 5. 채용공고 UPSERT
# =====================================================================


# job_id 기준 UPSERT. (신규 insert 수, 갱신 update 수) 반환
def upsert_jobs(con, df) -> tuple[int, int]:

    df = df.reindex(columns=JOB_COLS)

    # 저장하려는 공고 ID들 뽑기
    ids = [int(x) for x in df["job_id"].tolist()]

    existing = set()

    # 이번에 저장할 job_id 중 DB에 이미 들어 있는 ID 찾기
    if ids:
        qmarks = ",".join("?" * len(ids))

        # 기존 job_id 확인
        existing = {
            row[0]
            for row in con.execute(
                f"""
                SELECT job_id
                FROM jobs
                WHERE job_id IN ({qmarks})
                """,
                ids,
            ).fetchall()
        }

    sql = (
        # 그냥 INSERT만 사용하면 이미 존재하는 job_id가 들어왔을 때 충돌 발생할 가능성 있음
        # 이미 존재하는 job_id가 있는 경우 기존 행을 새로운 데이터로 교체
        f"INSERT OR REPLACE INTO jobs "
        f"({','.join(JOB_COLS)}) "
        f"VALUES ({','.join('?' * len(JOB_COLS))})"
    )

    con.executemany(
        sql,
        df.where(
            pd.notna(df),
            None,
        ).itertuples(
            index=False,
            name=None,
        ),
    )

    con.commit()

    updated = sum(1 for job_id in ids if job_id in existing)

    inserted = len(ids) - updated

    return inserted, updated


# =====================================================================

# connect()에서 jobs.db에 연결
# SCHEMA를 실행해 jobs, build_log 테이블과 인덱스를 생성함

# DB 저장 컬럼 통일
# JOB_COLS에 jobs 테이블에 저장할 15개 컬럼을 정의함
# reindex(colums=JOB_COLS)로 DataFrame의 컬럼과 순서를 맞춤

# 신규/갱신 공고를 구분하기 위해 실제 저장 전에 조회하도록 설계함
# 새로 들어온 jobs_id를 ids에 저장
# DB에 이미 존재하는 job_id를 조회해 existing 집합에 저장

# INSERT OR REPLACE를 사용해 새로운 job_id는 추가, 기존 것은 새로운 내용으로 교체

# DataFrame의 NaN을 None으로 바꿔 SQLite의 NULL로 저장함

# existing에 있던 job_id 개수 = updated
# 전체 ids 개수 - updated = inserted
# 최종적으로 (inserted, updated)를 반환하도록 작성함
