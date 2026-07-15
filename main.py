"""
Task API — a small in-memory CRUD API built with FastAPI.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Then open:
    http://localhost:8000/          -> API info
    http://localhost:8000/health    -> health check
    http://localhost:8000/docs      -> Swagger UI
"""

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A tiny in-memory CRUD API for managing a to-do list.",
)

# ---------------------------------------------------------------------------
# In-memory "database" — just a Python list. Data is lost on restart.
# This is intentional for Week 2 (databases arrive Week 3).
# ---------------------------------------------------------------------------

DEFAULT_TASKS = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Read FastAPI docs", "done": True},
    {"id": 3, "title": "Push code to GitHub", "done": False},
]

tasks: List[dict] = [t.copy() for t in DEFAULT_TASKS]
next_id = 4


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str = Field(..., description="Title of the task")


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


# ---------------------------------------------------------------------------
# Stage 1 — root & health
# ---------------------------------------------------------------------------

@app.get("/", summary="API info")
def root():
    """Basic info about this API and its endpoints."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks", "/tasks/{id}", "/health", "/stats"],
    }


@app.get("/health", summary="Health check")
def health():
    """Used to check the server is alive."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Stage 2 — Read
# ---------------------------------------------------------------------------

@app.get("/tasks", summary="List tasks (optionally filter/search)")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    """
    List all tasks.

    Optional query params (extras):
    - done: filter by completion status, e.g. /tasks?done=true
    - search: filter by title containing text, e.g. /tasks?search=milk
    """
    result = tasks

    if done is not None:
        result = [t for t in result if t["done"] == done]

    if search is not None:
        result = [t for t in result if search.lower() in t["title"].lower()]

    return result


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    for t in tasks:
        if t["id"] == task_id:
            return t
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---------------------------------------------------------------------------
# Stage 3 — Create
# ---------------------------------------------------------------------------

@app.post("/tasks", status_code=201, summary="Create a task")
def create_task(payload: dict = Body(...)):
    title = payload.get("title")

    if not title or not isinstance(title, str) or not title.strip():
        raise HTTPException(
            status_code=400,
            detail="Field 'title' is required and cannot be empty",
        )

    global next_id
    new_task = {"id": next_id, "title": title.strip(), "done": False}
    tasks.append(new_task)
    next_id += 1

    return new_task


# ---------------------------------------------------------------------------
# Stage 4 — Update & Delete
# ---------------------------------------------------------------------------

@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, payload: dict = Body(...)):
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if not payload or ("title" not in payload and "done" not in payload):
        raise HTTPException(
            status_code=400,
            detail="Request body must include 'title' and/or 'done'",
        )

    if "title" in payload:
        title = payload["title"]
        if not title or not isinstance(title, str) or not title.strip():
            raise HTTPException(
                status_code=400, detail="Field 'title' cannot be empty"
            )
        task["title"] = title.strip()

    if "done" in payload:
        if not isinstance(payload["done"], bool):
            raise HTTPException(
                status_code=400, detail="Field 'done' must be true or false"
            )
        task["done"] = payload["done"]

    return task


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


# ---------------------------------------------------------------------------
# ★ Extras (optional but included — easy wins)
# ---------------------------------------------------------------------------

@app.get("/stats", summary="Task statistics")
def stats():
    total = len(tasks)
    done = len([t for t in tasks if t["done"]])
    return {"total": total, "done": done, "open": total - done}


@app.post("/reset", summary="Reset to the 3 example tasks")
def reset():
    global tasks, next_id
    tasks = [t.copy() for t in DEFAULT_TASKS]
    next_id = 4
    return {"message": "Tasks reset to defaults", "tasks": tasks}