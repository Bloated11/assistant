from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/quotes", tags=["Quotes"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def quotes_page(request: Request, user: dict = Depends(get_current_user)):
    quotes = phenom.quote_collection.get_all_quotes()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("quotes_.html", {"request": request, "user": user, "quotes": quotes})

@router.post("/api/add")
async def add_quote(request: Request):
    data = await request.json()
    quote = phenom.quote_collection.add_quote(data.get("text"), data.get("author"))
    return quote

@router.get("/api/all")
async def get_quotes():
    return phenom.quote_collection.get_all_quotes()

@router.get("/api/random")
async def get_random():
    return phenom.quote_collection.get_random_quote()
