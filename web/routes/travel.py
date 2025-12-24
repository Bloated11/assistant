from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/travel", tags=["Travel"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def travel_page(request: Request, user: dict = Depends(get_current_user)):
    trips = phenom.travel_planner.get_all_trips()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("travel_.html", {"request": request, "user": user, "trips": trips})

@router.post("/api/add")
async def add_trip(request: Request):
    data = await request.json()
    trip = phenom.travel_planner.add_trip(data.get("destination"), data.get("start_date"), data.get("end_date"))
    return trip

@router.get("/api/all")
async def get_trips():
    return phenom.travel_planner.get_all_trips()
