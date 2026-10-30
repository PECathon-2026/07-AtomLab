# DevPilot — Autonomous Code-Change Workspace

**DevPilot** is an AI-powered autonomous development system designed to transform natural-language instructions into validated code changes.

Instead of treating a prompt as one large task, DevPilot decomposes it into smaller, domain-specific tasks, processes them through a dynamic agent pipeline, and validates every change through iterative testing and cross-task consistency checks.

The goal is to create a system that can **understand, modify, test, review, and integrate code changes autonomously** while maintaining the correctness and compatibility of the existing codebase.

---

## Overview

Developers often need to make multiple changes across a codebase. These changes may involve different domains, such as:

- Algorithm implementation
- Code optimization
- UI and styling modifications
- Configuration updates
- Bug fixing
- Code review

When these tasks are handled independently, changes may conflict with one another.

DevPilot addresses this problem through a structured workflow involving task decomposition, dynamic agent execution, testing, feedback-driven correction, and cross-task validation.

## Architecture

The DevPilot workflow consists of the following major stages:

1. User Input
2. Prompt Parser
3. Domain Queue
4. Dynamic Agent Pipeline
5. Iterative Testing and Feedback
6. Cross-Task Consistency Review
7. Final Code Integration

### Workflow Diagram

![DevPilot Workflow Architecture](DevPilot_Workflow_Architecture.png)

---

## How It Works

### 1. User Input

The user provides:

- A natural-language prompt describing the required changes.
- The source code files that need to be modified.

For example:

> Implement an algorithm to find the maximum height in the heights array, optimize its time complexity, and change the homepage color to red.

DevPilot processes the request as a sequence of related development tasks.

### 2. Prompt Parser

The Prompt Parser analyzes the input prompt and decomposes it into smaller task units, referred to as **task tokens**.

Each token represents an individual development objective.

For the example above, the parser identifies:

| Task Token | Objective |
|---|---|
| Task 1 | Implement the maximum-height algorithm |
| Task 2 | Change the homepage color to red |
| Task 3 | Optimize the algorithm's time complexity |

The parser then organizes these tasks according to their dependencies and execution priority.

### 3. Domain Queue

The extracted tasks are placed into a prioritized **Domain Queue**.

The queue determines the order in which tasks are executed.

For example:

```text
Domain Queue: [Task 1, Task 3, Task 2]
```

This ordering ensures that the algorithm is implemented before it is optimized, while the UI modification is processed afterward.

The queue follows a FIFO execution strategy once the task order has been established.

### 4. Dynamic Agent Pipeline

The core of DevPilot is its dynamic agent pipeline, consisting of three components:

| Component | Responsibility |
|---|---|
| Builder | Manages the working code files and integrates validated changes |
| Dynamic Agent | Performs the required code modifications based on the current task |
| Tester | Validates the changes and checks compatibility with previously completed tasks |

These components receive the context of the current task.

The Dynamic Agent is not restricted to a single development role. Its behavior adapts to the task requirements, allowing it to perform operations such as:

- Writing algorithms
- Optimizing existing code
- Modifying CSS and UI components
- Editing configuration files
- Implementing bug fixes

This allows the same pipeline to handle different development domains without requiring a separate fixed agent for every task type.

### 5. Iterative Testing and Feedback

After the Dynamic Agent modifies the code, the changes are passed to the Tester.

The Tester executes task-specific validation and checks whether the requirements have been satisfied.

If a test fails:

1. The Tester identifies the issue.
2. A feedback description is generated.
3. The feedback is passed back to the Dynamic Agent.
4. The Dynamic Agent corrects the code.
5. The Tester executes the tests again.

This feedback loop continues until the task satisfies the required validation criteria.

```text
Dynamic Agent
      |
      v
   Modified Code
      |
      v
     Tester
      |
      +---- Tests Failed ----> Feedback
      |                          |
      |                          v
      |                    Dynamic Agent
      |
      +---- Tests Passed ----> Builder
```

### 6. Cross-Task Consistency Review

One of DevPilot's key architectural features is its persistent Tester context.

While the Builder and Dynamic Agent refresh their task-specific context after each validated task, the Tester retains information about previously completed tasks.

For example:

```text
After Task 1:
Tester Context = [Task 1]

After Task 3:
Tester Context = [Task 1, Task 3]

After Task 2:
Tester Context = [Task 1, Task 3, Task 2]
```

When a new task is completed, the Tester validates it against the previously completed tasks.

