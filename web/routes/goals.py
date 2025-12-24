from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/goals", tags=["Goals"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def goals_page(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("goals_.html", {"request": request, "user": user})

@router.post("/api/add")
async def add_goal(request: Request):
    data = await request.json()
    goal = phenom.goal_tracker.add_goal(
        data.get("title"),
        description=data.get("description", ""),
        target_date=data.get("target_date")
    )
    return goal

@router.post("/api/progress/{goal_id}")
async def update_progress(goal_id: str, request: Request):
    data = await request.json()
    result = phenom.goal_tracker.update_progress(
        goal_id,
        progress=data.get("progress")
    )
    return {"success": result}

@router.get("/api/all")
async def get_goals():
    goals_list = phenom.goal_tracker.get_all_goals()
    goals_dict = {g['id']: g for g in goals_list}
    return {"goals": goals_dict}

@router.delete("/api/{goal_id}")
async def delete_goal(goal_id: str):
    success = phenom.goal_tracker.remove_goal(goal_id)
    return {"success": success}
