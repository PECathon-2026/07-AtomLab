
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def create_mission(prompt: str) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "prompt": prompt,
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tasks": [],
        "current_task": None,
        "files_changed": [],
        "test_results": [],
        "agent_logs": [],
        "repair_attempts": 0,
        "final_report": None,
        "error": None,
    }


def add_log(
    mission: dict[str, Any],
    agent: str,
    message: str,
    level: str = "info",
) -> None:
    mission["agent_logs"].append(
        {
            "time": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "message": message,
            "level": level,
        }
    )


def update_status(
    mission: dict[str, Any],
    status: str,
) -> None:
    mission["status"] = status