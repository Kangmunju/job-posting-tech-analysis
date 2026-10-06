import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

import _common as C


# =====================================================================
# 1. 직무별 스킬 등장률 분석
# =====================================================================


def main():

    # 전체 공고 로드
    df = C.load_jobs()

    # 공고 × 스킬 0/1 매트릭스
    mat, sub = C.build_skill_matrix(df)

    skill_cols = [column for column in mat.columns if column != "role"]

    # =================================================================
    # 2. 직무별 스킬 등장률 계산
    # =================================================================

    # 직무 × 스킬 등장률(%)
    # 0/1 매트릭스이므로 직무별 평균 = 해당 스킬이 등장한 공고의 비율
    freq = mat.groupby("role")[skill_cols].mean().mul(100).round(1)

    # 분석 직무 순서로 정렬
    freq = freq.reindex(C.ROLE_ORDER)

    # =================================================================
    # 3. 등장률 CSV 저장
    # =================================================================

    model_dir = C.ROOT / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    freq.T.to_csv(
        model_dir / "skill_freq_by_role.csv",
        encoding="utf-8",
    )

    # =================================================================
    # 4. 직무별 상위 요구 기술 출력
    # =================================================================

    C.rule("a2 — 직무별 상위 요구 기술 (등장률 = 그 직무 공고 중 %)")

    for role in C.ROLE_ORDER:
        top = freq.loc[role].sort_values(ascending=False).head(12)

        n = (mat["role"] == role).sum()

        print(f"\n[{C.ROLE_KO[role]}] n={n:,}")

        print(" " + ", ".join(f"{skill} {value:.0f}%" for skill, value in top.items()))

    # =================================================================
    # 5. 전체 상위 기술 그룹 막대그래프
    # =================================================================

    figure_dir = C.ROOT / "outputs" / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    # 5개 직무 전체에서 평균 등장률이 높은 기술 12개
    top_skills = freq.mean(axis=0).sort_values(ascending=False).head(12).index

    plot_df = freq[top_skills].T.rename(columns=C.ROLE_KO)

    ax = plot_df.plot(
        kind="bar",
        figsize=(14, 7),
    )

    ax.set_title("직무별 상위 요구 기술 등장률")
    ax.set_xlabel("기술")
    ax.set_ylabel("등장률 (%)")

    plt.xticks(
        rotation=45,
        ha="right",
    )

    plt.tight_layout()

    plt.savefig(
        figure_dir / "pc_a2_grouped_bar.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    # =================================================================
    # 6. 직무별 워드클라우드
    # =================================================================

    try:
        from wordcloud import WordCloud

        font_path = None

        for font in fm.fontManager.ttflist:
            if font.name in (
                "AppleGothic",
                "NanumGothic",
                "Malgun Gothic",
            ):
                font_path = font.fname
                break

        if font_path is None:
            print("\n[WARN] 워드클라우드용 한글 폰트를 찾지 못했습니다.")

        else:
            fig, axes = plt.subplots(
                2,
                3,
                figsize=(15, 9),
            )

            axes = axes.flatten()

            for index, role in enumerate(C.ROLE_ORDER):
                freqs = freq.loc[role].loc[lambda x: x > 0].to_dict()

                wc = WordCloud(
                    font_path=font_path,
                    background_color="white",
                    colormap="viridis",
                    width=800,
                    height=500,
                ).generate_from_frequencies(freqs)

                axes[index].imshow(
                    wc,
                    interpolation="bilinear",
                )

                axes[index].set_title(C.ROLE_KO[role])

                axes[index].axis("off")

            # 5개 직무이므로 남는 마지막 칸 제거
            axes[-1].axis("off")

            plt.tight_layout()

            plt.savefig(
                figure_dir / "pc_a2_wordcloud.png",
                dpi=150,
                bbox_inches="tight",
            )

            plt.close()

    except ImportError:
        print("\n[WARN] wordcloud가 설치되지 않아 워드클라우드를 건너뜁니다.")


# =====================================================================
# 7. 실행
# =====================================================================

if __name__ == "__main__":
    main()


# ========================================================================
# a2 — 직무별 상위 요구 기술 (등장률 = 그 직무 공고 중 %)
# ========================================================================

# [데이터 분석가] n=71
#  SQL 83%, Python 61%, Tableau 42%, A/B Test 37%, BigQuery 24%, Airflow 16%, Looker 13%, Power BI 13%, R 11%, dbt 11%, Vue.js 11%, AWS 10%

# [데이터 엔지니어] n=94
#  Python 69%, SQL 63%, AWS 57%, Airflow 51%, Spark 48%, Kafka 45%, Kubernetes 33%, dbt 31%, LLM 30%, Snowflake 24%, Java 22%, GCP 22%

# [데이터 사이언티스트] n=122
#  Python 74%, LLM 56%, Machine Learning 38%, Deep Learning 32%, PyTorch 30%, RAG 28%, AWS 25%, SQL 23%, GCP 16%, Docker 16%, Computer Vision 16%, Vue.js 15%

# [백엔드] n=287
#  AWS 58%, Kubernetes 48%, CI/CD 45%, Python 40%, Docker 38%, Vue.js 32%, React 30%, Git 30%, TypeScript 26%, LLM 25%, Java 25%, Terraform 25%

# [프론트엔드] n=150
#  React 95%, TypeScript 83%, Vue.js 59%, Next.js 54%, JavaScript 39%, CSS 33%, CI/CD 31%, Git 26%, AWS 25%, REST API 25%, React Native 24%, HTML 20%


# =====================================================================

# 공고 × 스킬 0/1 매트릭스를 직무별로 묶어 평균 × 100으로 스킬 등장률(%)을 계산함
# 직무별 공고 수가 다르므로 절대빈도가 아닌 등장률을 사용해 표본 크기의 영향을 줄임

# 직무별 상귀 12개 요구 기술을 추출함
# 전체 등장률 결과를 skill_freq_by_role.csv로 저장함
# 전체 상위 기술의 직무별 등장률을 그룹 막대그래프를 생성해 비교함
# 직무별 등장률을 가중치로 사용해 워드클라우드를 생성함
