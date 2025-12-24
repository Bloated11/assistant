from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/reading", tags=["Reading"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def reading_page(request: Request, user: dict = Depends(get_current_user)):
    books = phenom.reading_list.get_all_books()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("reading_.html", {"request": request, "user": user, "books": books})

@router.post("/api/add")
async def add_book(request: Request):
    data = await request.json()
    book = phenom.reading_list.add_book(data.get("title"), data.get("author"))
    return book

@router.get("/api/all")
async def get_books():
    return phenom.reading_list.get_all_books()
