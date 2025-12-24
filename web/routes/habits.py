from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/habits", tags=["Habits"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def habits_page(request: Request, user: dict = Depends(get_current_user)):
    habits = phenom.habit_tracker.get_all_habits()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("habits_.html", {"request": request, "user": user, "habits": habits})

@router.post("/api/add")
async def add_habit(request: Request):
    data = await request.json()
    habit = phenom.habit_tracker.add_habit(
        data.get("name"),
        frequency=data.get("frequency", "daily")
    )
    return habit

@router.post("/api/log/{habit_id}")
async def log_habit(habit_id: str):
    success = phenom.habit_tracker.log_habit(habit_id)
    return {"success": success}

@router.get("/api/all")
async def get_habits():
    return phenom.habit_tracker.get_all_habits()

@router.get("/api/stats/{habit_id}")
async def get_stats(habit_id: str):
    return phenom.habit_tracker.get_stats(habit_id)

@router.delete("/api/{habit_id}")
async def delete_habit(habit_id: str):
    success = phenom.habit_tracker.delete_habit(habit_id)
    return {"success": success}
