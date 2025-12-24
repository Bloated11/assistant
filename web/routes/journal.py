from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/journal", tags=["Journal"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def journal_page(request: Request, user: dict = Depends(get_current_user)):
    entries = phenom.journal.get_recent_entries()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("journal_.html", {"request": request, "user": user, "entries": entries})

@router.post("/api/add")
async def add_entry(request: Request):
    data = await request.json()
    entry = phenom.journal.add_entry(data.get("content"), mood=data.get("mood"))
    return entry

@router.get("/api/all")
async def get_entries():
    return phenom.journal.get_recent_entries()
