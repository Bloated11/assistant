from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/time", tags=["Time"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def time_page(request: Request, user: dict = Depends(get_current_user)):
    summary = phenom.time_tracker.get_time_summary()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("time_.html", {"request": request, "user": user, "summary": summary})

@router.post("/api/start")
async def start_tracking(request: Request):
    data = await request.json()
    result = phenom.time_tracker.start_tracking(data.get("activity"))
    return result

@router.post("/api/stop")
async def stop_tracking():
    result = phenom.time_tracker.stop_tracking()
    return result

@router.get("/api/summary")
async def get_time_summary():
    return phenom.time_tracker.get_time_summary()
