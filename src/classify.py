# 채용공고 제목이 특정 직무 표현을 포함하는지 찾는 데 사용함
import re


# =====================================================================
# 1. 직무 분류 규칙
# =====================================================================

# (직무 라벨, 표시 이름, 제목 매칭 정규식)
#
# 위에서부터 순서대로 검사하고 처음 일치한 직무로 확정함
# 구체적인 직무를 먼저 검사하고 범위가 넓은 백엔드는 마지막에 검사함

# 하나의 규칙이 3개짜리 튜플(문자열 + 문자열 + 정규식)
# 그러한 튜플이 여러 개 들어있는 리스트 형태로 묶어줌
# 분류할 때 사용할 기준표를 미리 만들어 두었음
RULES: list[tuple[str, str, re.Pattern]] = [
    # -----------------------------------------------------------------
    # 데이터 엔지니어
    # -----------------------------------------------------------------
    (
        "data_engineer",
        "데이터 엔지니어",
        re.compile(
            r"(데이터\s*엔지니어|data\s*engineer|"
            r"데이터\s*플랫폼|data\s*platform|"
            r"빅데이터\s*엔지니어|데이터\s*인프라)",
            re.I,
        ),
    ),
    # -----------------------------------------------------------------
    # 데이터 사이언티스트 / ML / AI
    # -----------------------------------------------------------------
    (
        "data_scientist",
        "데이터 사이언티스트·ML",
        re.compile(
            r"(데이터\s*사이언|data\s*scien|"
            r"머신\s*러닝|machine\s*learning|"
            r"\bml\s*engineer|ml\s*엔지니어|"
            r"딥러닝|deep\s*learning|"
            r"\bai\s*engineer|ai\s*엔지니어|"
            r"research\s*scientist|llm)",
            re.I,
        ),
    ),
    # -----------------------------------------------------------------
    # 데이터 분석가
    # -----------------------------------------------------------------
    (
        "data_analyst",
        "데이터 분석가",
        re.compile(
            r"(데이터\s*분석|data\s*analy|"
            r"비즈니스\s*분석|business\s*analy|"
            r"\bba\b|analytics\s*engineer|"
            r"프로덕트\s*분석|product\s*analy|"
            r"그로스\s*분석|바이\s*애널)",
            re.I,
        ),
    ),
    # -----------------------------------------------------------------
    # 프론트엔드
    # -----------------------------------------------------------------
    (
        "frontend",
        "프론트엔드 개발자",
        re.compile(
            r"(프론트\s*엔드|front\s*end|frontend|"
            r"퍼블리셔|웹\s*퍼블|"
            r"\bui\s*개발|react\s*개발|vue\s*개발|"
            r"웹\s*개발자|web\s*(개발|front))",
            re.I,
        ),
    ),
    # -----------------------------------------------------------------
    # 백엔드
    # -----------------------------------------------------------------
    (
        "backend",
        "백엔드 개발자",
        re.compile(
            r"(백\s*엔드|back\s*end|backend|"
            r"서버\s*개발|server\s*(dev|engineer)|"
            r"api\s*개발|플랫폼\s*개발자|"
            r"java\s*개발|python\s*개발|node\s*개발|"
            r"\bgo\s*개발|spring\s*개발|"
            r"풀\s*스택|full\s*stack|"
            r"devops|데브옵스|"
            r"소프트웨어\s*엔지니어|software\s*engineer|"
            r"앱\s*개발|웹.?앱|"
            r"인프라\s*엔지니어|클라우드\s*엔지니어|"
            r"플랫폼\s*엔지니어|시스템\s*엔지니어)",
            re.I,
        ),
    ),
]


# =====================================================================
# 2. 공고 제목을 직무로 분류
# =====================================================================


# 공고 제목 하나를 받아서 어떤 직무인지 반환하는 함수
def classify(position: str) -> str:
    # 제목이 없으면 분류할 수 없으므로 other
    if not position:
        return "other"

    # 문자열이 아닌 값이 들어오는 경우 방어
    if not isinstance(position, str):
        return "other"

    # Front-End / Back_End / Full/Stack처럼
    # 구분자가 들어간 표현을 공백 형태로 통일
    norm = re.sub(r"[-_/]", " ", position)

    # 위에서부터 규칙을 검사하고
    # 처음 일치한 직무를 바로 반환
    for label, _name, pattern in RULES:
        if pattern.search(norm):
            return label

    # 5개 직무 어디에도 해당하지 않으면 other
    return "other"


# =====================================================================
# 3. 직무 표시 이름
# =====================================================================


def role_name(label: str) -> str:
    for rule_label, name, _pattern in RULES:
        if rule_label == label:
            return name

    return "기타"


# =====================================================================
# 4. 자체 테스트
# =====================================================================


