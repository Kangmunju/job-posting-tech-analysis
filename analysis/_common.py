from pathlib import Path
import sys


# 현재 컴퓨터에 있는 폰트를 찾아서
import matplotlib.pyplot as plt

# 찾은 폰트를 matplotlib 그래프에 적용
import matplotlib.font_manager as fm

# 채용공고와 스킬 매트릭스를 DataFrame으로 처리
import pandas as pd


# =====================================================================
# 1. 프로젝트 경로 설정
# =====================================================================

# resolve() : 절대 경로 변환, 경로 정규화, 심볼릭 링크 해결
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# analysis 폴더에서 실행해도 src의 모듈을 import할 수 있도록 경로 추가
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# =====================================================================
# 2. 한글 폰트 설정
# =====================================================================

font_names = {font.name for font in fm.fontManager.ttflist}

for candidate in [
    "AppleGothic",
    "Malgun Gothic",
    "NanumGothic",
    "NanumBarunGothic",
]:
    if candidate in font_names:
        # plt.rcParams : Runtime Configuration Parameters
        # 전역 설정, 일관성 유지, 즉시 반영
        # 사용 가능한 한글 폰트 찾으면 matplotlib 기본 폰트로 설정
        plt.rcParams["font.family"] = candidate
        break
else:
    print("[WARN] 한글 폰트를 찾지 못했습니다.")

# 그래프의 마이너스 기호 깨짐 방지
plt.rcParams["axes.unicode_minus"] = False


# =====================================================================
# 3. 분석 대상 직무
# =====================================================================

# 내부 계산은 영문 label로 하고 사람에게 보여줄 때만 한글로 표시함
ROLE_ORDER = [
    "data_analyst",
    "data_engineer",
    "data_scientist",
    "backend",
    "frontend",
]

ROLE_KO = {
    "data_analyst": "데이터 분석가",
    "data_engineer": "데이터 엔지니어",
    "data_scientist": "데이터 사이언티스트",
    "backend": "백엔드",
    "frontend": "프론트엔드",
}


# =====================================================================
# 4. 출력 구분선
# =====================================================================


def rule(title: str):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# =====================================================================
# 5. DB에서 채용공고 불러오기
# =====================================================================


def load_jobs() -> pd.DataFrame:
    """
    DB의 전체 채용공고를 불러오고
    공고 제목을 기준으로 role 컬럼을 추가한다.
    """

    # load_jobs()에서만 사용하는 src 모듈이므로 함수 내부에서 import함
    import db as DB
    import classify

    con = DB.connect()

    # 조회 중 오류 발생하더라도 DB 연결 종료 가능하도록 작성
    try:
        df = DB.read_jobs(con)
    finally:
        con.close()

    df["role"] = df["position"].map(classify.classify)

    return df


# =====================================================================
# 6. 공고 × 스킬 0/1 매트릭스 생성
# =====================================================================


def build_skill_matrix(df: pd.DataFrame):
    """
    분석 대상 5개 직무의 공고 × 스킬 0/1 매트릭스를 만든다.
    """

    # build_skill_matrix()에서만 사용하는 src 모듈이므로 함수 내부에서 import함
    import preprocess
    import skills as SK

    skill_names = SK.all_skill_names()

    # role의 각 값이 ROLE_ORDER 안에 들어 있는지 확인
    # other를 제외하고 분석 대상 5개 직무만 사용
    # 이후 원본에 영향을 주지 않기 위해 copy() 사용하여 sub에 저장
    sub = df[df["role"].isin(ROLE_ORDER)].copy()

    records = []

    for _, row_data in sub.iterrows():
        # 자격요건 + 우대사항 + 주요업무
        text = preprocess.build_text(row_data.to_dict())

        # 해당 공고에서 발견된 기술
        found = SK.extract_skills(text)

        # 전체 표준 스킬을 확인해 공고에서 기술 발견하면 1, 없으면 0
        row = {skill: 1 if skill in found else 0 for skill in skill_names}

        # 어떤 공고인지 식별
        row["job_id"] = int(row_data["job_id"])

        # 어떤 직무의 공고인지 구분
        row["role"] = row_data["role"]

        records.append(row)

    # set_index()로 "job_id" 열을 DataFrame의 행 인덱스로 지정
    mat = pd.DataFrame(records).set_index("job_id")

    return mat, sub


# =====================================================================
# 7. 자체 테스트
# =====================================================================


def main():

    df = load_jobs()

    # mat : 공고 × 스킬 0/1 매트릭스
    # sub : other를 제외한 분석 대상 원본 공고
    mat, sub = build_skill_matrix(df)

    # skill_cols에 90개 스킬 컬럼 이름만 남김
    skill_cols = [column for column in mat.columns if column != "role"]

    skill_counts = mat[skill_cols].sum(axis=1)

    rule("공통 분석 모듈 테스트")

    print(f"전체 공고: {len(df):,}건")
    print(f"분석 대상: {len(sub):,}건")
    print(f"스킬 수: {len(skill_cols):,}개")
    print(f"매트릭스 크기: {mat.shape}")

    print()
    print("[직무별 공고 수]")

    for role in ROLE_ORDER:
        count = (mat["role"] == role).sum()
        print(f"{ROLE_KO[role]}: {count:,}건")

    print()
    print("[스킬 추출 커버리지]")
    print(f"공고당 평균 스킬: {skill_counts.mean():.1f}개")
    print(f"공고당 중앙값 스킬: {skill_counts.median():.0f}개")
    print(f"스킬 0개 공고: {(skill_counts == 0).sum():,}건")


if __name__ == "__main__":
    main()


# ========================================================================
# 공통 분석 모듈 테스트
# ========================================================================
# 전체 공고: 1,273건
# 분석 대상: 724건
# 스킬 수: 90개
# 매트릭스 크기: (724, 91)

# [직무별 공고 수]
# 데이터 분석가: 71건
# 데이터 엔지니어: 94건
# 데이터 사이언티스트: 122건
# 백엔드: 287건
# 프론트엔드: 150건

# [스킬 추출 커버리지]
# 공고당 평균 스킬: 7.5개
# 공고당 중앙값 스킬: 7개
# 스킬 0개 공고: 14건


# =====================================================================

# 프로젝트 루트와 src 경로를 설정해 analysis 폴더에도 src 모듈을 불러올 수 있도록 함
# 사용 가능한 한글 폰트를 자동으로 찾아 matplotlib 그래프의 한글 및 기호 깨짐 방지

# 분석 대상 직무 5개와 출력 순서를 ROLE_ORDER로 정의함
# 한글 직무명을 ROLE_KO로 관리함

# other를 제외한 5개 직무만 분석 대상으로 사용하였음
# preprocess.py로 requirements + preferred + main_tasks를 합치고 skills.py로 기술을 추출함
# 전체 90개 표준 스킬을 기준으로 발견된 기술은 1, 없으면 0인 공고 × 스킬 매트릭스를 생성함
# job_id는 매트릭스 인덱스로 사용하고 role은 직무별 분석을 위해 유지함
