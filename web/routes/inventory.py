from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def inventory_page(request: Request, user: dict = Depends(get_current_user)):
    items = phenom.inventory_manager.get_all_items()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("inventory_.html", {"request": request, "user": user, "items": items})

@router.post("/api/add")
async def add_item(request: Request):
    data = await request.json()
    item = phenom.inventory_manager.add_item(data.get("name"), data.get("quantity", 1))
    return item

@router.get("/api/all")
async def get_items():
    return phenom.inventory_manager.get_all_items()
