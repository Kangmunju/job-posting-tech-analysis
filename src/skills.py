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
    "R": [
        r"\bR\b(?!&D)",
    ],
    "C++": [
        r"c\+\+",
    ],
    "C#": [
        "c#",
        "c sharp",
    ],
    # C++ / C#의 C를 C 언어로 중복 인식하지 않도록 방어
    "C": [
        r"\bC\b(?!\+|#)",
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
        r"\betl\b",
        r"\belt\b",
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
        r"\bk8s\b",
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
        r"\bcicd\b",
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
        "뷰",
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
        r"\bgit\b",
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

    for canon, pattern in _COMPILED:
        if pattern.search(text):
            found.add(canon)

    return found


# =====================================================================
# 5. 스킬 사전 정보
# =====================================================================


def skill_count() -> int:
    return len(SKILLS)


def alias_count() -> int:
    return sum(len(aliases) for aliases in SKILLS.values())


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


# ================================================================
# 스킬 사전 테스트
# ================================================================
# 입력: 자격요건: Python/파이썬, SQL 능숙. AWS, k8s(쿠버네티스) 경험 우대. React.js, node.js, PostgreSQL(postgres). C++ 및 R&D 경험. LLM/RAG 관심.

# 추출: ['AWS', 'C++', 'Kubernetes', 'LLM', 'Node.js', 'PostgreSQL', 'Python', 'RAG', 'React', 'SQL']

# 사전 규모: 표준스킬 90개, 별칭패턴 210개

# [자체 테스트]
# PASS | Python/파이썬 → ['Python'] (기대: ['Python'])
# PASS | k8s 쿠버네티스 → ['Kubernetes'] (기대: ['Kubernetes'])
# PASS | C++ → ['C++'] (기대: ['C++'])
# PASS | R&D → [] (기대: [])
# PASS | React.js → ['React'] (기대: ['React'])
# PASS | node.js → ['Node.js'] (기대: ['Node.js'])
# PASS | PostgreSQL postgres → ['PostgreSQL'] (기대: ['PostgreSQL'])
# PASS | LLM RAG → ['LLM', 'RAG'] (기대: ['LLM', 'RAG'])

# 테스트 결과: 8/8 통과


# =====================================================================

# 채용공고 텍스트에서 기술명을 찾아 표준 스킬명으로 통일함
# 같은 기술의 영문, 한글, 약어 등을 하나의 스킬로 묶어 추출함

# 영문 기술명은 문자열 경계를 적용해 다른 단어에 포함된 경우의 오탐을 방지하였음
# 한글 기술명은 조사가 붙을 수 있어 경계를 적용하지 않고 작성함

# R, C, Go 등 짧은 기술명은 별도 정규식/별칭 제한으로 오탐을 방지하였음
# extract_skills()는 공고별 기술 등장 여부만 확인하도록 set으로 반환
