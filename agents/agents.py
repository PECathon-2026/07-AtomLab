
import httpx


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5-coder:7b"


async def ask_ai(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0,
) -> str:
    data = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            OLLAMA_URL,
            json=data,
        )

    response.raise_for_status()

    result = response.json()

    return result["message"]["content"]


async def edit_code(
    task: dict,
    file_path: str,
    file_content: str,
) -> str:
    system_prompt = """
You are DevPilot's Dynamic Coding Agent.

You receive one coding task and the current contents of one file.

Your job is to make the requested change while preserving
the existing code style and unrelated functionality.

Rules:
- Return the COMPLETE updated file.
- Do not use Markdown code fences.
- Do not explain your answer.
- Do not omit existing code.
- Do not invent requirements.
- If the task does not require changing this file,
  return the original file unchanged.
"""

    user_prompt = f"""
TASK:
{task["title"]}

DESCRIPTION:
{task["description"]}

ACCEPTANCE CRITERIA:
{task["acceptance_criteria"]}

FILE:
{file_path}

CURRENT FILE CONTENTS:
{file_content}

Return the complete updated file.
"""

    return await ask_ai(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


async def review_test_results(
    task: dict,
    test_output: str,
) -> str:
    system_prompt = """
You are DevPilot's Tester Agent.

Analyze the actual output from the repository's tests.

Determine whether the task's acceptance criteria appear
to be satisfied.

Rules:
- Use only the evidence in the test output.
- Do not claim tests passed if they failed.
- Identify relevant failures clearly.
- If the output is empty or inconclusive, say so.
- Return a concise report.
"""

    user_prompt = f"""
TASK:
{task["title"]}

DESCRIPTION:
{task["description"]}

ACCEPTANCE CRITERIA:
{task["acceptance_criteria"]}

ACTUAL TEST OUTPUT:
{test_output}

Analyze the test results.
"""

    return await ask_ai(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


async def review_code(
    task: dict,
    file_path: str,
    file_content: str,
    test_output: str,
) -> str:
    system_prompt = """
You are DevPilot's independent Code Reviewer.

Review the updated code for:
- Correctness
- Readability
- Consistency with existing code
- Possible regressions
- Security problems
- Whether the task's acceptance criteria are satisfied

Rules:
- Do not modify the code.
- Do not claim a test passed unless the test output supports it.
- Focus on concrete findings.
- Separate confirmed problems from possible concerns.
- If you find no issues, say so.
- Return a concise review.
"""

    user_prompt = f"""
TASK:
{task["title"]}

DESCRIPTION:
{task["description"]}

ACCEPTANCE CRITERIA:
{task["acceptance_criteria"]}

FILE:
{file_path}

UPDATED CODE:
{file_content}

TEST OUTPUT:
{test_output}

Review this change.
"""

    return await ask_ai(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
