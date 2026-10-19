import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


# =====================================================================
# 1. 설정
# =====================================================================

ROLE_KO = {
    "data_analyst": "데이터 분석가",
    "data_engineer": "데이터 엔지니어",
    "data_scientist": "데이터 사이언티스트",
    "backend": "백엔드",
    "frontend": "프론트엔드",
}

# 가장 잘 맞는 직무의 막대 색과 나머지 막대 색
ACCENT_COLOR = "#E4572E"
MUTED_COLOR = "#C9C2B3"


# =====================================================================
# 2. 데이터 불러오기
# =====================================================================


def find_models_dir() -> Path:
    """
    분석 결과 CSV가 있는 models 폴더를 찾는다.
    환경변수 JOB_MODELS_DIR, 프로젝트 루트의 models, app 폴더의 models 순서로 확인한다.
    """

    here = Path(__file__).resolve()

    candidates = []

    env_path = os.environ.get("JOB_MODELS_DIR")

    if env_path:
        candidates.append(Path(env_path))

    candidates.append(here.parents[1] / "models")
    candidates.append(here.parent / "models")

    for candidate in candidates:
        if (candidate / "skill_freq_by_role.csv").exists():
            return candidate

    raise FileNotFoundError(
        "models/skill_freq_by_role.csv 를 찾지 못했습니다. JOB_MODELS_DIR 로 경로를 지정하세요."
    )


@st.cache_data
def load(models_dir: str):
    # 행 = 기술, 열 = 직무, 값 = 등장률(%)
    freq = pd.read_csv(Path(models_dir) / "skill_freq_by_role.csv", index_col=0)

    # 기술 쌍의 공동출현 횟수와 Jaccard 유사도
    cooc = pd.read_csv(Path(models_dir) / "skill_cooccurrence.csv")

    return freq, cooc


# =====================================================================
# 3. 계산
# =====================================================================


def coverage(freq: pd.DataFrame, mine: list) -> pd.DataFrame:
    """
    매칭 점수 = 내가 가진 기술의 등장률 합 / 그 직무 전체 기술의 등장률 합 x 100
    """

    total = freq.sum(axis=0)

    owned = freq.loc[freq.index.isin(mine)]

    have = owned.sum(axis=0)

    rows = []

    for role in freq.columns:
        rows.append(
            {
                "role": role,
                "직무": ROLE_KO[role],
                "score": round(have[role] / total[role] * 100, 1),
                "n_have": int((owned[role] > 0).sum()),
            }
        )

    result = pd.DataFrame(rows)

    return result.sort_values("score", ascending=False).reset_index(drop=True)


def next_skills(freq: pd.DataFrame, mine: list, role: str, top_n: int = 3) -> pd.DataFrame:
    """
    하나 더 배우면 점수가 가장 많이 오르는 기술을 찾는다.
    아직 없는 기술 중에서 그 직무의 등장률이 가장 높은 기술이다.
    """

    total = freq[role].sum()

    candidates = freq.loc[~freq.index.isin(mine), role].sort_values(ascending=False).head(top_n)

    return pd.DataFrame(
        {
            "기술": candidates.index,
            "등장률(%)": candidates.values,
            "점수 상승(%p)": (candidates.values / total * 100).round(1),
        }
    )


def partners(cooc: pd.DataFrame, mine: list, top_n: int = 8) -> pd.DataFrame:
    """
    내 기술과 같은 공고에 자주 나오는 기술 중 내가 아직 없는 기술을 Jaccard 순서로 찾는다.
    """

    # 내 기술이 skill_a 쪽에 있는 경우
    left = cooc[cooc["skill_a"].isin(mine) & ~cooc["skill_b"].isin(mine)].rename(
        columns={"skill_a": "내 기술", "skill_b": "함께 나오는 기술"}
    )

    # 내 기술이 skill_b 쪽에 있는 경우
    right = cooc[cooc["skill_b"].isin(mine) & ~cooc["skill_a"].isin(mine)].rename(
        columns={"skill_b": "내 기술", "skill_a": "함께 나오는 기술"}
    )

    both = pd.concat([left, right]).sort_values("jaccard", ascending=False)

    # 같은 기술이 여러 번 나오면 Jaccard가 가장 높은 한 줄만 남김
    both = both.drop_duplicates("함께 나오는 기술").head(top_n)

    both = both[["함께 나오는 기술", "내 기술", "co_count", "jaccard"]]

    return both.rename(columns={"co_count": "함께 등장(건)", "jaccard": "Jaccard"})


# =====================================================================
# 4. 화면
# =====================================================================


