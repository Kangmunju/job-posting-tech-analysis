# re : 파이썬에 기본 내장된 정규표현식 모듈
#      정교한 조건으로 문자열을 찾아야하므로 사용함
import re


# =====================================================================
# 1. 스킬 사전
# =====================================================================

# 표준 스킬명 : 채용공고에서 실제로 나타날 수 있는 별칭
#
# 같은 기술이 서로 다른 표기로 작성되어도 하나의 표준 스킬명으로 통일
# ex) Python / python / 파이썬 → Python
#
# 짧고 일반적인 문자열은 오탐을 줄이기 위해 별칭을 제한하거나 직접 정규식을 사용

SKILLS: dict[str, list[str]] = {
    # -----------------------------------------------------------------
    # 프로그래밍 언어
    # -----------------------------------------------------------------
    "Python": [
        "python",
        "파이썬",
    ],
    "SQL": [
        "sql",
    ],
    "Java": [
        "java",
        "자바",
    ],
    "JavaScript": [
        "javascript",
        "자바스크립트",
    ],
    "TypeScript": [
        "typescript",
        "타입스크립트",
    ],
    # 단독 go는 일반 영어 표현과 충돌할 가능성이 높아 제외
    "Go": [
        "golang",
        "go 언어",
        "go lang",
    ],
    # R&D의 R을 R 언어로 잘못 잡지 않도록 방어
    # 대문자 R만 인정하고, R을·R과처럼 한글 조사가 붙는 경우도 잡도록 영문/숫자 경계를 직접 지정
    "R": [
        r"(?<![A-Za-z0-9])R(?![A-Za-z0-9])(?!&D)",
    ],
    "C++": [
        r"c\+\+",
    ],
    "C#": [
        "c#",
        "c sharp",
    ],
    # C++ / C#의 C를 C 언어로 중복 인식하지 않도록 방어
    # 시리즈 C 투자, C-level, 목록 번호(C.)가 C 언어로 잡히지 않도록 C/C++, C, Python, C 언어처럼
    # 다른 기술과 나열되거나 C 언어로 쓰인 문맥만 인정함
    "C": [
        # C/C++, C, C++ 처럼 C 뒤에 구분 기호가 오는 경우
        r"(?<!시리즈 )(?<![A-Za-z0-9])C(?![A-Za-z0-9+#])(?=\s*[/,·])",
        # Java, C, Python 처럼 C 앞에 구분 기호가 오는 경우
        r"(?:(?<=[,·])|(?<=[,·]\s))C(?![A-Za-z0-9+#\-])(?!\s*레벨)",
        # C 언어, C언어
        r"(?<![A-Za-z0-9])C\s*언어",
    ],
    "Kotlin": [
        "kotlin",
        "코틀린",
    ],
    "Swift": [
        "swift",
        "스위프트",
    ],
    "Scala": [
        "scala",
        "스칼라",
    ],
    "PHP": [
        "php",
    ],
    "Ruby": [
        "ruby",
        "루비",
    ],
    # -----------------------------------------------------------------
    # 데이터 분석 / 머신러닝 라이브러리
    # -----------------------------------------------------------------
    "Pandas": [
        "pandas",
        "판다스",
    ],
    "NumPy": [
        "numpy",
        "넘파이",
    ],
    "SciPy": [
        "scipy",
    ],
    "Scikit-learn": [
        "scikit-learn",
        "scikit learn",
        "sklearn",
        "사이킷런",
    ],
    "PyTorch": [
        "pytorch",
        "파이토치",
        "torch",
    ],
    "TensorFlow": [
        "tensorflow",
        "텐서플로",
        "텐서플로우",
    ],
    "Keras": [
        "keras",
        "케라스",
    ],
    "OpenCV": [
        "opencv",
    ],
    "Hugging Face": [
        "hugging face",
        "huggingface",
        "허깅페이스",
    ],
    # -----------------------------------------------------------------
    # AI / 머신러닝
    # -----------------------------------------------------------------
    "Machine Learning": [
        "machine learning",
        "머신러닝",
        "기계학습",
    ],
    "Deep Learning": [
        "deep learning",
        "딥러닝",
        "심층학습",
    ],
    "NLP": [
        "nlp",
        "natural language processing",
        "자연어처리",
        "자연어 처리",
    ],
    "Computer Vision": [
        "computer vision",
        "컴퓨터비전",
        "컴퓨터 비전",
    ],
    "LLM": [
        "llm",
        "large language model",
        "large language models",
        "대규모 언어 모델",
    ],
    "RAG": [
        "rag",
        "retrieval augmented",
        "retrieval-augmented",
    ],
    "Recommendation": [
        "recommendation system",
        "recommender system",
        "추천 시스템",
        "추천시스템",
    ],
    # -----------------------------------------------------------------
    # 데이터 처리 / 빅데이터
    # -----------------------------------------------------------------
    "Spark": [
        "spark",
        "스파크",
        "pyspark",
    ],
    "Hadoop": [
        "hadoop",
        "하둡",
    ],
    "Kafka": [
        "kafka",
        "카프카",
    ],
    "Airflow": [
        "airflow",
        "에어플로우",
        "에어플로",
    ],
    "Flink": [
        "flink",
    ],
    "dbt": [
        "dbt",
    ],
    "ETL": [
        "etl",
        "elt",
    ],
    # -----------------------------------------------------------------
    # 데이터베이스 / 데이터웨어하우스
    # -----------------------------------------------------------------
    "MySQL": [
        "mysql",
    ],
    "PostgreSQL": [
        "postgresql",
        "postgres",
    ],
    "Oracle": [
        "oracle",
        "오라클",
    ],
    "MongoDB": [
        "mongodb",
        "mongo db",
    ],
    "Redis": [
        "redis",
        "레디스",
    ],
    "Elasticsearch": [
        "elasticsearch",
        "elastic search",
        "엘라스틱서치",
    ],
    "DynamoDB": [
        "dynamodb",
        "dynamo db",
    ],
    "BigQuery": [
        "bigquery",
        "big query",
        "빅쿼리",
    ],
    "Snowflake": [
        "snowflake",
        "스노우플레이크",
    ],
    "Redshift": [
        "redshift",
    ],
    # -----------------------------------------------------------------
    # 클라우드 / 인프라 / DevOps
    # -----------------------------------------------------------------
    "AWS": [
        "aws",
        "amazon web services",
        "아마존웹서비스",
        "아마존 웹 서비스",
    ],
    "GCP": [
        "gcp",
        "google cloud platform",
        "google cloud",
        "구글 클라우드",
    ],
    "Azure": [
        "azure",
        "애저",
    ],
    "Docker": [
        "docker",
        "도커",
    ],
    "Kubernetes": [
        "kubernetes",
        "쿠버네티스",
        "k8s",
    ],
    "Terraform": [
        "terraform",
        "테라폼",
    ],
    "Jenkins": [
        "jenkins",
        "젠킨스",
    ],
    "GitHub Actions": [
        "github actions",
        "github action",
    ],
    "CI/CD": [
        "ci/cd",
        "ci cd",
        "cicd",
    ],
    "Linux": [
        "linux",
        "리눅스",
    ],
    "Nginx": [
        "nginx",
        "엔진엑스",
    ],
    # -----------------------------------------------------------------
    # 백엔드 / 서버
    # -----------------------------------------------------------------
    "Spring": [
        "spring",
        "spring framework",
        "스프링",
    ],
    "Spring Boot": [
        "spring boot",
        "springboot",
        "스프링부트",
        "스프링 부트",
    ],
    "Django": [
        "django",
        "장고",
    ],
    "Flask": [
        "flask",
        "플라스크",
    ],
    "FastAPI": [
        "fastapi",
        "fast api",
    ],
    "Node.js": [
        "node.js",
        "nodejs",
        "node js",
    ],
    "Express": [
        "express.js",
        "expressjs",
        "express js",
    ],
    "NestJS": [
        "nestjs",
        "nest.js",
        "nest js",
    ],
    "REST API": [
        "rest api",
        "restful api",
        "restful",
    ],
    "GraphQL": [
        "graphql",
        "graph ql",
    ],
    # -----------------------------------------------------------------
    # 프론트엔드
    # -----------------------------------------------------------------
    "HTML": [
        "html",
    ],
    "CSS": [
        "css",
    ],
    "React": [
        "react",
        "react.js",
        "reactjs",
        "리액트",
    ],
    "Vue.js": [
        "vue.js",
        "vuejs",
        "vue js",
        "vue",
    ],
    "Angular": [
        "angular",
        "앵귤러",
    ],
    "Next.js": [
        "next.js",
        "nextjs",
        "next js",
    ],
    "Svelte": [
        "svelte",
    ],
    "Redux": [
        "redux",
        "리덕스",
    ],
    # -----------------------------------------------------------------
    # 분석 / BI
    # -----------------------------------------------------------------
    "Tableau": [
        "tableau",
        "태블로",
    ],
    "Power BI": [
        "power bi",
        "powerbi",
        "파워비아이",
    ],
    "Looker": [
        "looker",
    ],
    "Excel": [
        "excel",
        "엑셀",
    ],
    "A/B Test": [
        "a/b test",
        "a/b testing",
        "a/b 테스트",
        "ab test",
        "ab테스트",
    ],
    # -----------------------------------------------------------------
    # 개발 / 협업 도구
    # -----------------------------------------------------------------
    "Git": [
        "git",
        "github",
        "gitlab",
        "깃허브",
        "깃랩",
    ],
    "Jira": [
        "jira",
        "지라",
    ],
    "Confluence": [
        "confluence",
        "컨플루언스",
    ],
    "Slack": [
        "slack",
        "슬랙",
    ],
    # -----------------------------------------------------------------
    # 모바일 / 기타 플랫폼
    # -----------------------------------------------------------------
    "Android": [
        "android",
        "안드로이드",
    ],
    "iOS": [
        "ios",
    ],
    "React Native": [
        "react native",
        "리액트 네이티브",
    ],
    "Flutter": [
        "flutter",
        "플러터",
    ],
}


