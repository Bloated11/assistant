from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def contacts_page(request: Request, user: dict = Depends(get_current_user)):
    contacts = phenom.contact_manager.get_all_contacts()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("contacts_.html", {"request": request, "user": user, "contacts": contacts})

@router.post("/api/add")
async def add_contact(request: Request):
    data = await request.json()
    contact = phenom.contact_manager.add_contact(data.get("name"), email=data.get("email"), phone=data.get("phone"))
    return contact

@router.get("/api/all")
async def get_contacts():
    return phenom.contact_manager.get_all_contacts()