def main():
    st.set_page_config(page_title="내 기술로 확인해 보기", layout="centered")

    try:
        freq, cooc = load(str(find_models_dir()))
    except FileNotFoundError as error:
        st.error(str(error))
        return

    st.title("내 기술로 직접 확인해 보기")

    st.caption(
        "원티드 채용공고를 분석한 결과(직무별 기술 등장률, 공동출현)로 계산합니다. "
        "예측 모델은 아니고, 공고 문장에 기술이 나왔는지를 센 결과입니다."
    )

    mine = st.multiselect("내가 쓸 수 있는 기술", list(freq.index), default=["Python", "SQL"])

    with st.expander("점수는 이렇게 계산해요", expanded=False):
        st.markdown(
            "매칭 점수는 (내 기술들의 그 직무 등장률 합) ÷ (그 직무 전체 기술의 등장률 합) × 100입니다. "
            "그 직무 공고에 자주 나오는 기술을 가질수록 높아지고, "
            f"사전의 {len(freq.index)}개 기술을 모두 가지면 100이 됩니다.\n\n"
            "다음에 배울 기술은 아직 없는 기술 가운데 그 직무 등장률이 가장 높은 것입니다. "
            "하나를 더했을 때 점수가 가장 많이 오릅니다.\n\n"
            "함께 나오는 기술은 내 기술과 같은 공고에 같이 등장하는 정도(Jaccard)로 골랐고, "
            "20건 이상 등장한 기술만 대상입니다.\n\n"
            "기술이 공고에 나왔는지만 세기 때문에 숙련도, 필수와 우대의 구분, "
            "실제 합격 가능성은 반영하지 않습니다."
        )

    if not mine:
        st.info("기술을 하나 이상 골라 주세요.")
        return

    cov = coverage(freq, mine)

    best = cov.iloc[0]

    # 가장 잘 맞는 직무인지 표시하는 열 (막대 색 구분에 사용)
    cov["is_best"] = cov["role"] == best["role"]

    st.subheader(f"가장 잘 맞는 직무: {best['직무']} (매칭 점수 {best['score']})")

    chart = (
        alt.Chart(cov)
        .mark_bar()
        .encode(
            y=alt.Y("직무:N", sort=list(cov["직무"]), title=None),
            x=alt.X("score:Q", title="매칭 점수 (0~100)"),
            color=alt.condition(
                alt.datum.is_best,
                alt.value(ACCENT_COLOR),
                alt.value(MUTED_COLOR),
            ),
            tooltip=[
                "직무",
                alt.Tooltip("score:Q", title="매칭 점수"),
                alt.Tooltip("n_have:Q", title="해당 직무에 등장하는 내 기술 수"),
            ],
        )
    )

    st.altair_chart(chart, width="stretch")

    st.subheader("직무별로 다음에 배우면 점수가 가장 많이 오르는 기술 TOP3")

    tabs = st.tabs(list(cov["직무"]))

    for tab, role in zip(tabs, cov["role"]):
        with tab:
            st.dataframe(next_skills(freq, mine, role), hide_index=True, width="stretch")

    st.subheader("내 기술과 같은 공고에 자주 나오는 기술")

    partner_table = partners(cooc, mine)

    if partner_table.empty:
        st.write("선택한 기술은 공동출현 표(20건 이상 등장한 기술)에 없어서 짝을 찾지 못했습니다.")
    else:
        st.dataframe(partner_table, hide_index=True, width="stretch")

    st.caption("출처: models/skill_freq_by_role.csv, models/skill_cooccurrence.csv. 원티드 공고 2026-09-17 수집.")


main()


# =====================================================================
# [구현 핵심]
# =====================================================================

# 분석 결과 CSV 두 개만 읽어서 내 기술 조합이 각 직무 공고와 얼마나 겹치는지를 보여주는 Streamlit 앱
# 예측 모델이 아니라 이미 계산된 직무별 기술 등장률과 공동출현 결과를 그대로 사용함 (재계산·보정 없음)
#   - models/skill_freq_by_role.csv : 직무 x 기술 등장률(%), analysis/a2_skill_frequency.py 산출물
#   - models/skill_cooccurrence.csv : 기술 쌍 공동출현 횟수와 Jaccard, analysis/a4_cooccurrence.py 산출물

# 매칭 점수 = 내 기술의 직무 등장률 합 / 그 직무 전체 기술의 등장률 합 x 100
# 다음에 배울 기술 = 아직 없는 기술 중 그 직무 등장률이 가장 높은 기술 (하나 더하면 점수가 가장 많이 오름)
# 함께 나오는 기술 = 내 기술과 같은 공고에 자주 나오는(Jaccard) 기술

# 실행: pip install -r app/requirements.txt 후 streamlit run app/streamlit_app.py
# 배포: Streamlit Community Cloud에서 저장소를 연결하고 Main file path에 app/streamlit_app.py를 지정함
# models 폴더 위치가 다르면 환경변수 JOB_MODELS_DIR로 경로를 지정할 수 있음


# =====================================================================
# [수정 사항]
# =====================================================================

# 파일 이름을 predict_tab.py에서 streamlit_app.py로 바꿈 (예측 모델이 아니라서)
# 리스트 컴프리헨션을 for문으로 풀어 쓰고, 안내 문구에 박혀 있던 공고 건수와 기술 수를 제거하거나 데이터에서 읽도록 바꿈
# 막대 색 구분에 한글 열 이름 대신 is_best 열을 사용하도록 바꿈 (그래프 표현식에서 한글 열 이름을 쓰지 않기 위해)
# models 폴더를 찾지 못하면 오류로 멈추지 않고 안내 문구를 화면에 보여주도록 바꿈