# =====================================================================
# 2. 별칭 → 정규식 변환
# =====================================================================


# SKILLS 안에 적어둔 별칭 하나를 실제 검색에 사용할 정규식으로 바꿔주는 함수
def _compile(alias: str) -> re.Pattern:
    # 이미 직접 작성한 정규식 패턴이면 그대로 사용
    if alias.startswith(r"\b") or "(?" in alias or alias.startswith(r"\."):
        return re.compile(alias)

    # C++, C#, react.js처럼 특수문자 처리가 필요한 별칭
    if r"\+" in alias or alias.endswith("#") or r"\." in alias:
        return re.compile(alias, re.IGNORECASE)

    # 일반 별칭은 정규식에서 안전하게 사용할 수 있도록 변환
    esc = re.escape(alias)

    # 영문/숫자로 시작하면 앞에 영숫자가 붙지 못하도록 경계 설정
    if alias[0].isascii() and alias[0].isalnum():
        left = r"(?<![A-Za-z0-9])"
    elif "가" <= alias[0] <= "힣":
        # 한글로 시작하면 앞에 한글이 붙지 못하도록 경계 설정 (예: 리뷰, 웹뷰 안의 글자 오탐 방지)
        # 뒤에는 조사가 붙을 수 있으므로 경계를 두지 않음
        left = r"(?<![가-힣])"
    else:
        left = ""

    # 영문/숫자로 끝나면 뒤에 영숫자가 붙지 못하도록 경계 설정
    if alias[-1].isascii() and alias[-1].isalnum():
        right = r"(?![A-Za-z0-9])"
    else:
        right = ""

    return re.compile(
        left + esc + right,
        re.IGNORECASE,
    )