This review checks for:

- Conflicting code modifications
- Incompatible implementations
- Broken dependencies
- Contradictory requirements
- Loss of functionality from earlier tasks

If a conflict is detected, the Tester sends corrective feedback to the Dynamic Agent.

The code is modified and tested again until the new task is compatible with the existing validated changes.

This ensures that the system does not simply validate each task independently, but also considers how the tasks work together.

### 7. Builder Integration

Once a task passes both individual validation and cross-task consistency checks, the Builder integrates the validated changes into the working codebase.

After integration:

- The Builder refreshes its task-specific context.
- The Dynamic Agent resets its task-specific context.
- The Tester retains the completed task's validation context.
- The Domain Queue advances to the next task.

This process repeats until all queued tasks have been processed.

### 8. Final Output

After every task has been completed and validated, DevPilot produces the final integrated code files.

The output contains the updated codebase with all requested changes applied.

The final result is designed to satisfy both:

- Individual task requirements
- Cross-task compatibility and consistency requirements

---

## Key Features

### Dynamic Task-Based Agents
Agents adapt their roles according to the current development task rather than being restricted to fixed programming domains.

### Task Decomposition
Large development requests are divided into smaller, manageable tasks.

### Feedback-Driven Correction
Failed tests generate feedback that guides the Dynamic Agent toward corrective changes.

### Persistent Tester Context
The Tester retains knowledge of previously validated tasks.

### Cross-Task Validation
New changes are checked against earlier changes to identify potential conflicts.

### Incremental Code Integration
Validated changes are integrated into the working codebase task by task.

### Local-First Development
DevPilot is designed around a local development workflow using a locally hosted language model.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend implementation |
| FastAPI | API and backend framework |
| HTML | Frontend structure |
| CSS | User interface styling |
| JavaScript | Frontend interaction |
| Ollama | Local language model runtime |
| Qwen2.5-Coder 7B | Code generation and modification model |

---

## Project Structure

```text
devpilot/
│
├── app.py
│
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── .venv/
│
└── README.md
```

---

## Getting Started

### Prerequisites

Make sure the following are installed:

- Python 3.10 or later
- Git
- Ollama
- Qwen2.5-Coder 7B model

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/devpilot.git
cd devpilot
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Environment

For Git Bash:

```bash
source .venv/Scripts/activate
```

For Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install fastapi uvicorn python-multipart
```

### 5. Install and Run the Model

Install Ollama from:

https://ollama.com

Pull the model:

```bash
ollama pull qwen2.5-coder:7b
```

Make sure Ollama is running locally.

### 6. Start DevPilot

```bash
uvicorn app:app --reload
```

### 7. Open the Application

Navigate to:

```text
http://127.0.0.1:8000
```

---

## Example Use Case

Consider the following development request:

> Implement a maximum-height algorithm, optimize its time complexity, and change the homepage background color to red.

DevPilot processes the request as follows:

```text
User Prompt + Code Files
          |
          v
     Prompt Parser
          |
          v
    Domain Queue
          |
          v
   Task 1: Implement Algorithm
          |
          v
   Dynamic Agent -> Tester
          |
          v
     Task 1 Validated
          |
          v
   Task 3: Optimize Algorithm
          |
          v
   Dynamic Agent -> Tester
          |
          v
 Cross-Task Consistency Check
          |
          v
     Task 3 Validated
          |
          v
    Task 2: Modify UI
          |
          v
   Dynamic Agent -> Tester
          |
          v
 Cross-Task Consistency Check
          |
          v
    Final Integration
          |
          v
   Updated Code Files
```

---

## Future Improvements

Potential future improvements include:

- More advanced dependency-aware task scheduling
- Parallel execution of independent tasks
- Improved automated test generation
- Better error classification and feedback generation
- Support for larger codebases
- Enhanced repository-level code understanding
- More robust rollback and recovery mechanisms
- Improved validation across multiple programming languages

---

## Project Objective

DevPilot aims to move beyond simple AI code generation by introducing a structured, iterative, and validation-driven approach to autonomous software development.

By combining task decomposition, dynamic agent behavior, feedback-based testing, and persistent cross-task review, DevPilot seeks to make autonomous code modification more reliable, consistent, and practical.

---

## Author

**Naitik Bansal**

BE — Artificial Intelligence & Machine Learning

---

## License

This project is currently under development.

A license can be added when the project is ready for public distribution.
