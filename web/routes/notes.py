from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/notes", tags=["Notes"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def notes_page(request: Request, user: dict = Depends(get_current_user)):
    notes = phenom.notes_manager.get_all_notes()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("notes_.html", {"request": request, "user": user, "notes": notes})

@router.post("/api/add")
async def add_note(request: Request):
    data = await request.json()
    note = phenom.notes_manager.add_note(
        data.get("title"),
        data.get("content"),
        tags=data.get("tags", [])
    )
    return note

@router.get("/api/all")
async def get_notes():
    return phenom.notes_manager.get_all_notes()

@router.delete("/api/{note_id}")
async def delete_note(note_id: str):
    success = phenom.notes_manager.delete_note(note_id)
    return {"success": success}
