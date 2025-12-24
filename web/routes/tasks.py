from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def tasks_page(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("tasks_.html", {"request": request, "user": user})

@router.post("/api/add")
async def add_task(request: Request):
    data = await request.json()
    task = phenom.tasks.add_task(
        data.get("title"),
        priority=data.get("priority", "medium"),
        due_date=data.get("due_date")
    )
    return task

@router.post("/api/complete")
async def complete_task(request: Request):
    data = await request.json()
    task_id = int(data.get("task_id"))
    success = phenom.tasks.complete_task(task_id)
    return {"success": success}

@router.post("/api/delete")
async def delete_task(request: Request):
    data = await request.json()
    task_id = int(data.get("task_id"))
    success = phenom.tasks.delete_task(task_id)
    return {"success": success}

@router.get("/api/all")
async def get_tasks():
    tasks = phenom.tasks.get_all_tasks()
    for task in tasks:
        task["completed"] = task["status"] == "completed"
    return tasks
