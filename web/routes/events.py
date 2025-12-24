from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/events", tags=["Events"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def events_page(request: Request, user: dict = Depends(get_current_user)):
    events = phenom.event_tracker.get_all_events()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("events_.html", {"request": request, "user": user, "events": events})

@router.post("/api/add")
async def add_event(request: Request):
    data = await request.json()
    event = phenom.event_tracker.add_event(data.get("title"), data.get("date"))
    return event

@router.get("/api/all")
async def get_events():
    return phenom.event_tracker.get_all_events()
