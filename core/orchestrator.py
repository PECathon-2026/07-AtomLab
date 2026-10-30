import asyncio
import json
import re

from agents.agents import (
    ask_ai,
    edit_code,
    review_code,
    review_test_results,
)
from core.state import add_log, update_status
from tools.repo_tools import (
    list_files,
    read_file,
    run_tests,
    scout_repository,
    write_file,
)


PLANNER_PROMPT = """
You are the Planner of DevPilot, a multi-agent coding system.

Break the user's request into 1 to 3 small, ordered tasks.
For simple requests, create exactly 1 task.

Keep tasks concise.
Do not create research or documentation tasks unless requested.
Do not invent files.
Do not write code.

Each task must contain:
- A unique integer ID.
- A short title.
- A clear description.
- Acceptance criteria.
- Relevant files, if known.

Return ONLY valid JSON in this format:

{
  "tasks": [
    {
      "id": 1,
      "title": "Short title",
      "description": "What needs to be done",
      "acceptance_criteria": ["Criterion one"],
      "relevant_files": ["file.py"]
    }
  ]
}
"""


def parse_plan_response(response: str) -> dict:
    """Parse JSON returned by the Planner."""

    if not response or not response.strip():
        raise ValueError("The Planner returned an empty response.")

    response = response.strip()

    # Remove Markdown code fences.
    response = re.sub(
        r"^```(?:json)?\s*",
        "",
        response,
        flags=re.IGNORECASE,
    )

    response = re.sub(
        r"\s*```$",
        "",
        response,
    )

    # Try parsing the complete response.
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Extract JSON if extra text surrounds it.
    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            "The Planner did not return a valid JSON object."
        )

    json_text = response[start:end + 1]

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"The Planner returned invalid JSON: {error}"
        )


def create_fallback_plan(
    prompt: str,
    repository_files: list[str],
) -> list[dict]:
    """
    Create a simple plan if the AI Planner is unavailable.

    This keeps the demo moving without waiting indefinitely
    for the model to generate a plan.
    """

    prompt_lower = prompt.lower()

    # Find files whose names relate to the user's request.
    matching_files = []

    for file_path in repository_files:
        file_name = file_path.lower()

        if any(
            word in file_name
            for word in [
                "validator",
                "email",
                "validation",
            ]
        ):
            matching_files.append(file_path)

    # For the email-validator demo, prefer validator.py.
    if "email" in prompt_lower and matching_files:
        matching_files.sort(
            key=lambda path: (
                "validator.py" not in path.lower(),
                len(path),
            )
        )

    # If no matching file was found, use the first repository file.
    if not matching_files and repository_files:
        matching_files = [repository_files[0]]

    return [
        {
            "id": 1,
            "title": "Implement the requested code change",
            "description": prompt,
            "acceptance_criteria": [
                "The requested change is implemented.",
                "Existing functionality is preserved.",
                "Repository tests are executed.",
            ],
            "relevant_files": matching_files,
        }
    ]


async def create_plan(
    mission: dict,
    repository_files: list[str],
) -> list[dict]:

    add_log(
        mission,
        "Planner",
        "Creating a task plan.",
    )

    user_prompt = f"""
USER REQUEST:
{mission["prompt"]}

REPOSITORY FILES:
{json.dumps(repository_files, indent=2)}

Create a dependency-aware plan.

For a simple request, create exactly one task.
Use only files that exist in the repository.
Return only valid JSON.
"""

    try:
        add_log(
            mission,
            "Planner",
            "Waiting for the AI Planner.",
        )

        response = await asyncio.wait_for(
            ask_ai(
                PLANNER_PROMPT,
                user_prompt,
            ),
            timeout=30,
        )

        plan = parse_plan_response(response)

        if not isinstance(plan, dict):
            raise ValueError(
                "The Planner response must be a JSON object."
            )

        tasks = plan.get("tasks")

        if not isinstance(tasks, list) or not tasks:
            raise ValueError(
                "The Planner returned no tasks."
            )

        for task in tasks:

            if not isinstance(task, dict):
                raise ValueError(
                    "A task must be a JSON object."
                )

            required = {
                "id",
                "title",
                "description",
                "acceptance_criteria",
            }

            if not required.issubset(task):
                raise ValueError(
                    "A task is missing required fields."
                )

            if not isinstance(
                task["acceptance_criteria"],
                list,
            ):
                raise ValueError(
                    "Acceptance criteria must be a list."
                )

            if "relevant_files" not in task:
                task["relevant_files"] = []

            # Do not allow the Planner to select files
            # that are not actually in the repository.
            task["relevant_files"] = [
                path
                for path in task["relevant_files"]
                if path in repository_files
            ]

        add_log(
            mission,
            "Planner",
            f"Created {len(tasks)} tasks.",
        )

    except Exception as error:

        add_log(
            mission,
            "Planner",
            f"AI planning failed: {error}",
            level="warning",
        )

        add_log(
            mission,
            "Planner",
            "Using a simple fallback plan.",
            level="warning",
        )

        tasks = create_fallback_plan(
            mission["prompt"],
            repository_files,
        )

    mission["tasks"] = tasks

    add_log(
        mission,
        "Planner",
        f"Plan ready with {len(tasks)} task(s).",
    )

    return tasks


