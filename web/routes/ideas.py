from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/ideas", tags=["Ideas"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def ideas_page(request: Request, user: dict = Depends(get_current_user)):
    ideas = phenom.idea_tracker.get_all_ideas()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("ideas_.html", {"request": request, "user": user, "ideas": ideas})

@router.post("/api/add")
async def add_idea(request: Request):
    data = await request.json()
    idea = phenom.idea_tracker.add_idea(data.get("title"), data.get("description"))
    return idea

@router.get("/api/all")
async def get_ideas():
    return phenom.idea_tracker.get_all_ideas()