def main():
    tests = [
        (
            "[쿠팡] 데이터 분석가 (CRM FP&A)",
            "data_analyst",
        ),
        (
            "Data Engineer (Growth)",
            "data_engineer",
        ),
        (
            "LLM 트레이닝 엔지니어(데이터 사이언티스트)",
            "data_scientist",
        ),
        (
            "[그라운드] 백엔드 개발자 (Backend Developer)",
            "backend",
        ),
        (
            "프론트엔드 엔지니어 (3년 이상/부산)",
            "frontend",
        ),
        (
            "재무회계담당자 5년이상 팀장급",
            "other",
        ),
        (
            "AI Engineer (Edge AI 최적화)",
            "data_scientist",
        ),
        (
            "Data Analytics Engineer",
            "data_analyst",
        ),
    ]

    print("=" * 64)
    print("직무 재분류 테스트")
    print("=" * 64)

    passed = 0

    for position, expected in tests:
        result = classify(position)

        if result == expected:
            state = "PASS"
            passed += 1
        else:
            state = "FAIL"

        print(f"{state} | {result} <- {position} (기대: {expected})")

    print()
    print(f"테스트 결과: {passed}/{len(tests)} 통과")

    if passed != len(tests):
        raise RuntimeError("직무 재분류 자체 테스트에 실패했습니다.")

    # -------------------------------------------------------------
    # 실제 DB 전체 직무 분포 확인
    # -------------------------------------------------------------

    from pathlib import Path
    import sqlite3

    root = Path(__file__).resolve().parents[1]
    db_path = root / "data" / "jobs.db"

    if not db_path.exists():
        print()
        print(f"[분포 확인 생략] DB를 찾을 수 없습니다: {db_path}")
        return

    con = sqlite3.connect(db_path)

    try:
        rows = con.execute(
            """
            SELECT position
            FROM jobs
            """
        ).fetchall()

    finally:
        con.close()

    counts = {
        "data_analyst": 0,
        "data_engineer": 0,
        "data_scientist": 0,
        "backend": 0,
        "frontend": 0,
        "other": 0,
    }

    for row in rows:
        position = row[0]
        role = classify(position)
        counts[role] += 1

    analysis_total = (
        counts["data_analyst"]
        + counts["data_engineer"]
        + counts["data_scientist"]
        + counts["backend"]
        + counts["frontend"]
    )

    total = len(rows)

    print()
    print("=" * 40)
    print("실제 DB 직무 재분류 결과")
    print("=" * 40)
    print(f"{'데이터 분석가':<18} {counts['data_analyst']:>6,}건")
    print(f"{'데이터 엔지니어':<18} {counts['data_engineer']:>6,}건")
    print(f"{'데이터 사이언티스트':<18} {counts['data_scientist']:>6,}건")
    print(f"{'백엔드':<18} {counts['backend']:>6,}건")
    print(f"{'프론트엔드':<18} {counts['frontend']:>6,}건")
    print(f"{'other':<18} {counts['other']:>6,}건")
    print("-" * 40)
    print(f"{'분석 대상':<18} {analysis_total:>6,}건")
    print(f"{'전체':<18} {total:>6,}건")
    print("=" * 40)


if __name__ == "__main__":
    main()


# ================================================================
# 직무 재분류 테스트
# ================================================================
# PASS | data_analyst <- [쿠팡] 데이터 분석가 (CRM FP&A) (기대: data_analyst)
# PASS | data_engineer <- Data Engineer (Growth) (기대: data_engineer)
# PASS | data_scientist <- LLM 트레이닝 엔지니어(데이터 사이언티스트) (기대: data_scientist)
# PASS | backend <- [그라운드] 백엔드 개발자 (Backend Developer) (기대: backend)
# PASS | frontend <- 프론트엔드 엔지니어 (3년 이상/부산) (기대: frontend)
# PASS | other <- 재무회계담당자 5년이상 팀장급 (기대: other)
# PASS | data_scientist <- AI Engineer (Edge AI 최적화) (기대: data_scientist)
# PASS | data_analyst <- Data Analytics Engineer (기대: data_analyst)

# 테스트 결과: 8/8 통과

# ========================================
# 실제 DB 직무 재분류 결과
# ========================================
# 데이터 분석가                71건
# 데이터 엔지니어               94건
# 데이터 사이언티스트            122건
# 백엔드                   287건
# 프론트엔드                 150건
# other                 549건
# ----------------------------------------
# 분석 대상                 724건
# 전체                  1,273건
# ========================================


# =====================================================================

# 원티드 수집 카테고리를 그대로 사용하지 않고 공고 제목(position)을 기준으로 직무 재분류
# 데이터 엔지니어 → 데이터 사이언티스트 → 데이터 분석가 → 프론트엔드 → 백엔드 순으로 구현
# 구체적 직무를 먼저 검사하고 범위가 넓은 백엔드는 마지막에 검사함

# 정규식을 이용해 수많은 직무명 표현을 매칭하였음
# 기타 특수문자들은 공백으로 변환해 표기를 통일함
# 처음 일치한 직무의 label을 반환하고 5개 직무에 해당하지 않으면 other로 분류함