async def process_task(
    mission: dict,
    root: str,
    task: dict,
) -> dict:

    add_log(
        mission,
        "Builder",
        f"Starting task {task['id']}: {task['title']}",
    )

    mission["current_task"] = task["id"]

    relevant_files = task.get(
        "relevant_files",
        [],
    )

    if not relevant_files:
        relevant_files = list_files(root)

    task_results = []

    for relative_path in relevant_files:

        try:
            original_content = read_file(
                root,
                relative_path,
            )

        except (
            FileNotFoundError,
            IsADirectoryError,
        ):
            continue

        add_log(
            mission,
            "Dynamic Agent",
            f"Analyzing {relative_path}.",
        )

        updated_content = await edit_code(
            task,
            relative_path,
            original_content,
        )

        if not updated_content.strip():

            add_log(
                mission,
                "Dynamic Agent",
                f"Empty response for {relative_path}.",
                level="warning",
            )

            continue

        if (
            updated_content.strip()
            == original_content.strip()
        ):

            add_log(
                mission,
                "Dynamic Agent",
                f"No change proposed for {relative_path}.",
            )

            continue

        write_file(
            root,
            relative_path,
            updated_content,
        )

        if (
            relative_path
            not in mission["files_changed"]
        ):
            mission["files_changed"].append(
                relative_path
            )

        add_log(
            mission,
            "Builder",
            f"Updated {relative_path}.",
        )

        task_results.append(relative_path)

    if not task_results:

        add_log(
            mission,
            "Builder",
            "No files were changed for this task.",
            level="warning",
        )

    add_log(
        mission,
        "Tester",
        "Running repository tests.",
    )

    test_result = run_tests(root)

    mission["test_results"].append(
        {
            "task_id": task["id"],
            **test_result,
        }
    )

    add_log(
        mission,
        "Tester",
        (
            "Tests passed."
            if test_result["passed"]
            else "Tests failed."
        ),
        level=(
            "info"
            if test_result["passed"]
            else "error"
        ),
    )

    test_report = await review_test_results(
        task,
        test_result["output"],
    )

    add_log(
        mission,
        "Tester",
        test_report,
    )

    if not test_result["passed"]:

        mission["repair_attempts"] += 1

        add_log(
            mission,
            "Dynamic Agent",
            "Tests failed. A repair is needed.",
            level="warning",
        )

    for relative_path in task_results:

        updated_content = read_file(
            root,
            relative_path,
        )

        review = await review_code(
            task,
            relative_path,
            updated_content,
            test_result["output"],
        )

        add_log(
            mission,
            "Reviewer",
            review,
        )

    return {
        "task_id": task["id"],
        "passed": test_result["passed"],
        "files_changed": task_results,
        "test_output": test_result["output"],
        "tester_report": test_report,
    }


async def run_mission(
    mission: dict,
    root: str,
) -> dict:

    update_status(
        mission,
        "running",
    )

    try:

        add_log(
            mission,
            "Repository Scout",
            "Inspecting the repository.",
        )

        scout = scout_repository(root)

        add_log(
            mission,
            "Repository Scout",
            (
                f"Found {scout['file_count']} files "
                f"and {scout['test_count']} test files."
            ),
        )

        tasks = await create_plan(
            mission,
            scout["files"],
        )

        results = []

        for task in tasks:

            result = await process_task(
                mission,
                root,
                task,
            )

            results.append(result)

        update_status(
            mission,
            "completed",
        )

        mission["final_report"] = {
            "tasks_completed": len(results),
            "tasks_passed": sum(
                1
                for result in results
                if result["passed"]
            ),
            "files_changed": mission["files_changed"],
            "results": results,
        }

        add_log(
            mission,
            "Builder",
            "Mission completed.",
        )

        return mission

    except Exception as error:

        update_status(
            mission,
            "failed",
        )

        mission["error"] = str(error)

        add_log(
            mission,
            "Orchestrator",
            f"Mission failed: {error}",
            level="error",
        )

        raise