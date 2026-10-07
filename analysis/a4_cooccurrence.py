import itertools

import matplotlib.pyplot as plt

# 관계 데이터를 네트워크 형태의 그래프로 시각화하기 위해 import
import networkx as nx
import pandas as pd

import _common as C


# =====================================================================
# 1. 공동출현 분석 실행
# =====================================================================


def main():

    # DB 전체 공고 로드
    df = C.load_jobs()

    # 공고 × 스킬 0/1 매트릭스
    mat, _ = C.build_skill_matrix(df)

    # 90개 스킬 이름만 저장
    skill_cols = [column for column in mat.columns if column != "role"]

    # =================================================================
    # 2. 공고 × 스킬 행렬 준비
    # =================================================================

    # 공고 × 스킬 0/1 값만 추출
    X = mat[skill_cols].values

    # 각 스킬이 등장한 전체 공고 수
    colsum = X.sum(axis=0)

    # =================================================================
    # 3. 희귀 스킬 제거
    # =================================================================

    # enumerate()로 스킬 이름에 인덱스 번호를 붙여줌
    # 최소 20개 이상의 공고에서 등장한 스킬만 사용
    keep = [i for i, skill in enumerate(skill_cols) if colsum[i] >= 20]

    # keep에 저장한 스킬 인덱스 번호를 이용해 다시 실제 스킬 이름을 가져옴
    names = [skill_cols[i] for i in keep]

    # 모든 채용 공고 그대로 유지(724개 공고)
    # 20개 이상 공고에서 등장한 스킬열만 남김(필터를 통과한 스킬)
    Xk = X[:, keep]

    # =================================================================
    # 4. 스킬 공동출현 행렬
    # =================================================================

    # (스킬 × 공고) @ (공고 × 스킬)
    # co = 스킬 × 스킬
    # (a, b)는 두 스킬이 함께 등장한 공고 수
    # 대각선에 놓이는 (a, a)는 해당 스킬 자체의 등장 공고 수
    co = Xk.T @ Xk

    # =================================================================
    # 5. Jaccard 유사도 계산
    # =================================================================

    rows = []

    for a, b in itertools.combinations(
        range(len(names)),
        2,
    ):
        # 두 기술이 함께 나온 공고 수 = 교집합
        inter = co[a, b]

        if inter == 0:
            continue

        # A 또는 B가 나온 공고 수 = 합집합
        union = co[a, a] + co[b, b] - inter

        jac = inter / union if union else 0

        rows.append(
            (
                names[a],
                names[b],
                int(inter),
                round(jac, 3),
            )
        )

    # =================================================================
    # 6. 공동출현 결과 저장
    # =================================================================

    cooc = pd.DataFrame(
        rows,
        columns=[
            "skill_a",
            "skill_b",
            "co_count",
            "jaccard",
        ],
    )

    cooc = cooc.sort_values(
        "jaccard",
        ascending=False,
    ).reset_index(drop=True)

    model_dir = C.ROOT / "models"

    model_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    cooc.to_csv(
        model_dir / "skill_cooccurrence.csv",
        index=False,
        encoding="utf-8",
    )

    # =================================================================
    # 7. 주요 공동출현 결과 출력
    # =================================================================

    C.rule("a4 — 함께 요구되는 기술 쌍")

    print("\n[동시빈도 TOP 12] (같은 공고에 함께 등장한 횟수)")

    top_count = cooc.sort_values(
        "co_count",
        ascending=False,
    ).head(12)

    for _, row in top_count.iterrows():
        print(
            f"{row['skill_a']} + {row['skill_b']}: "
            f"{int(row['co_count'])}회 "
            f"(Jaccard {row['jaccard']:.3f})"
        )

    print("\n[Jaccard TOP 12] (인기 편향 보정 — 진짜 '세트'로 붙어다니는 조합)")

    for _, row in cooc.head(12).iterrows():
        print(
            f"{row['skill_a']} + {row['skill_b']}: "
            f"Jaccard {row['jaccard']:.3f} "
            f"({int(row['co_count'])}회)"
        )

    # =================================================================
    # 8. 각 기술의 주 요구 직무 계산
    # =================================================================

    tf = mat.groupby("role")[skill_cols].mean().reindex(C.ROLE_ORDER)

    dom_role = {skill: tf[skill].idxmax() for skill in names}

    # =================================================================
    # 9. 네트워크 그래프 생성
    # =================================================================

    # Jaccard 0.2 이상인 상위 45개 조합만 사용
    top_edges = cooc[cooc["jaccard"] >= 0.20].head(45)

    G = nx.Graph()

    for _, row in top_edges.iterrows():
        G.add_edge(
            row["skill_a"],
            row["skill_b"],
            weight=row["jaccard"],
        )

    # 연결이 없는 노드 제거
    G.remove_nodes_from([node for node in G.nodes if G.degree(node) == 0])

    # =================================================================
    # 10. 네트워크 시각화
    # =================================================================

    fig, ax = plt.subplots(
        figsize=(14, 10),
    )

    pos = nx.spring_layout(
        G,
        seed=42,
    )

    role_index = {role: i for i, role in enumerate(C.ROLE_ORDER)}

    node_colors = [role_index[dom_role[node]] for node in G.nodes]

    node_sizes = [int(colsum[skill_cols.index(node)]) * 8 for node in G.nodes]

    edge_widths = [G[u][v]["weight"] * 6 for u, v in G.edges]

    nx.draw_networkx(
        G,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        width=edge_widths,
        cmap=plt.cm.Set2,
        font_family=plt.rcParams["font.family"],
        font_size=9,
        edge_color="gray",
        alpha=0.85,
    )

    ax.set_title("기술 공동출현 네트워크 (Jaccard ≥ 0.2)")

    ax.axis("off")

    plt.tight_layout()

    # =================================================================
    # 11. 네트워크 그래프 저장
    # =================================================================

    figure_dir = C.ROOT / "outputs" / "figures"

    figure_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.savefig(
        figure_dir / "pc_a4_network.png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


# =====================================================================
# 12. 실행
# =====================================================================

if __name__ == "__main__":
    main()


# ========================================================================
# a4 — 함께 요구되는 기술 쌍
# ========================================================================

# [동시빈도 TOP 12] (같은 공고에 함께 등장한 횟수)
# TypeScript + React: 184회 (Jaccard 0.692)
# Python + AWS: 149회 (Jaccard 0.320)
# AWS + CI/CD: 135회 (Jaccard 0.372)
# React + Next.js: 128회 (Jaccard 0.516)
# Python + SQL: 128회 (Jaccard 0.348)
# AWS + Kubernetes: 124회 (Jaccard 0.341)
# React + Vue.js: 123회 (Jaccard 0.370)
# Python + LLM: 114회 (Jaccard 0.280)
# TypeScript + Next.js: 112회 (Jaccard 0.475)
# AWS + Docker: 110회 (Jaccard 0.311)
# TypeScript + Vue.js: 107회 (Jaccard 0.334)
# Docker + Kubernetes: 102회 (Jaccard 0.395)

# [Jaccard TOP 12] (인기 편향 보정 — 진짜 '세트'로 붙어다니는 조합)
# Android + iOS: Jaccard 0.815 (22회)
# TypeScript + React: Jaccard 0.692 (184회)
# HTML + CSS: Jaccard 0.536 (37회)
# Jira + Slack: Jaccard 0.529 (36회)
# React + Next.js: Jaccard 0.516 (128회)
# GitHub Actions + Git: Jaccard 0.483 (69회)
# Spring + Spring Boot: Jaccard 0.475 (38회)
# TypeScript + Next.js: Jaccard 0.475 (112회)
# Jira + Confluence: Jaccard 0.463 (25회)
# Java + Spring: Jaccard 0.459 (56회)
# PyTorch + TensorFlow: Jaccard 0.455 (20회)
# PyTorch + Deep Learning: Jaccard 0.410 (25회)


# =====================================================================

# 공고 × 스킬 0/1 매트릭스를 이용해 한 공고에서 함께 요구되는 기술 조합을 분석함
# 단순 개별 기술의 등장률이 아닌 실제로 같이 요구되는 기술 스택을 찾을 수 있도록 작성함

# 등장 횟수가 적은 희귀 기술은 몇 번의 공동출현만으로도 Jaccard가 과도하게 높아지는 것을 확인함
# 잡음을 줄이기 위해 20개 이상 공고에서 등장한 기술만 분석에 사용하였음

# 공고 × 스킬 0/1 행렬 X에 대해 XᵀX를 계산하여 스킬 × 스킬 공동출현 행렬을 생성함
# 행렬 곱을 이용해 모든 기술 쌍의 공동 출현 횟수를 한 번에 계산함

# 모든 기술을 2개씩 조합하여 교집합과 합집합을 구하고 Jaccard 유사도를 계산함
# Jaccard = 두 기술이 함께 나온 공고 수 / 두 기술 중 하나라도 나온 공고 수
# 단순 동시빈도에 존재하는 인기 기술 편향을 보정함

# 실제 데이터에서 Python + AWS는 149회로 동시빈도 2위였지만 Jaccard는 0.320이었음
# 반면 Android + iOS는 공동출현이 22회뿐이지만 Jaccard 0.815로 가장 강한 결합을 보임
# TypeScript + React는 184회 / Jaccard 0.692로 빈도와 결합도가 모두 높은 대표적인 스택으로 나타남

# Jaccard 0.2 이상인 상위 45개 기술 조합을 이용해 공동출현 네트워크를 생성함
# 기술을 노드, 기술 간 공동출현 관계를 엣지로 표현하고
# 노드 크기는 등장 공고 수, 노드 색은 해당 기술을 가장 많이 요구하는 직무를 나타냄
