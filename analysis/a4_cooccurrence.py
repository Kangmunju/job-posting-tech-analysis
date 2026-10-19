import itertools

import matplotlib.pyplot as plt

# 글자에 흰 테두리를 두르고, 직무별 색 범례를 만들기 위해 import
from matplotlib import patheffects
from matplotlib.patches import Patch

# 관계 데이터를 네트워크 형태의 그래프로 시각화하기 위해 import
import networkx as nx
import pandas as pd

import _common as C


# =====================================================================
# 0. 네트워크 그림 그리기 함수
# =====================================================================

# 직무별 색 (직무별 등장률 그룹 막대그래프와 같은 색을 사용)
ROLE_COLORS = {
    "data_analyst": "#1f77b4",
    "data_engineer": "#ff7f0e",
    "data_scientist": "#2ca02c",
    "backend": "#d62728",
    "frontend": "#9467bd",
}

# 이 값 이상의 Jaccard를 가진 연결선에는 수치를 표시함
LABEL_JACCARD = 0.5


def spread_nodes(pos, min_x, min_y, rounds=300):
    """
    글자가 서로 겹치지 않도록 가까운 노드를 서로 밀어낸다.
    가로로 긴 글자를 고려해 가로(min_x)와 세로(min_y)의 최소 간격을 따로 둔다.
    """

    names = list(pos.keys())

    for _ in range(rounds):
        moved = False

        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a = names[i]
                b = names[j]

                dx = pos[b][0] - pos[a][0]
                dy = pos[b][1] - pos[a][1]

                # 두 노드 사이 거리를 최소 간격 기준으로 환산 (1보다 작으면 겹침)
                gap = ((dx / min_x) ** 2 + (dy / min_y) ** 2) ** 0.5

                if gap >= 1:
                    continue

                # 위치가 완전히 같으면 가로로 조금 떼어 놓고 시작
                if gap == 0:
                    dx = 0.01
                    dy = 0.0
                    gap = dx / min_x

                # 간격이 정확히 1이 되도록 두 노드를 같은 거리만큼 반대쪽으로 이동
                shift_x = dx / gap - dx
                shift_y = dy / gap - dy

                pos[a][0] -= shift_x / 2
                pos[a][1] -= shift_y / 2
                pos[b][0] += shift_x / 2
                pos[b][1] += shift_y / 2

                moved = True

        if not moved:
            break

    return pos


