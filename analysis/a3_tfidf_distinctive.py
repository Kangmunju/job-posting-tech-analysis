# IDF 계산에 필요한 log 계산을 위해 import함
import numpy as np
import matplotlib.pyplot as plt

import _common as C


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
            (f"{skill}(TFIDF {value:.3f}, 등장 {tf.loc[role, skill] * 100:.0f}%)")
            for skill, value in top.items()
        ]

        print(f"\n[{C.ROLE_KO[role]}]")

        print(" " + "; ".join(parts))

    # =================================================================
    # 7. TF-IDF 히트맵
    # =================================================================

    # 각 직무의 상위 변별 기술을 모아 히트맵에 사용할 기술 목록 생성
    heatmap_skills = []

    for role in C.ROLE_ORDER:
        # .index를 사용해 현재 직무의 TF-IDF 상위 5개 기술 이름만 가져옴
        top_skills = tfidf.loc[role].sort_values(ascending=False).head(5).index

        for skill in top_skills:
            if skill not in heatmap_skills:
                heatmap_skills.append(skill)

    # 직무 × 변별 기술 TF-IDF 값
    heatmap_data = tfidf[heatmap_skills]

    fig, ax = plt.subplots(
        figsize=(14, 6),
    )

    image = ax.imshow(
        heatmap_data.values,
        aspect="auto",
        cmap="YlGn",
    )

    ax.set_xticks(range(len(heatmap_skills)))

    ax.set_xticklabels(
        heatmap_skills,
        rotation=45,
        ha="right",
    )

    ax.set_yticks(range(len(C.ROLE_ORDER)))

    ax.set_yticklabels([C.ROLE_KO[role] for role in C.ROLE_ORDER])

    ax.set_title("직무별 변별 기술 TF-IDF")

    ax.set_xlabel("기술")
    ax.set_ylabel("직무")

    fig.colorbar(
        image,
        ax=ax,
        label="TF-IDF",
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
        figure_dir / "pc_a3_tfidf_heatmap.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


# =====================================================================
# 9. 실행
# =====================================================================

if __name__ == "__main__":
    main()


# ========================================================================
# a3 — 직무를 '변별'하는 기술 TOP (TF-IDF: 그 직무에서 유독 두드러짐)
# ========================================================================

# [데이터 분석가]
#  SQL(TFIDF 0.982, 등장 83%); Tableau(TFIDF 0.887, 등장 42%); Python(TFIDF 0.716, 등장 61%); A/B Test(TFIDF 0.515, 등장 37%); BigQuery(TFIDF 0.405, 등장 24%); Looker(TFIDF 0.266, 등장 13%); Power BI(TFIDF 0.266, 등장 13%); R(TFIDF 0.236, 등장 11%)

# [데이터 엔지니어]
#  Python(TFIDF 0.818, 등장 69%); Kafka(TFIDF 0.757, 등장 45%); SQL(TFIDF 0.742, 등장 63%); Airflow(TFIDF 0.718, 등장 51%); Spark(TFIDF 0.673, 등장 48%); AWS(TFIDF 0.574, 등장 57%); dbt(TFIDF 0.522, 등장 31%); Flink(TFIDF 0.424, 등장 20%)

# [데이터 사이언티스트]
#  Python(TFIDF 0.872, 등장 74%); Deep Learning(TFIDF 0.671, 등장 32%); PyTorch(TFIDF 0.619, 등장 30%); LLM(TFIDF 0.557, 등장 56%); Machine Learning(TFIDF 0.541, 등장 39%); RAG(TFIDF 0.392, 등장 28%); Computer Vision(TFIDF 0.327, 등장 16%); NLP(TFIDF 0.275, 등장 13%)

# [백엔드]
#  AWS(TFIDF 0.582, 등장 58%); Kubernetes(TFIDF 0.569, 등장 48%); CI/CD(TFIDF 0.536, 등장 45%); Python(TFIDF 0.474, 등장 40%); Docker(TFIDF 0.449, 등장 38%); React(TFIDF 0.426, 등장 30%); Terraform(TFIDF 0.425, 등장 25%); Java(TFIDF 0.425, 등장 25%)

# [프론트엔드]
#  React(TFIDF 1.340, 등장 95%); TypeScript(TFIDF 1.171, 등장 83%); Next.js(TFIDF 0.914, 등장 54%); JavaScript(TFIDF 0.655, 등장 39%); Vue.js(TFIDF 0.587, 등장 59%); CSS(TFIDF 0.564, 등장 33%); HTML(TFIDF 0.420, 등장 20%); React Native(TFIDF 0.406, 등장 24%)


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
# 특정 직무에서 집중적으로 등장하는 기술은 변벽력이 높게 평가되는 것을 확인함
