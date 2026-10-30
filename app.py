from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED
import shutil
import uuid

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.orchestrator import run_mission
from core.state import create_mission

app = FastAPI(title="DevPilot")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:7b"

missions = {}
mission_dirs = {}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_FILES = 50


@app.get("/api/health")
def health():
    return {"status": "DevPilot backend is running", "model": OLLAMA_MODEL}


@app.get("/api/test-ai")
async def test_ai():
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": "Reply with exactly: DevPilot local AI connection successful!"}],
                    "stream": False,
                    "options": {"temperature": 0},
                },
            )
        response.raise_for_status()
        return {"status": "success", "model": OLLAMA_MODEL, "reply": response.json()["message"]["content"]}
    except httpx.HTTPStatusError as error:
        raise HTTPException(error.response.status_code, "Ollama returned an error. Check that the model is installed.")
    except httpx.RequestError:
        raise HTTPException(502, "Could not connect to Ollama. Make sure Ollama is running.")


def safe_relative_path(filename: str) -> Path:
    # Normalize Windows separators and reject absolute paths / traversal.
    normalized = filename.replace("\\", "/").strip("/")
    parts = Path(normalized).parts
    if not normalized or Path(normalized).is_absolute() or any(part in ("..", "") for part in parts):
        raise HTTPException(400, f"Unsafe file path: {filename}")
    return Path(*parts)


async def execute_mission(mission_id: str, root: Path):
    mission = missions[mission_id]
    try:
        await run_mission(mission, str(root))
    except Exception as exc:
        mission["status"] = "failed"
        mission.setdefault("logs", []).append({"agent": "SYSTEM", "message": f"Mission error: {exc}"})
    finally:
        # Package the resulting workspace, even if the agent reports a failure.
        archive = root.parent / f"{mission_id}_result.zip"
        try:
            with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
                for path in root.rglob("*"):
                    if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts and ".venv" not in path.parts:
                        zip_file.write(path, path.relative_to(root))
            mission["download_ready"] = archive.exists()
            mission["download_name"] = f"devpilot-{mission_id}.zip"
            mission_dirs[mission_id]["archive"] = archive
        except Exception as exc:
            mission.setdefault("logs", []).append({"agent": "SYSTEM", "message": f"Could not package result: {exc}"})


@app.post("/api/missions")
async def create_new_mission(
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    files: list[UploadFile] = File(default=[]),
):
    if not prompt.strip():
        raise HTTPException(400, "Please provide a coding request.")
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Please upload no more than {MAX_FILES} files.")

    work_root = Path(TemporaryDirectory(prefix="devpilot_").name)
    # Keep the temporary workspace alive for the duration of the mission.
    work_root.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    try:
        for upload in files:
            relative = safe_relative_path(upload.filename or "")
            destination = work_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = await upload.read()
            total_bytes += len(content)
            if total_bytes > MAX_UPLOAD_BYTES:
                raise HTTPException(413, "Combined upload size must be 20 MB or less.")
            destination.write_bytes(content)
    except Exception:
        shutil.rmtree(work_root, ignore_errors=True)
        raise
    finally:
        for upload in files:
            await upload.close()

    if not files:
        # Empty uploads use the built-in demo workspace.
        demo = BASE_DIR / "demo_repo"
        if not demo.exists():
            shutil.rmtree(work_root, ignore_errors=True)
            raise HTTPException(400, "Attach project files to start a mission.")
        shutil.copytree(demo, work_root, dirs_exist_ok=True)

    mission = create_mission(prompt.strip())
    mission["logs"] = mission.get("logs", [])
    missions[mission["id"]] = mission
    mission_dirs[mission["id"]] = {"root": work_root}

    background_tasks.add_task(execute_mission, mission["id"], work_root)
    return {"id": mission["id"], "status": mission["status"], "prompt": mission["prompt"]}


@app.get("/api/missions/{mission_id}")
def get_mission(mission_id: str):
    mission = missions.get(mission_id)
    if mission is None:
        raise HTTPException(404, "Mission not found.")
    return mission


@app.get("/api/missions/{mission_id}/download")
def download_result(mission_id: str):
    mission = missions.get(mission_id)
    archive = mission_dirs.get(mission_id, {}).get("archive")
    if mission is None:
        raise HTTPException(404, "Mission not found.")
    if not archive or not archive.exists():
        raise HTTPException(409, "The result archive is not ready yet.")
    return FileResponse(archive, media_type="application/zip", filename=mission.get("download_name", "devpilot-result.zip"))


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
