
from pathlib import Path

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}


def get_repo_path(root: str, relative_path: str = "") -> Path:
    repo = Path(root).resolve()
    target = (repo / relative_path).resolve()

    if target != repo and repo not in target.parents:
        raise ValueError("Path is outside the repository.")

    return target


def list_files(root: str, limit: int = 200) -> list[str]:
    repo = get_repo_path(root)
    files = []

    for path in repo.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue

        if path.is_file():
            files.append(str(path.relative_to(repo)))

        if len(files) >= limit:
            break

    return sorted(files)


def read_file(root: str, relative_path: str) -> str:
    path = get_repo_path(root, relative_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")

    return path.read_text(encoding="utf-8", errors="replace")


def search_files(
    root: str,
    search_text: str,
    limit: int = 50,
) -> list[dict[str, str]]:
    results = []

    for relative_path in list_files(root):
        path = get_repo_path(root, relative_path)

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            if search_text.lower() in line.lower():
                results.append(
                    {
                        "file": relative_path,
                        "line": str(line_number),
                        "text": line.strip(),
                    }
                )

                if len(results) >= limit:
                    return results

    return results




import subprocess
import sys


def write_file(
    root: str,
    relative_path: str,
    content: str,
) -> None:
    path = get_repo_path(root, relative_path)

    if path.is_dir():
        raise IsADirectoryError(
            f"Cannot write to a directory: {relative_path}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_tests(root: str) -> dict:
    repo = get_repo_path(root)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        check=False,
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
    )

    return {
        "passed": result.returncode == 0,
        "exit_code": result.returncode,
        "output": result.stdout + result.stderr,
    }



def scout_repository(root: str) -> dict:
    files = list_files(root)

    test_files = [
        path
        for path in files
        if "test" in Path(path).name.lower()
    ]

    return {
        "files": files,
        "test_files": test_files,
        "file_count": len(files),
        "test_count": len(test_files),
    }