# 하위 기술 : 상위 기술
#
# 하위 기술의 이름 안에 상위 기술의 이름이 들어 있어서 둘이 함께 잡히는 경우를 정리하기 위한 표
# ex) Spring Boot 안의 Spring, React Native 안의 React, GitHub Actions 안의 GitHub(Git)
# 하위 기술이 차지한 글자는 상위 기술을 찾을 때만 가리고, 상위 기술이 따로 언급되면 그대로 인정함

SUB_SKILLS: dict[str, str] = {
    "Spring Boot": "Spring",
    "React Native": "React",
    "GitHub Actions": "Git",
}


# =====================================================================
# 3. 모든 스킬 패턴 미리 컴파일
# =====================================================================

_COMPILED: list[tuple[str, re.Pattern]] = []

for canon, aliases in SKILLS.items():
    for alias in aliases:
        _COMPILED.append(
            (
                canon,
                _compile(alias),
            )
        )


# =====================================================================
# 4. 텍스트에서 스킬 추출
# =====================================================================


def extract_skills(text: str) -> set[str]:
    # None, 빈 문자열 등은 스킬이 없는 것으로 처리
    if not text:
        return set()

    # pandas 등의 결측값이 넘어오는 경우까지 방어
    if not isinstance(text, str):
        return set()

    found = set()

    # 상위 기술을 찾을 때 사용할 텍스트 (상위 기술 이름 : 하위 기술이 차지한 글자를 공백으로 가린 텍스트)
    masked_texts = {}

    # 1단계: 하위 기술을 먼저 찾고, 그 글자를 해당 상위 기술용 텍스트에서 가림
    for canon, pattern in _COMPILED:
        if canon not in SUB_SKILLS:
            continue

        parent = SUB_SKILLS[canon]

        for match in pattern.finditer(text):
            found.add(canon)

            base_text = masked_texts.get(parent, text)
            blank = " " * (match.end() - match.start())
            masked_texts[parent] = base_text[: match.start()] + blank + base_text[match.end() :]

    # 2단계: 나머지 기술을 찾음 (상위 기술은 가려진 텍스트에서 찾음)
    for canon, pattern in _COMPILED:
        if canon in SUB_SKILLS:
            continue

        target_text = masked_texts.get(canon, text)

        if pattern.search(target_text):
            found.add(canon)

    return found


