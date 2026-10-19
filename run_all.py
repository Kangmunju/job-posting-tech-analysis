import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path


# =====================================================================
# 1. 경로와 실행 순서 설정
# =====================================================================

ROOT = Path(__file__).resolve().parent

LOG_DIR = ROOT / "outputs" / "logs"

# (실행할 파일, 로그 파일 이름)
#
# 앞에서부터 순서대로 실행하고, 하나라도 실패하면 바로 멈춤
# 자체 테스트를 먼저 실행해 기술 사전이나 분류 규칙에 문제가 있으면 분석 전에 확인함
# collect_wanted.py는 원티드 API를 호출하므로 포함하지 않음 (수집은 따로 실행)
STEPS = [
    ("src/skills.py", "skills.txt"),
    ("src/preprocess.py", "preprocess.txt"),
    ("src/build_db.py", "build_db.txt"),
    ("src/classify.py", "classify.txt"),
    ("analysis/_common.py", "common.txt"),
    ("analysis/a1_eda.py", "a1_eda.txt"),
    ("analysis/a2_skill_frequency.py", "a2_skill_frequency.txt"),
    ("analysis/a3_tfidf_distinctive.py", "a3_tfidf_distinctive.txt"),
    ("analysis/a4_cooccurrence.py", "a4_cooccurrence.txt"),
    ("analysis/a5_insights.py", "a5_insights.txt"),
]

# 실행 환경 로그에 버전을 기록할 패키지
PACKAGES = [
    "pandas",
    "numpy",
    "matplotlib",
    "requests",
    "networkx",
    "wordcloud",
    "scipy",
]


# =====================================================================
# 2. 로그 저장
# =====================================================================


def clean_log_text(text: str) -> str:
    """
    로그에 들어간 내 컴퓨터의 절대 경로를 상대 경로로 바꿔 어디서 실행해도 같은 로그가 되도록 한다.
    """

    root_text = str(ROOT)

    cleaned = text.replace(root_text, ".")
    cleaned = cleaned.replace(root_text.replace("\\", "/"), ".")

    return cleaned


def save_log(file_name: str, text: str):
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 운영체제와 관계없이 줄바꿈을 통일해 저장
    with open(LOG_DIR / file_name, "w", encoding="utf-8", newline="\n") as file:
        file.write(clean_log_text(text))


def save_environment_log():
    """
    재현에 필요한 Python과 패키지 버전을 기록한다.
    """

    lines = []

    lines.append(f"Python {sys.version.split()[0]}")
    lines.append("")

    for name in PACKAGES:
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            version = "설치되어 있지 않음"

        lines.append(f"{name}=={version}")

    save_log("environment.txt", "\n".join(lines) + "\n")


# =====================================================================
# 3. 파일 하나 실행
# =====================================================================


def run_step(script: str, log_name: str) -> int:
    """
    파일 하나를 실행하고 출력 내용을 로그 파일로 저장한다. 종료 코드를 반환한다.
    """

    env = os.environ.copy()

    # 하위 프로세스의 출력이 한글로 깨지지 않도록 UTF-8로 고정
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, str(ROOT / script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    log_text = result.stdout

    # 경고나 오류 메시지가 있으면 로그 아래에 함께 남김
    if result.stderr.strip():
        log_text += "\n[stderr]\n" + result.stderr

    save_log(log_name, log_text)

    if result.returncode != 0:
        print(result.stderr)

    return result.returncode


# =====================================================================
# 4. 전체 실행
# =====================================================================


def main():
    print("=" * 64)
    print("전체 분석 실행")
    print("=" * 64)

    save_environment_log()

    total = len(STEPS)

    for number, (script, log_name) in enumerate(STEPS, start=1):
        print(f"[{number}/{total}] {script} ...", flush=True)

        return_code = run_step(script, log_name)

        if return_code != 0:
            print(f"실패: {script} (종료 코드 {return_code})")
            print(f"로그: outputs/logs/{log_name}")
            sys.exit(1)

    print()
    print(f"모든 단계가 끝났습니다. 로그: {LOG_DIR}")


if __name__ == "__main__":
    main()


# =====================================================================
# [구현 핵심]
# =====================================================================

# 자체 테스트, DB 적재, 직무 분류, 분석 5개를 정해진 순서대로 한 번에 실행함
# 각 파일의 출력은 outputs/logs/에 파일로 저장함 (코드 아래 주석에 남기면 코드가 바뀔 때 낡아지기 때문)
# 로그에 들어간 내 컴퓨터의 절대 경로는 상대 경로로 바꿔 저장함
# 실행 환경(Python과 패키지 버전)은 outputs/logs/environment.txt에 기록함

# 하나라도 실패하면 이후 단계를 실행하지 않고 멈춤
# 자체 테스트를 가장 먼저 실행해 기술 사전이나 분류 규칙의 문제를 분석 전에 발견하도록 함
# 원티드 API를 호출하는 collect_wanted.py는 포함하지 않았고, 수집은 따로 실행해야 함
