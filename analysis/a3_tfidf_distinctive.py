# IDF 계산에 필요한 log 계산을 위해 import함
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import _common as C


# =====================================================================
# 0. 공통 함수
# =====================================================================


def collect_top_skills(table, top_n):
    """
    직무별로 값이 큰 상위 top_n개 기술을 모아 중복 없이 반환한다.
    """

    skills = []

    for role in C.ROLE_ORDER:
        # .index를 사용해 현재 직무의 상위 기술 이름만 가져옴
        top_skills = table.loc[role].sort_values(ascending=False).head(top_n).index

        for skill in top_skills:
            if skill not in skills:
                skills.append(skill)

    return skills


def save_heatmap(data, title, bar_label, file_name, cmap, vmin=None, vmax=None):
    """
    직무 × 기술 표를 히트맵으로 그려 outputs/figures에 저장한다.
    """

    fig, ax = plt.subplots(
        figsize=(14, 6),
    )

    image = ax.imshow(
        data.values,
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )

    ax.set_xticks(range(len(data.columns)))

    ax.set_xticklabels(
        data.columns,
        rotation=45,
        ha="right",
    )

    ax.set_yticks(range(len(C.ROLE_ORDER)))

    role_labels = []

    for role in C.ROLE_ORDER:
        role_labels.append(C.ROLE_KO[role])

    ax.set_yticklabels(role_labels)

    ax.set_title(title)

    ax.set_xlabel("기술")
    ax.set_ylabel("직무")

    fig.colorbar(
        image,
        ax=ax,
        label=bar_label,
    )

    plt.tight_layout()

    figure_dir = C.ROOT / "outputs" / "figures"

    figure_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.savefig(
        figure_dir / file_name,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


# =====================================================================
# 1. TF-IDF 분석 실행
# =====================================================================


def main():

    # DB 전체 공고 로드
    df = C.load_jobs()

    # 공고 × 스킬 0/1 매트릭스
    mat, _ = C.build_skill_matrix(df)

    # 90개의 스킬 이름만 저장
    skill_cols = [column for column in mat.columns if column != "role"]

    # =================================================================
    # 2. TF(Term Frequency) 계산
    # =================================================================

    # 직무 × 스킬 등장률
    # 스킬 매트릭스의 값 : 1(공고에 기술 있음) 또는 0(없음)이 되도록 작성했음
    # 0과 1의 평균 = 그 기술이 등장한 공고의 비율
    # 0/1 매트릭스의 직무별 평균이므로 TF 역할을 함
    tf = mat.groupby("role")[skill_cols].mean().reindex(C.ROLE_ORDER)

    # =================================================================
    # 3. DF(Document Frequency)와 IDF(Inverse Document Frequency) 계산
    # =================================================================

    # 등장률 5% 이상인 경우
    # 해당 직무에서 실제로 등장한 기술로 판단
    # 각 기술 열을 기준으로 5개 직무를 세로로 내려가면서 합산하여 구함
    present = (tf >= 0.05).sum(axis=0)

    # 전체 직무 수(5)
    n_roles = len(C.ROLE_ORDER)

    # 스무딩 IDF
    # present가 크면 여러 직무에서 흔하다는 의미이므로 나눈 값이 작음
    # present가 작으면 일부 직무에 집중되었다는 의미이므로 나눈 값 큼
    # 0 나눗셈 에러를 방지하기 위해 분자와 분모에 각각 1을 더해줌
    # 흔한 기술도 최소한의 가중치는 유지할 수 있도록 마지막에 1을 더해 보정
    idf = np.log((1 + n_roles) / (1 + present)) + 1

    # =================================================================
    # 4. TF-IDF 계산
    # =================================================================

    # tf : 직무별로 해당 기술이 얼마나 많이 등장하는지를 나타내는 값
    # idf : 각 기술이 얼마나 직무를 구별해주는지를 반영하는 가중치
    # 각 스킬의 IDF를 열 방향으로 곱함
    tfidf = tf.mul(
        idf,
        axis=1,
    )

    # =================================================================
    # 5. TF-IDF 결과 저장
    # =================================================================

    model_dir = C.ROOT / "models"
    model_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    tfidf.T.round(4).to_csv(
        model_dir / "tfidf_by_role.csv",
        encoding="utf-8",
    )

    # =================================================================
    # 6. 직무별 변별 기술 출력
    # =================================================================

    C.rule("a3 — 직무를 '변별'하는 기술 TOP (TF-IDF: 그 직무에서 유독 두드러짐)")

    for role in C.ROLE_ORDER:
        top = tfidf.loc[role].sort_values(ascending=False).head(8)

        parts = [
            (
                f"{skill}(TFIDF {value:.3f}, 등장 {round(tf.loc[role, skill] * 100, 1):.0f}%)"
            )
            for skill, value in top.items()
        ]

        print(f"\n[{C.ROLE_KO[role]}]")

        print(" " + "; ".join(parts))

    # =================================================================
    # 7. TF-IDF 히트맵
    # =================================================================

    # 각 직무의 상위 변별 기술을 모아 히트맵에 사용할 기술 목록 생성
    heatmap_skills = collect_top_skills(tfidf, 5)

    # 직무 × 변별 기술 TF-IDF 값을 히트맵으로 저장
    save_heatmap(
        tfidf[heatmap_skills],
        "직무별 변별 기술 TF-IDF",
        "TF-IDF",
        "pc_a3_tfidf_heatmap.png",
        "YlGn",
    )

    # =================================================================
    # 8. 직무 고유 기술 : 해당 직무 등장률 - 다른 직무 등장률 (%p)
    # =================================================================

    # TF-IDF는 문서 단위가 공고가 아니라 직무 5개라서 IDF가 가질 수 있는 값이 5가지뿐임
    # 그래서 결과가 등장률 순위를 거의 그대로 따라가고, 모든 직무에서 흔한 Python이 상위에 남음
    # 같은 기술이 다른 직무 공고에서는 얼마나 덜 등장하는지를 직접 빼서 직무 고유 기술을 확인함
    gap_rows = {}

    for role in C.ROLE_ORDER:
        # 해당 직무가 아닌 모든 공고에서 기술별 등장 비율
        others = mat[mat["role"] != role][skill_cols].mean()

        gap_rows[role] = (tf.loc[role] - others) * 100

    # 직무 × 스킬 등장률 차이(%p)
    gap = pd.DataFrame(gap_rows).T.reindex(C.ROLE_ORDER)

    gap.T.round(1).to_csv(
        model_dir / "distinctive_gap_by_role.csv",
        encoding="utf-8",
    )

    C.rule("a3 — 직무 고유 기술 TOP (해당 직무 등장률 − 다른 직무 등장률, %p)")

    for role in C.ROLE_ORDER:
        top = gap.loc[role].sort_values(ascending=False).head(8)

        parts = []

        for skill, value in top.items():
            in_role = tf.loc[role, skill] * 100
            parts.append(
                f"{skill}(+{value:.0f}%p, 해당 {in_role:.0f}% vs 그 외 {in_role - value:.0f}%)"
            )

        print(f"\n[{C.ROLE_KO[role]}]")

        print(" " + "; ".join(parts))

    # =================================================================
    # 9. %p 차이 히트맵
    # =================================================================

    gap_skills = collect_top_skills(gap, 5)

    gap_data = gap[gap_skills]

    # 0을 기준으로 양수(해당 직무에서 더 많이 요구)와 음수(덜 요구)가 대칭이 되도록 색 범위를 맞춤
    limit = float(np.abs(gap_data.values).max())

    save_heatmap(
        gap_data,
        "직무별 고유 기술 (해당 직무 등장률 - 다른 직무 등장률, %p)",
        "등장률 차이 (%p)",
        "pc_a3_gap_heatmap.png",
        "RdBu_r",
        vmin=-limit,
        vmax=limit,
    )

# =====================================================================
# 10. 실행
# =====================================================================

if __name__ == "__main__":
    main()


# =====================================================================
# [구현 핵심]
# =====================================================================

# 해당 직무에서 많이 등장하면서 다른 직무에서는 상대적으로 덜 등장하는 기술을 찾도록 구현함
# a2의 등장률은 직무에서 많이 요구되는 기술로 정의함
# a3의 TF-IDF는 해당 직무를 다른 직무와 구별해 주는 변별 기술로 정의함

# 공고 × 스킬 0/1 매트릭스를 직무별로 평균내어 스킬 등장률을 TF로 사용
# TF : 해당 직무의 전체 공고 중 특정 기술이 등장한 비율

# 몇 공고에서 우연히 등장한 기술의 영향을 줄이기 위한 기준이 필요하다고 판단함
# 등장률이 5% 이상인 직무만 해당 기술이 실제로 등장한 것으로 설정

# 여러 직무에서 흔한 기술은 낮은 가중치, 일부 직무에 집중된 기술은 높은 가중치를 부여함
# +1 스무딩으로 0에 의한 계산 문제를 방지하고 IDF가 완전히 0이 되는 것을 막도록 작성함

# TF × IDF로 최종 TF-IDF를 계산
# 등장률이 높더라도 여러 직무에서 흔한 기술은 상대적으로 가중치가 낮아지는 것을 확인함
# 특정 직무에서 집중적으로 등장하는 기술은 변별력이 높게 평가되는 것을 확인함

# 최종 점검 시 a2와 a3의 Machine Learning 등장률이 38%와 39%로 서로 다르게 출력되는 것을 확인함
# 반올림 시점의 차이가 원인으로 판명되어 a3 출력 부분에 round()를 추가해 통일하였음
# TF-IDF 계산값은 변경하지 않고 출력 형식만 수정함


# =====================================================================
# [수정 사항]
# =====================================================================

# TF-IDF의 문서 단위가 공고가 아니라 직무 5개라서 IDF가 가질 수 있는 값이 5가지뿐임
# 그래서 결과가 등장률 순위를 거의 그대로 따라가고 모든 직무에서 흔한 Python이 상위에 남는 한계가 있었음
# 해당 직무 등장률 - 다른 직무 공고 전체의 등장률(%p)을 직무 고유 기술로 추가함
# 기존 TF-IDF 계산과 산출물은 비교를 위해 그대로 유지함
# 새 산출물은 models/distinctive_gap_by_role.csv, outputs/figures/pc_a3_gap_heatmap.png임
# 히트맵 저장과 상위 기술 모으기는 함수로 분리해 TF-IDF와 %p 차이가 같은 코드를 사용함