# =====================================================================
# 5. 스킬 사전 정보
# =====================================================================


def skill_count() -> int:
    return len(SKILLS)


def alias_count() -> int:
    return sum(len(aliases) for aliases in SKILLS.values())


def all_skill_names() -> list[str]:
    return list(SKILLS.keys())


# =====================================================================
# 6. 자체 테스트
# =====================================================================


def main():
    sample = (
        "자격요건: Python/파이썬, SQL 능숙. "
        "AWS, k8s(쿠버네티스) 경험 우대. "
        "React.js, node.js, PostgreSQL(postgres). "
        "C++ 및 R&D 경험. "
        "LLM/RAG 관심."
    )

    found = extract_skills(sample)

    print("=" * 64)
    print("스킬 사전 테스트")
    print("=" * 64)

    print(f"입력: {sample}")
    print()
    print(f"추출: {sorted(found)}")
    print()
    print(f"사전 규모: 표준스킬 {skill_count()}개, 별칭패턴 {alias_count()}개")

    # -------------------------------------------------------------
    # 핵심 오탐 / 정규화 테스트
    # -------------------------------------------------------------

    tests = [
        ("Python/파이썬", {"Python"}),
        ("k8s 쿠버네티스", {"Kubernetes"}),
        ("C++", {"C++"}),
        ("R&D", set()),
        ("React.js", {"React"}),
        ("node.js", {"Node.js"}),
        ("PostgreSQL postgres", {"PostgreSQL"}),
        ("LLM RAG", {"LLM", "RAG"}),
        ("Vue.js", {"Vue.js"}),
        ("vue 3, Vuex", {"Vue.js"}),
        ("코드 리뷰, 웹뷰, 인터뷰, 어트리뷰션", set()),
        ("그루비 데이터 분석", set()),
        ("루비 온 레일즈", {"Ruby"}),
        ("C/C++, Python", {"C", "C++", "Python"}),
        ("Java, C, Python 경험", {"Java", "C", "Python"}),
        ("C 언어 개발", {"C"}),
        ("C-level 임원과 소통", set()),
        ("CEO·C레벨 리더십", set()),
        ("시리즈 C 투자 유치", set()),
        ("C. 아래 중 5가지 이상", set()),
        ("Spring Boot", {"Spring Boot"}),
        ("Spring Boot, Spring Security, Spring", {"Spring Boot", "Spring"}),
        ("React Native", {"React Native"}),
        ("React Native와 React 경험", {"React Native", "React"}),
        ("GitHub Actions", {"GitHub Actions"}),
        ("GitHub Actions, Git", {"GitHub Actions", "Git"}),
        ("ETL/ELT 파이프라인", {"ETL"}),
        ("ETL을 구축", {"ETL"}),
        ("Git, K8S", {"Git", "Kubernetes"}),
        ("Python 또는 R을 활용한 분석", {"Python", "R"}),
        ("R&D 경험", set()),
        ("gitlab", {"Git"}),
    ]

    print()
    print("[자체 테스트]")

    passed = 0

    for text, expected in tests:
        result = extract_skills(text)

        if result == expected:
            state = "PASS"
            passed += 1
        else:
            state = "FAIL"

        print(f"{state} | {text} → {sorted(result)} (기대: {sorted(expected)})")

    print()
    print(f"테스트 결과: {passed}/{len(tests)} 통과")

    if passed != len(tests):
        raise RuntimeError("스킬 사전 자체 테스트에 실패했습니다.")


