from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/archive", tags=["Archive"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def archive_page(request: Request, user: dict = Depends(get_current_user)):
    items = phenom.archive_manager.get_all_documents()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("archive_.html", {"request": request, "user": user, "items": items})

@router.post("/api/add")
async def add_item(request: Request):
    data = await request.json()
    item = phenom.archive_manager.add_item(data.get("title"), data.get("content"))
    return item

@router.get("/api/all")
async def get_items():
    return phenom.archive_manager.get_all_documents()
