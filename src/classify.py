# 채용공고 제목이 특정 직무 표현을 포함하는지 찾는 데 사용함
import re


# =====================================================================
# 1. 직무 분류 규칙
# =====================================================================

# (직무 라벨, 표시 이름, 제목 매칭 정규식)
#
# 위에서부터 순서대로 검사하고 처음 일치한 직무로 확정함
# 풀스택은 프론트엔드와 백엔드가 섞인 직무라서 가장 먼저 검사해 분석 대상에서 분리함
# 그 다음 구체적인 직무를 먼저 검사하고 범위가 넓은 백엔드는 마지막에 검사함

# 하나의 규칙이 3개짜리 튜플(문자열 + 문자열 + 정규식)
# 그러한 튜플이 여러 개 들어있는 리스트 형태로 묶어줌
# 분류할 때 사용할 기준표를 미리 만들어 두었음
RULES: list[tuple[str, str, re.Pattern]] = [
    # -----------------------------------------------------------------
    # 풀스택 (분석 대상 5개 직무에는 포함하지 않음)
    # -----------------------------------------------------------------
    (
        "fullstack",
        "풀스택 개발자",
        re.compile(
            r"(풀\s*스택|full\s*stack)",
            re.I,
        ),
    ),
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
            r"(프론트\s*(엔[드트]|개발|엔지니어)|front\s*end|frontend|"
            r"front\s*(개발|dev|engineer)|"
            r"(?<![A-Za-z])fe(?![A-Za-z])|"
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
            r"(?<![A-Za-z])be(?![A-Za-z])|"
            r"서버\s*개발|server\s*(dev|engineer)|"
            r"api\s*개발|플랫폼\s*개발자|"
            r"java\s*개발|python\s*개발|node\s*개발|"
            r"\bgo\s*개발|spring\s*개발|"
            r"devops|devsecops|데브옵스|"
            r"소프트웨어\s*엔지니어|software\s*engineer|"
            r"앱\s*개발|웹.?앱|"
            r"인프라\s*엔지니어|infrastructure\s*(engineer|엔지니어)|"
            r"클라우드\s*엔지니어|"
            r"플랫폼\s*엔지니어|platform\s*(engineer|엔지니어)|"
            r"시스템\s*엔지니어)",
            re.I,
        ),
    ),
    # -----------------------------------------------------------------
    # 데이터 사이언티스트 / ML / AI (보조 규칙)
    # -----------------------------------------------------------------
    # MLOps, AI 개발자, AI Agent·Research 엔지니어, Applied Scientist는
    # 제목에 프론트엔드·백엔드가 함께 있으면 그 직무가 우선이므로 가장 마지막에 검사함
    (
        "data_scientist",
        "데이터 사이언티스트·ML",
        re.compile(
            r"(mlops|ml\s*ops|"
            r"\bai(\s*[/·]\s*ml)?\s*(개발자|developer|engineer|엔지니어(?!링))|"
            r"ai\s*(research|agent)\s*(engineer|엔지니어|개발자)|ai\s*리서치|"
            r"applied\s*scientist|ai\s*scientist)",
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
        (
            "FE 개발자 3년 이상",
            "frontend",
        ),
        (
            "[인턴] BE Engineer (전환형)",
            "backend",
        ),
        (
            "Senior MLOps 엔지니어",
            "data_scientist",
        ),
        (
            "AI 개발자 팀원/팀장 (사원~과장)",
            "data_scientist",
        ),
        (
            "Applied Scientist (Agent)",
            "data_scientist",
        ),
        (
            "풀스택 개발자 (React / Node.js)",
            "fullstack",
        ),
        (
            "[팀 스케일업] AI 풀스택 개발자 (LLM 파이프라인)",
            "fullstack",
        ),
        (
            "주니어 프론트엔드 (풀스택 성장형) 개발자",
            "fullstack",
        ),
        (
            "AI·엔지니어링 총괄 (Head of AI & Engineering)",
            "other",
        ),
        (
            "AI Tutor - Arabic",
            "other",
        ),
        (
            "Frontend Engineer (MLOps, Vision AI Platform)",
            "frontend",
        ),
        (
            "AI FM 모델 개발 · MLOps 백엔드/플랫폼 엔지니어",
            "backend",
        ),
        (
            "프론트개발자(web, app)",
            "frontend",
        ),
        (
            "프론트 엔지니어",
            "frontend",
        ),
        (
            "Lucy Studio Front 개발자 (신입/주니어)",
            "frontend",
        ),
        (
            "프론트엔트 개발자",
            "frontend",
        ),
        (
            "Platform Engineer",
            "backend",
        ),
        (
            "Senior Infrastructure Engineer",
            "backend",
        ),
        (
            "DevSecOps 리드",
            "backend",
        ),
        (
            "[AI Work Agent] AI Research Engineer - Post-training",
            "data_scientist",
        ),
        (
            "사운드AI 리서치 엔지니어 (3년차 이상)",
            "data_scientist",
        ),
        (
            "AI Agent Engineer (5년이상)",
            "data_scientist",
        ),
        (
            "[SK inc.(AX)] AI Agent 엔지니어",
            "data_scientist",
        ),
        (
            "[SK inc.(AX)] AI Agent 개발자",
            "data_scientist",
        ),
        (
            "Front Office 운영 담당자",
            "other",
        ),
        (
            "프론트 오피스 운영 담당자",
            "other",
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
        "fullstack": 0,
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

    # 분석 대상 + 풀스택 + other가 전체와 같아야 함 (분류 누락·중복 방지)
    if analysis_total + counts["fullstack"] + counts["other"] != total:
        raise RuntimeError("직무별 분류 건수의 합이 전체 공고 수와 다릅니다.")

    print()
    print("=" * 40)
    print("실제 DB 직무 재분류 결과")
    print("=" * 40)
    print(f"{'데이터 분석가':<18} {counts['data_analyst']:>6,}건")
    print(f"{'데이터 엔지니어':<18} {counts['data_engineer']:>6,}건")
    print(f"{'데이터 사이언티스트':<18} {counts['data_scientist']:>6,}건")
    print(f"{'백엔드':<18} {counts['backend']:>6,}건")
    print(f"{'프론트엔드':<18} {counts['frontend']:>6,}건")
    print("-" * 40)
    print(f"{'분석 대상':<18} {analysis_total:>6,}건")
    print(f"{'풀스택(분석 제외)':<18} {counts['fullstack']:>6,}건")
    print(f"{'other(분석 제외)':<18} {counts['other']:>6,}건")
    print(f"{'전체':<18} {total:>6,}건")
    print("=" * 40)


if __name__ == "__main__":
    main()


# =====================================================================
# [구현 핵심]
# =====================================================================

# 원티드 수집 카테고리를 그대로 사용하지 않고 공고 제목(position)을 기준으로 직무 재분류
# 데이터 엔지니어 → 데이터 사이언티스트 → 데이터 분석가 → 프론트엔드 → 백엔드 순으로 구현
# 구체적 직무를 먼저 검사하고 범위가 넓은 백엔드는 마지막에 검사함

# 정규식을 이용해 수많은 직무명 표현을 매칭하였음
# 기타 특수문자들은 공백으로 변환해 표기를 통일함
# 처음 일치한 직무의 label을 반환하고 5개 직무에 해당하지 않으면 other로 분류함

# 제목에 풀스택이 있으면 프론트엔드가 함께 있어도(예: 프론트엔드 (풀스택 성장형)) 풀스택으로 분류함
# 성장형 포지션은 결국 풀스택이 되고, 예외 규칙을 두면 규칙이 복잡해져 모순이 생길 수 있어 단순한 기준을 유지함


# =====================================================================
# [수정 사항]
# =====================================================================

# 풀스택은 프론트엔드·백엔드 기술이 섞이므로 fullstack 라벨을 새로 두고 가장 먼저 검사해 분석 대상에서 제외함
# FE/BE 약어, MLOps, AI 개발자, Applied Scientist 표기가 other로 빠지던 문제를 규칙 추가로 해결함
# MLOps·AI 개발자·Applied Scientist는 제목에 프론트엔드·백엔드가 함께 있으면 그 직무를 우선하도록 마지막 보조 규칙으로 둠
# 실제 DB 집계에 fullstack을 추가하고, 분류 건수의 합이 전체와 다르면 에러를 내도록 검증을 추가함

# other 521건 중 무작위 50건을 직접 라벨링해 분석 대상이었어야 하는데 빠진 공고 비율을 확인함 (12건, 24%)
# 프론트개발자·프론트 엔지니어·Front 개발자·프론트엔트(오타), Platform·Infrastructure Engineer, DevSecOps,
# AI Research·Agent Engineer(개발자), AI 리서치 표기를 규칙에 추가함
# 추가 후 other를 다시 무작위 50건 뽑아 확인하니 규칙으로 잡을 수 있는 누락은 3건(6%)으로 줄어듦
# 데이터 아키텍트, 모바일 엔지니어, AI 애플리케이션 개발자처럼 직무 범위가 애매한 표기는 오탐을 막기 위해 추가하지 않음

# 자체 테스트 8개 → 34개로 늘려 모두 통과함