if __name__ == "__main__":
    main()


# =====================================================================
# [구현 핵심]
# =====================================================================

# 채용공고 텍스트에서 기술명을 찾아 표준 스킬명으로 통일함
# 같은 기술의 영문, 한글, 약어 등을 하나의 스킬로 묶어 추출함

# 영문 기술명은 문자열 경계를 적용해 다른 단어에 포함된 경우의 오탐을 방지하였음
# 한글 기술명은 조사가 붙을 수 있어 경계를 적용하지 않고 작성함

# R, C, Go 등 짧은 기술명은 별도 정규식/별칭 제한으로 오탐을 방지하였음
# extract_skills()는 공고별 기술 등장 여부만 확인하도록 set으로 반환

# 이후 스킬 매트릭스 생성을 위해 전체 표준 스킬명 목록을 반환하도록 all_skill_names() 추가함


# =====================================================================
# [수정 사항]
# =====================================================================

# Vue.js 별칭 "뷰"가 리뷰, 웹뷰, 인터뷰 같은 단어 안의 글자까지 Vue.js로 잡아 별칭에서 삭제함
# 한글로 시작하는 별칭은 앞에 한글이 붙어 있으면 매칭하지 않도록 앞쪽 경계를 추가함 (뒤쪽은 조사 때문에 열어 둠)
# 같은 경계로 그루비 안의 루비가 Ruby로 잡히던 오탐도 함께 사라짐
# 수정 전후를 전체 공고로 비교해 Vue.js 259건, Ruby 1건만 줄어든 것을 확인함

# Spring Boot, React Native, GitHub Actions처럼 이름 안에 상위 기술이 들어 있는 경우를 SUB_SKILLS 표로 정리함
# 하위 기술이 차지한 글자는 상위 기술을 찾을 때만 가리고, 상위 기술이 따로 언급되면 그대로 인정함
# (하위 기술이 잡히면 상위 기술을 통째로 빼면 React Native 공고 70건 중 React를 따로 요구한 59건이 사라지기 때문)

# C 언어는 시리즈 C 투자, C-level, 목록 번호(C.)가 잡히던 문제가 있어 C/C++, C, Python, C 언어처럼 나열되거나 C 언어로 쓰인 문맥만 인정함
# 수정 전후를 전체 공고로 비교해 C 34건 → 20건이 되었고, 사라진 14건은 모두 오탐이었음

# \b로 시작하는 정규식 별칭은 대소문자를 구분하고 한글 조사가 붙으면 놓쳐서 ETL이 0건으로 집계되던 문제를 발견함
# etl, elt, k8s, cicd, git은 일반 별칭으로 바꾸고 R은 영문/숫자 경계를 직접 지정해 대문자 표기와 한글 조사 표기도 인식함
# ETL 0건 → 80건, Git 180건 → 259건(GitHub Actions 단독 언급 제외), Kubernetes +13건, R +4건, CI/CD +1건

# 오탐·누락 케이스를 자체 테스트에 추가해 8개 → 32개로 늘려 모두 통과함
