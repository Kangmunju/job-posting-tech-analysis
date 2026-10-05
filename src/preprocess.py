# 웹에서 가져온 HTML 표현을 일반 문자로 복원하기 위해 사용
import html
import re


# =====================================================================
# 1. 문자열 안전 변환
# =====================================================================


def _s(value) -> str:
    # None 처리
    if value is None:
        # 빈 문자열로 바꿔두어야 나중에 텍스트 합칠 때 편함
        return ""

    try:
        # NaN은 자기 자신과 비교했을 때 False가 나오는 특성 활용
        # 이 값이 NaN이라면
        if value != value:
            return ""
    except Exception:
        pass

    return str(value)


# =====================================================================
# 2. 분석에 사용할 본문 합치기
# =====================================================================


# 공고 한 건을 딕셔너리로 받아 분석할 본문 문자열 하나로 만드는 함수
def build_text(row: dict) -> str:
    """
    요구 기술 신호가 있는 필드만 합친다.
    """

    parts = [
        # 위에서 None일지라도 ""을 반환하도록 작성하였음
        _s(row.get("requirements")),  # 자격요건
        _s(row.get("preferred")),  # 우대사항
        _s(row.get("main_tasks")),  # 주요업무
    ]

    # 빈 문자열 제외하고 합쳐서 리턴
    return "\n".join(part for part in parts if part)


# =====================================================================
# 3. 텍스트 정규화
# =====================================================================


# 채용공고 텍스트 원문을 분석이 편하도록 전처리
def normalize(text: str) -> str:
    # 비어있으면 굳이 전처리하지 않고 빈 문자열 바로 반환
    if not text:
        return ""

    text = _s(text)

    # &amp; → & 등 HTML 엔티티 복원
    text = html.unescape(text)

    # 제로폭 공백과 nbsp(non-breaking space)를 일반 공백으로 변경
    text = text.replace("\u200b", " ").replace("\xa0", " ")

    # 불릿·기호를 공백으로 변경
    # 기술명에 필요한 # . + / 는 제거하지 않음
    text = re.sub(
        r"[•▪◦●○·※★☆■□▶►➤✓✔\-–—*_>|]",
        " ",
        text,
    )

    # 줄바꿈, 탭 등을 공백으로 변경
    text = re.sub(r"[\r\n\t]+", " ", text)

    # 연속된 공백을 하나로 정리
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


# =====================================================================
# 4. 한글 경량 스테밍
# =====================================================================


KO_SUFFIXES = [
    "으로서",
    "이라면",
    "습니다",
    "합니다",
    "입니다",
    "으로",
    "에서",
    "에게",
    "이나",
    "이라",
    "이며",
    "하며",
    "하고",
    "하는",
    "한",
    "을",
    "를",
    "은",
    "는",
    "이",
    "가",
    "의",
    "에",
    "도",
    "와",
    "과",
    "로",
    "만",
]


KO_STOPWORDS = {
    "경우",
    "관련",
    "대한",
    "통해",
    "위한",
    "있는",
    "있습니다",
    "합니다",
    "업무",
    "경험",
    "우대",
    "자격",
    "지원",
    "담당",
    "개발",
    "서비스",
    "기술",
}


def tokenize_ko(text: str) -> list[str]:
    """
    한글 일반어 토큰(2글자 이상).
    경량 스테밍 + 불용어 제거.
    기술 추출은 skills.py가 담당한다.
    """

    text = normalize(text)

    # 한글 2~8글자 어절 추출
    tokens = re.findall(r"[가-힣]{2,8}", text)

    result = []

    for token in tokens:
        # 뒤에 붙은 조사·어미를 한 번 제거
        for suffix in KO_SUFFIXES:
            if token.endswith(suffix) and len(token) - len(suffix) >= 2:
                token = token[: -len(suffix)]
                break

        # 2글자 이상이고 불용어가 아니면 저장
        if len(token) >= 2 and token not in KO_STOPWORDS:
            result.append(token)

    return result


# =====================================================================
# 5. 자체 테스트
# =====================================================================


def main():
    sample = {
        "requirements": "• Python과 SQL을 활용한 데이터 분석 경험",
        "preferred": "AWS / Docker 경험자 우대 &amp; C++ 가능자",
        "main_tasks": "데이터 파이프라인 개발 및 운영",
        "intro": "자유로운 분위기의 회사입니다.",
        "benefits": "맛있는 간식을 제공합니다.",
    }

    text = build_text(sample)
    normalized = normalize(text)
    tokens = tokenize_ko(text)

    print("=" * 64)
    print("텍스트 전처리 테스트")
    print("=" * 64)

    print()
    print("[본문 합치기]")
    print(text)

    print()
    print("[정규화]")
    print(normalized)

    print()
    print("[한글 토큰]")
    print(tokens)

    print()
    print("[확인]")

    checks = [
        (
            "intro 제외",
            "자유로운 분위기" not in text,
        ),
        (
            "benefits 제외",
            "맛있는 간식" not in text,
        ),
        (
            "HTML 엔티티 복원",
            "&" in normalized,
        ),
        (
            "C++ 보존",
            "C++" in normalized,
        ),
        (
            "슬래시 보존",
            "/" in normalized,
        ),
    ]

    passed = 0

    for name, success in checks:
        if success:
            state = "PASS"
            passed += 1
        else:
            state = "FAIL"

        print(f"{state} | {name}")

    print()
    print(f"테스트 결과: {passed}/{len(checks)} 통과")

    if passed != len(checks):
        raise RuntimeError("텍스트 전처리 자체 테스트에 실패했습니다.")


if __name__ == "__main__":
    main()


# ================================================================
# 텍스트 전처리 테스트
# ================================================================

# [본문 합치기]
# • Python과 SQL을 활용한 데이터 분석 경험
# AWS / Docker 경험자 우대 &amp; C++ 가능자
# 데이터 파이프라인 개발 및 운영

# [정규화]
# Python과 SQL을 활용한 데이터 분석 경험 AWS / Docker 경험자 우대 & C++ 가능자 데이터 파이프라인 개발 및 운영

# [한글 토큰]
# ['활용', '데이터', '분석', '경험자', '가능자', '데이터', '파이프라인', '운영']

# [확인]
# PASS | intro 제외
# PASS | benefits 제외
# PASS | HTML 엔티티 복원
# PASS | C++ 보존
# PASS | 슬래시 보존

# 테스트 결과: 5/5 통과


# =====================================================================

# requirements + preferred + main_tasks만 합쳐 분석용 텍스트 생성
# None/NaN은 _s()에서 빈 문자열로 변환해 결측치로 인한 문자열 처리 오류를 방지함

# HTML 엔티티와 특수 공백, 불필요한 불릿 및 기호를 정리함
# C++, C#, node.js, ci/cd 같은 기술명은 보존이 필요해 해당 기호들은 제거하지 않았음

# 한글 일반어는 2~8글자로 추출한 뒤 조사와 어미를 한 번 제거하는 경량 스테밍 적용함
# KO_SUFFIXES는 순서대로 검사하기 위해 list로 구성함
# KO_STOPWORDS는 포함 여부 확인용이므로 set으로 구성함
# 채용공고에 반복되는 불용어(경험, 업무, 우대 등)는 제외함

# 한글 토큰화는 워드클라우드용 보조 처리
# 실제 기술 추출은 skills.py의 스킬 사전이 담당함
