from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/reminders", tags=["Reminders"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def reminders_page(request: Request, user: dict = Depends(get_current_user)):
    reminders = phenom.reminder_system.get_all_reminders()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("reminders_.html", {"request": request, "user": user, "reminders": reminders})

@router.post("/api/add")
async def add_reminder(request: Request):
    data = await request.json()
    reminder = phenom.reminder_system.add_reminder(data.get("title"), data.get("time"))
    return reminder

@router.get("/api/all")
async def get_reminders():
    return phenom.reminder_system.get_all_reminders()
