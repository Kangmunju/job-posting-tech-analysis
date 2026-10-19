import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import _common as C


# =====================================================================
# 0. 통계 함수
# =====================================================================


def wilson_interval(count, total):
    """
    비율(count / total)의 Wilson 95% 신뢰구간을 %로 반환한다.
    """

    result = stats.binomtest(int(count), int(total)).proportion_ci(
        confidence_level=0.95,
        method="wilson",
    )

    return result.low * 100, result.high * 100


def mcnemar_exact_p(only_first, only_second):
    """
    같은 공고 안에서 두 기술을 짝지어 비교하는 McNemar 정확검정의 p값을 반환한다.
    두 기술 중 하나만 등장한 공고가 어느 쪽이든 같은 확률로 나온다는 가정을 이항검정으로 확인한다.
    """

    discordant = int(only_first) + int(only_second)

    if discordant == 0:
        return 1.0

    result = stats.binomtest(
        int(min(only_first, only_second)),
        discordant,
        0.5,
    )

    return result.pvalue


def format_p(p_value):
    if p_value < 0.001:
        return "p < 0.001"

    return f"p = {p_value:.3f}"


# =====================================================================
# 1. 반직관 발견 분석 실행
# =====================================================================


def main():

    df = C.load_jobs()
    mat, sub = C.build_skill_matrix(df)

    skill_cols = [column for column in mat.columns if column != "role"]

    # 직무별 스킬 등장률(%)
    tf = mat.groupby("role")[skill_cols].mean().reindex(C.ROLE_ORDER).mul(100)

    C.rule("a5 — 반직관 발견")

    # =================================================================
    # 2. 발견 1 — 데이터 분석가 SQL vs Python
    # =================================================================

    print("\n[발견 1] 데이터 분석가: SQL vs Python")

    da = tf.loc["data_analyst"]
    da_jobs = mat[mat["role"] == "data_analyst"]
    da_count = len(da_jobs)

    sql_low, sql_high = wilson_interval((da_jobs["SQL"] == 1).sum(), da_count)
    python_low, python_high = wilson_interval((da_jobs["Python"] == 1).sum(), da_count)

    print(
        f"SQL {da['SQL']:.0f}% (95% 신뢰구간 {sql_low:.0f}~{sql_high:.0f}%) / "
        f"Python {da['Python']:.0f}% (95% 신뢰구간 {python_low:.0f}~{python_high:.0f}%) "
        f"(차이 {da['SQL'] - da['Python']:+.0f}%p, n={da_count})"
    )

    # 같은 공고 안에서 SQL과 Python을 짝지어 비교
    only_sql = int(((da_jobs["SQL"] == 1) & (da_jobs["Python"] == 0)).sum())
    only_python = int(((da_jobs["SQL"] == 0) & (da_jobs["Python"] == 1)).sum())
    both = int(((da_jobs["SQL"] == 1) & (da_jobs["Python"] == 1)).sum())
    neither = int(((da_jobs["SQL"] == 0) & (da_jobs["Python"] == 0)).sum())

    print(
        f"같은 공고 안 비교: SQL만 {only_sql}건 / Python만 {only_python}건 / "
        f"둘 다 {both}건 / 둘 다 없음 {neither}건"
    )

    print(f"McNemar 정확검정: {format_p(mcnemar_exact_p(only_sql, only_python))}")

    print("\n[직무별 SQL / Python 등장률 (95% 신뢰구간)]")

    for role in C.ROLE_ORDER:
        role_jobs = mat[mat["role"] == role]
        role_count = len(role_jobs)

        sql_low, sql_high = wilson_interval((role_jobs["SQL"] == 1).sum(), role_count)
        python_low, python_high = wilson_interval(
            (role_jobs["Python"] == 1).sum(), role_count
        )

        print(
            f"{C.ROLE_KO[role]}: "
            f"SQL {tf.loc[role, 'SQL']:.0f}% ({sql_low:.0f}~{sql_high:.0f}%) / "
            f"Python {tf.loc[role, 'Python']:.0f}% ({python_low:.0f}~{python_high:.0f}%) "
            f"(n={role_count})"
        )

    # =================================================================
    # 3. 발견 2 — LLM 요구 공고의 직무별 분포
    # =================================================================

    print("\n[발견 2] LLM의 직무별 확산")

    print("\n[직무별 LLM / RAG 등장률 (LLM은 95% 신뢰구간)]")

    for role in C.ROLE_ORDER:
        role_jobs = mat[mat["role"] == role]

        llm_low, llm_high = wilson_interval((role_jobs["LLM"] == 1).sum(), len(role_jobs))

        print(
            f"{C.ROLE_KO[role]}: "
            f"LLM {tf.loc[role, 'LLM']:.0f}% ({llm_low:.0f}~{llm_high:.0f}%) / "
            f"RAG {tf.loc[role, 'RAG']:.0f}%"
        )

    llm_jobs = mat[mat["LLM"] == 1]

    print(f"\nLLM 요구 공고 총 {len(llm_jobs)}건")

    for role in C.ROLE_ORDER:
        count = (llm_jobs["role"] == role).sum()

        print(f"{C.ROLE_KO[role]}: {count}건")

    # 데이터 사이언티스트 분류 규칙에 제목의 llm이 포함되어 있어서
    # 제목에 LLM이 있는 공고는 분류 단계에서 이미 LLM이 반영된 공고임
    ds_llm_jobs = llm_jobs[llm_jobs["role"] == "data_scientist"]
    positions = sub.set_index("job_id")["position"]

    title_llm_count = 0

    for job_id in ds_llm_jobs.index:
        if "llm" in str(positions[job_id]).lower():
            title_llm_count += 1

    print(
        f"\n데이터 사이언티스트 LLM 공고 {len(ds_llm_jobs)}건 중 "
        f"{title_llm_count}건은 제목에 LLM이 있어 직무 분류 단계에서 이미 LLM이 반영됨"
    )

    # =================================================================
    # 4. 발견 3 — 경력대별 요구 스킬 수
    # =================================================================

    print("\n[발견 3] 경력대별 요구 스킬 수")

    # mat : 공고 × 스킬 0/1 매트릭스
    # 공고마다 등장한 스킬 개수
    per_job = mat[skill_cols].sum(axis=1)

    sub2 = sub.set_index("job_id").copy()

    sub2["n_skills"] = per_job

    def band(a):

        if pd.isna(a):
            return "미상"

        a = float(a)

        if a <= 1:
            return "신입~1년"

        if a <= 4:
            return "2~4년"

        return "5년+"

    sub2["exp_band"] = sub2["annual_from"].map(band)

    g = (
        sub2.groupby("exp_band")["n_skills"]
        # agg()를 사용해 각 그룹에 세 가지 통계를 한 번에 계산
        .agg(["mean", "median", "std", "count"])
        .reindex(["신입~1년", "2~4년", "5년+", "미상"])
        .dropna(subset=["count"])
    )

    # exp_band : 현재 행의 인덱스(경력 구간 이름)
    # row : 해당 경력 구간의 평균, 중앙값, 공고 수가 담긴 Series
    # iterrows()를 사용해 데이터프레임을 한 행씩 순회하도록 함
    for exp_band, row in g.iterrows():
        print(
            f"{exp_band}: "
            f"평균 {row['mean']:.1f}개 / "
            f"중앙값 {row['median']:.0f}개 / "
            f"표준편차 {row['std']:.1f}개 "
            f"(n={int(row['count'])})"
        )

    # 경력 구간 3개(미상 제외)의 공고당 스킬 수 분포가 서로 다른지 Kruskal-Wallis 검정으로 확인
    groups = []

    for exp_band in ["신입~1년", "2~4년", "5년+"]:
        groups.append(sub2[sub2["exp_band"] == exp_band]["n_skills"].values)

    h_value, kruskal_p = stats.kruskal(*groups)

    print(f"\nKruskal-Wallis 검정 (미상 제외): H = {h_value:.2f}, {format_p(kruskal_p)}")

    if kruskal_p < 0.05:
        print("→ 경력 구간별 요구 스킬 수에 통계적으로 유의한 차이가 있음")
    else:
        print("→ 경력 구간별 요구 스킬 수에 통계적으로 유의한 차이는 없음")

    # =================================================================
    # 5. 발견 4 — 직무 간 코사인 유사도
    # =================================================================

    print("\n[발견 4] 직무 간 스킬 프로필 유사도")

    # tf : 직무별 스킬등장률을 계산한 데이터프레임
    # 직무 × 스킬 등장률 벡터
    # V : 5개 직무와 90개 스킬 (5, 90)
    V = tf.fillna(0).values

    # 직무별 벡터의 크기
    # np.linalg.norm()으로 벡터의 크기를 계산
    # 각 직무의 스킬 등장률을 하나의 벡터로 보고 직무별로 크기를 계산함
    # 계산 후에도 2차원 형태를 유지하도록 함
    norm = np.linalg.norm(
        V,
        axis=1,
        keepdims=True,
    )

    # 코사인 유사도 계산
    # 원소별로 곱해 두 직무의 벡터 크기를 곱한 값을 구함
    denominator = norm * norm.T

    # np.divide()로 요소별 나눗셈을 수행함
    sim = np.divide(
        # 두 직무의 내적을 계산 (5, 5)
        V @ V.T,
        denominator,
        out=np.zeros_like(denominator),
        # 0으로 나누는 오류를 방지하도록 보완
        where=denominator != 0,
    )

    simdf = pd.DataFrame(
        sim,
        index=C.ROLE_ORDER,
        columns=C.ROLE_ORDER,
    ).round(2)

    print(simdf.to_string())

    print(
        "\n데이터 엔지니어 ↔ 데이터 분석가: "
        f"{simdf.loc['data_engineer', 'data_analyst']:.2f}"
    )

    print(f"데이터 엔지니어 ↔ 백엔드: {simdf.loc['data_engineer', 'backend']:.2f}")

    # =================================================================
    # 6. 코사인 유사도 결과 저장
    # =================================================================

    model_dir = C.ROOT / "models"

    model_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    simdf.to_csv(
        model_dir / "role_similarity.csv",
        encoding="utf-8-sig",
    )

    # =================================================================
    # 7. 직무 간 유사도 히트맵
    # =================================================================

    fig, ax = plt.subplots(
        figsize=(9, 7),
    )

    im = ax.imshow(
        sim,
        cmap="Blues",
        vmin=0,
        vmax=1,
    )

    labels = [C.ROLE_KO[role] for role in C.ROLE_ORDER]

    ax.set_xticks(
        range(len(labels)),
        labels=labels,
        rotation=35,
        ha="right",
    )

    ax.set_yticks(
        range(len(labels)),
        labels=labels,
    )

    for i in range(len(labels)):
        for j in range(len(labels)):
            value = sim[i, j]

            ax.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                color="white" if value >= 0.5 else "black",
            )

    ax.set_title("직무 간 스킬 프로필 코사인 유사도")

    fig.colorbar(
        im,
        ax=ax,
        label="Cosine Similarity",
    )

    plt.tight_layout()

    # =================================================================
    # 8. 히트맵 저장
    # =================================================================

    figure_dir = C.ROOT / "outputs" / "figures"

    figure_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.savefig(
        figure_dir / "pc_a5_role_similarity.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


# =====================================================================
# 9. 실행
# =====================================================================

if __name__ == "__main__":
    main()


# =====================================================================
# [구현 핵심]
# =====================================================================

# 앞선 분석에서 추출한 스킬 데이터를 활용해 직무별 기술 요구의 특징을 비교
# 단순 빈도 분석만으로 알기 어려운 관계를 파악하고자 함
# 특히 직무 간 요구 기술의 구성이 얼마나 유사한지 정량적으로 비교함

# 코사인 유사도를 사용한 이유
# 직무마다 공고 수와 스킬 등장 빈도가 달라 단순 개수 비교에 한계가 있음을 느낌
# 각 직무를 '스킬별 등장률'로 구성된 벡터로 표현해 공고 수 차이를 완화함
# 코사인 유사도는 벡터의 크기보다 방향에 초점을 맞춘다는 특징을 이용
# 어떤 기술을 상대적으로 더 많이 요구하는지(기술 구성 패턴) 비교하기에 적합하다고 판단함
# 단순히 스킬을 많이 요구하는 직무보다 비슷한 기술 조합을 요구하는 직무를 찾으려는 목적

# 단, 유사도가 높아도 실제 업무 내용이나 요구 숙련도가 같다는 의미는 아님
# 채용 공고에 명시된 기술을 기준으로 계산한 유사도이기 때문에 관계 해석 참고 지표 정도로 활용


# =====================================================================
# [수정 사항]
# =====================================================================

# 경력 구간별 공고당 스킬 수의 표준편차(4.0~4.6개)가 구간 평균 차이(0.8개 이내)보다 커서 Kruskal-Wallis 검정을 추가함
# 데이터 분석가의 SQL과 Python 요구는 같은 공고 안에서 짝지어 비교하는 비교라 McNemar 정확검정을 추가함
# 직무별 공고 수가 71~227건으로 작아 비율 옆에 Wilson 95% 신뢰구간을 함께 출력함
# 데이터 사이언티스트 분류 규칙에 제목의 llm이 들어 있어 LLM 공고 중 제목에 LLM이 있는 공고 수를 함께 출력함
# 통계 함수는 scipy.stats만 사용하고 statsmodels로 같은 값이 나오는 것을 확인함