def draw_component(ax, sub, dom_role, skill_counts):
    """
    서로 연결된 기술 묶음 하나를 ax에 그린다.
    노드 크기는 기술이 등장한 공고 수, 노드 색은 그 기술을 가장 많이 요구하는 직무,
    선 굵기는 Jaccard 유사도를 나타낸다.
    """

    # 같은 묶음 안에서 노드를 고르게 펼쳐 배치함 (연결 거리 dist가 짧을수록 가깝게 놓임)
    # 계산 방식에 무작위가 없어 항상 같은 그림이 나옴
    pos = nx.kamada_kawai_layout(sub, weight="dist")

    # 칸이 가로로 넓은 만큼 노드 배치도 가로로 넓힘 (최대 2배)
    box = ax.get_position()
    fig_width, fig_height = ax.figure.get_size_inches()
    ratio = (box.width * fig_width) / (box.height * fig_height)
    ratio = max(1.0, min(2.0, ratio))

    for node in pos:
        pos[node] = [pos[node][0] * ratio, pos[node][1]]

    # 겹치는 글자를 밀어내 간격을 확보함
    pos = spread_nodes(pos, min_x=0.75, min_y=0.32)

    node_colors = []
    node_sizes = []

    for node in sub.nodes:
        node_colors.append(ROLE_COLORS[dom_role[node]])
        node_sizes.append(300 + skill_counts[node] * 2.5)

    edge_widths = []

    for u, v in sub.edges:
        edge_widths.append(1 + sub[u][v]["weight"] * 7)

    nx.draw_networkx_edges(
        sub,
        pos,
        ax=ax,
        width=edge_widths,
        edge_color="#8a8a8a",
        alpha=0.7,
    )

    nx.draw_networkx_nodes(
        sub,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.92,
        linewidths=1.5,
        edgecolors="white",
    )

    labels = nx.draw_networkx_labels(
        sub,
        pos,
        ax=ax,
        font_size=12,
        font_weight="bold",
        font_family=plt.rcParams["font.family"],
        clip_on=False,
    )

    # 노드가 겹쳐도 글자가 읽히도록 흰 테두리를 두름
    for text in labels.values():
        text.set_path_effects([patheffects.withStroke(linewidth=3, foreground="white")])

    # 결합이 강한 연결선에는 Jaccard 수치를 표시
    strong_edges = {}

    for u, v in sub.edges:
        weight = sub[u][v]["weight"]

        if weight >= LABEL_JACCARD:
            strong_edges[(u, v)] = f"{weight:.2f}"

    nx.draw_networkx_edge_labels(
        sub,
        pos,
        edge_labels=strong_edges,
        ax=ax,
        font_size=10,
        font_color="#444444",
        rotate=False,
        bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.85},
    )

    # 노드가 놓인 범위에 여백을 두어 글자가 잘리지 않게 함
    xs = []
    ys = []

    for node in pos:
        xs.append(pos[node][0])
        ys.append(pos[node][1])

    ax.set_xlim(min(xs) - 0.5, max(xs) + 0.5)
    ax.set_ylim(min(ys) - 0.3, max(ys) + 0.3)
    ax.axis("off")


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

    # 모든 채용 공고 그대로 유지(분석 대상 공고 전체)
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
            # 그림에서 두 기술을 놓을 거리 (Jaccard가 높을수록 가깝게, 너무 겹치지 않게 최소 거리를 둠)
            dist=1.4 - row["jaccard"],
        )

    # 연결이 없는 노드 제거
    G.remove_nodes_from([node for node in G.nodes if G.degree(node) == 0])

    # =================================================================
    # 10. 네트워크 시각화
    # =================================================================

    # 노드 크기에 사용할 기술별 등장 공고 수
    skill_counts = {}

    for node in G.nodes:
        skill_counts[node] = int(colsum[skill_cols.index(node)])

    # 서로 연결된 기술 묶음을 큰 순서로 정렬함
    # 연결되지 않은 묶음을 한 그림에 같이 그리면 서로 멀리 흩어지므로, 묶음마다 따로 배치함
    # 큰 묶음 2개는 위쪽 한 줄, 나머지 작은 묶음은 아래쪽 한 줄에 나란히 놓음
    components = sorted(nx.connected_components(G), key=len, reverse=True)

    top_row = components[:2]
    bottom_row = components[2:]

    fig = plt.figure(figsize=(12, 9))

    row_count = 2

    if len(bottom_row) == 0:
        row_count = 1

    grid = fig.add_gridspec(
        row_count,
        1,
        height_ratios=[2.1, 1][:row_count],
        hspace=0.04,
        top=0.82,
        bottom=0.03,
        left=0.02,
        right=0.98,
    )

    top_widths = []

    for comp in top_row:
        top_widths.append(len(comp) + 4)

    top_grid = grid[0].subgridspec(1, len(top_row), width_ratios=top_widths, wspace=0.05)

    panels = []

    for index, comp in enumerate(top_row):
        panels.append((fig.add_subplot(top_grid[0, index]), comp))

    if len(bottom_row) > 0:
        bottom_widths = []

        for comp in bottom_row:
            bottom_widths.append(len(comp) + 2)

        bottom_grid = grid[1].subgridspec(1, len(bottom_row), width_ratios=bottom_widths, wspace=0.05)

        for index, comp in enumerate(bottom_row):
            panels.append((fig.add_subplot(bottom_grid[0, index]), comp))

    for ax, comp in panels:
        # 묶음의 노드를 G에 들어 있는 순서대로 담아 항상 같은 그림이 나오게 함
        # (집합은 실행할 때마다 순회 순서가 달라져 배치 계산의 시작 위치가 바뀜)
        sub = nx.Graph()

        for node in G.nodes:
            if node in comp:
                sub.add_node(node)

        for u, v, data in G.edges(data=True):
            if u in comp and v in comp:
                sub.add_edge(u, v, **data)

        draw_component(ax, sub, dom_role, skill_counts)

    # 제목, 읽는 법, 직무별 색 범례
    fig.suptitle(
        "기술 공동출현 네트워크 (Jaccard ≥ 0.2)",
        fontsize=20,
        fontweight="bold",
        y=0.975,
    )

    fig.text(
        0.5,
        0.925,
        "노드 크기 = 등장 공고 수  ·  선 굵기 = Jaccard 유사도  ·  숫자 = Jaccard 0.5 이상인 조합",
        ha="center",
        fontsize=12,
        color="#555555",
    )

    legend_handles = []

    for role in C.ROLE_ORDER:
        legend_handles.append(Patch(facecolor=ROLE_COLORS[role], label=C.ROLE_KO[role]))

    fig.legend(
        handles=legend_handles,
        title="색 = 그 기술을 가장 많이 요구하는 직무",
        loc="upper center",
        bbox_to_anchor=(0.5, 0.9),
        ncol=len(legend_handles),
        frameon=False,
        fontsize=12,
        title_fontsize=12,
    )

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


# =====================================================================
# [구현 핵심]
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

# 실제 데이터에서 Python + AWS는 144회로 동시빈도 2위였지만 Jaccard는 0.316이었음
# 반면 Android + iOS는 공동출현이 25회뿐이지만 Jaccard 0.926으로 가장 강한 결합을 보임
# TypeScript + React는 154회 / Jaccard 0.733으로 빈도와 결합도가 모두 높은 대표적인 스택으로 나타남

# Jaccard 0.2 이상인 상위 45개 기술 조합을 이용해 공동출현 네트워크를 생성함
# 기술을 노드, 기술 간 공동출현 관계를 엣지로 표현하고
# 노드 크기는 등장 공고 수, 노드 색은 해당 기술을 가장 많이 요구하는 직무를 나타냄


# =====================================================================
# [수정 사항]
# =====================================================================

# 실행 결과를 코드 아래 주석으로 남기면 코드가 바뀔 때 낡은 값이 남으므로 삭제함
# 실행 로그는 run_all.py가 outputs/logs/에 파일로 저장함

# 구현 핵심의 Python + AWS, Android + iOS, TypeScript + React 수치를 재실행 결과에 맞게 갱신함

# 네트워크 그림에서 연결되지 않은 묶음이 화면 전체에 흩어지고 글자가 작고 겹쳐 읽기 어려운 문제를 개선함
# 연결된 기술 묶음마다 따로 배치해 큰 묶음 2개는 위쪽, 작은 묶음은 아래쪽 한 줄에 놓음
# 노드를 고르게 펼치는 배치(Kamada-Kawai)를 쓰고, 글자가 겹치면 서로 밀어내는 간격 조정을 추가함
# 글자는 키우고 흰 테두리를 둘러 겹쳐도 읽히게 했으며, 직무별 색 범례와 읽는 법 설명을 추가함
# Jaccard 0.5 이상인 연결선에는 수치를 표시함
# 노드 순서를 집합이 아닌 G에 들어 있는 순서로 고정해 실행할 때마다 같은 그림이 나오는 것을 확인함
