from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/finance", tags=["Finance"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def finance_page(request: Request, user: dict = Depends(get_current_user)):
    summary = phenom.finance_tracker.get_summary()
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("finance_.html", {"request": request, "user": user, "summary": summary})

@router.post("/api/transaction")
async def add_transaction(request: Request):
    data = await request.json()
    transaction = phenom.finance_tracker.add_transaction(
        data.get("type"),
        data.get("amount"),
        data.get("category"),
        description=data.get("description", "")
    )
    return transaction

@router.get("/api/summary")
async def get_summary():
    return phenom.finance_tracker.get_summary()

@router.get("/api/transactions")
async def get_transactions():
    return phenom.finance_tracker.get_all_transactions()
