from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/health", tags=["Health"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def health_page(request: Request, user: dict = Depends(get_current_user)):
    summary = phenom.health_tracker.get_summary()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("health_.html", {"request": request, "user": user, "summary": summary})

@router.post("/api/weight")
async def add_weight(request: Request):
    data = await request.json()
    entry = phenom.health_tracker.add_weight_entry(
        data.get("weight"),
        unit=data.get("unit", "kg")
    )
    return entry

@router.get("/api/summary")
async def get_summary():
    return phenom.health_tracker.get_summary()
